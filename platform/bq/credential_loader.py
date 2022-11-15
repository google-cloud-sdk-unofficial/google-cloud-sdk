#!/usr/bin/env python
"""Credential-related classes and functions for bq cli."""
import argparse
import json
import os
import sys

from absl import app
from absl import flags
from google_reauth.reauth_creds import Oauth2WithReauthCredentials
import httplib2
import oauth2client_4_0
import oauth2client_4_0.contrib
import oauth2client_4_0.contrib.gce
import oauth2client_4_0.contrib.multiprocess_file_storage
import oauth2client_4_0.file
import oauth2client_4_0.service_account
import oauth2client_4_0.tools
import requests

import bigquery_client
import bq_auth_flags
import bq_utils
import wrapped_credentials


FLAGS = flags.FLAGS

if os.environ.get('CLOUDSDK_WRAPPER') == '1':
  _CLIENT_ID = '32555940559.apps.googleusercontent.com'
  _CLIENT_SECRET = 'ZmssLNjJy2998hD4CTg2ejr2'
  _CLIENT_USER_AGENT = 'google-cloud-sdk' + os.environ.get(
      'CLOUDSDK_VERSION', bq_utils.VERSION_NUMBER)
else:
  _CLIENT_ID = '977385342095.apps.googleusercontent.com'
  _CLIENT_SECRET = 'wbER7576mc_1YOII0dGk7jEE'
  _CLIENT_USER_AGENT = 'bq/' + bq_utils.VERSION_NUMBER

_CLIENT_INFO = {
    'client_id': _CLIENT_ID,
    'client_secret': _CLIENT_SECRET,
    'user_agent': _CLIENT_USER_AGENT,
}



class CredentialLoader(object):
  """Base class for credential loader."""

  def Load(self):
    """Loads credential."""
    cred = self._Load()
    cred._user_agent = _CLIENT_USER_AGENT  # pylint: disable=protected-access
    return cred

  def _Load(self):
    raise NotImplementedError()


class CachedCredentialLoader(CredentialLoader):
  """Base class to add cache capability to credential loader.

  It will attempt to load credential from local cache file first before calling
  derived class to load credential from source. Once credential is retrieved, it
  will save to local cache file for future use.
  """

  def __init__(self, credential_cache_file, read_cache_first=True):
    """Creates CachedCredentialLoader instance.

    Args:
      credential_cache_file: path to a local file to cache credential.
      read_cache_first: whether to load credential from cache first.

    Raises:
      BigqueryError: if cache file cannot be created to store credential.
    """
    self.credential_cache_file = credential_cache_file
    self._read_cache_first = read_cache_first
    # MultiprocessFileStorage recommends using scopes as the key for single-user
    # credentials storage.
    self._scopes_key = ','.join(sorted(bq_utils.GetClientScopeFromFlags()))
    try:
      self._storage = oauth2client_4_0.contrib.multiprocess_file_storage.MultiprocessFileStorage(
          credential_cache_file, self._scopes_key)
    except OSError as e:
      raise bigquery_client.BigqueryError(
          'Cannot create credential file %s: %s' % (credential_cache_file, e))

  @property
  def storage(self):
    return self._storage

  def Load(self):
    cred = self._LoadFromCache() if self._read_cache_first else None
    if cred:
      return cred

    cred = super(CachedCredentialLoader, self).Load()
    if not cred:
      return None

    # Save credentials to storage now to reuse and also avoid a warning message.
    self._storage.put(cred)

    cred.set_store(self._storage)
    return cred

  def _LoadFromCache(self):
    """Loads credential from cache file."""
    if not os.path.exists(self.credential_cache_file):
      return None

    try:
      creds = self._storage.get()

      if not creds:
        legacy_storage = oauth2client_4_0.file.Storage(
            self.credential_cache_file)
        creds = legacy_storage.get()
        if creds:
          self._storage.put(creds)

    except BaseException as e:  # pylint: disable=broad-except
      self._RaiseCredentialsCorrupt(e)

    if not creds:
      return None  # Nothing cached.

    scopes = bq_utils.GetClientScopeFromFlags()
    if not creds.has_scopes(scopes):
      # Our cached credentials do not cover the required scopes.
      return None

    return creds

  def _RaiseCredentialsCorrupt(self, e):
    bq_utils.ProcessError(
        e,
        name='GetCredentialsFromFlags',
        message_prefix=(
            'Credentials appear corrupt. Please delete the credential file '
            'and try your command again. You can delete your credential '
            'file using "bq init --delete_credentials".\n\nIf that does '
            'not work, you may have encountered a bug in the BigQuery CLI.'))
    sys.exit(1)


class ServiceAccountPrivateKeyLoader(CachedCredentialLoader):
  """Base class for loading credential from service account."""

  def Load(self):
    if not oauth2client_4_0.client.HAS_OPENSSL:
      raise app.UsageError(
          'BigQuery requires OpenSSL to be installed in order to use '
          'service account credentials. Please install OpenSSL '
          'and the Python OpenSSL package.')
    return super(ServiceAccountPrivateKeyLoader, self).Load()


class ServiceAccountPrivateKeyFileLoader(ServiceAccountPrivateKeyLoader):
  """Credential loader for private key stored in a file."""

  def __init__(self, service_account, file_path, password, *args, **kwargs):
    """Creates ServiceAccountPrivateKeyFileLoader instance.

    Args:
      service_account: service account the private key is for.
      file_path: path to the file containing private key (in P12 format).
      password: password to uncrypt the private key file.
      *args: additional arguments to apply to base class.
      **kwargs: additional keyword arguments to apply to base class.
    """
    super(ServiceAccountPrivateKeyFileLoader, self).__init__(*args, **kwargs)
    self._service_account = service_account
    self._file_path = file_path
    self._password = password

  def _Load(self):
    try:
      return (oauth2client_4_0.service_account.ServiceAccountCredentials
              .from_p12_keyfile(
                  service_account_email=self._service_account,
                  filename=self._file_path,
                  scopes=bq_utils.GetClientScopeFromFlags(),
                  private_key_password=self._password,
                  token_uri=oauth2client_4_0.GOOGLE_TOKEN_URI,
                  revoke_uri=oauth2client_4_0.GOOGLE_REVOKE_URI))
    except IOError as e:
      raise app.UsageError(
          'Service account specified, but private key in file "%s" '
          'cannot be read:\n%s' % (self._file_path, e))




class ApplicationDefaultCredentialFileLoader(CachedCredentialLoader):
  """Credential loader for application default credential file."""

  def __init__(self, credential_file, *args, **kwargs):
    """Creates ApplicationDefaultCredentialFileLoader instance.

    Args:
      credential_file: path to credential file in json format.
      *args: additional arguments to apply to base class.
      **kwargs: additional keyword arguments to apply to base class.
    """
    super(ApplicationDefaultCredentialFileLoader,
          self).__init__(*args, **kwargs)
    self._credential_file = credential_file

  def _Load(self):
    """Loads credentials from given application default credential file."""
    with open(self._credential_file) as file_obj:
      credentials = json.load(file_obj)

    client_scope = bq_utils.GetClientScopeFromFlags()
    if credentials['type'] == oauth2client_4_0.client.AUTHORIZED_USER:
      return Oauth2WithReauthCredentials(
          access_token=None,
          client_id=credentials['client_id'],
          client_secret=credentials['client_secret'],
          refresh_token=credentials['refresh_token'],
          token_expiry=None,
          token_uri=oauth2client_4_0.GOOGLE_TOKEN_URI,
          user_agent=_CLIENT_USER_AGENT,
          scopes=client_scope)
    elif credentials['type'] == 'external_account':
      return wrapped_credentials.WrappedCredentials.for_external_account(
          self._credential_file)
    else:  # Service account
      token_uri = None
      revoke_uri = None
      credentials['type'] = oauth2client_4_0.client.SERVICE_ACCOUNT
      service_account_credentials = (
          oauth2client_4_0.service_account.ServiceAccountCredentials
          .from_json_keyfile_dict(
              keyfile_dict=credentials,
              scopes=client_scope,
              token_uri=token_uri,
              revoke_uri=revoke_uri))
      service_account_credentials._user_agent = _CLIENT_USER_AGENT  # pylint: disable=protected-access
      return service_account_credentials


def _GetCredentialsLoaderFromFlags():
  """Returns a CredentialsLoader based on user-supplied flags."""

  if FLAGS.service_account:
    if not FLAGS.service_account_credential_file:
      raise app.UsageError(
          'The flag --service_account_credential_file must be specified '
          'if --service_account is used.')
    if FLAGS.service_account_private_key_file:
      return ServiceAccountPrivateKeyFileLoader(
          credential_cache_file=FLAGS.service_account_credential_file,
          read_cache_first=True,
          service_account=FLAGS.service_account,
          file_path=FLAGS.service_account_private_key_file,
          password=FLAGS.service_account_private_key_password)
    raise app.UsageError('Service account authorization requires '
                         '--service_account_private_key_file flag to be set.')

  if FLAGS.application_default_credential_file:
    if not FLAGS.credential_file:
      raise app.UsageError('The flag --credential_file must be specified if '
                           '--application_default_credential_file is used.')
    return ApplicationDefaultCredentialFileLoader(
        credential_cache_file=FLAGS.credential_file,
        read_cache_first=True,
        credential_file=FLAGS.application_default_credential_file)
  raise app.UsageError(
      'bq.py should not be invoked. Use bq command instead.')


def GetCredentialsFromFlags():
  """Returns credentials based on user-supplied flags."""


  if FLAGS.use_gce_service_account:
    # In the case of a GCE service account, we can skip the entire
    # process of loading from storage.
    return oauth2client_4_0.contrib.gce.AppAssertionCredentials()


  loader = _GetCredentialsLoaderFromFlags()
  credentials = loader.Load()


  if type(credentials) == oauth2client_4_0.client.OAuth2Credentials:  # pylint: disable=unidiomatic-typecheck
    credentials = _GetReauthCredentials(credentials)

  return credentials


def _GetReauthCredentials(oauth2_creds):
  reauth_creds = Oauth2WithReauthCredentials.from_OAuth2Credentials(
      oauth2_creds)
  reauth_creds.store = oauth2_creds.store
  return reauth_creds
