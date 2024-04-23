#!/usr/bin/env python
"""BigQuery client that exists for some reason."""

import logging
import sys
import textwrap

from absl import app
from absl import flags

import httplib2
import termcolor

import bigquery_client
import bq_auth_flags
import bq_flags
import bq_utils
import credential_loader
from auth import main_credential_loader
from frontend import utils as bq_frontend_utils
from utils import bq_logging


FLAGS = flags.FLAGS
BigqueryClient = bigquery_client.BigqueryClient




def _GetWaitPrinterFactoryFromFlags():
  """Returns the default wait_printer_factory to use while waiting for jobs."""
  if FLAGS.quiet:
    return BigqueryClient.QuietWaitPrinter
  if FLAGS.headless:
    return BigqueryClient.TransitionWaitPrinter
  return BigqueryClient.VerboseWaitPrinter


class Client(object):
  """Class caching bigquery_client.BigqueryClient based on arguments."""
  client_cache = {}

  @staticmethod
  def _CollectArgs(config_logging=True, **kwds):
    """Collect and combine FLAGS and kwds to create BQ Client.

    Args:
      config_logging: if True, set python logging according to --apilog.
      **kwds: keyword arguments for creating BigqueryClient.
    """

    def KwdsOrFlags(name):
      return kwds[name] if name in kwds else getattr(FLAGS, name)

    # Note that we need to handle possible initialization tasks
    # for the case of being loaded as a library.
    bq_utils.ProcessBigqueryrc()
    if config_logging:
      bq_logging.ConfigureLogging(bq_flags.APILOG.value)
    # Gcloud config currently gets processed twice.
    bq_utils.ProcessGcloudConfig(flag_values=FLAGS)

    if (
        bq_flags.UNIVERSE_DOMAIN.present
        and not bq_auth_flags.USE_GOOGLE_AUTH.value
    ):
      raise app.UsageError(
          'Attempting to use TPC without setting `use_google_auth`.')

    if FLAGS.httplib2_debuglevel:
      httplib2.debuglevel = FLAGS.httplib2_debuglevel

    client_args = {}
    global_args = (
        'credential_file',
        'job_property',
        'project_id',
        'dataset_id',
        'trace',
        'sync',
        'use_google_auth',
        'api',
        'api_version',
        'quota_project_id',
    )
    for name in global_args:
      client_args[name] = KwdsOrFlags(name)

    logging.debug('Global args collected: %s', client_args)

    client_args['wait_printer_factory'] = _GetWaitPrinterFactoryFromFlags()
    if FLAGS.discovery_file:
      with open(FLAGS.discovery_file) as f:
        client_args['discovery_document'] = f.read()
    client_args['enable_resumable_uploads'] = (
        True if FLAGS.enable_resumable_uploads is None else
        FLAGS.enable_resumable_uploads)
    if FLAGS.max_rows_per_request:
      client_args['max_rows_per_request'] = FLAGS.max_rows_per_request
    logging.info('Client args collected: %s', client_args)

    return client_args

  @staticmethod
  def Create(config_logging=True, **kwds):
    """Build a new BigqueryClient configured from kwds and FLAGS.

    Args:
      config_logging: if True, set python logging according to --apilog.
      **kwds: keyword arguments for creating BigqueryClient.
    """
    # Resolve flag values first.
    logging.debug('Collecting args before creating a BigqueryClient: %s', kwds)
    client_args = Client._CollectArgs(config_logging, **kwds)

    if 'credentials' in kwds:
      logging.info('Credentials passed in directly')
      credentials = kwds.pop('credentials')
    elif bq_auth_flags.USE_GOOGLE_AUTH.value:
      logging.info('Credentials loaded using Google Auth')
      credentials = main_credential_loader.GetCredentialsFromFlags()
    else:
      logging.info('Credentials loaded using oauth2client')
      credentials = credential_loader.GetCredentialsFromFlags()
    assert credentials is not None

    bigquery_client_factory = Factory.GetBigqueryClientFactory()
    return bigquery_client_factory(credentials=credentials, **client_args)


  @classmethod
  def _GetClientCacheKey(cls, **kwds):
    logging.debug('In Client._GetClientCacheKey: %s', kwds)
    client_args = Client._CollectArgs(**kwds)
    return ('client_args={client_args},'
            'service_account_credential_file={service_account_credential_file},'
            'apilog={apilog},'.format(
                client_args=client_args,
                service_account_credential_file=FLAGS
                .service_account_credential_file,
                apilog=FLAGS.apilog))

  @classmethod
  def Get(cls):
    """Return a BigqueryClient initialized from flags."""
    logging.debug('In Client.Get')
    cache_key = Client._GetClientCacheKey()
    if cache_key not in cls.client_cache:
      try:
        cls.client_cache[cache_key] = Client.Create()
      except ValueError as e:
        # Convert constructor parameter errors into flag usage errors.
        raise app.UsageError(e)

    return cls.client_cache[cache_key]

  @classmethod
  def Delete(cls):
    """Delete the existing client.

    This is needed when flags have changed, and we need to force
    client recreation to reflect new flag values.
    """
    cache_key = Client._GetClientCacheKey()
    if cache_key in cls.client_cache:
      del cls.client_cache[cache_key]


class Factory(object):
  """Class encapsulating factory creation of BigqueryClient."""
  _BIGQUERY_CLIENT_FACTORY = None

  class ClientTablePrinter(object):
    """Class encapsulating factory creation of TablePrinter."""
    _TABLE_PRINTER = None

    @classmethod
    def GetTablePrinter(cls):
      if cls._TABLE_PRINTER is None:
        cls._TABLE_PRINTER = bq_frontend_utils.TablePrinter()
      return cls._TABLE_PRINTER

    @classmethod
    def SetTablePrinter(cls, printer):
      if not isinstance(printer, bq_frontend_utils.TablePrinter):
        raise TypeError('Printer must be an instance of TablePrinter.')
      cls._TABLE_PRINTER = printer

  @classmethod
  def GetBigqueryClientFactory(cls):
    if cls._BIGQUERY_CLIENT_FACTORY is None:
      cls._BIGQUERY_CLIENT_FACTORY = bigquery_client.BigqueryClient
    return cls._BIGQUERY_CLIENT_FACTORY

  @classmethod
  def SetBigqueryClientFactory(cls, factory):
    if not issubclass(factory, bigquery_client.BigqueryClient):
      raise TypeError('Factory must be subclass of BigqueryClient.')
    cls._BIGQUERY_CLIENT_FACTORY = factory
