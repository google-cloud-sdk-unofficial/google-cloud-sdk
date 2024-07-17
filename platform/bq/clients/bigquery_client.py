#!/usr/bin/env python
"""BigqueryClient class."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import enum
from http import client as http_client_lib
import json
import logging
import re
import tempfile
import time
import traceback
from typing import Any, Callable, List, Optional, Union
import urllib


# To configure apiclient logging.
from absl import flags
import googleapiclient
from googleapiclient import discovery
import httplib2

import bq_flags
import bq_utils
from clients import bigquery_http
from clients import utils as bq_client_utils
from discovery_documents import discovery_document_cache
from discovery_documents import discovery_document_loader
from utils import bq_api_utils
from utils import bq_error


try:
  from google.auth import credentials as google_credentials

  _HAS_GOOGLE_AUTH = True
except ImportError:
  _HAS_GOOGLE_AUTH = False

try:
  import google_auth_httplib2

  _HAS_GOOGLE_AUTH_HTTPLIB2 = True
except ImportError:
  _HAS_GOOGLE_AUTH_HTTPLIB2 = False

# A unique non-None default, for use in kwargs that need to
# distinguish default from None.
_DEFAULT = object()

Service = bq_api_utils.Service


class BigqueryClient:
  """Class encapsulating interaction with the BigQuery service."""


  def __init__(
      self,
      *,
      api: str,
      api_version: str,
      project_id: Optional[str] = '',
      dataset_id: Optional[str] = '',
      discovery_document: Union[bytes, object, None] = _DEFAULT,
      job_property: str = '',
      trace: Optional[str] = None,
      sync: bool = True,
      wait_printer_factory: Optional[
          Callable[[], bq_client_utils.TransitionWaitPrinter]
      ] = bq_client_utils.TransitionWaitPrinter,
      job_id_generator: bq_client_utils.JobIdGenerator = bq_client_utils.JobIdGeneratorIncrementing(
          bq_client_utils.JobIdGeneratorRandom()
      ),
      max_rows_per_request: Optional[int] = None,
      quota_project_id: Optional[str] = None,
      use_google_auth: bool = False,
      **kwds,
  ):
    """Initializes BigqueryClient.

    Required keywords:
      api: the api to connect to, for example "bigquery".
      api_version: the version of the api to connect to, for example "v2".

    Optional keywords:
      project_id: a default project id to use. While not required for
        initialization, a project_id is required when calling any
        method that creates a job on the server. Methods that have
        this requirement pass through **kwds, and will raise
        bq_error.BigqueryClientConfigurationError if no project_id can be
        found.
      dataset_id: a default dataset id to use.
      discovery_document: the discovery document to use. If None, one
        will be retrieved from the discovery api. If not specified,
        the built-in discovery document will be used.
      job_property: a list of "key=value" strings defining properties
        to apply to all job operations.
      trace: a tracing header to include in all bigquery api requests.
      sync: boolean, when inserting jobs, whether to wait for them to
        complete before returning from the insert request.
      wait_printer_factory: a function that returns a WaitPrinter.
        This will be called for each job that we wait on. See WaitJob().

    Raises:
      ValueError: if keywords are missing or incorrectly specified.
    """
    super().__init__()
    self.api = api
    self.api_version = api_version
    self.project_id = project_id
    self.dataset_id = dataset_id
    self.discovery_document = discovery_document
    self.job_property = job_property
    self.trace = trace
    self.sync = sync
    self.wait_printer_factory = wait_printer_factory
    self.job_id_generator = job_id_generator
    self.max_rows_per_request = max_rows_per_request
    self.quota_project_id = quota_project_id
    self.use_google_auth = use_google_auth
    # TODO(b/324243535): Delete this block to make attributes explicit.
    for key, value in kwds.items():
      setattr(self, key, value)
    self._apiclient = None
    self._routines_apiclient = None
    self._row_access_policies_apiclient = None
    self._op_transfer_client = None
    self._op_reservation_client = None
    self._op_bi_reservation_client = None
    self._models_apiclient = None
    self._op_connection_service_client = None
    self._iam_policy_apiclient = None
    default_flag_values = {
        'iam_policy_discovery_document': _DEFAULT,
        'connection_service_path': None,
    }
    for flagname, default in default_flag_values.items():
      if not hasattr(self, flagname):
        setattr(self, flagname, default)

  columns_to_include_for_transfer_run = [
      'updateTime',
      'schedule',
      'runTime',
      'scheduleTime',
      'params',
      'endTime',
      'dataSourceId',
      'destinationDatasetId',
      'state',
      'startTime',
      'name',
  ]

  # These columns appear to be empty with scheduling a new transfer run
  # so there are listed as excluded from the transfer run output.
  columns_excluded_for_make_transfer_run = ['schedule', 'endTime', 'startTime']

  def GetHttp(
      self,
  ) -> Union[
      httplib2.Http,
  ]:
    """Returns the httplib2 Http to use."""

    proxy_info = httplib2.proxy_info_from_environment
    if flags.FLAGS.proxy_address and flags.FLAGS.proxy_port:
      try:
        port = int(flags.FLAGS.proxy_port)
      except ValueError:
        raise ValueError(
            'Invalid value for proxy_port: {}'.format(flags.FLAGS.proxy_port)
        )
      proxy_info = httplib2.ProxyInfo(
          proxy_type=3,
          proxy_host=flags.FLAGS.proxy_address,
          proxy_port=port,
          proxy_user=flags.FLAGS.proxy_username or None,
          proxy_pass=flags.FLAGS.proxy_password or None,
      )

    http = httplib2.Http(
        proxy_info=proxy_info,
        ca_certs=flags.FLAGS.ca_certificates_file or None,
        disable_ssl_certificate_validation=flags.FLAGS.disable_ssl_validation,
    )

    if hasattr(http, 'redirect_codes'):
      http.redirect_codes = set(http.redirect_codes) - {308}

    if flags.FLAGS.mtls:
      _, self._cert_file = tempfile.mkstemp()
      _, self._key_file = tempfile.mkstemp()
      discovery.add_mtls_creds(
          http, discovery.get_client_options(), self._cert_file, self._key_file
      )
    return http

  def GetDiscoveryUrl(self, service: Service, api_version: str) -> str:
    """Returns the url to the discovery document for bigquery."""
    discovery_url = ''
    if not discovery_url:
      discovery_url = bq_api_utils.get_discovery_url_from_root_url(
          bq_api_utils.get_tpc_root_url_from_flags(
              service=service, inputted_flags=bq_flags, local_params=self
          ),
          api_version=api_version,
      )
    return discovery_url

  def GetAuthorizedHttp(
      self,
      credentials: Any,
      http: Union[
          'httplib2.Http',
      ],
      is_for_discovery: bool = False,
  ) -> Union[
      'httplib2.Http',
      'google_auth_httplib2.AuthorizedHttp',
  ]:
    """Returns an http client that is authorized with the given credentials."""
    if is_for_discovery:
      # Discovery request shouldn't have any quota project ID set.
      credentials = bq_utils.GetSanitizedCredentialForDiscoveryRequest(
          self.use_google_auth, credentials
      )

    if self.use_google_auth:
      if not _HAS_GOOGLE_AUTH:
        logging.error(
            'System is set to use `google.auth`, but it did not load.'
        )
      if not isinstance(credentials, google_credentials.Credentials):
        logging.error(
            'The system is using `google.auth` but the parsed credentials are'
            ' of an incorrect type.'
        )
    else:
      logging.debug('System is set to not use `google.auth`.')

    if _HAS_GOOGLE_AUTH and isinstance(
        credentials, google_credentials.Credentials
    ):
      if not _HAS_GOOGLE_AUTH_HTTPLIB2:
        raise ValueError(
            'Credentials from google.auth specified, but '
            'google-api-python-client is unable to use these credentials '
            'unless google-auth-httplib2 is installed. Please install '
            'google-auth-httplib2.'
        )
      return google_auth_httplib2.AuthorizedHttp(credentials, http=http)
    return credentials.authorize(http)

  def BuildApiClient(
      self,
      service: Service,
      discovery_url: Optional[str] = None,
  ) -> discovery.Resource:
    """Build and return BigQuery Dynamic client from discovery document."""
    logging.info('BuildApiClient discovery_url: %s', discovery_url)
    http_client = self.GetHttp()
    http = self.GetAuthorizedHttp(
        self.credentials, http_client, is_for_discovery=True
    )
    bigquery_model = bigquery_http.BigqueryModel(
        trace=self.trace,
        quota_project_id=bq_utils.GetEffectiveQuotaProjectIDForHTTPHeader(
            self.quota_project_id, self.use_google_auth, self.credentials
        ),
    )
    bq_request_builder = bigquery_http.BigqueryHttp.Factory(
        bigquery_model,
        self.use_google_auth,
    )
    discovery_document = None
    if self.discovery_document != _DEFAULT:
      discovery_document = self.discovery_document
      logging.info(
          'Skipping local discovery document load since discovery_document has'
          ' a value: %s',
          discovery_document,
      )
    elif discovery_url is not None:
      logging.info(
          'Skipping local discovery document load since discovery_url has'
          ' a value'
      )
    # For now, align this strictly with the default flag values. We can loosen
    # this but for a first pass I'm keeping the current code flow.
    # TODO(b/318711380): Local discovery load for different APIs.
    elif (
        self.api not in discovery_document_loader.SUPPORTED_BIGQUERY_APIS
        or self.api_version != 'v2'
    ):
      logging.info(
          'Loading discovery doc from the server since this is not'
          ' v2 (%s) and the API endpoint (%s) is not one of (%s).',
          self.api_version,
          self.api,
          ', '.join(discovery_document_loader.SUPPORTED_BIGQUERY_APIS),
      )
    else:
      # Use the api description packed with this client, if one exists
      # TODO(b/318711380): Local discovery load for different APIs.
      try:
        discovery_document = discovery_document_loader.load_local_discovery_doc(
            discovery_document_loader.DISCOVERY_NEXT_BIGQUERY
        )
      except FileNotFoundError as e:
        logging.warning('Failed to load discovery doc from local files: %s', e)

    if discovery_document is not None:
      logging.info('Discovery doc is already loaded')
    else:
      # Attempt to retrieve discovery doc with retry logic for transient,
      # retry-able errors.
      max_retries = 3
      iterations = 0
      headers = (
          {'X-ESF-Use-Cloud-UberMint-If-Enabled': '1'}
          if hasattr(self, 'use_uber_mint') and self.use_uber_mint
          else None
      )
      while iterations < max_retries and discovery_document is None:
        if iterations > 0:
          # Wait briefly before retrying with exponentially increasing wait.
          time.sleep(2**iterations)
        iterations += 1
        try:
          if discovery_url is None:
            discovery_url = self.GetDiscoveryUrl(
                service=service, api_version=self.api_version
            )
          logging.info('Requesting discovery document from %s', discovery_url)
          if headers:
            response_metadata, discovery_document = http.request(
                discovery_url, headers=headers
            )
          else:
            response_metadata, discovery_document = http.request(discovery_url)
          discovery_document = discovery_document.decode('utf-8')
          if int(response_metadata.get('status')) >= 400:
            msg = 'Got %s response from discovery url: %s' % (
                response_metadata.get('status'),
                discovery_url,
            )
            logging.error('%s:\n%s', msg, discovery_document)
            raise bq_error.BigqueryCommunicationError(msg)
        except (
            httplib2.HttpLib2Error,
            googleapiclient.errors.HttpError,
            http_client_lib.HTTPException,
        ) as e:
          # We can't find the specified server. This can be thrown for
          # multiple reasons, so inspect the error.
          if hasattr(e, 'content'):
            if iterations == max_retries:
              content = ''
              if hasattr(e, 'content'):
                content = e.content
              raise bq_error.BigqueryCommunicationError(
                  'Cannot contact server. Please try again.\nError: %r'
                  '\nContent: %s' % (e, content)
              )
          else:
            if iterations == max_retries:
              raise bq_error.BigqueryCommunicationError(
                  'Cannot contact server. Please try again.\nTraceback: %s'
                  % (traceback.format_exc(),)
              )
        except IOError as e:
          if iterations == max_retries:
            raise bq_error.BigqueryCommunicationError(
                'Cannot contact server. Please try again.\nError: %r' % (e,)
            )
        except googleapiclient.errors.UnknownApiNameOrVersion as e:
          # We can't resolve the discovery url for the given server.
          # Don't retry in this case.
          raise bq_error.BigqueryCommunicationError(
              'Invalid API name or version: %s' % (str(e),)
          )

    discovery_document_to_build_client = self.OverrideEndpoint(
        discovery_document=discovery_document, service=service
    )

    built_client = None
    try:
      # The http object comes from self.GetAuthorizedHttp above with
      # is_for_discovery=True. This means if the underlying credentials object
      # is of type google.oauth2, it will not carry a quota project ID
      # regardless of whether an ID is provided explicitly. This specific http
      # object has to be used for the discovery requests, and so far has found
      # to have no effect on BQ API requests in practice.
      built_client = discovery.build_from_document(
          discovery_document_to_build_client,
          http=http,
          model=bigquery_model,
          requestBuilder=bq_request_builder,
      )
    except Exception:
      logging.error(
          'Error building from discovery document: %s', discovery_document
      )
      raise


    return built_client

  def BuildDiscoveryNextApiClient(self) -> discovery.Resource:
    """Builds and returns BigQuery API client from discovery_next document."""
    http = self.GetAuthorizedHttp(self.credentials, self.GetHttp())
    bigquery_model = bigquery_http.BigqueryModel(
        trace=self.trace,
        quota_project_id=bq_utils.GetEffectiveQuotaProjectIDForHTTPHeader(
            self.quota_project_id, self.use_google_auth, self.credentials
        ),
    )
    bq_request_builder = bigquery_http.BigqueryHttp.Factory(
        bigquery_model,
        self.use_google_auth,
    )
    models_doc = None
    try:
      models_doc = discovery_document_loader.load_local_discovery_doc(
          discovery_document_loader.DISCOVERY_NEXT_BIGQUERY
      )
      models_doc = self.OverrideEndpoint(
          discovery_document=models_doc, service=Service.BIGQUERY
      )
    except (bq_error.BigqueryClientError, FileNotFoundError) as e:
      logging.warning('Failed to load discovery doc from local files: %s', e)
      raise

    try:
      return discovery.build_from_document(
          models_doc,
          http=http,
          model=bigquery_model,
          requestBuilder=bq_request_builder,
      )
    except Exception:
      logging.error('Error building from models document: %s', models_doc)
      raise

  def BuildIAMPolicyApiClient(self) -> discovery.Resource:
    """Builds and returns IAM policy API client from discovery document."""
    http = self.GetAuthorizedHttp(self.credentials, self.GetHttp())
    bigquery_model = bigquery_http.BigqueryModel(
        trace=self.trace,
        quota_project_id=bq_utils.GetEffectiveQuotaProjectIDForHTTPHeader(
            self.quota_project_id, self.use_google_auth, self.credentials
        ),
    )
    bq_request_builder = bigquery_http.BigqueryHttp.Factory(
        bigquery_model,
        self.use_google_auth,
    )
    try:
      iam_pol_doc = discovery_document_loader.load_local_discovery_doc(
          discovery_document_loader.DISCOVERY_NEXT_IAM_POLICY
      )
      iam_pol_doc = self.OverrideEndpoint(
          discovery_document=iam_pol_doc, service=Service.BQ_IAM
      )
    except (bq_error.BigqueryClientError, FileNotFoundError) as e:
      logging.warning('Failed to load discovery doc from local files: %s', e)
      raise

    try:
      return discovery.build_from_document(
          iam_pol_doc,
          http=http,
          model=bigquery_model,
          requestBuilder=bq_request_builder,
      )
    except Exception:
      logging.error('Error building from iam policy document: %s', iam_pol_doc)
      raise

  @property
  def apiclient(self) -> discovery.Resource:
    """Returns a singleton ApiClient built for the BigQuery core API."""
    if self._apiclient:
      logging.info('Using the cached BigQuery API client')
    else:
      self._apiclient = self.BuildApiClient(service=Service.BIGQUERY)
    return self._apiclient

  def GetModelsApiClient(self) -> discovery.Resource:
    """Returns the apiclient attached to self."""
    if self._models_apiclient is None:
      self._models_apiclient = self.BuildDiscoveryNextApiClient()
    return self._models_apiclient

  def GetRoutinesApiClient(self) -> discovery.Resource:
    """Return the apiclient attached to self."""
    if self._routines_apiclient is None:
      self._routines_apiclient = self.BuildDiscoveryNextApiClient()
    return self._routines_apiclient

  def GetRowAccessPoliciesApiClient(self) -> discovery.Resource:
    """Return the apiclient attached to self."""
    if self._row_access_policies_apiclient is None:
      self._row_access_policies_apiclient = self.BuildDiscoveryNextApiClient()
    return self._row_access_policies_apiclient

  def GetIAMPolicyApiClient(self) -> discovery.Resource:
    """Return the apiclient attached to self."""
    if self._iam_policy_apiclient is None:
      self._iam_policy_apiclient = self.BuildIAMPolicyApiClient()
    return self._iam_policy_apiclient

  def GetInsertApiClient(self) -> discovery.Resource:
    """Return the apiclient that supports insert operation."""
    insert_client = self.apiclient
    return insert_client

  def GetTransferV1ApiClient(
      self, transferserver_address: Optional[str] = None
  ) -> discovery.Resource:
    """Return the apiclient that supports Transfer v1 operation."""
    logging.info(
        'GetTransferV1ApiClient transferserver_address: %s',
        transferserver_address,
    )

    if self._op_transfer_client:
      logging.info('Using the cached Transfer API client')
    else:
      path = transferserver_address or bq_api_utils.get_tpc_root_url_from_flags(
          service=Service.DTS, inputted_flags=bq_flags, local_params=self
      )
      discovery_url = bq_api_utils.get_discovery_url_from_root_url(
          path, api_version='v1'
      )
      self._op_transfer_client = self.BuildApiClient(
          discovery_url=discovery_url,
          service=Service.DTS,
      )
    return self._op_transfer_client

  def GetReservationApiClient(
      self, reservationserver_address: Optional[str] = None
  ) -> discovery.Resource:
    """Return the apiclient that supports reservation operations."""
    if self._op_reservation_client:
      logging.info('Using the cached Reservations API client')
    else:
      path = (
          reservationserver_address
          or bq_api_utils.get_tpc_root_url_from_flags(
              service=Service.RESERVATIONS,
              inputted_flags=bq_flags,
              local_params=self,
          )
      )
      reservation_version = 'v1'
      # TODO(b/302038541): Add support for query params.
      discovery_url = bq_api_utils.get_discovery_url_from_root_url(
          path, api_version=reservation_version
      )
      self._op_reservation_client = self.BuildApiClient(
          discovery_url=discovery_url,
          service=Service.RESERVATIONS,
      )
    return self._op_reservation_client

  def GetConnectionV1ApiClient(
      self, connection_service_address: Optional[str] = None
  ) -> discovery.Resource:
    """Return the apiclient that supports connections operations."""
    if self._op_connection_service_client:
      logging.info('Using the cached Connections API client')
    else:
      path = (
          connection_service_address
          or bq_api_utils.get_tpc_root_url_from_flags(
              service=Service.CONNECTIONS,
              inputted_flags=bq_flags,
              local_params=self,
          )
      )
      discovery_url = bq_api_utils.get_discovery_url_from_root_url(
          path, api_version='v1'
      )
      self._op_connection_service_client = self.BuildApiClient(
          discovery_url=discovery_url,
          service=Service.CONNECTIONS,
      )
    return self._op_connection_service_client

  def OverrideEndpoint(
      self, discovery_document: Union[str, bytes], service: Service
  ) -> Optional[str]:
    """Override rootUrl for regional endpoints.

    Args:
      discovery_document: BigQuery discovery document.
      service: The BigQuery service being used.

    Returns:
      discovery_document updated discovery document.

    Raises:
      bq_error.BigqueryClientError: if location is not set and
        use_regional_endpoints is.
    """
    if discovery_document is None:
      return discovery_document

    discovery_document = bq_api_utils.parse_discovery_doc(discovery_document)

    logging.info(
        'Discovery doc loaded, considering overriding rootUrl: %s',
        discovery_document['rootUrl'],
    )

    is_prod = True

    if is_prod:
      discovery_document['rootUrl'] = bq_api_utils.get_tpc_root_url_from_flags(
          service=service, inputted_flags=bq_flags, local_params=self
      )


    discovery_document['baseUrl'] = urllib.parse.urljoin(
        discovery_document['rootUrl'], discovery_document['servicePath']
    )

    return json.dumps(discovery_document)
