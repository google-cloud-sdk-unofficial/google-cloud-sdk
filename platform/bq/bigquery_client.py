#!/usr/bin/env python
# pylint: disable=g-unknown-interpreter
# Copyright 2012 Google Inc. All Rights Reserved.
"""Bigquery Client library for Python."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import enum
import itertools
import json
import logging
import os
import re
import string
import sys
import tempfile
import time
import traceback
from typing import Any, Dict, List, Optional, Union
import uuid


# To configure apiclient logging.
from absl import flags
from google.api_core.iam import Policy
import googleapiclient
from googleapiclient import discovery
from googleapiclient import http as http_request
import httplib2
import inflection
import six
from six.moves import map
from six.moves import range
from six.moves import zip
import six.moves.http_client
from six.moves.urllib.parse import urljoin

# pylint: disable=unused-import
import bq_flags
import bq_utils
from clients import bigquery_http
from clients import utils as bq_client_utils
from discovery_documents import discovery_document_cache
from discovery_documents import discovery_document_loader
from utils import bq_api_utils
from utils import bq_error
from utils import bq_id_utils
from utils import bq_logging
from utils import bq_processor_utils
from pyglib import stringutil


try:
  from google.auth import credentials as google_credentials
  _HAS_GOOGLE_AUTH = True
except ImportError:
  _HAS_GOOGLE_AUTH = False

try:
  import google_auth_httplib2
except ImportError:
  google_auth_httplib2 = None

# A unique non-None default, for use in kwargs that need to
# distinguish default from None.
_DEFAULT = object()


collections_abc = collections
if sys.version_info > (3, 8):
  collections_abc = collections.abc

Service = bq_api_utils.Service

# Data Transfer Service Authorization Info
AUTHORIZATION_CODE = 'authorization_code'
VERSION_INFO = 'version_info'

# IAM role name that represents being a grantee on a row access policy.
_FILTERED_DATA_VIEWER_ROLE = 'roles/bigquery.filteredDataViewer'


# TODO(b/324243535): Delete these once the migration is complete.
# pylint: disable=protected-access
MakeAccessRolePropertiesJson = bq_processor_utils.MakeAccessRolePropertiesJson
MakeTenantIdPropertiesJson = bq_processor_utils.MakeTenantIdPropertiesJson
MakeAzureFederatedAppClientIdPropertiesJson = (
    bq_processor_utils.MakeAzureFederatedAppClientIdPropertiesJson
)
MakeAzureFederatedAppClientAndTenantIdPropertiesJson = (
    bq_processor_utils.MakeAzureFederatedAppClientAndTenantIdPropertiesJson
)
_ToLowerCamel = bq_processor_utils.ToLowerCamel
_ApplyParameters = bq_processor_utils.ApplyParameters
_FormatProjectIdentifierForTransfers = (
    bq_processor_utils.FormatProjectIdentifierForTransfers
)
_ParseJson = bq_processor_utils.ParseJson
InsertEntry = bq_processor_utils.InsertEntry
JsonToInsertEntry = bq_processor_utils.JsonToInsertEntry
_PrintFormattedJsonObject = bq_client_utils._PrintFormattedJsonObject
MaybePrintManualInstructionsForConnection = (
    bq_client_utils.MaybePrintManualInstructionsForConnection
)
# pylint: enable=protected-access


# TODO(b/324243535): Delete these once the migration is complete.
# pylint: disable=protected-access
_ToFilename = bq_client_utils._ToFilename
_OverwriteCurrentLine = bq_client_utils._OverwriteCurrentLine
_FormatLabels = bq_client_utils._FormatLabels
_FormatTableReference = bq_client_utils._FormatTableReference
_FormatTags = bq_client_utils._FormatTags
_FormatResourceTags = bq_client_utils._FormatResourceTags
_FormatStandardSqlFields = bq_client_utils._FormatStandardSqlFields
# pylint: enable=protected-access



# TODO(b/324243535): Delete these once the migration is complete.
# pylint: disable=protected-access
_ParseJobIdentifier = bq_client_utils._ParseJobIdentifier
_ParseReservationIdentifier = bq_client_utils._ParseReservationIdentifier
_ParseReservationPath = bq_client_utils.ParseReservationPath
_ParseCapacityCommitmentIdentifier = (
    bq_client_utils._ParseCapacityCommitmentIdentifier
)
_ParseCapacityCommitmentPath = bq_client_utils.ParseCapacityCommitmentPath
_ParseReservationAssignmentIdentifier = (
    bq_client_utils._ParseReservationAssignmentIdentifier
)
_ParseReservationAssignmentPath = (
    bq_client_utils._ParseReservationAssignmentPath
)
_ParseConnectionIdentifier = bq_client_utils._ParseConnectionIdentifier
_ParseConnectionPath = bq_client_utils._ParseConnectionPath
ReadTableConstrants = bq_client_utils.ReadTableConstrants
BigqueryModel = bigquery_http.BigqueryModel
BigqueryHttp = bigquery_http.BigqueryHttp
# pylint: enable=protected-access

# TODO(b/324243535): Delete these once the migration is complete.
JobIdGenerator = bq_client_utils.JobIdGenerator
JobIdGeneratorNone = bq_client_utils.JobIdGeneratorNone
JobIdGeneratorRandom = bq_client_utils.JobIdGeneratorRandom
JobIdGeneratorFingerprint = bq_client_utils.JobIdGeneratorFingerprint
JobIdGeneratorIncrementing = bq_client_utils.JobIdGeneratorIncrementing


class TransferScheduleArgs:
  """Arguments to customize data transfer schedule."""

  def __init__(self,
               schedule=None,
               start_time=None,
               end_time=None,
               disable_auto_scheduling=False):
    self.schedule = schedule
    self.start_time = start_time
    self.end_time = end_time
    self.disable_auto_scheduling = disable_auto_scheduling

  def ToScheduleOptionsPayload(self, options_to_copy=None):
    """Returns a dictionary of schedule options.

    Args:
      options_to_copy: Existing options to be copied.

    Returns:
      A dictionary of schedule options expected by the
      bigquery.transfers.create and bigquery.transfers.update API methods.
    """

    # Copy the current options or start with an empty dictionary.
    options = dict(options_to_copy or {})

    if self.start_time is not None:
      options['startTime'] = self._TimeOrInfitity(self.start_time)
    if self.end_time is not None:
      options['endTime'] = self._TimeOrInfitity(self.end_time)

    options['disableAutoScheduling'] = self.disable_auto_scheduling

    return options

  def _TimeOrInfitity(self, time_str):
    """Returns None to indicate Inifinity, if time_str is an empty string."""
    return time_str or None


class BigqueryClient:
  """Class encapsulating interaction with the BigQuery service."""


  def __init__(self, **kwds):
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
    for required_flag in ('api', 'api_version'):
      if required_flag not in kwds:
        raise ValueError('Missing required flag: %s' % (required_flag,))
    default_flag_values = {
        'project_id': '',
        'dataset_id': '',
        'discovery_document': _DEFAULT,
        'iam_policy_discovery_document': _DEFAULT,
        'job_property': '',
        'trace': None,
        'sync': True,
        'wait_printer_factory': bq_client_utils.TransitionWaitPrinter,
        'job_id_generator': bq_client_utils.JobIdGeneratorIncrementing(
            bq_client_utils.JobIdGeneratorRandom()),
        'max_rows_per_request': None,
        'connection_service_path': None,
        'quota_project_id': None,
        'use_google_auth': False,
    }
    for flagname, default in default_flag_values.items():
      if not hasattr(self, flagname):
        setattr(self, flagname, default)

  columns_to_include_for_transfer_run = [
      'updateTime', 'schedule', 'runTime', 'scheduleTime', 'params', 'endTime',
      'dataSourceId', 'destinationDatasetId', 'state', 'startTime', 'name'
  ]

  # These columns appear to be empty with scheduling a new transfer run
  # so there are listed as excluded from the transfer run output.
  columns_excluded_for_make_transfer_run = ['schedule', 'endTime', 'startTime']


  def GetHttp(self):
    """Returns the httplib2 Http to use."""

    proxy_info = httplib2.proxy_info_from_environment
    if flags.FLAGS.proxy_address and flags.FLAGS.proxy_port:
      try:
        port = int(flags.FLAGS.proxy_port)
      except ValueError:
        raise ValueError('Invalid value for proxy_port: {}'.format(
            flags.FLAGS.proxy_port))
      proxy_info = httplib2.ProxyInfo(
          proxy_type=3,
          proxy_host=flags.FLAGS.proxy_address,
          proxy_port=port,
          proxy_user=flags.FLAGS.proxy_username or None,
          proxy_pass=flags.FLAGS.proxy_password or None)

    http = httplib2.Http(
        proxy_info=proxy_info,
        ca_certs=flags.FLAGS.ca_certificates_file or None,
        disable_ssl_certificate_validation=flags.FLAGS.disable_ssl_validation)

    if hasattr(http, 'redirect_codes'):
      http.redirect_codes = set(http.redirect_codes) - {308}

    if flags.FLAGS.mtls:
      _, self._cert_file = tempfile.mkstemp()
      _, self._key_file = tempfile.mkstemp()
      discovery.add_mtls_creds(http, discovery.get_client_options(),
                               self._cert_file, self._key_file)

    return http


  def GetDiscoveryUrl(self, service: Service, api_version: string) -> str:
    """Returns the url to the discovery document for bigquery."""
    discovery_url = ''
    if not discovery_url:
      discovery_url = bq_api_utils.get_discovery_url_from_root_url(
          bq_api_utils.get_tpc_root_url_from_flags(
              service=service, inputted_flags=bq_flags, local_params=self
          ),
          api_version=api_version
      )
    return discovery_url

  def GetAuthorizedHttp(
      self,
      credentials: Any,
      http: Any,
      is_for_discovery: bool = False):
    """Returns an http client that is authorized with the given credentials."""
    if is_for_discovery:
      # Discovery request shouldn't have any quota project ID set.
      credentials = bq_utils.GetSanitizedCredentialForDiscoveryRequest(
          self.use_google_auth, credentials)

    if self.use_google_auth:
      if not _HAS_GOOGLE_AUTH:
        logging.error(
            'System is set to use `google.auth`, but it did not load.')
      if not isinstance(credentials, google_credentials.Credentials):
        logging.error(
            'The system is using `google.auth` but the parsed credentials are'
            ' of an incorrect type.'
            )
    else:
      logging.debug('System is set to not use `google.auth`.')

    if _HAS_GOOGLE_AUTH and isinstance(credentials,
                                       google_credentials.Credentials):
      if google_auth_httplib2 is None:
        raise ValueError(
            'Credentials from google.auth specified, but '
            'google-api-python-client is unable to use these credentials '
            'unless google-auth-httplib2 is installed. Please install '
            'google-auth-httplib2.')
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
        self.credentials,
        http_client,
        is_for_discovery=True)
    bigquery_model = bigquery_http.BigqueryModel(
        trace=self.trace,
        quota_project_id=bq_utils.GetEffectiveQuotaProjectIDForHTTPHeader(
            self.quota_project_id, self.use_google_auth, self.credentials
        ))
    bq_request_builder = bigquery_http.BigqueryHttp.Factory(
        bigquery_model,
        self.use_google_auth,
    )
    discovery_document = None
    if self.discovery_document != _DEFAULT:
      discovery_document = self.discovery_document
      logging.info(
          'Skipping local discovery document load since discovery_document has'
          ' a value: %s', discovery_document
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
        discovery_document = (
            discovery_document_loader.load_local_discovery_doc(
                discovery_document_loader.DISCOVERY_NEXT_BIGQUERY
            )
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
            response_metadata, discovery_document = http.request(
                discovery_url
            )
          discovery_document = discovery_document.decode('utf-8')
          if int(response_metadata.get('status')) >= 400:
            msg = 'Got %s response from discovery url: %s' % (
                response_metadata.get('status'), discovery_url)
            logging.error('%s:\n%s', msg, discovery_document)
            raise bq_error.BigqueryCommunicationError(msg)
        except (httplib2.HttpLib2Error, googleapiclient.errors.HttpError,
                six.moves.http_client.HTTPException) as e:
          # We can't find the specified server. This can be thrown for
          # multiple reasons, so inspect the error.
          if hasattr(e, 'content'):
            if iterations == max_retries:
              raise bq_error.BigqueryCommunicationError(
                  'Cannot contact server. Please try again.\nError: %r'
                  '\nContent: %s' % (e, e.content))
          else:
            if iterations == max_retries:
              raise bq_error.BigqueryCommunicationError(
                  'Cannot contact server. Please try again.\n'
                  'Traceback: %s' % (traceback.format_exc(),))
        except IOError as e:
          if iterations == max_retries:
            raise bq_error.BigqueryCommunicationError(
                'Cannot contact server. Please try again.\nError: %r' % (e,))
        except googleapiclient.errors.UnknownApiNameOrVersion as e:
          # We can't resolve the discovery url for the given server.
          # Don't retry in this case.
          raise bq_error.BigqueryCommunicationError(
              'Invalid API name or version: %s' % (str(e),))

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
          requestBuilder=bq_request_builder)
    except Exception:
      logging.error('Error building from discovery document: %s',
                    discovery_document)
      raise


    return built_client

  def BuildDiscoveryNextApiClient(self) -> discovery.Resource:
    """Builds and returns BigQuery API client from discovery_next document."""
    http = self.GetAuthorizedHttp(self.credentials, self.GetHttp())
    bigquery_model = bigquery_http.BigqueryModel(
        trace=self.trace,
        quota_project_id=bq_utils.GetEffectiveQuotaProjectIDForHTTPHeader(
            self.quota_project_id, self.use_google_auth, self.credentials))
    bq_request_builder = bigquery_http.BigqueryHttp.Factory(
        bigquery_model,
        self.use_google_auth,
    )
    models_doc = None
    try:
      models_doc = discovery_document_loader.load_local_discovery_doc(
          discovery_document_loader.DISCOVERY_NEXT_BIGQUERY)
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
          requestBuilder=bq_request_builder)
    except Exception:
      logging.error('Error building from models document: %s', models_doc)
      raise

  def BuildIAMPolicyApiClient(self) -> discovery.Resource:
    """Builds and returns IAM policy API client from discovery document."""
    http = self.GetAuthorizedHttp(self.credentials, self.GetHttp())
    bigquery_model = bigquery_http.BigqueryModel(
        trace=self.trace,
        quota_project_id=bq_utils.GetEffectiveQuotaProjectIDForHTTPHeader(
            self.quota_project_id, self.use_google_auth, self.credentials))
    bq_request_builder = bigquery_http.BigqueryHttp.Factory(
        bigquery_model,
        self.use_google_auth,
    )
    try:
      iam_pol_doc = discovery_document_loader.load_local_discovery_doc(
          discovery_document_loader.DISCOVERY_NEXT_IAM_POLICY)
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
          requestBuilder=bq_request_builder)
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
      self,
      transferserver_address: Optional[str] = None) -> discovery.Resource:
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
          service=Service.DTS
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
          service=Service.RESERVATIONS
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
          service=Service.CONNECTIONS
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


    discovery_document['baseUrl'] = urljoin(
        discovery_document['rootUrl'], discovery_document['servicePath']
    )

    return json.dumps(discovery_document)


  #################################
  ## Utility methods
  #################################
  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTime(secs):
    return bq_client_utils.FormatTime(secs)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTimeFromProtoTimestampJsonString(json_string):
    """Converts google.protobuf.Timestamp formatted string to BQ format."""
    return bq_client_utils.FormatTimeFromProtoTimestampJsonString(json_string)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatAcl(acl):
    """Format a server-returned ACL for printing."""
    return bq_client_utils.FormatAcl(acl)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatSchema(schema):
    """Format a schema for printing."""
    return bq_client_utils.FormatSchema(schema)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def NormalizeWait(wait):
    return bq_client_utils.NormalizeWait(wait)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def ValidatePrintFormat(print_format):
    return bq_client_utils.ValidatePrintFormat(print_format)

  # TODO(b/324243535): Delete these once the migration is complete.
  # pylint: disable=protected-access
  @staticmethod
  def _ParseDatasetIdentifier(identifier):
    return bq_client_utils._ParseDatasetIdentifier(identifier)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def _ShiftInformationSchema(dataset_id, table_id):
    """Moves "INFORMATION_SCHEMA" to table_id for dataset qualified tables."""
    return bq_client_utils._ShiftInformationSchema(dataset_id, table_id)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def _ParseIdentifier(identifier):
    """Parses identifier into a tuple of (possibly empty) identifiers.

    This will parse the identifier into a tuple of the form
    (project_id, dataset_id, table_id) without doing any validation on
    the resulting names; missing names are returned as ''. The
    interpretation of these identifiers depends on the context of the
    caller. For example, if you know the identifier must be a job_id,
    then you can assume dataset_id is the job_id.

    Args:
      identifier: string, identifier to parse

    Returns:
      project_id, dataset_id, table_id: (string, string, string)
    """
    return bq_client_utils._ParseIdentifier(identifier)
  # pylint: enable=protected-access

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetProjectReference(self, identifier=''):
    """Determine a project reference from an identifier and self."""
    return bq_client_utils.GetProjectReference(
        id_fallbacks=self,
        identifier=identifier
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetDatasetReference(self, identifier=''):
    """Determine a DatasetReference from an identifier and self."""
    return bq_client_utils.GetDatasetReference(
        id_fallbacks=self,
        identifier=identifier
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetTableReference(self, identifier='', default_dataset_id=''):
    """Determine a TableReference from an identifier and self."""
    return bq_client_utils.GetTableReference(
        id_fallbacks=self,
        identifier=identifier,
        default_dataset_id=default_dataset_id
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetModelReference(self, identifier=''):
    """Returns a ModelReference from an identifier."""
    return bq_client_utils.GetModelReference(
        id_fallbacks=self,
        identifier=identifier
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetRoutineReference(self, identifier=''):
    """Returns a RoutineReference from an identifier."""
    return bq_client_utils.GetRoutineReference(
        id_fallbacks=self,
        identifier=identifier
    )

  # TODO(b/324243535): Delete these once the migration is complete.
  def GetQueryDefaultDataset(self, identifier):
    return bq_client_utils.GetQueryDefaultDataset(self, identifier)

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetReference(self, identifier=''):
    """Try to deduce a project/dataset/table reference from a string.

    If the identifier is not compound, treat it as the most specific
    identifier we don't have as a flag, or as the table_id. If it is
    compound, fill in any unspecified part.

    Args:
      identifier: string, Identifier to create a reference for.

    Returns:
      A valid ProjectReference, DatasetReference, or TableReference.

    Raises:
      bq_error.BigqueryError: if no valid reference can be determined.
    """
    return bq_client_utils.GetReference(
        id_fallbacks=self,
        identifier=identifier
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetJobReference(self, identifier='', default_location=None):
    """Determine a JobReference from an identifier, location, and self."""
    return bq_client_utils.GetJobReference(
        id_fallbacks=self,
        identifier=identifier,
        default_location=default_location
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetReservationReference(self,
                              identifier=None,
                              default_location=None,
                              default_reservation_id=None,
                              check_reservation_project=True):
    """Determine a ReservationReference from an identifier and location."""
    return bq_client_utils.GetReservationReference(
        id_fallbacks=self,
        identifier=identifier,
        default_location=default_location,
        default_reservation_id=default_reservation_id,
        check_reservation_project=check_reservation_project
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetBiReservationReference(self, default_location=None):
    """Determine a ReservationReference from an identifier and location."""
    return bq_client_utils.GetBiReservationReference(
        id_fallbacks=self,
        default_location=default_location
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetCapacityCommitmentReference(self,
                                     identifier=None,
                                     path=None,
                                     default_location=None,
                                     default_capacity_commitment_id=None,
                                     allow_commas=None):
    """Determine a CapacityCommitmentReference from an identifier and location."""
    return bq_client_utils.GetCapacityCommitmentReference(
        id_fallbacks=self,
        identifier=identifier,
        path=path,
        default_location=default_location,
        default_capacity_commitment_id=default_capacity_commitment_id,
        allow_commas=allow_commas
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetReservationAssignmentReference(self,
                                        identifier=None,
                                        path=None,
                                        default_location=None,
                                        default_reservation_id=None,
                                        default_reservation_assignment_id=None):
    """Determine a ReservationAssignmentReference from an identifier and location."""
    return bq_client_utils.GetReservationAssignmentReference(
        id_fallbacks=self,
        identifier=identifier,
        path=path,
        default_location=default_location,
        default_reservation_id=default_reservation_id,
        default_reservation_assignment_id=default_reservation_assignment_id
    )

  # TODO(b/324243535): Migrate `bq.py` off of this.
  def GetConnectionReference(self,
                             identifier=None,
                             path=None,
                             default_location=None,
                             default_connection_id=None):
    """Determine a ConnectionReference from an identifier and location."""
    return bq_client_utils.GetConnectionReference(
        id_fallbacks=self,
        identifier=identifier,
        path=path,
        default_location=default_location,
        default_connection_id=default_connection_id
    )

  def GetObjectInfo(self, reference):
    """Get all data returned by the server about a specific object."""
    # Projects are handled separately, because we only have
    # bigquery.projects.list.
    if isinstance(reference, bq_id_utils.ApiClientHelper.ProjectReference):
      max_project_results = 1000
      projects = self.ListProjects(max_results=max_project_results)
      for project in projects:
        if bq_processor_utils.ConstructObjectReference(project) == reference:
          project['kind'] = 'bigquery#project'
          return project
      if len(projects) >= max_project_results:
        raise bq_error.BigqueryError(
            'Number of projects found exceeded limit, please instead run'
            ' gcloud projects describe %s' % (reference,),
        )
      raise bq_error.BigqueryNotFoundError('Unknown %r' % (reference,),
                                           {'reason': 'notFound'}, [])

    if isinstance(reference, bq_id_utils.ApiClientHelper.JobReference):
      return self.apiclient.jobs().get(**dict(reference)).execute()
    elif isinstance(reference, bq_id_utils.ApiClientHelper.DatasetReference):
      return self.apiclient.datasets().get(**dict(reference)).execute()
    elif isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
      return self.apiclient.tables().get(**dict(reference)).execute()
    elif isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference):
      return self.GetModelsApiClient().models().get(
          projectId=reference.projectId,
          datasetId=reference.datasetId,
          modelId=reference.modelId).execute()
    elif isinstance(reference, bq_id_utils.ApiClientHelper.RoutineReference):
      return self.GetRoutinesApiClient().routines().get(
          projectId=reference.projectId,
          datasetId=reference.datasetId,
          routineId=reference.routineId).execute()
    else:
      raise TypeError('Type of reference must be one of: ProjectReference, '
                      'JobReference, DatasetReference, or TableReference')

  def GetTableSchema(self, table_dict):
    table_info = self.apiclient.tables().get(**table_dict).execute()
    return table_info.get('schema', {})

  def InsertTableRows(self,
                      table_dict,
                      inserts,
                      skip_invalid_rows=None,
                      ignore_unknown_values=None,
                      template_suffix=None):
    """Insert rows into a table.

    Arguments:
      table_dict: table reference into which rows are to be inserted.
      inserts: array of InsertEntry tuples where insert_id can be None.
      skip_invalid_rows: Optional. Attempt to insert any valid rows, even if
        invalid rows are present.
      ignore_unknown_values: Optional. Ignore any values in a row that are not
        present in the schema.
      template_suffix: Optional. The suffix used to generate the template
        table's name.

    Returns:
      result of the operation.
    """

    def _EncodeInsert(insert):
      encoded = dict(json=insert.record)
      if insert.insert_id:
        encoded['insertId'] = insert.insert_id
      return encoded

    op = self.GetInsertApiClient().tabledata().insertAll(
        body=dict(
            skipInvalidRows=skip_invalid_rows,
            ignoreUnknownValues=ignore_unknown_values,
            templateSuffix=template_suffix,
            rows=list(map(_EncodeInsert, inserts))),
        **table_dict)
    return op.execute()

  def GetTransferConfig(self, transfer_id):
    client = self.GetTransferV1ApiClient()
    return client.projects().locations().transferConfigs().get(
        name=transfer_id).execute()

  def GetTransferRun(self, identifier):
    transfer_client = self.GetTransferV1ApiClient()
    return transfer_client.projects().locations().transferConfigs().runs().get(
        name=identifier).execute()

  def GetBodyForCreateReservation(
      self,
      slots: int,
      ignore_idle_slots: bool,
      edition,
      target_job_concurrency: int,
      multi_region_auxiliary: bool,
      autoscale_max_slots: int = None,
  ) -> Dict[str, Any]:
    """Return the request body for CreateReservation.

    Arguments:
      slots: Number of slots allocated to this reservation subtree.
      ignore_idle_slots: Specifies whether queries should ignore idle slots from
        other reservations.
      edition: The edition for this reservation.
      target_job_concurrency: Job concurrency target.
      multi_region_auxiliary: Whether this reservation is for the auxiliary
        region.
      autoscale_max_slots: Number of slots to be scaled when needed.

    Returns:
      Reservation object that was created.

    Raises:
      bq_error.BigqueryError: if autoscale_max_slots is used with other
        version.
    """
    reservation = {}
    reservation['slot_capacity'] = slots
    reservation['ignore_idle_slots'] = ignore_idle_slots
    if multi_region_auxiliary is not None:
      reservation['multi_region_auxiliary'] = multi_region_auxiliary
    if target_job_concurrency is not None:
      reservation['concurrency'] = target_job_concurrency

    if autoscale_max_slots is not None:
      reservation['autoscale'] = {}
      reservation['autoscale']['max_slots'] = autoscale_max_slots


    if edition is not None:
      reservation['edition'] = edition

    return reservation

  def CreateReservation(
      self,
      reference,
      slots: int,
      ignore_idle_slots: bool,
      edition,
      target_job_concurrency: int,
      multi_region_auxiliary: bool,
      autoscale_max_slots: int = None,
  ) -> Dict[str, Any]:
    """Create a reservation with the given reservation reference.

    Arguments:
      reference: Reservation to create.
      slots: Number of slots allocated to this reservation subtree.
      ignore_idle_slots: Specifies whether queries should ignore idle slots from
        other reservations.
      edition: The edition for this reservation.
      target_job_concurrency: Job concurrency target.
      multi_region_auxiliary: Whether this reservation is for the auxiliary
        region.
      autoscale_max_slots: Number of slots to be scaled when needed.

    Returns:
      Reservation object that was created.

    Raises:
      bq_error.BigqueryError: if autoscale_max_slots is used with other
        version.
    """
    reservation = self.GetBodyForCreateReservation(
        slots,
        ignore_idle_slots,
        edition,
        target_job_concurrency,
        multi_region_auxiliary,
        autoscale_max_slots,
    )
    client = self.GetReservationApiClient()
    parent = 'projects/%s/locations/%s' % (reference.projectId,
                                           reference.location)
    return client.projects().locations().reservations().create(
        parent=parent, body=reservation,
        reservationId=reference.reservationId).execute()

  def ListReservations(self, reference, page_size, page_token):
    """List reservations in the project and location for the given reference.

    Arguments:
      reference: Reservation reference containing project and location.
      page_size: Number of results to show.
      page_token: Token to retrieve the next page of results.

    Returns:
      Reservation object that was created.
    """
    parent = 'projects/%s/locations/%s' % (reference.projectId,
                                           reference.location)
    client = self.GetReservationApiClient()
    return client.projects().locations().reservations().list(
        parent=parent, pageSize=page_size, pageToken=page_token).execute()

  def ListBiReservations(self, reference):
    """List BI reservations in the project and location for the given reference.

    Arguments:
      reference: Reservation reference containing project and location.

    Returns:
      List of BI reservations in the given project/location.
    """
    parent = 'projects/%s/locations/%s/biReservation' % (reference.projectId,
                                                         reference.location)
    client = self.GetReservationApiClient()
    response = client.projects().locations().getBiReservation(
        name=parent).execute()
    return response

  def GetReservation(self, reference):
    """Gets a reservation with the given reservation reference.

    Arguments:
      reference: Reservation to get.

    Returns:
      Reservation object corresponding to the given id.
    """
    client = self.GetReservationApiClient()
    return client.projects().locations().reservations().get(
        name=reference.path()).execute()

  def DeleteReservation(
      self,
      reference: ...
  ):
    """Deletes a reservation with the given reservation reference.

    Arguments:
      reference: Reservation to delete.
    """
    client = self.GetReservationApiClient()
    client.projects().locations().reservations().delete(
        name=reference.path()
    ).execute()

  def UpdateBiReservation(self, reference, reservation_size):
    """Updates a BI reservation with the given reservation reference.

    Arguments:
      reference: Reservation to update.
      reservation_size: size of reservation in GBs. It may only contain digits,
        optionally followed by 'G', 'g', 'GB, 'gb', 'gB', or 'Gb'.

    Returns:
      Reservation object that was updated.
    Raises:
      ValueError: if reservation_size is malformed.
    """
    client = self.GetReservationApiClient()

    if (reservation_size.upper().endswith('GB') and
        reservation_size[:-2].isdigit()):
      reservation_digits = reservation_size[:-2]
    elif (reservation_size.upper().endswith('G') and
          reservation_size[:-1].isdigit()):
      reservation_digits = reservation_size[:-1]
    elif reservation_size.isdigit():
      reservation_digits = reservation_size
    else:
      raise ValueError("""Invalid reservation size. The unit for BI reservations
      is GB. The specified reservation size may only contain digits, optionally
      followed by G, g, GB, gb, gB, or Gb.""")

    reservation_size = int(reservation_digits) * 1024 * 1024 * 1024

    bi_reservation = {}
    update_mask = ''
    bi_reservation['size'] = reservation_size
    update_mask += 'size,'
    return client.projects().locations().updateBiReservation(
        name=reference.path(), updateMask=update_mask,
        body=bi_reservation).execute()


  def GetParamsForUpdateReservation(
      self,
      slots,
      ignore_idle_slots,
      target_job_concurrency,
      autoscale_max_slots,
  ):
    """Return the request body and update mask for UpdateReservation.

    Arguments:
      slots: Number of slots allocated to this reservation subtree.
      ignore_idle_slots: Specifies whether queries should ignore idle slots from
        other reservations.
      target_job_concurrency: Job concurrency target.
      autoscale_max_slots: Number of slots to be scaled when needed.

    Returns:
      Reservation object that was updated.

    Raises:
      bq_error.BigqueryError: if autoscale_max_slots is used with other
        version.
    """
    reservation = {}
    update_mask = ''
    if slots is not None:
      reservation['slot_capacity'] = slots
      update_mask += 'slot_capacity,'

    if ignore_idle_slots is not None:
      reservation['ignore_idle_slots'] = ignore_idle_slots
      update_mask += 'ignore_idle_slots,'

    if target_job_concurrency is not None:
      reservation['concurrency'] = target_job_concurrency
      update_mask += 'concurrency,'

    if autoscale_max_slots is not None:
      if autoscale_max_slots != 0:
        reservation['autoscale'] = {}
        reservation['autoscale']['max_slots'] = autoscale_max_slots
        update_mask += 'autoscale.max_slots,'
      else:
        # Disable autoscale.
        update_mask += 'autoscale,'

    return reservation, update_mask

  def UpdateReservation(
      self,
      reference,
      slots,
      ignore_idle_slots,
      target_job_concurrency,
      autoscale_max_slots,
  ):
    """Updates a reservation with the given reservation reference.

    Arguments:
      reference: Reservation to update.
      slots: Number of slots allocated to this reservation subtree.
      ignore_idle_slots: Specifies whether queries should ignore idle slots from
        other reservations.
      target_job_concurrency: Job concurrency target.
      autoscale_max_slots: Number of slots to be scaled when needed.

    Returns:
      Reservation object that was updated.

    Raises:
      bq_error.BigqueryError: if autoscale_max_slots is used with other
        version.
    """
    reservation, update_mask = self.GetParamsForUpdateReservation(
        slots,
        ignore_idle_slots,
        target_job_concurrency,
        autoscale_max_slots,
    )
    client = self.GetReservationApiClient()
    return client.projects().locations().reservations().patch(
        name=reference.path(), updateMask=update_mask,
        body=reservation).execute()

  def CreateCapacityCommitment(
      self,
      reference,
      edition,
      slots: int,
      plan: str,
      renewal_plan: str,
      multi_region_auxiliary: bool,
  ) -> Dict[str, Any]:
    """Create a capacity commitment.

    Arguments:
      reference: Project to create a capacity commitment within.
      edition: The edition for this capacity commitment.
      slots: Number of slots in this commitment.
      plan: Commitment plan for this capacity commitment.
      renewal_plan: Renewal plan for this capacity commitment.
      multi_region_auxiliary: Whether this commitment is for the auxiliary
        region.

    Returns:
      Capacity commitment object that was created.
    """
    capacity_commitment = {}
    capacity_commitment['slot_count'] = slots
    capacity_commitment['plan'] = plan
    capacity_commitment['renewal_plan'] = renewal_plan
    if multi_region_auxiliary is not None:
      capacity_commitment['multi_region_auxiliary'] = multi_region_auxiliary
    if edition is not None:
      capacity_commitment['edition'] = edition
    client = self.GetReservationApiClient()
    parent = 'projects/%s/locations/%s' % (reference.projectId,
                                           reference.location)
    request = client.projects().locations().capacityCommitments().create(
        parent=parent, body=capacity_commitment)
    return request.execute()

  def ListCapacityCommitments(self, reference, page_size, page_token):
    """Lists capacity commitments for given project and location.

    Arguments:
      reference: Reference to the project and location.
      page_size: Number of results to show.
      page_token: Token to retrieve the next page of results.

    Returns:
      list of CapacityCommitments objects.
    """
    parent = 'projects/%s/locations/%s' % (reference.projectId,
                                           reference.location)
    client = self.GetReservationApiClient()
    return client.projects().locations().capacityCommitments().list(
        parent=parent, pageSize=page_size, pageToken=page_token).execute()

  def GetCapacityCommitment(self, reference):
    """Gets a capacity commitment with the given capacity commitment reference.

    Arguments:
      reference: Capacity commitment to get.

    Returns:
      Capacity commitment object corresponding to the given id.
    """
    client = self.GetReservationApiClient()
    return client.projects().locations().capacityCommitments().get(
        name=reference.path()).execute()

  def DeleteCapacityCommitment(self, reference, force=None):
    """Deletes a capacity commitment with the given capacity commitment reference.

    Arguments:
      reference: Capacity commitment to delete.
      force: Force delete capacity commitment, ignoring commitment end time.
    """
    client = self.GetReservationApiClient()
    client.projects().locations().capacityCommitments().delete(
        name=reference.path(), force=force).execute()

  def UpdateCapacityCommitment(self, reference, plan, renewal_plan):
    """Updates a capacity commitment with the given reference.

    Arguments:
      reference: Capacity commitment to update.
      plan: Commitment plan for this capacity commitment.
      renewal_plan: Renewal plan for this capacity commitment.

    Returns:
      Capacity commitment object that was updated.

    Raises:
      bq_error.BigqueryError: if capacity commitment cannot be updated.
    """
    if plan is None and renewal_plan is None:
      raise bq_error.BigqueryError('Please specify fields to be updated.')
    capacity_commitment = {}
    update_mask = []
    if plan is not None:
      capacity_commitment['plan'] = plan
      update_mask.append('plan')
    if renewal_plan is not None:
      capacity_commitment['renewal_plan'] = renewal_plan
      update_mask.append('renewal_plan')

    client = self.GetReservationApiClient()
    return client.projects().locations().capacityCommitments().patch(
        name=reference.path(),
        updateMask=','.join(update_mask),
        body=capacity_commitment).execute()

  def SplitCapacityCommitment(self, reference, slots):
    """Splits a capacity commitment with the given reference into two.

    Arguments:
      reference: Capacity commitment to split.
      slots: Number of slots in the first capacity commitment after the split.

    Returns:
      List of capacity commitment objects after the split.

    Raises:
      bq_error.BigqueryError: if capacity commitment cannot be updated.
    """
    if slots is None:
      raise bq_error.BigqueryError('Please specify slots for the split.')
    client = self.GetReservationApiClient()
    body = {'slotCount': slots}
    response = client.projects().locations().capacityCommitments().split(
        name=reference.path(), body=body).execute()
    if 'first' not in response or 'second' not in response:
      raise bq_error.BigqueryError('internal error')
    return [response['first'], response['second']]

  def MergeCapacityCommitments(self, location, capacity_commitment_ids):
    """Merges capacity commitments into one.

    Arguments:
      location: Capacity commitments location.
      capacity_commitment_ids: List of capacity commitment ids.

    Returns:
      Merged capacity commitment.

    Raises:
      bq_error.BigqueryError: if capacity commitment cannot be merged.
    """
    if not self.project_id:
      raise bq_error.BigqueryError('project id must be specified.')
    if not location:
      raise bq_error.BigqueryError('location must be specified.')
    if capacity_commitment_ids is None or len(capacity_commitment_ids) < 2:
      raise bq_error.BigqueryError(
          'at least 2 capacity commitments must be specified.')
    client = self.GetReservationApiClient()
    parent = 'projects/%s/locations/%s' % (self.project_id, location)
    body = {'capacityCommitmentIds': capacity_commitment_ids}
    return client.projects().locations().capacityCommitments().merge(
        parent=parent, body=body).execute()

  def CreateReservationAssignment(self, reference, job_type, priority,
                                  assignee_type, assignee_id):
    """Creates a reservation assignment for a given project/folder/organization.

    Arguments:
      reference: Reference to the project reservation is assigned. Location must
        be the same location as the reservation.
      job_type: Type of jobs for this assignment.
      priority: Default job priority for this assignment.
      assignee_type: Type of assignees for the reservation assignment.
      assignee_id: Project/folder/organization ID, to which the reservation is
        assigned.

    Returns:
      ReservationAssignment object that was created.

    Raises:
      bq_error.BigqueryError: if assignment cannot be created.
    """
    reservation_assignment = {}
    if not job_type:
      raise bq_error.BigqueryError('job_type not specified.')
    reservation_assignment['job_type'] = job_type
    if priority:
      reservation_assignment['priority'] = priority
    if not assignee_type:
      raise bq_error.BigqueryError('assignee_type not specified.')
    if not assignee_id:
      raise bq_error.BigqueryError('assignee_id not specified.')
    # assignee_type is singular, that's why we need additional 's' inside
    # format string for assignee below.
    reservation_assignment['assignee'] = '%ss/%s' % (assignee_type.lower(),
                                                     assignee_id)
    client = self.GetReservationApiClient()
    return client.projects().locations().reservations().assignments().create(
        parent=reference.path(), body=reservation_assignment).execute()

  def DeleteReservationAssignment(self, reference):
    """Deletes given reservation assignment.

    Arguments:
      reference: Reference to the reservation assignment.
    """
    client = self.GetReservationApiClient()
    client.projects().locations().reservations().assignments().delete(
        name=reference.path()).execute()

  def MoveReservationAssignment(self, reference, destination_reservation_id,
                                default_location):
    """Moves given reservation assignment under another reservation."""
    destination_reservation_reference = self.GetReservationReference(
        identifier=destination_reservation_id,
        default_location=default_location,
        check_reservation_project=False)
    client = self.GetReservationApiClient()
    body = {'destinationId': destination_reservation_reference.path()}

    return client.projects().locations().reservations().assignments().move(
        name=reference.path(), body=body).execute()

  def UpdateReservationAssignment(self, reference, priority):
    """Updates reservation assignment.

    Arguments:
      reference: Reference to the reservation assignment.
      priority: Default job priority for this assignment.

    Returns:
      Reservation assignment object that was updated.

    Raises:
      bq_error.BigqueryError: if assignment cannot be updated.
    """
    reservation_assignment = {}
    update_mask = ''
    if priority is not None:
      if not priority:
        priority = 'JOB_PRIORITY_UNSPECIFIED'
      reservation_assignment['priority'] = priority
      update_mask += 'priority,'

    client = self.GetReservationApiClient()
    return client.projects().locations().reservations().assignments().patch(
        name=reference.path(),
        updateMask=update_mask,
        body=reservation_assignment).execute()

  def ListReservationAssignments(self, reference, page_size, page_token):
    """Lists reservation assignments for given project and location.

    Arguments:
      reference: Reservation reference for the parent.
      page_size: Number of results to show.
      page_token: Token to retrieve the next page of results.

    Returns:
      ReservationAssignment object that was created.
    """
    client = self.GetReservationApiClient()
    return client.projects().locations().reservations().assignments().list(
        parent=reference.path(), pageSize=page_size,
        pageToken=page_token).execute()


  def SearchAllReservationAssignments(
      self,
      location: str,
      job_type: str,
      assignee_type: str,
      assignee_id: str) -> Dict[str, Any]:
    """Searches reservations assignments for given assignee.

    Arguments:
      location: location of interest.
      job_type: type of job to be queried.
      assignee_type: Type of assignees for the reservation assignment.
      assignee_id: Project/folder/organization ID, to which the reservation is
        assigned.

    Returns:
      ReservationAssignment object if it exists.

    Raises:
      bq_error.BigqueryError: If required parameters are not passed in or
        reservation assignment not found.
    """
    if not location:
      raise bq_error.BigqueryError('location not specified.')
    if not job_type:
      raise bq_error.BigqueryError('job_type not specified.')
    if not assignee_type:
      raise bq_error.BigqueryError('assignee_type not specified.')
    if not assignee_id:
      raise bq_error.BigqueryError('assignee_id not specified.')
    # assignee_type is singular, that's why we need additional 's' inside
    # format string for assignee below.
    assignee = '%ss/%s' % (assignee_type.lower(), assignee_id)
    query = 'assignee=%s' % assignee
    parent = 'projects/-/locations/%s' % location
    client = self.GetReservationApiClient()

    response = client.projects().locations().searchAllAssignments(
        parent=parent, query=query).execute()
    if 'assignments' in response:
      for assignment in response['assignments']:
        if assignment['jobType'] == job_type:
          return assignment
    raise bq_error.BigqueryError('Reservation assignment not found')

  def GetConnection(self, reference):
    """Gets connection with the given connection reference.

    Arguments:
      reference: Connection to get.

    Returns:
      Connection object with the given id.
    """
    client = self.GetConnectionV1ApiClient()
    return client.projects().locations().connections().get(
        name=reference.path()).execute()

  def CreateConnection(
      self,
      project_id,
      location,
      connection_type,
      properties,
      connection_credential=None,
      display_name=None,
      description=None,
      connection_id=None,
      kms_key_name=None,
      connector_configuration=None,
  ):
    """Create a connection with the given connection reference.

    Arguments:
      project_id: Project ID.
      location: Location of connection.
      connection_type: Type of connection, allowed values: ['CLOUD_SQL']
      properties: Connection properties in JSON format.
      connection_credential: Connection credentials in JSON format.
      display_name: Friendly name for the connection.
      description: Description of the connection.
      connection_id: Optional connection ID.
      kms_key_name: Optional KMS key name.
      connector_configuration: Optional configuration for connector.

    Returns:
      Connection object that was created.
    """

    connection = {}

    if display_name:
      connection['friendlyName'] = display_name

    if description:
      connection['description'] = description

    if kms_key_name:
      connection['kmsKeyName'] = kms_key_name

    property_name = bq_client_utils.CONNECTION_TYPE_TO_PROPERTY_MAP.get(
        connection_type)
    if property_name:
      connection[property_name] = bq_processor_utils.ParseJson(properties)
      if connection_credential:
        connection[property_name]['credential'] = bq_processor_utils.ParseJson(
            connection_credential
        )
    elif connector_configuration:
      connection['configuration'] = bq_processor_utils.ParseJson(
          connector_configuration
      )
    else:
      error = (
          'connection_type %s is unsupported or connector_configuration is not'
          ' specified' % connection_type
      )
      raise ValueError(error)

    client = self.GetConnectionV1ApiClient()
    parent = 'projects/%s/locations/%s' % (project_id, location)
    return client.projects().locations().connections().create(
        parent=parent, connectionId=connection_id, body=connection).execute()

  def UpdateConnection(
      self,
      reference,
      connection_type,
      properties,
      connection_credential=None,
      display_name=None,
      description=None,
      kms_key_name=None,
      connector_configuration=None,
  ):
    """Update connection with the given connection reference.

    Arguments:
      reference: Connection to update
      connection_type: Type of connection, allowed values: ['CLOUD_SQL']
      properties: Connection properties
      connection_credential: Connection credentials in JSON format.
      display_name: Friendly name for the connection
      description: Description of the connection
      kms_key_name: Optional KMS key name.
      connector_configuration: Optional configuration for connector
    Raises:
      bq_error.BigqueryClientError: The connection type is not defined
        when updating
      connection_credential or properties.
    Returns:
      Connection object that was created.
    """

    if (connection_credential or properties) and not connection_type:
      raise bq_error.BigqueryClientError(
          'connection_type is required when updating connection_credential or'
          ' properties'
      )
    connection = {}
    update_mask = []

    def GetUpdateMask(base_path, json_properties):
      """Creates an update mask from json_properties.

      Arguments:
        base_path: 'cloud_sql'
        json_properties: { 'host': ... , 'instanceId': ... }

      Returns:
         list of  paths in snake case:
         mask = ['cloud_sql.host', 'cloud_sql.instance_id']
      """
      return [
          base_path + '.' + inflection.underscore(json_property)
          for json_property in json_properties
      ]

    def GetUpdateMaskRecursively(prefix, json_value):
      if not isinstance(json_value, dict):
        return [inflection.underscore(prefix)]

      result = []
      for name in json_value:
        new_prefix = prefix + '.' + name
        new_json_value = json_value.get(name)
        result.extend(GetUpdateMaskRecursively(new_prefix, new_json_value))

      return result

    if display_name:
      connection['friendlyName'] = display_name
      update_mask.append('friendlyName')

    if description:
      connection['description'] = description
      update_mask.append('description')

    if kms_key_name is not None:
      update_mask.append('kms_key_name')
    if kms_key_name:
      connection['kmsKeyName'] = kms_key_name

    if connection_type == 'CLOUD_SQL':
      if properties:
        cloudsql_properties = bq_processor_utils.ParseJson(properties)
        connection['cloudSql'] = cloudsql_properties

        update_mask.extend(
            GetUpdateMask(connection_type.lower(), cloudsql_properties))

      else:
        connection['cloudSql'] = {}

      if connection_credential:
        connection['cloudSql']['credential'] = bq_processor_utils.ParseJson(
            connection_credential
        )
        update_mask.append('cloudSql.credential')

    elif connection_type == 'AWS':

      if properties:
        aws_properties = bq_processor_utils.ParseJson(properties)
        connection['aws'] = aws_properties
        if aws_properties.get('crossAccountRole') and \
            aws_properties['crossAccountRole'].get('iamRoleId'):
          update_mask.append('aws.crossAccountRole.iamRoleId')
        if aws_properties.get('accessRole') and \
            aws_properties['accessRole'].get('iamRoleId'):
          update_mask.append('aws.access_role.iam_role_id')
      else:
        connection['aws'] = {}

      if connection_credential:
        connection['aws']['credential'] = bq_processor_utils.ParseJson(
            connection_credential
        )
        update_mask.append('aws.credential')

    elif connection_type == 'Azure':
      if properties:
        azure_properties = bq_processor_utils.ParseJson(properties)
        connection['azure'] = azure_properties
        if azure_properties.get('customerTenantId'):
          update_mask.append('azure.customer_tenant_id')
        if azure_properties.get('federatedApplicationClientId'):
          update_mask.append('azure.federated_application_client_id')

    elif connection_type == 'SQL_DATA_SOURCE':
      if properties:
        sql_data_source_properties = bq_processor_utils.ParseJson(properties)
        connection['sqlDataSource'] = sql_data_source_properties

        update_mask.extend(
            GetUpdateMask(connection_type.lower(), sql_data_source_properties))

      else:
        connection['sqlDataSource'] = {}

      if connection_credential:
        connection['sqlDataSource']['credential'] = (
            bq_processor_utils.ParseJson(connection_credential)
        )
        update_mask.append('sqlDataSource.credential')

    elif connection_type == 'CLOUD_SPANNER':
      if properties:
        cloudspanner_properties = bq_processor_utils.ParseJson(properties)
        connection['cloudSpanner'] = cloudspanner_properties
        update_mask.extend(
            GetUpdateMask(connection_type.lower(), cloudspanner_properties))
      else:
        connection['cloudSpanner'] = {}

    elif connection_type == 'SPARK':
      if properties:
        spark_properties = bq_processor_utils.ParseJson(properties)
        connection['spark'] = spark_properties
        if 'sparkHistoryServerConfig' in spark_properties:
          update_mask.append('spark.spark_history_server_config')
        if 'metastoreServiceConfig' in spark_properties:
          update_mask.append('spark.metastore_service_config')
      else:
        connection['spark'] = {}
    elif connector_configuration:
      connection['configuration'] = bq_processor_utils.ParseJson(
          connector_configuration
      )
      update_mask.extend(
          GetUpdateMaskRecursively('configuration', connection['configuration'])
      )

    client = self.GetConnectionV1ApiClient()

    return client.projects().locations().connections().patch(
        name=reference.path(),
        updateMask=','.join(update_mask),
        body=connection).execute()

  def DeleteConnection(self, reference):
    """Delete a connection with the given connection reference.

    Arguments:
      reference: Connection to delete.
    """
    client = self.GetConnectionV1ApiClient()
    client.projects().locations().connections().delete(
        name=reference.path()).execute()

  def ListConnections(
      self,
      project_id: string,
      location: string,
      max_results: int,
      page_token: Optional[str],
  ):
    """List connections in the project and location for the given reference.

    Arguments:
      project_id: Project ID.
      location: Location.
      max_results: Number of results to show.
      page_token: Token to retrieve the next page of results.

    Returns:
      List of connection objects
    """
    parent = 'projects/%s/locations/%s' % (project_id, location)
    client = self.GetConnectionV1ApiClient()
    return client.projects().locations().connections().list(
        parent=parent, pageToken=page_token, pageSize=max_results).execute()

  def SetConnectionIAMPolicy(self, reference, policy):
    """Sets IAM policy for the given connection resource.

    Arguments:
      reference: the ConnectionReference for the connection resource.
      policy: The policy string in JSON format.

    Returns:
      The updated IAM policy attached to the given connection resource.

    Raises:
      TypeError: if reference is not a ConnectionReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ConnectionReference,
        method='SetConnectionIAMPolicy',
    )
    client = self.GetConnectionV1ApiClient()
    return client.projects().locations().connections().setIamPolicy(
        resource=reference.path(), body={'policy': policy}
    ).execute()

  def GetConnectionIAMPolicy(self, reference):
    """Gets IAM policy for the given connection resource.

    Arguments:
      reference: the ConnectionReference for the connection resource.

    Returns:
      The IAM policy attached to the given connection resource.

    Raises:
      TypeError: if reference is not a ConnectionReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ConnectionReference,
        method='GetConnectionIAMPolicy',
    )
    client = self.GetConnectionV1ApiClient()
    return (
        client.projects()
        .locations()
        .connections()
        .getIamPolicy(resource=reference.path())
        .execute()
    )

  def ReadSchemaAndRows(self,
                        table_dict,
                        start_row=None,
                        max_rows=None,
                        selected_fields=None):
    """Convenience method to get the schema and rows from a table.

    Arguments:
      table_dict: table reference dictionary.
      start_row: first row to read.
      max_rows: number of rows to read.
      selected_fields: a subset of fields to return.

    Returns:
      A tuple where the first item is the list of fields and the
      second item a list of rows.

    Raises:
      ValueError: will be raised if start_row is not explicitly provided.
      ValueError: will be raised if max_rows is not explicitly provided.
    """
    if start_row is None:
      raise ValueError('start_row is required')
    if max_rows is None:
      raise ValueError('max_rows is required')
    table_ref = bq_id_utils.ApiClientHelper.TableReference.Create(**table_dict)
    table_reader = _TableTableReader(self.apiclient, self.max_rows_per_request,
                                     table_ref)
    return table_reader.ReadSchemaAndRows(
        start_row, max_rows, selected_fields=selected_fields)

  def ReadSchemaAndJobRows(self,
                           job_dict,
                           start_row=None,
                           max_rows=None,
                           result_first_page=None):
    """Convenience method to get the schema and rows from job query result.

    Arguments:
      job_dict: job reference dictionary.
      start_row: first row to read.
      max_rows: number of rows to read.
      result_first_page: the first page of the result of a query job.

    Returns:
      A tuple where the first item is the list of fields and the
      second item a list of rows.
    Raises:
      ValueError: will be raised if start_row is not explicitly provided.
      ValueError: will be raised if max_rows is not explicitly provided.
    """
    if start_row is None:
      raise ValueError('start_row is required')
    if max_rows is None:
      raise ValueError('max_rows is required')
    if not job_dict:
      job_ref: bq_id_utils.ApiClientHelper.JobReference = None
    else:
      job_ref = bq_id_utils.ApiClientHelper.JobReference.Create(**job_dict)
    if flags.FLAGS.jobs_query_use_results_from_response and result_first_page:
      reader = _QueryTableReader(self.apiclient, self.max_rows_per_request,
                                 job_ref, result_first_page)
    else:
      reader = _JobTableReader(self.apiclient, self.max_rows_per_request,
                               job_ref)
    return reader.ReadSchemaAndRows(start_row, max_rows)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def ConfigureFormatter(formatter,
                         reference_type,
                         print_format='list',
                         object_info=None):
    """Configure a formatter for a given reference type.

    If print_format is 'show', configures the formatter with several
    additional fields (useful for printing a single record).

    Arguments:
      formatter: TableFormatter object to configure.
      reference_type: Type of object this formatter will be used with.
      print_format: Either 'show' or 'list' to control what fields are included.

    Raises:
      ValueError: If reference_type or format is unknown.
    """
    return bq_client_utils.ConfigureFormatter(
        formatter, reference_type, print_format, object_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def RaiseError(result):
    """Raises an appropriate BigQuery error given the json error result."""
    return bq_client_utils.RaiseError(result)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def IsFailedJob(job):
    """Predicate to determine whether or not a job failed."""
    return bq_client_utils.IsFailedJob(job)

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def GetSessionId(job):
    """Helper to return the session id if the job is part of one.

    Args:
      job: a job resource to get statistics and sessionInfo from.

    Returns:
      sessionId, if the job is part of a session.
    """
    return bq_processor_utils.GetSessionId(job)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def RaiseIfJobError(job):
    """Raises a BigQueryError if the job is in an error state.

    Args:
      job: a Job resource.

    Returns:
      job, if it is not in an error state.

    Raises:
      bq_error.BigqueryError: A bq_error.BigqueryError instance
        based on the job's error description.
    """
    return bq_client_utils.RaiseIfJobError(job)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def GetJobTypeName(job_info):
    """Helper for job printing code."""
    return bq_client_utils.GetJobTypeName(job_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def ProcessSources(source_string):
    """Take a source string and return a list of URIs.

    The list will consist of either a single local filename, which
    we check exists and is a file, or a list of gs:// uris.

    Args:
      source_string: A comma-separated list of URIs.

    Returns:
      List of one or more valid URIs, as strings.

    Raises:
      bq_error.BigqueryClientError: if no valid list of sources can be
        determined.
    """
    return bq_client_utils.ProcessSources(source_string)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def ReadSchema(schema):
    """Create a schema from a string or a filename.

    If schema does not contain ':' and is the name of an existing
    file, read it as a JSON schema. If not, it must be a
    comma-separated list of fields in the form name:type.

    Args:
      schema: A filename or schema.

    Returns:
      The new schema (as a dict).

    Raises:
      bq_error.BigquerySchemaError: If the schema is invalid or the
        filename does not exist.
    """
    return bq_client_utils.ReadSchema(schema)

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def _KindToName(kind):
    """Convert a kind to just a type name."""
    bq_processor_utils.KindToName(kind)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatInfoByType(object_info, object_type):
    """Format a single object_info (based on its 'kind' attribute)."""
    return bq_client_utils.FormatInfoByType(object_info, object_type)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatJobInfo(job_info):
    """Prepare a job_info for printing.

    Arguments:
      job_info: Job dict to format.

    Returns:
      The new job_info.
    """
    return bq_client_utils.FormatJobInfo(job_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatProjectInfo(project_info):
    """Prepare a project_info for printing.

    Arguments:
      project_info: Project dict to format.

    Returns:
      The new project_info.
    """
    return bq_client_utils.FormatProjectInfo(project_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatModelInfo(model_info):
    """Prepare a model for printing.

    Arguments:
      model_info: Model dict to format.

    Returns:
      A dictionary of model properties.
    """
    return bq_client_utils.FormatModelInfo(model_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRoutineDataType(data_type):
    """Converts a routine data type to a pretty string representation.

    Arguments:
      data_type: Routine data type dict to format.

    Returns:
      A formatted string.
    """
    return bq_client_utils.FormatRoutineDataType(data_type)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRoutineTableType(table_type):
    """Converts a routine table type to a pretty string representation.

    Arguments:
      table_type: Routine table type dict to format.

    Returns:
      A formatted string.
    """
    return bq_client_utils.FormatRoutineTableType(table_type)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRoutineArgumentInfo(routine_type, argument):
    """Converts a routine argument to a pretty string representation.

    Arguments:
      routine_type: The routine type of the corresponding routine. It's of
        string type corresponding to the string value of enum
        cloud.bigquery.v2.Routine.RoutineType.
      argument: Routine argument dict to format.

    Returns:
      A formatted string.
    """
    return bq_client_utils.FormatRoutineArgumentInfo(routine_type, argument)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRoutineInfo(routine_info):
    """Prepare a routine for printing.

    Arguments:
      routine_info: Routine dict to format.

    Returns:
      A dictionary of routine properties.
    """
    return bq_client_utils.FormatRoutineInfo(routine_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatRowAccessPolicyInfo(row_access_policy_info):
    """Prepare a row access policy for printing.

    Arguments:
      row_access_policy_info: Row access policy dict to format.

    Returns:
      A dictionary of row access policy properties.
    """
    return bq_client_utils.FormatRowAccessPolicyInfo(row_access_policy_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatDatasetInfo(dataset_info):
    """Prepare a dataset_info for printing.

    Arguments:
      dataset_info: Dataset dict to format.

    Returns:
      The new dataset_info.
    """
    return bq_client_utils.FormatDatasetInfo(dataset_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTableInfo(table_info):
    """Prepare a table_info for printing.

    Arguments:
      table_info: Table dict to format.

    Returns:
      The new table_info.
    """
    return bq_client_utils.FormatTableInfo(table_info)

  # TODO(b/324243535): Delete these once the migration is complete.

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTransferConfigInfo(transfer_config_info):
    """Prepare transfer config info for printing.

    Arguments:
      transfer_config_info: transfer config info to format.

    Returns:
      The new transfer config info.
    """
    return bq_client_utils.FormatTransferConfigInfo(transfer_config_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTrasferLogInfo(transfer_log_info):
    """Prepare transfer log info for printing.

    Arguments:
      transfer_log_info: transfer log info to format.

    Returns:
      The new transfer config log.
    """
    return bq_client_utils.FormatTransferLogInfo(transfer_log_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatTransferRunInfo(transfer_run_info):
    """Prepare transfer run info for printing.

    Arguments:
      transfer_run_info: transfer run info to format.

    Returns:
      The new transfer run info.
    """
    return bq_client_utils.FormatTransferRunInfo(transfer_run_info)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatReservationInfo(reservation, reference_type):
    """Prepare a reservation for printing.

    Arguments:
      reservation: reservation to format.
      reference_type: Type of reservation.

    Returns:
      A dictionary of reservation properties.
    """
    return bq_client_utils.FormatReservationInfo(reservation, reference_type)

  # TODO(b/324243535): Delete these once the migration is complete.
  @classmethod
  def FormatCapacityCommitmentInfo(cls, capacity_commitment):
    """Prepare a capacity commitment for printing.

    Arguments:
      capacity_commitment: capacity commitment to format.

    Returns:
      A dictionary of capacity commitment properties.
    """
    return bq_client_utils.FormatCapacityCommitmentInfo(capacity_commitment)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatReservationAssignmentInfo(reservation_assignment):
    """Prepare a reservation_assignment for printing.

    Arguments:
      reservation_assignment: reservation_assignment to format.

    Returns:
      A dictionary of reservation_assignment properties.
    """
    return bq_client_utils.FormatReservationAssignmentInfo(
        reservation_assignment)

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def GetConnectionType(connection):
    return bq_processor_utils.GetConnectionType(connection)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def FormatConnectionInfo(connection):
    """Prepare a connection object for printing.

    Arguments:
      connection: connection to format.

    Returns:
      A dictionary of connection properties.
    """
    return bq_client_utils.FormatConnectionInfo(connection)

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def ConstructObjectReference(object_info):
    """Construct a Reference from a server response."""
    return bq_processor_utils.ConstructObjectReference(object_info)

  # TODO(b/324243535): Delete this once the migration is complete.
  @staticmethod
  def ConstructObjectInfo(reference):
    """Construct an Object from an ObjectReference."""
    return bq_processor_utils.ConstructObjectInfo(reference)

  # TODO(b/324243535): Delete this once the migration is complete.
  def _PrepareListRequest(self,
                          reference,
                          max_results=None,
                          page_token=None,
                          filter_expression=None):
    """Create and populate a list request."""
    return bq_processor_utils.PrepareListRequest(
        reference, max_results, page_token, filter_expression
    )


  # TODO(b/324243535): Delete this once the migration is complete.
  def _PrepareTransferListRequest(self,
                                  reference,
                                  location,
                                  page_size=None,
                                  page_token=None,
                                  data_source_ids=None):
    """Create and populate a list request."""
    return bq_processor_utils.PrepareTransferListRequest(
        reference, location, page_size, page_token, data_source_ids
    )

  # TODO(b/324243535): Delete this once the migration is complete.
  def _PrepareTransferRunListRequest(self,
                                     reference,
                                     run_attempt,
                                     max_results=None,
                                     page_token=None,
                                     states=None):
    """Create and populate a transfer run list request."""
    return bq_processor_utils.PrepareTransferRunListRequest(
        reference, run_attempt, max_results, page_token, states
    )

  # TODO(b/324243535): Delete this once the migration is complete.
  def _PrepareListTransferLogRequest(self,
                                     reference,
                                     max_results=None,
                                     page_token=None,
                                     message_type=None):
    """Create and populate a transfer log list request."""
    return bq_processor_utils.PrepareListTransferLogRequest(
        reference, max_results, page_token, message_type
    )

  # TODO(b/324243535): Delete these once the migration is complete.
  def _NormalizeProjectReference(self, reference):
    return bq_client_utils.NormalizeProjectReference(self, reference)

  def ListJobRefs(self, **kwds):
    return list(
        map(  # pylint: disable=g-long-lambda
            bq_processor_utils.ConstructObjectReference, self.ListJobs(**kwds)))

  def ListJobs(self,
               reference=None,
               max_results=None,
               page_token=None,
               state_filter=None,
               min_creation_time=None,
               max_creation_time=None,
               all_users=None,
               parent_job_id=None):
    # pylint: disable=g-doc-args
    """Return a list of jobs.

    Args:
      reference: The ProjectReference to list jobs for.
      max_results: The maximum number of jobs to return.
      page_token: Current page token (optional).
      state_filter: A single state filter or a list of filters to apply. If not
        specified, no filtering is applied.
      min_creation_time: Timestamp in milliseconds. Only return jobs created
        after or at this timestamp.
      max_creation_time: Timestamp in milliseconds. Only return jobs created
        before or at this timestamp.
      all_users: Whether to list jobs for all users of the project. Requesting
        user must be an owner of the project to list all jobs.
      parent_job_id: Retrieve only child jobs belonging to this parent; None to
        retrieve top-level jobs.

    Returns:
      A list of jobs.
    """
    return self.ListJobsAndToken(reference, max_results, page_token,
                                 state_filter, min_creation_time,
                                 max_creation_time, all_users,
                                 parent_job_id)['results']

  def ListJobsAndToken(self,
                       reference=None,
                       max_results=None,
                       page_token=None,
                       state_filter=None,
                       min_creation_time=None,
                       max_creation_time=None,
                       all_users=None,
                       parent_job_id=None):
    # pylint: disable=g-doc-args
    """Return a list of jobs.

    Args:
      reference: The ProjectReference to list jobs for.
      max_results: The maximum number of jobs to return.
      page_token: Current page token (optional).
      state_filter: A single state filter or a list of filters to apply. If not
        specified, no filtering is applied.
      min_creation_time: Timestamp in milliseconds. Only return jobs created
        after or at this timestamp.
      max_creation_time: Timestamp in milliseconds. Only return jobs created
        before or at this timestamp.
      all_users: Whether to list jobs for all users of the project. Requesting
        user must be an owner of the project to list all jobs.
      parent_job_id: Retrieve only child jobs belonging to this parent; None to
        retrieve top-level jobs.

    Returns:
      A dict that contains enytries:
        'results': a list of jobs
        'token': nextPageToken for the last page, if present.
    """
    reference = bq_client_utils.NormalizeProjectReference(
        id_fallbacks=self,
        reference=reference
    )
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ProjectReference,
        method='ListJobs',
    )
    if max_results is not None:
      if max_results > bq_processor_utils.MAX_RESULTS:
        max_results = bq_processor_utils.MAX_RESULTS
    request = bq_processor_utils.PrepareListRequest(
        reference, max_results, page_token
    )
    if state_filter is not None:
      # The apiclient wants enum values as lowercase strings.
      if isinstance(state_filter, six.string_types):
        state_filter = state_filter.lower()
      else:
        state_filter = [s.lower() for s in state_filter]
    bq_processor_utils.ApplyParameters(
        request,
        projection='full',
        state_filter=state_filter,
        all_users=all_users,
        parent_job_id=parent_job_id)
    if min_creation_time is not None:
      request['minCreationTime'] = min_creation_time
    if max_creation_time is not None:
      request['maxCreationTime'] = max_creation_time
    result = self.apiclient.jobs().list(**request).execute()
    results = result.get('jobs', [])
    if max_results is not None:
      while 'nextPageToken' in result and len(results) < max_results:
        request['maxResults'] = max_results - len(results)
        request['pageToken'] = result['nextPageToken']
        result = self.apiclient.jobs().list(**request).execute()
        results.extend(result.get('jobs', []))
    if 'nextPageToken' in result:
      return dict(results=results, token=result['nextPageToken'])
    return dict(results=results)

  def ListTransferConfigs(self,
                          reference=None,
                          location=None,
                          page_size=None,
                          page_token=None,
                          data_source_ids=None):
    """Return a list of transfer configurations.

    Args:
      reference: The ProjectReference to list transfer configurations for.
      location: The location id, e.g. 'us' or 'eu'.
      page_size: The maximum number of transfer configurations to return.
      page_token: Current page token (optional).
      data_source_ids: The dataSourceIds to display transfer configurations for.

    Returns:
      A list of transfer configurations.
    """
    results = None
    client = self.GetTransferV1ApiClient()
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ProjectReference,
        method='ListTransferConfigs')
    if page_size is not None:
      if page_size > bq_processor_utils.MAX_RESULTS:
        page_size = bq_processor_utils.MAX_RESULTS
    request = bq_processor_utils.PrepareTransferListRequest(
        reference, location, page_size, page_token, data_source_ids
    )
    if request:
      bq_processor_utils.ApplyParameters(request)
      result = client.projects().locations().transferConfigs().list(
          **request).execute()
      results = result.get('transferConfigs', [])
      if page_size is not None:
        while 'nextPageToken' in result and len(results) < page_size:
          request = bq_processor_utils.PrepareTransferListRequest(
              reference,
              location,
              page_size - len(results),
              result['nextPageToken'],
              data_source_ids,
          )
          if request:
            bq_processor_utils.ApplyParameters(request)
            result = client.projects().locations().transferConfigs().list(
                **request).execute()
            results.extend(result.get('nextPageToken', []))
          else:
            return
      if len(results) < 1:
        logging.info('There are no transfer configurations to be shown.')
      if result.get('nextPageToken'):
        return (results, result.get('nextPageToken'))
    return (results,)

  def ListTransferRuns(self,
                       reference,
                       run_attempt,
                       max_results=None,
                       page_token=None,
                       states=None):
    """Return a list of transfer runs.

    Args:
      reference: The ProjectReference to list transfer runs for.
      run_attempt: Which runs should be pulled. The default value is 'LATEST',
        which only returns the latest run per day. To return all runs, please
        specify 'RUN_ATTEMPT_UNSPECIFIED'.
      max_results: The maximum number of transfer runs to return (optional).
      page_token: Current page token (optional).
      states: States to filter transfer runs (optional).

    Returns:
      A list of transfer runs.
    """
    transfer_client = self.GetTransferV1ApiClient()
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TransferRunReference,
        method='ListTransferRuns')
    reference = str(reference)
    request = bq_processor_utils.PrepareTransferRunListRequest(
        reference, run_attempt, max_results, page_token, states
    )
    response = transfer_client.projects().locations().transferConfigs().runs(
    ).list(**request).execute()
    transfer_runs = response.get('transferRuns', [])
    if max_results is not None:
      while 'nextPageToken' in response and len(transfer_runs) < max_results:
        page_token = response.get('nextPageToken')
        max_results -= len(transfer_runs)
        request = bq_processor_utils.PrepareTransferRunListRequest(
            reference, run_attempt, max_results, page_token, states
        )
        response = transfer_client.projects().locations().transferConfigs(
        ).runs().list(**request).execute()
        transfer_runs.extend(response.get('transferRuns', []))
      if response.get('nextPageToken'):
        return (transfer_runs, response.get('nextPageToken'))
    return (transfer_runs,)

  def ListTransferLogs(self,
                       reference,
                       message_type=None,
                       max_results=None,
                       page_token=None):
    """Return a list of transfer run logs.

    Args:
      reference: The ProjectReference to list transfer run logs for.
      message_type: Message types to return.
      max_results: The maximum number of transfer run logs to return.
      page_token: Current page token (optional).

    Returns:
      A list of transfer run logs.
    """
    transfer_client = self.GetTransferV1ApiClient()
    reference = str(reference)
    request = bq_processor_utils.PrepareListTransferLogRequest(
        reference,
        max_results=max_results,
        page_token=page_token,
        message_type=message_type)
    response = (
        transfer_client.projects().locations().transferConfigs().runs()
        .transferLogs().list(**request).execute())
    transfer_logs = response.get('transferMessages', [])
    if max_results is not None:
      while 'nextPageToken' in response and len(transfer_logs) < max_results:
        page_token = response['nextPageToken']
        max_results -= len(transfer_logs)
        request = bq_processor_utils.PrepareListTransferLogRequest(
            reference,
            max_results=max_results,
            page_token=page_token,
            message_type=message_type)
        response = (
            transfer_client.projects().locations().transferConfigs().runs()
            .transferLogs().list(**request).execute())
        transfer_logs.extend(response.get('transferMessages', []))
    if response.get('nextPageToken'):
      return (transfer_logs, response.get('nextPageToken'))
    return (transfer_logs,)

  def ListProjectRefs(self, **kwds):
    """List the project references this user has access to."""
    return list(
        map(
            bq_processor_utils.ConstructObjectReference,
            self.ListProjects(**kwds),
        )
    )

  def ListProjects(self, max_results=None, page_token=None):
    """List the projects this user has access to."""
    request = bq_processor_utils.PrepareListRequest({}, max_results, page_token)
    result = self._ExecuteListProjectsRequest(request)
    results = result.get('projects', [])
    while 'nextPageToken' in result and (max_results is not None and
                                         len(results) < max_results):
      request['pageToken'] = result['nextPageToken']
      result = self._ExecuteListProjectsRequest(request)
      results.extend(result.get('projects', []))
    return results

  def _ExecuteListProjectsRequest(self, request):
    return self.apiclient.projects().list(**request).execute()

  def ListDatasetRefs(self, **kwds):
    return list(
        map(
            bq_processor_utils.ConstructObjectReference,
            self.ListDatasets(**kwds),
        )
    )

  def ListDatasets(self,
                   reference=None,
                   max_results=None,
                   page_token=None,
                   list_all=None,
                   filter_expression=None):
    """List the datasets associated with this reference."""
    reference = bq_client_utils.NormalizeProjectReference(
        id_fallbacks=self,
        reference=reference
    )
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ProjectReference,
        method='ListDatasets',
    )
    request = bq_processor_utils.PrepareListRequest(
        reference, max_results, page_token, filter_expression
    )
    if list_all is not None:
      request['all'] = list_all
    result = self.apiclient.datasets().list(**request).execute()
    results = result.get('datasets', [])
    if max_results is not None:
      while 'nextPageToken' in result and len(results) < max_results:
        request['maxResults'] = max_results - len(results)
        request['pageToken'] = result['nextPageToken']
        result = self.apiclient.datasets().list(**request).execute()
        results.extend(result.get('datasets', []))
    return results

  def ListTableRefs(self, **kwds):
    return list(
        map(
            bq_processor_utils.ConstructObjectReference, self.ListTables(**kwds)
        )
    )

  def ListTables(self, reference, max_results=None, page_token=None):
    """List the tables associated with this reference."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.DatasetReference,
        method='ListTables',
    )
    request = bq_processor_utils.PrepareListRequest(
        reference, max_results, page_token
    )
    result = self.apiclient.tables().list(**request).execute()
    results = result.get('tables', [])
    if max_results is not None:
      while 'nextPageToken' in result and len(results) < max_results:
        request['maxResults'] = max_results - len(results)
        request['pageToken'] = result['nextPageToken']
        result = self.apiclient.tables().list(**request).execute()
        results.extend(result.get('tables', []))
    return results

  def ListModels(self, reference, max_results, page_token):
    """Lists models for the given dataset reference.

    Arguments:
      reference: Reference to the dataset.
      max_results: Number of results to return.
      page_token: Token to retrieve the next page of results.

    Returns:
      A dict that contains entries:
        'results': a list of models
        'token': nextPageToken for the last page, if present.
    """
    return self.GetModelsApiClient().models().list(
        projectId=reference.projectId,
        datasetId=reference.datasetId,
        maxResults=max_results,
        pageToken=page_token).execute()

  def ListRoutines(self, reference, max_results, page_token, filter_expression):
    """Lists routines for the given dataset reference.

    Arguments:
      reference: Reference to the dataset.
      max_results: Number of results to return.
      page_token: Token to retrieve the next page of results.
      filter_expression: An expression for filtering routines.

    Returns:
      A dict that contains entries:
        'routines': a list of routines.
        'token': nextPageToken for the last page, if present.
    """
    return self.GetRoutinesApiClient().routines().list(
        projectId=reference.projectId,
        datasetId=reference.datasetId,
        maxResults=max_results,
        pageToken=page_token,
        filter=filter_expression).execute()

  def _ListRowAccessPolicies(
      self,
      table_reference: 'bq_id_utils.ApiClientHelper.TableReference',
      page_size: int,
      page_token: str,
  ) -> Dict[str, List[Any]]:
    """Lists row access policies for the given table reference."""
    return self.GetRowAccessPoliciesApiClient().rowAccessPolicies().list(
        projectId=table_reference.projectId,
        datasetId=table_reference.datasetId,
        tableId=table_reference.tableId,
        pageSize=page_size,
        pageToken=page_token).execute()

  def ListRowAccessPoliciesWithGrantees(
      self,
      table_reference: 'bq_id_utils.ApiClientHelper.TableReference',
      page_size: int,
      page_token: str,
      max_concurrent_iam_calls: int = 1,
  ) -> Dict[str, List[Any]]:
    """Lists row access policies for the given table reference.

    Arguments:
      table_reference: Reference to the table.
      page_size: Number of results to return.
      page_token: Token to retrieve the next page of results.
      max_concurrent_iam_calls: Number of concurrent calls to getIAMPolicy.

    Returns:
      A dict that contains entries:
        'rowAccessPolicies': a list of row access policies, with an additional
          'grantees' field that contains the row access policy grantees.
        'nextPageToken': nextPageToken for the next page, if present.
    """
    response = self._ListRowAccessPolicies(
        table_reference, page_size, page_token
    )
    if 'rowAccessPolicies' in response:
      row_access_policies = response['rowAccessPolicies']
      parallel.RunInParallel(
          function=self._SetRowAccessPolicyGrantees,
          list_of_kwargs_to_function=[
              {'row_access_policy': row_access_policy}
              for row_access_policy in row_access_policies
          ],
          num_workers=max_concurrent_iam_calls,
          cancel_futures=True,
      )
    return response

  def _SetRowAccessPolicyGrantees(self, row_access_policy):
    """Sets the grantees on the given Row Access Policy."""
    row_access_policy_ref = (
        bq_id_utils.ApiClientHelper.RowAccessPolicyReference.Create(
            **row_access_policy['rowAccessPolicyReference']
        )
    )
    iam_policy = self.GetRowAccessPolicyIAMPolicy(row_access_policy_ref)
    grantees = self._GetGranteesFromRowAccessPolicyIamPolicy(iam_policy)
    row_access_policy['grantees'] = grantees

  def _GetGranteesFromRowAccessPolicyIamPolicy(self, iam_policy):
    """Returns the filtered data viewer members of the given IAM policy."""
    bindings = iam_policy.get('bindings')
    if not bindings:
      return []

    filtered_data_viewer_binding = next(
        (binding for binding in bindings
         if binding.get('role') == _FILTERED_DATA_VIEWER_ROLE), None)
    if not filtered_data_viewer_binding:
      return []

    return filtered_data_viewer_binding.get('members', [])

  def GetDatasetIAMPolicy(self, reference):
    """Gets IAM policy for the given dataset resource.

    Arguments:
      reference: the DatasetReference for the dataset resource.

    Returns:
      The IAM policy attached to the given dataset resource.

    Raises:
      TypeError: if reference is not a DatasetReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.DatasetReference,
        method='GetDatasetIAMPolicy')
    formatted_resource = ('projects/%s/datasets/%s' %
                          (reference.projectId, reference.datasetId))
    return self.GetIAMPolicyApiClient().datasets().getIamPolicy(
        resource=formatted_resource).execute()

  def GetTableIAMPolicy(self, reference):
    """Gets IAM policy for the given table resource.

    Arguments:
      reference: the TableReference for the table resource.

    Returns:
      The IAM policy attached to the given table resource.

    Raises:
      TypeError: if reference is not a TableReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='GetTableIAMPolicy',
    )
    formatted_resource = (
        'projects/%s/datasets/%s/tables/%s' %
        (reference.projectId, reference.datasetId, reference.tableId))
    return self.GetIAMPolicyApiClient().tables().getIamPolicy(
        resource=formatted_resource).execute()

  def GetRowAccessPolicyIAMPolicy(
      self, reference: 'bq_id_utils.ApiClientHelper.RowAccessPolicyReference'
  ) -> Policy:
    """Gets IAM policy for the given row access policy resource.

    Arguments:
      reference: the RowAccessPolicyReference for the row access policy
        resource.

    Returns:
      The IAM policy attached to the given row access policy resource.

    Raises:
      TypeError: if reference is not a RowAccessPolicyReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.RowAccessPolicyReference,
        method='GetRowAccessPolicyIAMPolicy')
    formatted_resource = (
        'projects/%s/datasets/%s/tables/%s/rowAccessPolicies/%s' %
        (reference.projectId, reference.datasetId, reference.tableId,
         reference.policyId))
    return self.GetIAMPolicyApiClient().rowAccessPolicies().getIamPolicy(
        resource=formatted_resource).execute()

  def SetDatasetIAMPolicy(self, reference, policy):
    """Sets IAM policy for the given dataset resource.

    Arguments:
      reference: the DatasetReference for the dataset resource.
      policy: The policy string in JSON format.

    Returns:
      The updated IAM policy attached to the given dataset resource.

    Raises:
      TypeError: if reference is not a DatasetReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.DatasetReference,
        method='SetDatasetIAMPolicy')
    formatted_resource = ('projects/%s/datasets/%s' %
                          (reference.projectId, reference.datasetId))
    request = {'policy': policy}
    return self.GetIAMPolicyApiClient().datasets().setIamPolicy(
        body=request, resource=formatted_resource).execute()

  def SetTableIAMPolicy(self, reference, policy):
    """Sets IAM policy for the given table resource.

    Arguments:
      reference: the TableReference for the table resource.
      policy: The policy string in JSON format.

    Returns:
      The updated IAM policy attached to the given table resource.

    Raises:
      TypeError: if reference is not a TableReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='SetTableIAMPolicy',
    )
    formatted_resource = (
        'projects/%s/datasets/%s/tables/%s' %
        (reference.projectId, reference.datasetId, reference.tableId))
    request = {'policy': policy}
    return self.GetIAMPolicyApiClient().tables().setIamPolicy(
        body=request, resource=formatted_resource).execute()

  #################################
  ##       Transfer run
  #################################
  def StartManualTransferRuns(self, reference, start_time, end_time, run_time):
    """Starts manual transfer runs.

    Args:
      reference: Transfer configuration name for the run.
      start_time: Start time of the range of transfer runs.
      end_time: End time of the range of transfer runs.
      run_time: Specific time for a transfer run.

    Returns:
      The list of started transfer runs.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TransferConfigReference,
        method='StartManualTransferRuns')
    transfer_client = self.GetTransferV1ApiClient()
    parent = str(reference)

    if run_time:
      body = {'requestedRunTime': run_time}
    else:
      body = {
          'requestedTimeRange': {
              'startTime': start_time,
              'endTime': end_time
          }
      }

    configs_request = transfer_client.projects().locations().transferConfigs()
    response = configs_request.startManualRuns(
        parent=parent, body=body).execute()

    return response.get('runs')

  #################################
  ## Table and dataset management
  #################################

  def CopyTable(
      self,
      source_references,
      dest_reference,
      create_disposition=None,
      write_disposition=None,
      ignore_already_exists=False,
      encryption_configuration=None,
      operation_type='COPY',
      destination_expiration_time=None,
      **kwds):
    """Copies a table.

    Args:
      source_references: TableReferences of source tables.
      dest_reference: TableReference of destination table.
      create_disposition: Optional. Specifies the create_disposition for the
        dest_reference.
      write_disposition: Optional. Specifies the write_disposition for the
        dest_reference.
      ignore_already_exists: Whether to ignore "already exists" errors.
      encryption_configuration: Optional. Allows user to encrypt the table from
        the copy table command with Cloud KMS key. Passed as a dictionary in the
        following format: {'kmsKeyName': 'destination_kms_key'}
      **kwds: Passed on to ExecuteJob.

    Returns:
      The job description, or None for ignored errors.

    Raises:
      BigqueryDuplicateError: when write_disposition 'WRITE_EMPTY' is
        specified and the dest_reference table already exists.
    """
    for src_ref in source_references:
      bq_id_utils.typecheck(
          src_ref,
          bq_id_utils.ApiClientHelper.TableReference,
          method='CopyTable',
      )
    bq_id_utils.typecheck(
        dest_reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='CopyTable',
    )
    copy_config = {
        'destinationTable': dict(dest_reference),
        'sourceTables': [dict(src_ref) for src_ref in source_references],
    }
    if encryption_configuration:
      copy_config[
          'destinationEncryptionConfiguration'] = encryption_configuration

    if operation_type:
      copy_config['operationType'] = operation_type

    if destination_expiration_time:
      copy_config['destinationExpirationTime'] = destination_expiration_time

    bq_processor_utils.ApplyParameters(
        copy_config,
        create_disposition=create_disposition,
        write_disposition=write_disposition)

    try:
      return self.ExecuteJob({'copy': copy_config}, **kwds)
    except bq_error.BigqueryDuplicateError as e:
      if ignore_already_exists:
        return None
      raise e

  def DatasetExists(
      self, reference: 'bq_id_utils.ApiClientHelper.DatasetReference'
  ) -> bool:
    """Returns true if a dataset exists."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.DatasetReference,
        method='DatasetExists',
    )
    try:
      self.apiclient.datasets().get(**dict(reference)).execute()
      return True
    except bq_error.BigqueryNotFoundError:
      return False

  def GetDatasetRegion(
      self, reference: 'bq_id_utils.ApiClientHelper.DatasetReference'
  ) -> str:
    """Returns the region of a dataset as a string."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.DatasetReference,
        method='GetDatasetRegion',
    )
    try:
      return (
          self.apiclient.datasets().get(**dict(reference)).execute()['location']
      )
    except bq_error.BigqueryNotFoundError:
      return None

  def GetTableRegion(
      self, reference: 'bq_id_utils.ApiClientHelper.TableReference'
  ) -> str:
    """Returns the region of a table as a string."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='GetTableRegion',
    )
    try:
      return (
          self.apiclient.tables().get(**dict(reference)).execute()['location']
      )
    except bq_error.BigqueryNotFoundError:
      return None

  def TableExists(
      self, reference: 'bq_id_utils.ApiClientHelper.TableReference'
  ) -> bool:
    """Returns true if the table exists."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='TableExists',
    )
    try:
      return self.apiclient.tables().get(**dict(reference)).execute()
    except bq_error.BigqueryNotFoundError:
      return False

  def JobExists(
      self, reference: 'bq_id_utils.ApiClientHelper.JobReference'
  ) -> bool:
    """Returns true if the job exists."""
    bq_id_utils.typecheck(
        reference, bq_id_utils.ApiClientHelper.JobReference, method='JobExists'
    )
    try:
      return self.apiclient.jobs().get(**dict(reference)).execute()
    except bq_error.BigqueryNotFoundError:
      return False

  def ModelExists(
      self, reference: 'bq_id_utils.ApiClientHelper.ModelReference'
  ) -> bool:
    """Returns true if the model exists."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ModelReference,
        method='ModelExists',
    )
    try:
      return (
          self.GetModelsApiClient()
          .models()
          .get(
              projectId=reference.projectId,
              datasetId=reference.datasetId,
              modelId=reference.modelId,
          )
          .execute()
      )
    except bq_error.BigqueryNotFoundError:
      return False

  def RoutineExists(
      self, reference: 'bq_id_utils.ApiClientHelper.RoutineReference'
  ) -> bool:
    """Returns true if the routine exists."""
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.RoutineReference,
        method='RoutineExists',
    )
    try:
      return self.GetRoutinesApiClient().routines().get(
          projectId=reference.projectId,
          datasetId=reference.datasetId,
          routineId=reference.routineId).execute()
    except bq_error.BigqueryNotFoundError:
      return False

  def TransferExists(
      self, reference: 'bq_id_utils.ApiClientHelper.TransferConfigReference'
  ) -> bool:
    """Returns true if the transfer exists."""
    # pylint: disable=missing-function-docstring
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TransferConfigReference,
        method='TransferExists')
    try:
      transfer_client = self.GetTransferV1ApiClient()
      transfer_client.projects().locations().transferConfigs().get(
          name=reference.transferConfigName).execute()
      return True
    except bq_error.BigqueryNotFoundError:
      return False

  # TODO(b/191712821): add tags modification here. For the Preview Tags are not
  # modifiable using BigQuery UI/Cli, only using ResourceManager.
  def CreateDataset(
      self,
      reference,
      ignore_existing=False,
      description=None,
      display_name=None,
      acl=None,
      default_table_expiration_ms=None,
      default_partition_expiration_ms=None,
      data_location=None,
      labels=None,
      default_kms_key=None,
      source_dataset_reference=None,
      external_source=None,
      connection_id=None,
      max_time_travel_hours=None,
      storage_billing_model=None,
      resource_tags=None,
  ):
    """Create a dataset corresponding to DatasetReference.

    Args:
      reference: the DatasetReference to create.
      ignore_existing: (boolean, default False) If False, raise an exception if
        the dataset already exists.
      description: an optional dataset description.
      display_name: an optional friendly name for the dataset.
      acl: an optional ACL for the dataset, as a list of dicts.
      default_table_expiration_ms: Default expiration time to apply to new
        tables in this dataset.
      default_partition_expiration_ms: Default partition expiration time to
        apply to new partitioned tables in this dataset.
      data_location: Location where the data in this dataset should be stored.
        Must be either 'EU' or 'US'. If specified, the project that owns the
        dataset must be enabled for data location.
      labels: An optional dict of labels.
      default_kms_key: An optional kms dey that will apply to all newly created
        tables in the dataset, if no explicit key is supplied in the creating
        request.
      source_dataset_reference: An optional ApiClientHelper.DatasetReference
        that will be the source of this linked dataset. #
      external_source: External source that backs this dataset.
      connection_id: Connection used for accessing the external_source.
      max_time_travel_hours: Optional. Define the max time travel in hours. The
        value can be from 48 to 168 hours (2 to 7 days). The default value is
        168 hours if this is not set.
      storage_billing_model: Optional. Sets the storage billing model for the
        dataset.
      resource_tags: an optional dict of tags to attach to the dataset.

    Raises:
      TypeError: if reference is not an ApiClientHelper.DatasetReference
        or if source_dataset_reference is provided but is not an
        bq_id_utils.ApiClientHelper.DatasetReference.
        or if both external_dataset_reference and source_dataset_reference
        are provided or if not all required arguments for external database is
        provided.
      BigqueryDuplicateError: if reference exists and ignore_existing
         is False.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.DatasetReference,
        method='CreateDataset',
    )

    body = bq_processor_utils.ConstructObjectInfo(reference)
    if display_name is not None:
      body['friendlyName'] = display_name
    if description is not None:
      body['description'] = description
    if acl is not None:
      body['access'] = acl
    if default_table_expiration_ms is not None:
      body['defaultTableExpirationMs'] = default_table_expiration_ms
    if default_partition_expiration_ms is not None:
      body['defaultPartitionExpirationMs'] = default_partition_expiration_ms
    if default_kms_key is not None:
      body['defaultEncryptionConfiguration'] = {'kmsKeyName': default_kms_key}
    if data_location is not None:
      body['location'] = data_location
    if labels:
      body['labels'] = {}
      for label_key, label_value in labels.items():
        body['labels'][label_key] = label_value
    if source_dataset_reference is not None:
      bq_id_utils.typecheck(
          source_dataset_reference,
          bq_id_utils.ApiClientHelper.DatasetReference,
          method='CreateDataset')
      body['linkedDatasetSource'] = {
          'sourceDataset':
              bq_processor_utils.ConstructObjectInfo(source_dataset_reference)
              ['datasetReference']
      }
    # externalDatasetReference can only be specified in case of externals
    # datasets. This option cannot be used in case of regular dataset or linked
    # datasets.
    # So we only set this if an external_source is specified.
    if external_source:
      body['externalDatasetReference'] = {
          'externalSource': external_source,
          'connection': connection_id,
      }

    if max_time_travel_hours is not None:
      body['maxTimeTravelHours'] = max_time_travel_hours
    if storage_billing_model is not None:
      body['storageBillingModel'] = storage_billing_model

    try:
      self.apiclient.datasets().insert(
          body=body, **dict(reference.GetProjectReference())).execute()
    except bq_error.BigqueryDuplicateError:
      if not ignore_existing:
        raise

  def CreateTable(
      self,
      reference,
      ignore_existing=False,
      schema=None,
      description=None,
      display_name=None,
      expiration=None,
      view_query=None,
      materialized_view_query=None,
      enable_refresh=None,
      refresh_interval_ms=None,
      max_staleness=None,
      external_data_config=None,
      biglake_config=None,
      view_udf_resources=None,
      use_legacy_sql=None,
      labels=None,
      time_partitioning=None,
      clustering=None,
      range_partitioning=None,
      require_partition_filter=None,
      destination_kms_key=None,
      location=None,
      table_constraints=None,
      resource_tags=None):
    """Create a table corresponding to TableReference.

    Args:
      reference: the TableReference to create.
      ignore_existing: (boolean, default False) If False, raise an exception if
        the dataset already exists.
      schema: an optional schema for tables.
      description: an optional description for tables or views.
      display_name: an optional friendly name for the table.
      expiration: optional expiration time in milliseconds since the epoch for
        tables or views.
      view_query: an optional Sql query for views.
      materialized_view_query: an optional standard SQL query for materialized
        views.
      enable_refresh: for materialized views, an optional toggle to enable /
        disable automatic refresh when the base table is updated.
      refresh_interval_ms: for materialized views, an optional maximum frequency
        for automatic refreshes.
      max_staleness: INTERVAL value that determines the maximum staleness
        allowed when querying a materialized view or an external table. By
        default no staleness is allowed.
      external_data_config: defines a set of external resources used to create
        an external table. For example, a BigQuery table backed by CSV files in
        GCS.
      biglake_config: specifies the configuration of a BigLake managed table.
      view_udf_resources: optional UDF resources used in a view.
      use_legacy_sql: The choice of using Legacy SQL for the query is optional.
        If not specified, the server will automatically determine the dialect
        based on query information, such as dialect prefixes. If no prefixes are
        found, it will default to Legacy SQL.
      labels: an optional dict of labels to set on the table.
      time_partitioning: if set, enables time based partitioning on the table
        and configures the partitioning.
      clustering: if set, enables and configures clustering on the table.
      range_partitioning: if set, enables range partitioning on the table and
        configures the partitioning.
      require_partition_filter: if set, partition filter is required for
        queiries over this table.
      destination_kms_key: User specified KMS key for encryption.
      location: an optional location for which to create tables or views.
      table_constraints: an optional primary key and foreign key configuration
        for the table.
      resource_tags: an optional dict of tags to attach to the table.

    Raises:
      TypeError: if reference is not a TableReference.
      BigqueryDuplicateError: if reference exists and ignore_existing
        is False.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='CreateTable',
    )

    try:
      body = bq_processor_utils.ConstructObjectInfo(reference)
      if schema is not None:
        body['schema'] = {'fields': schema}
      if display_name is not None:
        body['friendlyName'] = display_name
      if description is not None:
        body['description'] = description
      if expiration is not None:
        body['expirationTime'] = expiration
      if view_query is not None:
        view_args = {'query': view_query}
        if view_udf_resources is not None:
          view_args['userDefinedFunctionResources'] = view_udf_resources
        body['view'] = view_args
        if use_legacy_sql is not None:
          view_args['useLegacySql'] = use_legacy_sql
      if materialized_view_query is not None:
        materialized_view_args = {'query': materialized_view_query}
        if enable_refresh is not None:
          materialized_view_args['enableRefresh'] = enable_refresh
        if refresh_interval_ms is not None:
          materialized_view_args['refreshIntervalMs'] = refresh_interval_ms
        body['materializedView'] = materialized_view_args
      if external_data_config is not None:
        if max_staleness is not None:
          body['maxStaleness'] = max_staleness
        body['externalDataConfiguration'] = external_data_config
      if biglake_config is not None:
        body['biglakeConfiguration'] = biglake_config
      if labels is not None:
        body['labels'] = labels
      if time_partitioning is not None:
        body['timePartitioning'] = time_partitioning
      if clustering is not None:
        body['clustering'] = clustering
      if range_partitioning is not None:
        body['rangePartitioning'] = range_partitioning
      if require_partition_filter is not None:
        body['requirePartitionFilter'] = require_partition_filter
      if destination_kms_key is not None:
        body['encryptionConfiguration'] = {'kmsKeyName': destination_kms_key}
      if location is not None:
        body['location'] = location
      if table_constraints is not None:
        body['table_constraints'] = table_constraints
      if resource_tags is not None:
        body['resourceTags'] = resource_tags
      self.apiclient.tables().insert(
          body=body, **dict(reference.GetDatasetReference())).execute()
    except bq_error.BigqueryDuplicateError:
      if not ignore_existing:
        raise

  def _FetchDataSource(self, project_reference, data_source_id):
    transfer_client = self.GetTransferV1ApiClient()
    data_source_retrieval = (
        project_reference + '/locations/-/dataSources/' + data_source_id
    )

    return (
        transfer_client.projects()
        .locations()
        .dataSources()
        .get(name=data_source_retrieval)
        .execute()
    )

  def UpdateTransferConfig(self,
                           reference,
                           target_dataset=None,
                           display_name=None,
                           refresh_window_days=None,
                           params=None,
                           auth_info=None,
                           service_account_name=None,
                           destination_kms_key=None,
                           notification_pubsub_topic=None,
                           schedule_args=None):
    """Updates a transfer config.

    Args:
      reference: the TransferConfigReference to update.
      target_dataset: Optional updated target dataset.
      display_name: Optional change to the display name.
      refresh_window_days: Optional update to the refresh window days. Some data
        sources do not support this.
      params: Optional parameters to update.
      auth_info: A dict contains authorization info which can be either an
        authorization_code or a version_info that the user input if they want to
        update credentials.
      service_account_name: The service account that the user could act as and
        used as the credential to create transfer runs from the transfer config.
      destination_kms_key: Optional KMS key for encryption.
      notification_pubsub_topic: The Pub/Sub topic where notifications will be
        sent after transfer runs associated with this transfer config finish.
      schedule_args: Optional parameters to customize data transfer schedule.

    Raises:
      TypeError: if reference is not a TransferConfigReference.
      BigqueryNotFoundError: if dataset is not found
      bq_error.BigqueryError: required field not given.
    """

    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TransferConfigReference,
        method='UpdateTransferConfig')
    project_reference = 'projects/' + (
        bq_client_utils.GetProjectReference(id_fallbacks=self).projectId)
    transfer_client = self.GetTransferV1ApiClient()
    current_config = transfer_client.projects().locations().transferConfigs(
    ).get(name=reference.transferConfigName).execute()
    update_mask = []
    update_items = {}
    update_items['dataSourceId'] = current_config['dataSourceId']
    if target_dataset:
      dataset_reference = bq_client_utils.GetDatasetReference(
          id_fallbacks=self,
          identifier=target_dataset
      )
      if self.DatasetExists(dataset_reference):
        update_items['destinationDatasetId'] = target_dataset
        update_mask.append('transfer_config.destination_dataset_id')
      else:
        raise bq_error.BigqueryNotFoundError(
            'Unknown %r' % (dataset_reference,), {'reason': 'notFound'}, [])
      update_items['destinationDatasetId'] = target_dataset

    if display_name:
      update_mask.append('transfer_config.display_name')
      update_items['displayName'] = display_name

    if params:
      update_items = bq_processor_utils.ProcessParamsFlag(params, update_items)
      update_mask.append('transfer_config.params')

    # if refresh window provided, check that data source supports it
    if refresh_window_days:
      data_source_info = self._FetchDataSource(
          project_reference, current_config['dataSourceId']
      )
      update_items = bq_processor_utils.ProcessRefreshWindowDaysFlag(
          refresh_window_days,
          data_source_info,
          update_items,
          current_config['dataSourceId'],
      )
      update_mask.append('transfer_config.data_refresh_window_days')

    if schedule_args:
      if schedule_args.schedule is not None:
        # update schedule if a custom string was provided
        update_items['schedule'] = schedule_args.schedule
        update_mask.append('transfer_config.schedule')

      update_items['scheduleOptions'] = schedule_args.ToScheduleOptionsPayload(
          options_to_copy=current_config.get('scheduleOptions'))
      update_mask.append('transfer_config.scheduleOptions')

    if notification_pubsub_topic:
      update_items['notification_pubsub_topic'] = notification_pubsub_topic
      update_mask.append('transfer_config.notification_pubsub_topic')

    if auth_info is not None and AUTHORIZATION_CODE in auth_info:
      update_mask.append(AUTHORIZATION_CODE)

    if auth_info is not None and VERSION_INFO in auth_info:
      update_mask.append(VERSION_INFO)

    if service_account_name:
      update_mask.append('service_account_name')

    if destination_kms_key:
      update_items['encryption_configuration'] = {
          'kms_key_name': {'value': destination_kms_key}
      }
      update_mask.append('encryption_configuration.kms_key_name')

    transfer_client.projects().locations().transferConfigs().patch(
        body=update_items,
        name=reference.transferConfigName,
        updateMask=','.join(update_mask),
        authorizationCode=(None if auth_info is None else
                           auth_info.get(AUTHORIZATION_CODE)),
        versionInfo=None if auth_info is None else auth_info.get(VERSION_INFO),
        serviceAccountName=service_account_name,
        x__xgafv='2').execute()

  def CreateTransferConfig(self,
                           reference,
                           data_source,
                           target_dataset=None,
                           display_name=None,
                           refresh_window_days=None,
                           params=None,
                           auth_info=None,
                           service_account_name=None,
                           notification_pubsub_topic=None,
                           schedule_args=None,
                           destination_kms_key=None,
                           location=None):
    """Create a transfer config corresponding to TransferConfigReference.

    Args:
      reference: the TransferConfigReference to create.
      data_source: The data source for the transfer config.
      target_dataset: The dataset where the new transfer config will exist.
      display_name: An display name for the transfer config.
      refresh_window_days: Refresh window days for the transfer config.
      params: Parameters for the created transfer config. The parameters should
        be in JSON format given as a string. Ex: --params="{'param':'value'}".
        The params should be the required values needed for each data source and
        will vary.
      auth_info: A dict contains authorization info which can be either an
        authorization_code or a version_info that the user input if they need
        credentials.
      service_account_name: The service account that the user could act as and
        used as the credential to create transfer runs from the transfer config.
      notification_pubsub_topic: The Pub/Sub topic where notifications will be
        sent after transfer runs associated with this transfer config finish.
      schedule_args: Optional parameters to customize data transfer schedule.
      destination_kms_key: Optional KMS key for encryption.
      location: The location where the new transfer config will run.

    Raises:
      BigqueryNotFoundError: if a requested item is not found.
      bq_error.BigqueryError: if a required field isn't provided.

    Returns:
      The generated transfer configuration name.
    """
    create_items = {}
    transfer_client = self.GetTransferV1ApiClient()

    # The backend will check if the dataset exists.
    if target_dataset:
      create_items['destinationDatasetId'] = target_dataset

    if display_name:
      create_items['displayName'] = display_name
    else:
      raise bq_error.BigqueryError('A display name must be provided.')

    create_items['dataSourceId'] = data_source

    # if refresh window provided, check that data source supports it
    if refresh_window_days:
      data_source_info = self._FetchDataSource(reference, data_source)
      create_items = bq_processor_utils.ProcessRefreshWindowDaysFlag(
          refresh_window_days, data_source_info, create_items, data_source
      )

    # checks that all required params are given
    # if a param that isn't required is provided, it is ignored.
    if params:
      create_items = bq_processor_utils.ProcessParamsFlag(params, create_items)
    else:
      raise bq_error.BigqueryError('Parameters must be provided.')

    if location:
      parent = reference + '/locations/' + location
    else:
      # The location is infererred by the data transfer service from the
      # dataset location.
      parent = reference + '/locations/-'

    if schedule_args:
      if schedule_args.schedule is not None:
        create_items['schedule'] = schedule_args.schedule
      create_items['scheduleOptions'] = schedule_args.ToScheduleOptionsPayload()

    if notification_pubsub_topic:
      create_items['notification_pubsub_topic'] = notification_pubsub_topic

    if destination_kms_key:
      create_items['encryption_configuration'] = {
          'kms_key_name': {'value': destination_kms_key}
      }

    new_transfer_config = transfer_client.projects().locations(
    ).transferConfigs().create(
        parent=parent,
        body=create_items,
        authorizationCode=(None if auth_info is None else
                           auth_info.get(AUTHORIZATION_CODE)),
        versionInfo=None if auth_info is None else auth_info.get(VERSION_INFO),
        serviceAccountName=service_account_name).execute()

    return new_transfer_config['name']

  # TODO(b/324243535): Delete this once the migration is complete.
  def ProcessParamsFlag(self, params, items):
    """Processes the params flag.

    Args:
      params: The user specified parameters. The parameters should be in JSON
        format given as a string. Ex: --params="{'param':'value'}".
      items: The body that contains information of all the flags set.

    Returns:
      items: The body after it has been updated with the params flag.

    Raises:
      bq_error.BigqueryError: If there is an error with the given params.
    """
    return bq_processor_utils.ProcessParamsFlag(params, items)

  # TODO(b/324243535): Delete this once the migration is complete.
  def ProcessRefreshWindowDaysFlag(self, refresh_window_days, data_source_info,
                                   items, data_source):
    """Processes the Refresh Window Days flag.

    Args:
      refresh_window_days: The user specified refresh window days.
      data_source_info: The data source of the transfer config.
      items: The body that contains information of all the flags set.
      data_source: The data source of the transfer config.

    Returns:
      items: The body after it has been updated with the
      refresh window days flag.
    Raises:
      bq_error.BigqueryError: If the data source does not support (custom)
        window days.
    """
    return bq_processor_utils.ProcessRefreshWindowDaysFlag(
        refresh_window_days, data_source_info, items, data_source)

  def UpdateTable(
      self,
      reference,
      schema=None,
      description=None,
      display_name=None,
      expiration=None,
      view_query=None,
      materialized_view_query=None,
      enable_refresh=None,
      refresh_interval_ms=None,
      max_staleness=None,
      external_data_config=None,
      view_udf_resources=None,
      use_legacy_sql=None,
      labels_to_set=None,
      label_keys_to_remove=None,
      time_partitioning=None,
      range_partitioning=None,
      clustering=None,
      require_partition_filter=None,
      etag=None,
      encryption_configuration=None,
      location=None,
      autodetect_schema=False,
      table_constraints=None,
      tags_to_attach: Dict[str, str] = None,
      tags_to_remove: List[str] = None,
      clear_all_tags: bool = False):
    """Updates a table.

    Args:
      reference: the TableReference to update.
      schema: an optional schema for tables.
      description: an optional description for tables or views.
      display_name: an optional friendly name for the table.
      expiration: optional expiration time in milliseconds since the epoch for
        tables or views. Specifying 0 removes expiration time.
      view_query: an optional Sql query to update a view.
      materialized_view_query: an optional Standard SQL query for materialized
        views.
      enable_refresh: for materialized views, an optional toggle to enable /
        disable automatic refresh when the base table is updated.
      refresh_interval_ms: for materialized views, an optional maximum frequency
        for automatic refreshes.
      max_staleness: INTERVAL value that determines the maximum staleness
        allowed when querying a materialized view or an external table. By
        default no staleness is allowed.
      external_data_config: defines a set of external resources used to create
        an external table. For example, a BigQuery table backed by CSV files in
        GCS.
      view_udf_resources: optional UDF resources used in a view.
      use_legacy_sql: The choice of using Legacy SQL for the query is optional.
        If not specified, the server will automatically determine the dialect
        based on query information, such as dialect prefixes. If no prefixes are
        found, it will default to Legacy SQL.
      labels_to_set: an optional dict of labels to set on this table.
      label_keys_to_remove: an optional list of label keys to remove from this
        table.
      time_partitioning: if set, enables time based partitioning on the table
        and configures the partitioning.
      range_partitioning: if set, enables range partitioning on the table and
        configures the partitioning.
      clustering: if set, enables clustering on the table and configures the
        clustering spec.
      require_partition_filter: if set, partition filter is required for
        queiries over this table.
      etag: if set, checks that etag in the existing table matches.
      encryption_configuration: Updates the encryption configuration.
      location: an optional location for which to update tables or views.
      autodetect_schema: an optional flag to perform autodetect of file schema.
      table_constraints: an optional primary key and foreign key configuration
        for the table.
      tags_to_attach: an optional dict of tags to attach to the table
      tags_to_remove: an optional list of tag keys to remove from the table
      clear_all_tags: if set, clears all the tags attached to the table
    Raises:
      TypeError: if reference is not a TableReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='UpdateTable',
    )

    existing_table = {}
    if clear_all_tags:
      # getting existing table. This is required to clear all tags attached to
      # a table. Adding this at the start of the method as this can also be
      # used for other scenarios
      existing_table = self._ExecuteGetTableRequest(reference)
    table = bq_processor_utils.ConstructObjectInfo(reference)
    maybe_skip_schema = False
    if schema is not None:
      table['schema'] = {'fields': schema}
    elif not maybe_skip_schema:
      table['schema'] = None

    if encryption_configuration is not None:
      table['encryptionConfiguration'] = encryption_configuration
    if display_name is not None:
      table['friendlyName'] = display_name
    if description is not None:
      table['description'] = description
    if expiration is not None:
      if expiration == 0:
        table['expirationTime'] = None
      else:
        table['expirationTime'] = expiration
    if view_query is not None:
      view_args = {'query': view_query}
      if view_udf_resources is not None:
        view_args['userDefinedFunctionResources'] = view_udf_resources
      if use_legacy_sql is not None:
        view_args['useLegacySql'] = use_legacy_sql
      table['view'] = view_args
    materialized_view_args = {}
    if materialized_view_query is not None:
      materialized_view_args['query'] = materialized_view_query
    if enable_refresh is not None:
      materialized_view_args['enableRefresh'] = enable_refresh
    if refresh_interval_ms is not None:
      materialized_view_args['refreshIntervalMs'] = refresh_interval_ms
    if materialized_view_args:
      table['materializedView'] = materialized_view_args
    if external_data_config is not None:
      table['externalDataConfiguration'] = external_data_config
      if max_staleness is not None:
        table['maxStaleness'] = max_staleness
    if 'labels' not in table:
      table['labels'] = {}
    if labels_to_set:
      for label_key, label_value in labels_to_set.items():
        table['labels'][label_key] = label_value
    if label_keys_to_remove:
      for label_key in label_keys_to_remove:
        table['labels'][label_key] = None
    if time_partitioning is not None:
      table['timePartitioning'] = time_partitioning
    if range_partitioning is not None:
      table['rangePartitioning'] = range_partitioning
    if clustering is not None:
      if clustering == {}:  # pylint: disable=g-explicit-bool-comparison
        table['clustering'] = None
      else:
        table['clustering'] = clustering
    if require_partition_filter is not None:
      table['requirePartitionFilter'] = require_partition_filter
    if location is not None:
      table['location'] = location
    if table_constraints is not None:
      table['table_constraints'] = table_constraints
    resource_tags = {}
    if clear_all_tags and 'resourceTags' in existing_table:
      for tag in existing_table['resourceTags']:
        resource_tags[tag] = None
    else:
      for tag in tags_to_remove or []:
        resource_tags[tag] = None
    for tag in tags_to_attach or {}:
      resource_tags[tag] = tags_to_attach[tag]
    # resourceTags is used to add a new tag binding, update value of existing
    # tag and also to remove a tag binding
    # check go/bq-table-tags-api for details
    table['resourceTags'] = resource_tags
    self._ExecutePatchTableRequest(reference, table, autodetect_schema, etag)

  def _ExecuteGetTableRequest(self, reference):
    return self.apiclient.tables().get(**dict(reference)).execute()

  def _ExecutePatchTableRequest(self,
                                reference,
                                table,
                                autodetect_schema: bool = False,
                                etag: str = None):
    """Executes request to patch table.

    Args:
      reference: the TableReference to patch.
      table: the body of request
      autodetect_schema: an optional flag to perform autodetect of file schema.
      etag: if set, checks that etag in the existing table matches.
    """
    request = self.apiclient.tables().patch(
        autodetect_schema=autodetect_schema, body=table, **dict(reference))

    # Perform a conditional update to protect against concurrent
    # modifications to this table. If there is a conflicting
    # change, this update will fail with a "Precondition failed"
    # error.
    if etag:
      request.headers['If-Match'] = etag if etag else table['etag']
    request.execute()

  def UpdateModel(self,
                  reference,
                  description=None,
                  expiration=None,
                  labels_to_set=None,
                  label_keys_to_remove=None,
                  vertex_ai_model_id=None,
                  etag=None):
    """Updates a Model.

    Args:
      reference: the ModelReference to update.
      description: an optional description for model.
      expiration: optional expiration time in milliseconds since the epoch.
        Specifying 0 clears the expiration time for the model.
      labels_to_set: an optional dict of labels to set on this model.
      label_keys_to_remove: an optional list of label keys to remove from this
        model.
      vertex_ai_model_id: an optional string as Vertex AI model ID to register.
      etag: if set, checks that etag in the existing model matches.

    Raises:
      TypeError: if reference is not a ModelReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ModelReference,
        method='UpdateModel',
    )

    updated_model = {}
    if description is not None:
      updated_model['description'] = description
    if expiration is not None:
      updated_model['expirationTime'] = expiration or None
    if 'labels' not in updated_model:
      updated_model['labels'] = {}
    if labels_to_set:
      for label_key, label_value in labels_to_set.items():
        updated_model['labels'][label_key] = label_value
    if label_keys_to_remove:
      for label_key in label_keys_to_remove:
        updated_model['labels'][label_key] = None
    if vertex_ai_model_id is not None:
      updated_model['trainingRuns'] = [{
          'vertex_ai_model_id': vertex_ai_model_id
      }]

    request = self.GetModelsApiClient().models().patch(
        body=updated_model,
        projectId=reference.projectId,
        datasetId=reference.datasetId,
        modelId=reference.modelId)

    # Perform a conditional update to protect against concurrent
    # modifications to this model. If there is a conflicting
    # change, this update will fail with a "Precondition failed"
    # error.
    if etag:
      request.headers['If-Match'] = etag if etag else updated_model['etag']
    request.execute()

  def UpdateDataset(
      self,
      reference,
      description=None,
      display_name=None,
      acl=None,
      default_table_expiration_ms=None,
      default_partition_expiration_ms=None,
      labels_to_set=None,
      label_keys_to_remove=None,
      etag=None,
      default_kms_key=None,
      max_time_travel_hours=None,
      storage_billing_model=None,
      ):
    """Updates a dataset.

    Args:
      reference: the DatasetReference to update.
      description: an optional dataset description.
      display_name: an optional friendly name for the dataset.
      acl: an optional ACL for the dataset, as a list of dicts.
      default_table_expiration_ms: optional number of milliseconds for the
        default expiration duration for new tables created in this dataset.
      default_partition_expiration_ms: optional number of milliseconds for the
        default partition expiration duration for new partitioned tables created
        in this dataset.
      labels_to_set: an optional dict of labels to set on this dataset.
      label_keys_to_remove: an optional list of label keys to remove from this
        dataset.
      etag: if set, checks that etag in the existing dataset matches.
      default_kms_key: An optional kms dey that will apply to all newly created
        tables in the dataset, if no explicit key is supplied in the creating
        request.
      max_time_travel_hours: Optional. Define the max time travel in hours. The
        value can be from 48 to 168 hours (2 to 7 days). The default value is
        168 hours if this is not set.
      storage_billing_model: Optional. Sets the storage billing model for the
        dataset.

    Raises:
      TypeError: if reference is not a DatasetReference.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.DatasetReference,
        method='UpdateDataset',
    )

    # Get the existing dataset and associated ETag.
    dataset = self._ExecuteGetDatasetRequest(reference, etag)

    # Merge in the changes.
    if display_name is not None:
      dataset['friendlyName'] = display_name
    if description is not None:
      dataset['description'] = description
    if acl is not None:
      dataset['access'] = acl
    if default_table_expiration_ms is not None:
      dataset['defaultTableExpirationMs'] = default_table_expiration_ms
    if default_partition_expiration_ms is not None:
      if default_partition_expiration_ms == 0:
        dataset['defaultPartitionExpirationMs'] = None
      else:
        dataset['defaultPartitionExpirationMs'] = (
            default_partition_expiration_ms)
    if default_kms_key is not None:
      dataset['defaultEncryptionConfiguration'] = {
          'kmsKeyName': default_kms_key
      }
    if 'labels' not in dataset:
      dataset['labels'] = {}
    if labels_to_set:
      for label_key, label_value in labels_to_set.items():
        dataset['labels'][label_key] = label_value
    if label_keys_to_remove:
      for label_key in label_keys_to_remove:
        dataset['labels'][label_key] = None
    if max_time_travel_hours is not None:
      dataset['maxTimeTravelHours'] = max_time_travel_hours
    if storage_billing_model is not None:
      dataset['storageBillingModel'] = storage_billing_model
    self._ExecutePatchDatasetRequest(reference, dataset, etag)


  def _ExecuteGetDatasetRequest(self, reference, etag: str = None):
    """Executes request to get dataset.

    Args:
      reference: the DatasetReference to get.
      etag: if set, checks that etag in the existing dataset matches.

    Returns:
    The result of executing the request, if it succeeds.
    """
    get_request = self.apiclient.datasets().get(**dict(reference))
    if etag:
      get_request.headers['If-Match'] = etag
    dataset = get_request.execute()
    return dataset

  def _ExecutePatchDatasetRequest(self, reference, dataset, etag: str = None):
    """Executes request to patch dataset.

    Args:
      reference: the DatasetReference to patch.
      dataset: the body of request
      etag: if set, checks that etag in the existing dataset matches.
    """
    request = self.apiclient.datasets().patch(body=dataset, **dict(reference))

    # Perform a conditional update to protect against concurrent
    # modifications to this dataset.  By placing the ETag returned in
    # the get operation into the If-Match header, the API server will
    # make sure the dataset hasn't changed.  If there is a conflicting
    # change, this update will fail with a "Precondition failed"
    # error.
    if etag or dataset['etag']:
      request.headers['If-Match'] = etag if etag else dataset['etag']
    request.execute()

  def DeleteDataset(self,
                    reference,
                    ignore_not_found=False,
                    delete_contents=None):
    """Deletes DatasetReference reference.

    Args:
      reference: the DatasetReference to delete.
      ignore_not_found: Whether to ignore "not found" errors.
      delete_contents: [Boolean] Whether to delete the contents of non-empty
        datasets. If not specified and the dataset has tables in it, the delete
        will fail. If not specified, the server default applies.

    Raises:
      TypeError: if reference is not a DatasetReference.
      bq_error.BigqueryNotFoundError: if reference does not exist and
        ignore_not_found is False.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.DatasetReference,
        method='DeleteDataset',
    )

    args = dict(reference)

    if delete_contents is not None:
      args['deleteContents'] = delete_contents
    try:
      self.apiclient.datasets().delete(**args).execute()
    except bq_error.BigqueryNotFoundError:
      if not ignore_not_found:
        raise

  def DeleteTable(self, reference, ignore_not_found=False):
    """Deletes TableReference reference.

    Args:
      reference: the TableReference to delete.
      ignore_not_found: Whether to ignore "not found" errors.

    Raises:
      TypeError: if reference is not a TableReference.
      bq_error.BigqueryNotFoundError: if reference does not exist and
        ignore_not_found is False.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TableReference,
        method='DeleteTable',
    )
    try:
      self.apiclient.tables().delete(**dict(reference)).execute()
    except bq_error.BigqueryNotFoundError:
      if not ignore_not_found:
        raise

  def DeleteJob(self, reference, ignore_not_found=False):
    """Deletes JobReference reference.

    Args:
      reference: the JobReference to delete.
      ignore_not_found: Whether to ignore "not found" errors.

    Raises:
      TypeError: if reference is not a JobReference.
      bq_error.BigqueryNotFoundError: if reference does not exist and
        ignore_not_found is False.
    """
    bq_id_utils.typecheck(
        reference, bq_id_utils.ApiClientHelper.JobReference, method='DeleteJob'
    )
    try:
      self.apiclient.jobs().delete(**dict(reference)).execute()
    except bq_error.BigqueryNotFoundError:
      if not ignore_not_found:
        raise

  def DeleteModel(self, reference, ignore_not_found=False):
    """Deletes ModelReference reference.

    Args:
      reference: the ModelReference to delete.
      ignore_not_found: Whether to ignore "not found" errors.

    Raises:
      TypeError: if reference is not a ModelReference.
      bq_error.BigqueryNotFoundError: if reference does not exist and
        ignore_not_found is False.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.ModelReference,
        method='DeleteModel',
    )
    try:
      self.GetModelsApiClient().models().delete(
          projectId=reference.projectId,
          datasetId=reference.datasetId,
          modelId=reference.modelId).execute()
    except bq_error.BigqueryNotFoundError:
      if not ignore_not_found:
        raise

  def DeleteRoutine(self, reference, ignore_not_found=False):
    """Deletes RoutineReference reference.

    Args:
      reference: the RoutineReference to delete.
      ignore_not_found: Whether to ignore "not found" errors.

    Raises:
      TypeError: if reference is not a RoutineReference.
      bq_error.BigqueryNotFoundError: if reference does not exist and
        ignore_not_found is False.
    """
    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.RoutineReference,
        method='DeleteRoutine',
    )
    try:
      self.GetRoutinesApiClient().routines().delete(**dict(reference)).execute()
    except bq_error.BigqueryNotFoundError:
      if not ignore_not_found:
        raise

  def DeleteTransferConfig(self, reference, ignore_not_found=False):
    """Deletes TransferConfigReference reference.

    Args:
      reference: the TransferConfigReference to delete.
      ignore_not_found: Whether to ignore "not found" errors.

    Raises:
      TypeError: if reference is not a TransferConfigReference.
      bq_error.BigqueryNotFoundError: if reference does not exist and
        ignore_not_found is False.
    """

    bq_id_utils.typecheck(
        reference,
        bq_id_utils.ApiClientHelper.TransferConfigReference,
        method='DeleteTransferConfig')
    try:
      transfer_client = self.GetTransferV1ApiClient()
      transfer_client.projects().locations().transferConfigs().delete(
          name=reference.transferConfigName).execute()
    except bq_error.BigqueryNotFoundError as e:
      if not ignore_not_found:
        raise bq_error.BigqueryNotFoundError(
            'Not found: %r' % (reference,), {'reason': 'notFound'}, []) from e

  #################################
  ## Job control
  #################################

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def _ExecuteInChunksWithProgress(request):
    """Run an apiclient request with a resumable upload, showing progress.

    Args:
      request: an apiclient request having a media_body that is a
        MediaFileUpload(resumable=True).

    Returns:
      The result of executing the request, if it succeeds.

    Raises:
      BigQueryError: on a non-retriable error or too many retriable errors.
    """
    # pylint: disable=protected-access
    return bq_client_utils._ExecuteInChunksWithProgress(request)
    # pylint: enable=protected-access

  def StartJob(self,
               configuration,
               project_id=None,
               upload_file=None,
               job_id=None,
               location=None):
    """Start a job with the given configuration.

    Args:
      configuration: The configuration for a job.
      project_id: The project_id to run the job under. If None, self.project_id
        is used.
      upload_file: A file to include as a media upload to this request. Only
        valid on job requests that expect a media upload file.
      job_id: A unique job_id to use for this job. If a JobIdGenerator, a job id
        will be generated from the job configuration. If None, a unique job_id
        will be created for this request.
      location: Optional. The geographic location where the job should run.

    Returns:
      The job resource returned from the insert job request. If there is an
      error, the jobReference field will still be filled out with the job
      reference used in the request.

    Raises:
      bq_error.BigqueryClientConfigurationError: if project_id and
        self.project_id are None.
    """
    project_id = project_id or self.project_id
    if not project_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot start a job without a project id.')
    configuration = configuration.copy()
    if self.job_property:
      configuration['properties'] = dict(
          prop.partition('=')[0::2] for prop in self.job_property)
    job_request = {'configuration': configuration}

    # Use the default job id generator if no job id was supplied.
    job_id = job_id or self.job_id_generator

    if isinstance(job_id, bq_client_utils.JobIdGenerator):
      job_id = job_id.Generate(configuration)

    if job_id is not None:
      job_reference = {'jobId': job_id, 'projectId': project_id}
      job_request['jobReference'] = job_reference
      if location:
        job_reference['location'] = location
    media_upload = ''
    if upload_file:
      resumable = self.enable_resumable_uploads
      # There is a bug in apiclient http lib that make uploading resumable files
      # with 0 length broken.
      if os.stat(upload_file).st_size == 0:
        resumable = False
      media_upload = http_request.MediaFileUpload(
          filename=upload_file,
          mimetype='application/octet-stream',
          resumable=resumable)
    request = self.apiclient.jobs().insert(
        body=job_request, media_body=media_upload, projectId=project_id)
    if upload_file and resumable:
      result = bq_client_utils.ExecuteInChunksWithProgress(request)
    else:
      result = request.execute()
    return result

  def _StartQueryRpc(self,
                     query,
                     dry_run=None,
                     use_cache=None,
                     preserve_nulls=None,
                     request_id=None,
                     maximum_bytes_billed=None,
                     max_results=None,
                     timeout_ms=None,
                     min_completion_ratio=None,
                     project_id=None,
                     external_table_definitions_json=None,
                     udf_resources=None,
                     use_legacy_sql=None,
                     location=None,
                     connection_properties=None,
                     **kwds):
    """Executes the given query using the rpc-style query api.

    Args:
      query: Query to execute.
      dry_run: Optional. Indicates whether the query will only be validated and
        return processing statistics instead of actually running.
      use_cache: Optional. Whether to use the query cache. Caching is
        best-effort only and you should not make assumptions about whether or
        how long a query result will be cached.
      preserve_nulls: Optional. Indicates whether to preserve nulls in input
        data. Temporary flag; will be removed in a future version.
      request_id: Optional. The idempotency token for jobs.query
      maximum_bytes_billed: Optional. Upper limit on the number of billed bytes.
      max_results: Maximum number of results to return.
      timeout_ms: Timeout, in milliseconds, for the call to query().
      min_completion_ratio: Optional. Specifies the minimum fraction of data
        that must be scanned before a query returns. This value should be
        between 0.0 and 1.0 inclusive.
      project_id: Project id to use.
      external_table_definitions_json: Json representation of external table
        definitions.
      udf_resources: Array of inline and external UDF code resources.
      use_legacy_sql: The choice of using Legacy SQL for the query is optional.
        If not specified, the server will automatically determine the dialect
        based on query information, such as dialect prefixes. If no prefixes are
        found, it will default to Legacy SQL.
      location: Optional. The geographic location where the job should run.
      connection_properties: Optional. Connection properties to use when running
        the query, presented as a list of key/value pairs. A key of "time_zone"
        indicates that the query will be run with the default timezone
        corresponding to the value.
      **kwds: Extra keyword arguments passed directly to jobs.Query().

    Returns:
      The query response.

    Raises:
      bq_error.BigqueryClientConfigurationError: if project_id and
        self.project_id are None.
      bq_error.BigqueryError: if query execution fails.
    """
    project_id = project_id or self.project_id
    if not project_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot run a query without a project id.')
    request = {'query': query}
    if external_table_definitions_json:
      request['tableDefinitions'] = external_table_definitions_json
    if udf_resources:
      request['userDefinedFunctionResources'] = udf_resources
    if self.dataset_id:
      request['defaultDataset'] = bq_client_utils.GetQueryDefaultDataset(
          self.dataset_id)

    # If the request id flag is set, generate a random one if it is not provided
    # explicitly.
    if request_id is None and flags.FLAGS.jobs_query_use_request_id:
      request_id = str(uuid.uuid4())

    bq_processor_utils.ApplyParameters(
        request,
        preserve_nulls=preserve_nulls,
        request_id=request_id,
        maximum_bytes_billed=maximum_bytes_billed,
        use_query_cache=use_cache,
        timeout_ms=timeout_ms,
        max_results=max_results,
        use_legacy_sql=use_legacy_sql,
        min_completion_ratio=min_completion_ratio,
        location=location)
    bq_processor_utils.ApplyParameters(
        request, connection_properties=connection_properties
    )
    bq_processor_utils.ApplyParameters(request, dry_run=dry_run)
    logging.debug(
        'Calling self.apiclient.jobs().query(%s, %s, %s)',
        request, project_id, kwds)
    return self.apiclient.jobs().query(
        body=request, projectId=project_id, **kwds).execute()

  def GetQueryResults(self,
                      job_id=None,
                      project_id=None,
                      max_results=None,
                      timeout_ms=None,
                      location=None):
    """Waits for a query job to run and returns results if complete.

    By default, waits 10s for the provided job to complete and either returns
    the results or a response where jobComplete is set to false. The timeout can
    be increased but the call is not guaranteed to wait for the specified
    timeout.

    Args:
      job_id: The job id of the query job that we are waiting to complete.
      project_id: The project id of the query job.
      max_results: The maximum number of results.
      timeout_ms: The number of milliseconds to wait for the query to complete.
      location: Optional. The geographic location of the job.

    Returns:
      The getQueryResults() result.

    Raises:
      bq_error.BigqueryClientConfigurationError: if project_id and
        self.project_id are None.
    """
    project_id = project_id or self.project_id
    if not project_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot get query results without a project id.')
    kwds = {}
    bq_processor_utils.ApplyParameters(
        kwds,
        job_id=job_id,
        project_id=project_id,
        timeout_ms=timeout_ms,
        max_results=max_results,
        location=location)
    return self.apiclient.jobs().getQueryResults(**kwds).execute()

  def RunJobSynchronously(self,
                          configuration,
                          project_id=None,
                          upload_file=None,
                          job_id=None,
                          location=None):
    """Starts a job and waits for it to complete.

    Args:
      configuration: The configuration for a job.
      project_id: The project_id to run the job under. If None, self.project_id
        is used.
      upload_file: A file to include as a media upload to this request. Only
        valid on job requests that expect a media upload file.
      job_id: A unique job_id to use for this job. If a JobIdGenerator, a job id
        will be generated from the job configuration. If None, a unique job_id
        will be created for this request.
      location: Optional. The geographic location where the job should run.

    Returns:
      job, if it did not fail.

    Raises:
      BigQueryError: if the job fails.
    """
    result = self.StartJob(
        configuration,
        project_id=project_id,
        upload_file=upload_file,
        job_id=job_id,
        location=location)
    if result['status']['state'] != 'DONE':
      job_reference = bq_processor_utils.ConstructObjectReference(result)
      result = self.WaitJob(job_reference)
    return bq_client_utils.RaiseIfJobError(result)

  def ExecuteJob(self,
                 configuration,
                 sync=None,
                 project_id=None,
                 upload_file=None,
                 job_id=None,
                 location=None):
    """Execute a job, possibly waiting for results."""
    if sync is None:
      sync = self.sync

    if sync:
      job = self.RunJobSynchronously(
          configuration,
          project_id=project_id,
          upload_file=upload_file,
          job_id=job_id,
          location=location)
    else:
      job = self.StartJob(
          configuration,
          project_id=project_id,
          upload_file=upload_file,
          job_id=job_id,
          location=location)
      bq_client_utils.RaiseIfJobError(job)
    return job

  def CancelJob(self, project_id=None, job_id=None, location=None):
    """Attempt to cancel the specified job if it is running.

    Args:
      project_id: The project_id to the job is running under. If None,
        self.project_id is used.
      job_id: The job id for this job.
      location: Optional. The geographic location of the job.

    Returns:
      The job resource returned for the job for which cancel is being requested.

    Raises:
      bq_error.BigqueryClientConfigurationError: if project_id or job_id
        are None.
    """
    project_id = project_id or self.project_id
    if not project_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot cancel a job without a project id.')
    if not job_id:
      raise bq_error.BigqueryClientConfigurationError(
          'Cannot cancel a job without a job id.')

    job_reference = bq_id_utils.ApiClientHelper.JobReference.Create(
        projectId=project_id, jobId=job_id, location=location)
    result = (
        self.apiclient.jobs().cancel(**dict(job_reference)).execute()['job'])
    if result['status']['state'] != 'DONE' and self.sync:
      job_reference = bq_processor_utils.ConstructObjectReference(result)
      result = self.WaitJob(job_reference=job_reference)
    return result

  # TODO(b/324243535): Delete these once the migration is complete.
  # pylint: disable=invalid-name
  WaitPrinter = bq_client_utils.WaitPrinter
  WaitPrinterHelper = bq_client_utils.WaitPrinterHelper
  QuietWaitPrinter = bq_client_utils.QuietWaitPrinter
  VerboseWaitPrinter = bq_client_utils.VerboseWaitPrinter
  TransitionWaitPrinter = bq_client_utils.TransitionWaitPrinter
  # pylint: enable=invalid-name

  def WaitJob(self,
              job_reference,
              status='DONE',
              wait=sys.maxsize,
              wait_printer_factory=None):
    """Poll for a job to run until it reaches the requested status.

    Arguments:
      job_reference: JobReference to poll.
      status: (optional, default 'DONE') Desired job status.
      wait: (optional, default maxint) Max wait time.
      wait_printer_factory: (optional, defaults to self.wait_printer_factory)
        Returns a subclass of WaitPrinter that will be called after each job
        poll.

    Returns:
      The job object returned by the final status call.

    Raises:
      StopIteration: If polling does not reach the desired state before
        timing out.
      ValueError: If given an invalid wait value.
    """
    bq_id_utils.typecheck(
        job_reference,
        bq_id_utils.ApiClientHelper.JobReference,
        method='WaitJob',
    )
    start_time = time.time()
    job = None
    if wait_printer_factory:
      printer = wait_printer_factory()
    else:
      printer = self.wait_printer_factory()

    # This is a first pass at wait logic: we ping at 1s intervals a few
    # times, then increase to max(3, max_wait), and then keep waiting
    # that long until we've run out of time.
    waits = itertools.chain(
       itertools.repeat(1, 8), range(2, 30, 3),
       itertools.repeat(30))
    current_wait = 0
    current_status = 'UNKNOWN'
    in_error_state = False
    while current_wait <= wait:
      try:
        done, job = self.PollJob(job_reference, status=status, wait=wait)
        current_status = job['status']['state']
        in_error_state = False
        if done:
          printer.Print(job_reference.jobId, current_wait, current_status)
          break
      except bq_error.BigqueryCommunicationError as e:
        # Communication errors while waiting on a job are okay.
        logging.warning('Transient error during job status check: %s', e)
      except bq_error.BigqueryBackendError as e:
        # Temporary server errors while waiting on a job are okay.
        logging.warning('Transient error during job status check: %s', e)
      except BigqueryServiceError as e:
        # Among this catch-all class, some kinds are permanent
        # errors, so we don't want to retry indefinitely, but if
        # the error is transient we'd like "wait" to get past it.
        if in_error_state: raise
        in_error_state = True

      # For every second we're polling, update the message to the user.
      for _ in range(next(waits)):
        current_wait = time.time() - start_time
        printer.Print(job_reference.jobId, current_wait, current_status)
        time.sleep(1)
    else:
      raise StopIteration(
          'Wait timed out. Operation not finished, in state %s' %
          (current_status,))
    printer.Done()
    return job

  def PollJob(self, job_reference, status='DONE', wait=0):
    """Poll a job once for a specific status.

    Arguments:
      job_reference: JobReference to poll.
      status: (optional, default 'DONE') Desired job status.
      wait: (optional, default 0) Max server-side wait time for one poll call.

    Returns:
      Tuple (in_state, job) where in_state is True if job is
      in the desired state.

    Raises:
      ValueError: If given an invalid wait value.
    """
    bq_id_utils.typecheck(
        job_reference,
        bq_id_utils.ApiClientHelper.JobReference,
        method='PollJob',
    )
    wait = bq_client_utils.NormalizeWait(wait)
    job = self.apiclient.jobs().get(**dict(job_reference)).execute()
    current = job['status']['state']
    return (current == status, job)

  #################################
  ## Wrappers for job types
  #################################

  def RunQuery(self, start_row, max_rows, **kwds):
    """Run a query job synchronously, and return the result.

    Args:
      start_row: first row to read.
      max_rows: number of rows to read.
      **kwds: Passed on to self.Query.

    Returns:
      A tuple where the first item is the list of fields and the
      second item a list of rows.
    """
    new_kwds = dict(kwds)
    new_kwds['sync'] = True
    job = self.Query(**new_kwds)

    return self.ReadSchemaAndJobRows(
        job['jobReference'], start_row=start_row, max_rows=max_rows)

  def RunQueryRpc(self,
                  query,
                  dry_run=None,
                  use_cache=None,
                  preserve_nulls=None,
                  request_id=None,
                  maximum_bytes_billed=None,
                  max_results=None,
                  wait=sys.maxsize,
                  min_completion_ratio=None,
                  wait_printer_factory=None,
                  max_single_wait=None,
                  external_table_definitions_json=None,
                  udf_resources=None,
                  location=None,
                  connection_properties=None,
                  **kwds):
    """Executes the given query using the rpc-style query api.

    Args:
      query: Query to execute.
      dry_run: Optional. Indicates whether the query will only be validated and
        return processing statistics instead of actually running.
      use_cache: Optional. Whether to use the query cache. Caching is
        best-effort only and you should not make assumptions about whether or
        how long a query result will be cached.
      preserve_nulls: Optional. Indicates whether to preserve nulls in input
        data. Temporary flag; will be removed in a future version.
      request_id: Optional. Specifies the idempotency token for the request.
      maximum_bytes_billed: Optional. Upper limit on maximum bytes billed.
      max_results: Optional. Maximum number of results to return.
      wait: (optional, default maxint) Max wait time in seconds.
      min_completion_ratio: Optional. Specifies the minimum fraction of data
        that must be scanned before a query returns. This value should be
        between 0.0 and 1.0 inclusive.
      wait_printer_factory: (optional, defaults to self.wait_printer_factory)
        Returns a subclass of WaitPrinter that will be called after each job
        poll.
      max_single_wait: Optional. Maximum number of seconds to wait for each call
        to query() / getQueryResults().
      external_table_definitions_json: Json representation of external table
        definitions.
      udf_resources: Array of inline and remote UDF resources.
      location: Optional. The geographic location where the job should run.
      connection_properties: Optional. Connection properties to use when running
        the query, presented as a list of key/value pairs. A key of "time_zone"
        indicates that the query will be run with the default timezone
        corresponding to the value.
      **kwds: Passed directly to self.ExecuteSyncQuery.

    Raises:
      bq_error.BigqueryClientError: if no query is provided.
      StopIteration: if the query does not complete within wait seconds.
      bq_error.BigqueryError: if query fails.

    Returns:
      A tuple (schema fields, row results, execution metadata).
        For regular queries, the execution metadata dict contains
        the 'State' and 'status' elements that would be in a job result
        after FormatJobInfo().
        For dry run queries schema and rows are empty, the execution metadata
        dict contains statistics
    """
    if not self.sync:
      raise bq_error.BigqueryClientError(
          'Running RPC-style query asynchronously is not supported')
    if not query:
      raise bq_error.BigqueryClientError('No query string provided')

    if request_id is not None and not flags.FLAGS.jobs_query_use_request_id:
      raise bq_error.BigqueryClientError(
          'request_id is not yet supported')

    if wait_printer_factory:
      printer = wait_printer_factory()
    else:
      printer = self.wait_printer_factory()

    start_time = time.time()
    elapsed_time = 0
    job_reference = None
    current_wait_ms = None
    while True:
      try:
        elapsed_time = 0 if job_reference is None else time.time() - start_time
        remaining_time = wait - elapsed_time
        if max_single_wait is not None:
          # Compute the current wait, being careful about overflow, since
          # remaining_time may be counting down from sys.maxint.
          current_wait_ms = int(min(remaining_time, max_single_wait) * 1000)
          if current_wait_ms < 0:
            current_wait_ms = sys.maxsize
        if remaining_time < 0:
          raise StopIteration('Wait timed out. Query not finished.')
        if job_reference is None:
          # We haven't yet run a successful Query(), so we don't
          # have a job id to check on.
          rows_to_read = max_results
          if self.max_rows_per_request is not None:
            if rows_to_read is None:
              rows_to_read = self.max_rows_per_request
            else:
              rows_to_read = min(self.max_rows_per_request, int(rows_to_read))
          result = self._StartQueryRpc(
              query=query,
              preserve_nulls=preserve_nulls,
              request_id=request_id,
              maximum_bytes_billed=maximum_bytes_billed,
              use_cache=use_cache,
              dry_run=dry_run,
              min_completion_ratio=min_completion_ratio,
              timeout_ms=current_wait_ms,
              max_results=rows_to_read,
              external_table_definitions_json=external_table_definitions_json,
              udf_resources=udf_resources,
              location=location,
              connection_properties=connection_properties,
              **kwds)
          if dry_run:
            execution = dict(
                statistics=dict(
                    query=dict(
                        totalBytesProcessed=result['totalBytesProcessed'],
                        cacheHit=result['cacheHit'])))
            if 'schema' in result:
              execution['statistics']['query']['schema'] = result['schema']
            return ([], [], execution)
          if 'jobReference' in result:
            job_reference = bq_id_utils.ApiClientHelper.JobReference.Create(
                **result['jobReference'])
        else:
          # The query/getQueryResults methods do not return the job state,
          # so we just print 'RUNNING' while we are actively waiting.
          printer.Print(job_reference.jobId, elapsed_time, 'RUNNING')
          result = self.GetQueryResults(
              job_reference.jobId,
              max_results=max_results,
              timeout_ms=current_wait_ms,
              location=location)
        if result['jobComplete']:
          (schema, rows) = self.ReadSchemaAndJobRows(
              dict(job_reference) if job_reference else {},
              start_row=0,
              max_rows=max_results,
              result_first_page=result)
          # If we get here, we must have succeeded.  We could still have
          # non-fatal errors though.
          status = {}
          if 'errors' in result:
            status['errors'] = result['errors']
          execution = {
              'State': 'SUCCESS',
              'status': status,
              'jobReference': job_reference
          }
          return (schema, rows, execution)
      except bq_error.BigqueryCommunicationError as e:
        # Communication errors while waiting on a job are okay.
        logging.warning('Transient error during query: %s', e)
      except bq_error.BigqueryBackendError as e:
        # Temporary server errors while waiting on a job are okay.
        logging.warning('Transient error during query: %s', e)

  def Query(
      self,
      query,
      destination_table=None,
      create_disposition=None,
      write_disposition=None,
      priority=None,
      preserve_nulls=None,
      allow_large_results=None,
      dry_run=None,
      use_cache=None,
      min_completion_ratio=None,
      flatten_results=None,
      external_table_definitions_json=None,
      udf_resources=None,
      maximum_billing_tier=None,
      maximum_bytes_billed=None,
      use_legacy_sql=None,
      schema_update_options=None,
      labels=None,
      query_parameters=None,
      time_partitioning=None,
      destination_encryption_configuration=None,
      clustering=None,
      range_partitioning=None,
      script_options=None,
      job_timeout_ms=None,
      create_session=None,
      connection_properties=None,
      continuous=None,
      **kwds):
    # pylint: disable=g-doc-args
    """Execute the given query, returning the created job.

    The job will execute synchronously if sync=True is provided as an
    argument or if self.sync is true.

    Args:
      query: Query to execute.
      destination_table: (default None) If provided, send the results to the
        given table.
      create_disposition: Optional. Specifies the create_disposition for the
        destination_table.
      write_disposition: Optional. Specifies the write_disposition for the
        destination_table.
      priority: Optional. Priority to run the query with. Either 'INTERACTIVE'
        (default) or 'BATCH'.
      preserve_nulls: Optional. Indicates whether to preserve nulls in input
        data. Temporary flag; will be removed in a future version.
      allow_large_results: Enables larger destination table sizes.
      dry_run: Optional. Indicates whether the query will only be validated and
        return processing statistics instead of actually running.
      use_cache: Optional. Whether to use the query cache. If create_disposition
        is CREATE_NEVER, will only run the query if the result is already
        cached. Caching is best-effort only and you should not make assumptions
        about whether or how long a query result will be cached.
      min_completion_ratio: Optional. Specifies the minimum fraction of data
        that must be scanned before a query returns. This value should be
        between 0.0 and 1.0 inclusive.
      flatten_results: Whether to flatten nested and repeated fields in the
        result schema. If not set, the default behavior is to flatten.
      external_table_definitions_json: Json representation of external table
        definitions.
      udf_resources: Array of inline and remote UDF resources.
      maximum_billing_tier: Upper limit for billing tier.
      maximum_bytes_billed: Upper limit for bytes billed.
      use_legacy_sql: The choice of using Legacy SQL for the query is optional.
        If not specified, the server will automatically determine the dialect
        based on query information, such as dialect prefixes. If no prefixes are
        found, it will default to Legacy SQL.
      schema_update_options: schema update options when appending to the
        destination table or truncating a table partition.
      labels: an optional dict of labels to set on the query job.
      query_parameters: parameter values for use_legacy_sql=False queries.
      time_partitioning: Optional. Provides time based partitioning
        specification for the destination table.
      clustering: Optional. Provides clustering specification for the
        destination table.
      destination_encryption_configuration: Optional. Allows user to encrypt the
        table created from a query job with a Cloud KMS key.
      range_partitioning: Optional. Provides range partitioning specification
        for the destination table.
      script_options: Optional. Options controlling script execution.
      job_timeout_ms: Optional. How long to let the job run.
      continuous: Optional. Whether the query should be executed as continuous
        query.
      **kwds: Passed on to self.ExecuteJob.

    Raises:
      bq_error.BigqueryClientError: if no query is provided.

    Returns:
      The resulting job info.
    """
    if not query:
      raise bq_error.BigqueryClientError('No query string provided')
    query_config = {'query': query}
    if self.dataset_id:
      query_config['defaultDataset'] = bq_client_utils.GetQueryDefaultDataset(
          self.dataset_id)
    if external_table_definitions_json:
      query_config['tableDefinitions'] = external_table_definitions_json
    if udf_resources:
      query_config['userDefinedFunctionResources'] = udf_resources
    if destination_table:
      try:
        reference = bq_client_utils.GetTableReference(
            id_fallbacks=self, identifier=destination_table)
      except bq_error.BigqueryError as e:
        raise bq_error.BigqueryError(
            'Invalid value %s for destination_table: %s' %
            (destination_table, e))
      query_config['destinationTable'] = dict(reference)
    if destination_encryption_configuration:
      query_config['destinationEncryptionConfiguration'] = (
          destination_encryption_configuration)
    if script_options:
      query_config['scriptOptions'] = script_options
    bq_processor_utils.ApplyParameters(
        query_config,
        allow_large_results=allow_large_results,
        create_disposition=create_disposition,
        preserve_nulls=preserve_nulls,
        priority=priority,
        write_disposition=write_disposition,
        use_query_cache=use_cache,
        flatten_results=flatten_results,
        maximum_billing_tier=maximum_billing_tier,
        maximum_bytes_billed=maximum_bytes_billed,
        use_legacy_sql=use_legacy_sql,
        schema_update_options=schema_update_options,
        query_parameters=query_parameters,
        time_partitioning=time_partitioning,
        clustering=clustering,
        create_session=create_session,
        min_completion_ratio=min_completion_ratio,
        continuous=continuous,
        range_partitioning=range_partitioning)
    bq_processor_utils.ApplyParameters(
        query_config, connection_properties=connection_properties
    )
    request = {'query': query_config}
    bq_processor_utils.ApplyParameters(
        request, dry_run=dry_run, labels=labels, job_timeout_ms=job_timeout_ms)
    logging.debug('Calling self.ExecuteJob(%s, %s)', request, kwds)
    return self.ExecuteJob(request, **kwds)

  def Load(
      self,
      destination_table_reference,
      source,
      schema=None,
      create_disposition=None,
      write_disposition=None,
      field_delimiter=None,
      skip_leading_rows=None,
      encoding=None,
      quote=None,
      max_bad_records=None,
      allow_quoted_newlines=None,
      source_format=None,
      allow_jagged_rows=None,
      preserve_ascii_control_characters=None,
      ignore_unknown_values=None,
      projection_fields=None,
      autodetect=None,
      schema_update_options=None,
      null_marker=None,
      time_partitioning=None,
      clustering=None,
      destination_encryption_configuration=None,
      use_avro_logical_types=None,
      reference_file_schema_uri=None,
      range_partitioning=None,
      hive_partitioning_options=None,
      decimal_target_types=None,
      json_extension=None,
      file_set_spec_type=None,
      thrift_options=None,
      parquet_options=None,
      connection_properties=None,
      copy_files_only: Optional[bool] = None,
      **kwds):
    """Load the given data into BigQuery.

    The job will execute synchronously if sync=True is provided as an
    argument or if self.sync is true.

    Args:
      destination_table_reference: TableReference to load data into.
      source: String specifying source data to load.
      schema: (default None) Schema of the created table. (Can be left blank for
        append operations.)
      create_disposition: Optional. Specifies the create_disposition for the
        destination_table_reference.
      write_disposition: Optional. Specifies the write_disposition for the
        destination_table_reference.
      field_delimiter: Optional. Specifies the single byte field delimiter.
      skip_leading_rows: Optional. Number of rows of initial data to skip.
      encoding: Optional. Specifies character encoding of the input data. May be
        "UTF-8" or "ISO-8859-1". Defaults to UTF-8 if not specified.
      quote: Optional. Quote character to use. Default is '"'. Note that quoting
        is done on the raw binary data before encoding is applied.
      max_bad_records: Optional. Maximum number of bad records that should be
        ignored before the entire job is aborted. Only supported for CSV and
        NEWLINE_DELIMITED_JSON file formats.
      allow_quoted_newlines: Optional. Whether to allow quoted newlines in CSV
        import data.
      source_format: Optional. Format of source data. May be "CSV",
        "DATASTORE_BACKUP", or "NEWLINE_DELIMITED_JSON".
      allow_jagged_rows: Optional. Whether to allow missing trailing optional
        columns in CSV import data.
      preserve_ascii_control_characters: Optional. Whether to preserve embedded
        Ascii Control characters in CSV import data.
      ignore_unknown_values: Optional. Whether to allow extra, unrecognized
        values in CSV or JSON data.
      projection_fields: Optional. If sourceFormat is set to "DATASTORE_BACKUP",
        indicates which entity properties to load into BigQuery from a Cloud
        Datastore backup.
      autodetect: Optional. If true, then we automatically infer the schema and
        options of the source files if they are CSV or JSON formats.
      schema_update_options: schema update options when appending to the
        destination table or truncating a table partition.
      null_marker: Optional. String that will be interpreted as a NULL value.
      time_partitioning: Optional. Provides time based partitioning
        specification for the destination table.
      clustering: Optional. Provides clustering specification for the
        destination table.
      destination_encryption_configuration: Optional. Allows user to encrypt the
        table created from a load job with Cloud KMS key.
      use_avro_logical_types: Optional. Allows user to override default
        behaviour for Avro logical types. If this is set, Avro fields with
        logical types will be interpreted into their corresponding types (ie.
        TIMESTAMP), instead of only using their raw types (ie. INTEGER).
      reference_file_schema_uri: Optional. Allows user to provide a reference
        file with the reader schema, enabled for the format: AVRO, PARQUET, ORC.
      range_partitioning: Optional. Provides range partitioning specification
        for the destination table.
      hive_partitioning_options: (experimental) Options for configuring hive is
        picked if it is in the specified list and if it supports the precision
        and the scale. STRING supports all precision and scale values. If none
        of the listed types supports the precision and the scale, the type
        supporting the widest range in the specified list is picked, and if a
        value exceeds the supported range when reading the data, an error will
        be returned. This field cannot contain duplicate types. The order of the
      decimal_target_types: (experimental) Defines the list of possible SQL data
        types to which the source decimal values are converted. This list and
        the precision and the scale parameters of the decimal field determine
        the target type. In the order of NUMERIC, BIGNUMERIC, and STRING, a type
        is picked if it is in the specified list and if it supports the
        precision and the scale. STRING supports all precision and scale values.
        If none of the listed types supports the precision and the scale, the
        type supporting the widest range in the specified list is picked, and if
        a value exceeds the supported range when reading the data, an error will
        be returned. This field cannot contain duplicate types. The order of the
        types in this field is ignored. For example, ["BIGNUMERIC", "NUMERIC"]
        is the same as ["NUMERIC", "BIGNUMERIC"] and NUMERIC always takes
        precedence over BIGNUMERIC. Defaults to ["NUMERIC", "STRING"] for ORC
        and ["NUMERIC"] for the other file formats.
      json_extension: (experimental) Specify alternative parsing for JSON source
        format. To load newline-delimited JSON, specify 'GEOJSON'. Only
        applicable if `source_format` is 'NEWLINE_DELIMITED_JSON'.
      file_set_spec_type: (experimental) Set how to discover files for loading.
        Specify 'FILE_SYSTEM_MATCH' (default behavior) to expand source URIs by
        listing files from the underlying object store. Specify
        'NEW_LINE_DELIMITED_MANIFEST' to parse the URIs as new line delimited
        manifest files, where each line contains a URI (No wild-card URIs are
        supported).
      thrift_options: (experimental) Options for configuring Apache Thrift load,
        which is required if `source_format` is 'THRIFT'.
      parquet_options: Options for configuring parquet files load, only
        applicable if `source_format` is 'PARQUET'.
      connection_properties: Optional. ConnectionProperties for load job.
      copy_files_only: Optional. True to configures the load job to only copy
        files to the destination BigLake managed table, without reading file
        content and writing them to new files.
      **kwds: Passed on to self.ExecuteJob.

    Returns:
      The resulting job info.
    """
    bq_id_utils.typecheck(
        destination_table_reference, bq_id_utils.ApiClientHelper.TableReference
    )
    load_config = {'destinationTable': dict(destination_table_reference)}
    sources = bq_client_utils.ProcessSources(source)
    if sources[0].startswith(bq_processor_utils.GCS_SCHEME_PREFIX):
      load_config['sourceUris'] = sources
      upload_file = None
    else:
      upload_file = sources[0]
    if schema is not None:
      load_config['schema'] = {'fields': bq_client_utils.ReadSchema(schema)}
    if use_avro_logical_types is not None:
      load_config['useAvroLogicalTypes'] = use_avro_logical_types
    if reference_file_schema_uri is not None:
      load_config['reference_file_schema_uri'] = reference_file_schema_uri
    if file_set_spec_type is not None:
      load_config['fileSetSpecType'] = file_set_spec_type
    if json_extension is not None:
      load_config['jsonExtension'] = json_extension
    if parquet_options is not None:
      load_config['parquetOptions'] = parquet_options
    load_config['decimalTargetTypes'] = decimal_target_types
    if destination_encryption_configuration:
      load_config['destinationEncryptionConfiguration'] = (
          destination_encryption_configuration)
    bq_processor_utils.ApplyParameters(
        load_config,
        create_disposition=create_disposition,
        write_disposition=write_disposition,
        field_delimiter=field_delimiter,
        skip_leading_rows=skip_leading_rows,
        encoding=encoding,
        quote=quote,
        max_bad_records=max_bad_records,
        source_format=source_format,
        allow_quoted_newlines=allow_quoted_newlines,
        allow_jagged_rows=allow_jagged_rows,
        preserve_ascii_control_characters=preserve_ascii_control_characters,
        ignore_unknown_values=ignore_unknown_values,
        projection_fields=projection_fields,
        schema_update_options=schema_update_options,
        null_marker=null_marker,
        time_partitioning=time_partitioning,
        clustering=clustering,
        autodetect=autodetect,
        range_partitioning=range_partitioning,
        hive_partitioning_options=hive_partitioning_options,
        thrift_options=thrift_options,
        connection_properties=connection_properties,
        copy_files_only=copy_files_only,
        parquet_options=parquet_options)
    return self.ExecuteJob(
        configuration={'load': load_config}, upload_file=upload_file, **kwds)


  def Extract(self,
              reference,
              destination_uris,
              print_header=None,
              field_delimiter=None,
              destination_format=None,
              trial_id=None,
              add_serving_default_signature=None,
              compression=None,
              use_avro_logical_types=None,
              **kwds):
    """Extract the given table from BigQuery.

    The job will execute synchronously if sync=True is provided as an
    argument or if self.sync is true.

    Args:
      reference: TableReference to read data from.
      destination_uris: String specifying one or more destination locations,
        separated by commas.
      print_header: Optional. Whether to print out a header row in the results.
      field_delimiter: Optional. Specifies the single byte field delimiter.
      destination_format: Optional. Format to extract table to. May be "CSV",
        "AVRO" or "NEWLINE_DELIMITED_JSON".
      trial_id: Optional. 1-based ID of the trial to be exported from a
        hyperparameter tuning model.
      add_serving_default_signature: Optional. Whether to add serving_default
        signature for BigQuery ML trained tf based models.
      compression: Optional. The compression type to use for exported files.
        Possible values include "GZIP" and "NONE". The default value is NONE.
      use_avro_logical_types: Optional. Whether to use avro logical types for
        applicable column types on extract jobs.
      **kwds: Passed on to self.ExecuteJob.

    Returns:
      The resulting job info.

    Raises:
      bq_error.BigqueryClientError: if required parameters are invalid.
    """
    bq_id_utils.typecheck(
        reference,
        (
            bq_id_utils.ApiClientHelper.TableReference,
            bq_id_utils.ApiClientHelper.ModelReference,
        ),
        method='Extract',
    )
    uris = destination_uris.split(',')
    for uri in uris:
      if not uri.startswith(bq_processor_utils.GCS_SCHEME_PREFIX):
        raise bq_error.BigqueryClientError(
            'Illegal URI: {}. Extract URI must start with "{}".'.format(
                uri, bq_processor_utils.GCS_SCHEME_PREFIX))
    if isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
      extract_config = {'sourceTable': dict(reference)}
    elif isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference):
      extract_config = {'sourceModel': dict(reference)}
      if trial_id:
        extract_config.update({'modelExtractOptions': {'trialId': trial_id}})
      if add_serving_default_signature:
        extract_config.update({
            'modelExtractOptions': {
                'addServingDefaultSignature': add_serving_default_signature
            }
        })
    bq_processor_utils.ApplyParameters(
        extract_config,
        destination_uris=uris,
        destination_format=destination_format,
        print_header=print_header,
        field_delimiter=field_delimiter,
        compression=compression,
        use_avro_logical_types=use_avro_logical_types)
    return self.ExecuteJob(configuration={'extract': extract_config}, **kwds)




class _TableReader:
  """Base class that defines the TableReader interface.

  _TableReaders provide a way to read paginated rows and schemas from a table.
  """

  def ReadRows(self, start_row=0, max_rows=None, selected_fields=None):
    """Read at most max_rows rows from a table.

    Args:
      start_row: first row to return.
      max_rows: maximum number of rows to return.
      selected_fields: a subset of fields to return.

    Raises:
      BigqueryInterfaceError: when bigquery returns something unexpected.

    Returns:
      list of rows, each of which is a list of field values.
    """
    (_, rows) = self.ReadSchemaAndRows(
        start_row=start_row, max_rows=max_rows, selected_fields=selected_fields)
    return rows

  def ReadSchemaAndRows(self, start_row, max_rows, selected_fields=None):
    """Read at most max_rows rows from a table and the schema.

    Args:
      start_row: first row to read.
      max_rows: maximum number of rows to return.
      selected_fields: a subset of fields to return.

    Raises:
      BigqueryInterfaceError: when bigquery returns something unexpected.
      ValueError: when start_row is None.
      ValueError: when max_rows is None.

    Returns:
      A tuple where the first item is the list of fields and the
      second item a list of rows.
    """
    if start_row is None:
      raise ValueError('start_row is required')
    if max_rows is None:
      raise ValueError('max_rows is required')
    page_token = None
    rows = []
    schema = {}
    while len(rows) < max_rows:
      rows_to_read = max_rows - len(rows)
      if self.max_rows_per_request:
        rows_to_read = min(self.max_rows_per_request, rows_to_read)
      (more_rows, page_token, current_schema) = self._ReadOnePage(
          None if page_token else start_row,
          max_rows=rows_to_read,
          page_token=page_token,
          selected_fields=selected_fields)
      if not schema and current_schema:
        schema = current_schema.get('fields', [])
      for row in more_rows:
        rows.append(self._ConvertFromFV(schema, row))
        start_row += 1
      if not page_token or not more_rows:
        break
    return (schema, rows)

  def _ConvertFromFV(self, schema, row):
    """Converts from FV format to possibly nested lists of values."""
    if not row:
      return None
    values = [entry.get('v', '') for entry in row.get('f', [])]
    result = []
    for field, v in zip(schema, values):
      if 'type' not in field:
        raise bq_error.BigqueryCommunicationError(
            'Invalid response: missing type property')
      if field['type'].upper() == 'RECORD':
        # Nested field.
        subfields = field.get('fields', [])
        if field.get('mode', 'NULLABLE').upper() == 'REPEATED':
          # Repeated and nested. Convert the array of v's of FV's.
          result.append([
              self._ConvertFromFV(subfields, subvalue.get('v', ''))
              for subvalue in v
          ])
        else:
          # Nested non-repeated field. Convert the nested f from FV.
          result.append(self._ConvertFromFV(subfields, v))
      elif field.get('mode', 'NULLABLE').upper() == 'REPEATED':
        # Repeated but not nested: an array of v's.
        result.append([subvalue.get('v', '') for subvalue in v])
      else:
        # Normal flat field.
        result.append(v)
    return result

  def __str__(self):
    return self._GetPrintContext()

  def __repr__(self):
    return self._GetPrintContext()

  def _GetPrintContext(self):
    """Returns context for what is being read."""
    raise NotImplementedError('Subclass must implement GetPrintContext')

  def _ReadOnePage(self,
                   start_row,
                   max_rows,
                   page_token=None,
                   selected_fields=None):
    """Read one page of data, up to max_rows rows.

    Assumes that the table is ready for reading. Will signal an error otherwise.

    Args:
      start_row: first row to read.
      max_rows: maximum number of rows to return.
      page_token: Optional. current page token.
      selected_fields: a subset of field to return.

    Returns:
      tuple of:
      rows: the actual rows of the table, in f,v format.
      page_token: the page token of the next page of results.
      schema: the schema of the table.
    """
    raise NotImplementedError('Subclass must implement _ReadOnePage')


class _TableTableReader(_TableReader):
  """A TableReader that reads from a table."""

  def __init__(self, local_apiclient, max_rows_per_request, table_ref):
    self.table_ref = table_ref
    self.max_rows_per_request = max_rows_per_request
    self._apiclient = local_apiclient


  def _GetPrintContext(self):
    return '%r' % (self.table_ref,)

  def _ReadOnePage(self,
                   start_row,
                   max_rows,
                   page_token=None,
                   selected_fields=None):
    kwds = dict(self.table_ref)
    kwds['maxResults'] = max_rows
    if page_token:
      kwds['pageToken'] = page_token
    else:
      kwds['startIndex'] = start_row
    data = None
    if selected_fields is not None:
      kwds['selectedFields'] = selected_fields
    if data is None:
      data = self._apiclient.tabledata().list(**kwds).execute()
    page_token = data.get('pageToken', None)
    rows = data.get('rows', [])

    kwds = dict(self.table_ref)
    if selected_fields is not None:
      kwds['selectedFields'] = selected_fields
    table_info = self._apiclient.tables().get(**kwds).execute()
    schema = table_info.get('schema', {})

    return (rows, page_token, schema)


class _JobTableReader(_TableReader):
  """A TableReader that reads from a completed job."""

  def __init__(self, local_apiclient, max_rows_per_request, job_ref):
    self.job_ref = job_ref
    self.max_rows_per_request = max_rows_per_request
    self._apiclient = local_apiclient

  def _GetPrintContext(self):
    return '%r' % (self.job_ref,)

  def _ReadOnePage(self,
                   start_row,
                   max_rows,
                   page_token=None,
                   selected_fields=None):
    kwds = dict(self.job_ref)
    kwds['maxResults'] = max_rows
    # Sets the timeout to 0 because we assume the table is already ready.
    kwds['timeoutMs'] = 0
    if page_token:
      kwds['pageToken'] = page_token
    else:
      kwds['startIndex'] = start_row
    data = self._apiclient.jobs().getQueryResults(**kwds).execute()
    if not data['jobComplete']:
      raise bq_error.BigqueryError('Job %s is not done' % (self,))
    page_token = data.get('pageToken', None)
    schema = data.get('schema', None)
    rows = data.get('rows', [])
    return (rows, page_token, schema)


class _QueryTableReader(_TableReader):
  """A TableReader that reads from a completed query."""

  def __init__(self, local_apiclient, max_rows_per_request, job_ref, results):
    self.job_ref = job_ref
    self.max_rows_per_request = max_rows_per_request
    self._apiclient = local_apiclient
    self._results = results

  def _GetPrintContext(self):
    return '%r' % (self.job_ref,)

  def _ReadOnePage(self,
                   start_row,
                   max_rows,
                   page_token=None,
                   selected_fields=None):
    kwds = dict(self.job_ref) if self.job_ref else {}
    kwds['maxResults'] = max_rows
    # Sets the timeout to 0 because we assume the table is already ready.
    kwds['timeoutMs'] = 0
    if page_token:
      kwds['pageToken'] = page_token
    else:
      kwds['startIndex'] = start_row
    if not self._results['jobComplete']:
      raise bq_error.BigqueryError('Job %s is not done' % (self,))
    # DDL and DML statements return no rows, just delegate them to
    # getQueryResults.
    result_rows = self._results.get('rows', None)
    total_rows = self._results.get('totalRows', None)
    if (total_rows is not None and result_rows is not None and
        start_row is not None and
        len(result_rows) >= min(int(total_rows), start_row + max_rows)):
      page_token = self._results.get('pageToken', None)
      if (len(result_rows) < int(total_rows) and page_token is None):
        raise bq_error.BigqueryError(
            'Synchronous query %s did not return all rows, yet it did not'
            ' return a page token' % (self,))
      schema = self._results.get('schema', None)
      rows = self._results.get('rows', [])
    else:
      data = self._apiclient.jobs().getQueryResults(**kwds).execute()
      if not data['jobComplete']:
        raise bq_error.BigqueryError('Job %s is not done' % (self,))
      page_token = data.get('pageToken', None)
      schema = data.get('schema', None)
      rows = data.get('rows', [])
    return (rows, page_token, schema)


