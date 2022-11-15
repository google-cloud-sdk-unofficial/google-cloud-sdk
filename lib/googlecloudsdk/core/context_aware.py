# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Helper module for context aware access."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import atexit
import enum
import os

from google.auth import exceptions as google_auth_exceptions
from google.auth.transport import _mtls_helper
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files

import six


CONTEXT_AWARE_ACCESS_DENIED_ERROR = 'access_denied'
CONTEXT_AWARE_ACCESS_DENIED_ERROR_DESCRIPTION = 'Account restricted'
CONTEXT_AWARE_ACCESS_HELP_MSG = (
    'Access was blocked due to an organization policy, please contact your '
    'admin to gain access.'
)


def IsContextAwareAccessDeniedError(exc):
  exc_text = six.text_type(exc)
  return (CONTEXT_AWARE_ACCESS_DENIED_ERROR in exc_text and
          CONTEXT_AWARE_ACCESS_DENIED_ERROR_DESCRIPTION in exc_text)


DEFAULT_AUTO_DISCOVERY_FILE_PATH = os.path.join(
    files.GetHomeDir(), '.secureConnect', 'context_aware_metadata.json')


def _AutoDiscoveryFilePath():
  """Return the file path of the context aware configuration file."""
  # auto_discovery_file_path is an override used for testing purposes.
  cfg_file = properties.VALUES.context_aware.auto_discovery_file_path.Get()
  if cfg_file is not None:
    return cfg_file
  return DEFAULT_AUTO_DISCOVERY_FILE_PATH


class ConfigException(exceptions.Error):

  def __init__(self):
    super(ConfigException, self).__init__(
        'Use of client certificate requires endpoint verification agent. '
        'Run `gcloud topic client-certificate` for installation guide.')


class CertProvisionException(exceptions.Error):
  """Represents errors when provisioning a client certificate."""
  pass


def SSLCredentials(config_path):
  """Generates the client SSL credentials.

  Args:
    config_path: path to the context aware configuration file.

  Raises:
    CertProvisionException: if the cert could not be provisioned.
    ConfigException: if there is an issue in the context aware config.

  Returns:
    Tuple[bytes, bytes]: client certificate and private key bytes in PEM format.
  """
  try:
    (
        has_cert,
        cert_bytes,
        key_bytes,
        _
    ) = _mtls_helper.get_client_ssl_credentials(
        generate_encrypted_key=False,
        context_aware_metadata_path=config_path)
    if has_cert:
      return cert_bytes, key_bytes
  except google_auth_exceptions.ClientCertError as caught_exc:
    new_exc = CertProvisionException(caught_exc)
    six.raise_from(new_exc, caught_exc)
  raise ConfigException()


def EncryptedSSLCredentials(config_path):
  """Generates the encrypted client SSL credentials.

  The encrypted client SSL credentials are stored in a file which is returned
  along with the password.

  Args:
    config_path: path to the context aware configuration file.

  Raises:
    CertProvisionException: if the cert could not be provisioned.
    ConfigException: if there is an issue in the context aware config.

  Returns:
    Tuple[str, bytes]: cert and key file path and passphrase bytes.
  """
  try:
    (
        has_cert,
        cert_bytes,
        key_bytes,
        passphrase_bytes
    ) = _mtls_helper.get_client_ssl_credentials(
        generate_encrypted_key=True,
        context_aware_metadata_path=config_path)
    if has_cert:
      cert_path = os.path.join(
          config.Paths().global_config_dir, 'caa_cert.pem')
      with files.BinaryFileWriter(cert_path) as f:
        f.write(cert_bytes)
        f.write(key_bytes)
      return cert_path, passphrase_bytes
  except google_auth_exceptions.ClientCertError as caught_exc:
    new_exc = CertProvisionException(caught_exc)
    six.raise_from(new_exc, caught_exc)
  except files.Error as e:
    log.debug('context aware settings discovery file %s - %s', config_path, e)

  raise ConfigException()


class ConfigType(enum.Enum):
  ENTERPRISE_CERTIFICATE = 1
  ON_DISK_CERTIFICATE = 2


class _ConfigImpl(object):
  """Represents the configurations associated with context aware access.

  Both the encrypted and unencrypted certs need to be generated to support HTTP
  API clients and gRPC API clients, respectively.

  Only one instance of Config can be created for the program.
  """

  @classmethod
  def Load(cls):
    """Loads the context aware config."""
    if not properties.VALUES.context_aware.use_client_certificate.GetBool():
      return None

    certificate_config_file_path = properties.VALUES.context_aware.certificate_config_file_path.Get(
    )
    if certificate_config_file_path is None:
      certificate_config_file_path = config.CertConfigDefaultFilePath(
      )
    if certificate_config_file_path is not None:
      # The enterprise cert config file path will be used.
      return _EnterpriseCertConfigImpl(certificate_config_file_path)

    config_path = _AutoDiscoveryFilePath()
    # Raw cert and key
    cert_bytes, key_bytes = SSLCredentials(config_path)

    # Encrypted cert stored in a file
    encrypted_cert_path, password = EncryptedSSLCredentials(config_path)
    return _OnDiskCertConfigImpl(config_path, cert_bytes, key_bytes,
                                 encrypted_cert_path, password)

  def __init__(self, config_type):
    self.config_type = config_type


class _EnterpriseCertConfigImpl(_ConfigImpl):
  """Represents the configurations associated with context aware access through a enterprise certificate on TPM or OS key store."""

  def __init__(self, certificate_config_file_path):
    super(_EnterpriseCertConfigImpl,
          self).__init__(ConfigType.ENTERPRISE_CERTIFICATE)
    self.certificate_config_file_path = certificate_config_file_path


class _OnDiskCertConfigImpl(_ConfigImpl):
  """Represents the configurations associated with context aware access through a certificate on disk.

  Both the encrypted and unencrypted certs need to be generated to support HTTP
  API clients and gRPC API clients, respectively.

  Only one instance of Config can be created for the program.
  """

  def __init__(self, config_path, client_cert_bytes, client_key_bytes,
               encrypted_client_cert_path, encrypted_client_cert_password):
    super(_OnDiskCertConfigImpl, self).__init__(ConfigType.ON_DISK_CERTIFICATE)
    self.config_path = config_path
    self.client_cert_bytes = client_cert_bytes
    self.client_key_bytes = client_key_bytes
    self.encrypted_client_cert_path = encrypted_client_cert_path
    self.encrypted_client_cert_password = encrypted_client_cert_password
    atexit.register(self.CleanUp)

  def CleanUp(self):
    """Cleanup any files or resource provisioned during config init."""
    if (self.encrypted_client_cert_path is not None and
        os.path.exists(self.encrypted_client_cert_path)):
      try:
        os.remove(self.encrypted_client_cert_path)
        log.debug('unprovisioned client cert - %s',
                  self.encrypted_client_cert_path)
      except files.Error as e:
        log.error('failed to remove client certificate - %s', e)


singleton_config = None


def Config():
  """Represents the configurations associated with context aware access."""
  global singleton_config
  if not singleton_config:
    singleton_config = _ConfigImpl.Load()

  return singleton_config
