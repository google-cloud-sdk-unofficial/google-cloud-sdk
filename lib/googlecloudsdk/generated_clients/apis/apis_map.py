# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Base template using which the apis_map.py is generated."""

import collections.abc


class APIDef(object):
  """Struct for info required to instantiate clients/messages for API versions.

  Attributes:
    apitools: ApitoolsClientDef for this API version.
    gapic: GapicClientDef for this API version.
    default_version: bool, Whether this API version is the default version for
      the API.
    enable_mtls: bool, Whether this API version supports mTLS.
    mtls_endpoint_override: str, The mTLS endpoint for this API version. If
      empty, the MTLS_BASE_URL in the API client will be used.
    regional_endpoints: dict[str, str], The regional endpoints for this API
      version. Dictionary maps location to endpoint URL.
  """

  def __init__(self,
               apitools=None,
               gapic=None,
               default_version=False,
               enable_mtls=True,
               mtls_endpoint_override='',
               regional_endpoints=None):
    self.apitools = apitools
    self.gapic = gapic
    self.default_version = default_version
    self.enable_mtls = enable_mtls
    self.mtls_endpoint_override = mtls_endpoint_override
    self.regional_endpoints = regional_endpoints or {}

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            self.__dict__ == other.__dict__)

  def __ne__(self, other):
    return not self.__eq__(other)

  def get_init_source(self):
    src_fmt = 'APIDef({0}, {1}, {2}, {3}, "{4}")'
    return src_fmt.format(self.apitools, self.gapic,
                          self.default_version,
                          self.enable_mtls, self.mtls_endpoint_override)

  def __repr__(self):
    return self.get_init_source()


class ApitoolsClientDef(object):
  """Struct for info required to instantiate clients/messages for API versions.

  Attributes:
    class_path: str, Path to the package containing api related modules.
    client_classpath: str, Relative path to the client class for an API version.
    client_full_classpath: str, Full path to the client class for an API
      version.
    messages_modulepath: str, Relative path to the messages module for an API
      version.
    messages_full_modulepath: str, Full path to the messages module for an API
      version.
    base_url: str, The base_url used for the default version of the API.
  """

  def __init__(self,
               class_path,
               client_classpath,
               messages_modulepath,
               base_url):
    self.class_path = class_path
    self.client_classpath = client_classpath
    self.messages_modulepath = messages_modulepath
    self.base_url = base_url

  @property
  def client_full_classpath(self):
    return self.class_path + '.' + self.client_classpath

  @property
  def messages_full_modulepath(self):
    return self.class_path + '.' + self.messages_modulepath

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            self.__dict__ == other.__dict__)

  def __ne__(self, other):
    return not self.__eq__(other)

  def get_init_source(self):
    src_fmt = 'ApitoolsClientDef("{0}", "{1}", "{2}", "{3}")'
    return src_fmt.format(self.class_path, self.client_classpath,
                          self.messages_modulepath, self.base_url)

  def __repr__(self):
    return self.get_init_source()


class GapicClientDef(object):
  """Struct for info required to instantiate clients/messages for API versions.

  Attributes:
    class_path: str, Path to the package containing api related modules.
    client_full_classpath: str, Full path to the client class for an API
      version.
    async_client_full_classpath: str, Full path to the async client class for an
      API version.
    rest_client_full_classpath: str, Full path to the rest client class for an
      API version.
  """

  def __init__(self,
               class_path):
    self.class_path = class_path

  @property
  def client_full_classpath(self):
    return self.class_path + '.client.GapicWrapperClient'

  @property
  def async_client_full_classpath(self):
    return self.class_path + '.async_client.GapicWrapperClient'

  @property
  def rest_client_full_classpath(self):
    return self.class_path + '.rest_client.GapicWrapperClient'

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            self.__dict__ == other.__dict__)

  def __ne__(self, other):
    return not self.__eq__(other)

  def get_init_source(self):
    src_fmt = 'GapicClientDef("{0}")'
    return src_fmt.format(self.class_path)

  def __repr__(self):
    return self.get_init_source()


class _ApiVersionMap(collections.abc.MutableMapping):
  """Lazy mapping for API versions."""

  def __init__(self, raw_data):
    self._raw = raw_data
    self._cache = {}

  def __getitem__(self, key):
    if key not in self._cache:
      val = self._raw[key]
      apitools_def = None
      if val[0]:
        apitools_def = ApitoolsClientDef(*val[0])
      gapic_def = None
      if val[1]:
        gapic_def = GapicClientDef(*val[1])
      self._cache[key] = APIDef(
          apitools=apitools_def,
          gapic=gapic_def,
          default_version=val[2],
          enable_mtls=val[3],
          mtls_endpoint_override=val[4],
          regional_endpoints=val[5],
      )
    return self._cache[key]

  def __setitem__(self, key, value):
    self._cache[key] = value
    if key not in self._raw:
      self._raw[key] = None

  def __delitem__(self, key):
    if key in self._cache:
      del self._cache[key]
    if key in self._raw:
      del self._raw[key]

  def __iter__(self):
    return iter(self._raw)

  def __len__(self):
    return len(self._raw)


class _ApiDefMap(collections.abc.MutableMapping):
  """Lazy mapping for API names."""

  def __init__(self, raw_data):
    self._raw = raw_data
    self._cache = {}

  def __getitem__(self, key):
    if key not in self._cache:
      self._cache[key] = _ApiVersionMap(self._raw[key])
    return self._cache[key]

  def __setitem__(self, key, value):
    self._cache[key] = value
    if key not in self._raw:
      self._raw[key] = None

  def __delitem__(self, key):
    if key in self._cache:
      del self._cache[key]
    if key in self._raw:
      del self._raw[key]

  def __iter__(self):
    return iter(self._raw)

  def __len__(self):
    return len(self._raw)


MAP = _ApiDefMap({
    'accessapproval': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.accessapproval.v1', 'accessapproval_v1_client.AccessapprovalV1', 'accessapproval_v1_messages', 'https://accessapproval.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'accesscontextmanager': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.accesscontextmanager.v1', 'accesscontextmanager_v1_client.AccesscontextmanagerV1', 'accesscontextmanager_v1_messages', 'https://accesscontextmanager.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.accesscontextmanager.v1alpha', 'accesscontextmanager_v1alpha_client.AccesscontextmanagerV1alpha', 'accesscontextmanager_v1alpha_messages', 'https://accesscontextmanager.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'admin': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.admin.v1', 'admin_v1_client.AdminDirectoryV1', 'admin_v1_messages', 'https://www.googleapis.com/admin/directory/v1/'),
            None,
            True,
            True,
            'https://www.mtls.googleapis.com/admin/directory/v1/',
            {},
        ),
    },
    'agentregistry': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.agentregistry.v1alpha', 'agentregistry_v1alpha_client.AgentregistryV1alpha', 'agentregistry_v1alpha_messages', 'https://agentregistry.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'aiplatform': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.aiplatform.v1', 'aiplatform_v1_client.AiplatformV1', 'aiplatform_v1_messages', 'https://aiplatform.googleapis.com/'),
            ('googlecloudsdk.generated_clients.gapic_wrappers.aiplatform.v1',),
            False,
            True,
            '',
            {'africa-south1': 'https://africa-south1-aiplatform.googleapis.com/', 'asia-east1': 'https://asia-east1-aiplatform.googleapis.com/', 'asia-east2': 'https://asia-east2-aiplatform.googleapis.com/', 'asia-northeast1': 'https://asia-northeast1-aiplatform.googleapis.com/', 'asia-northeast2': 'https://asia-northeast2-aiplatform.googleapis.com/', 'asia-northeast3': 'https://asia-northeast3-aiplatform.googleapis.com/', 'asia-south1': 'https://asia-south1-aiplatform.googleapis.com/', 'asia-south2': 'https://asia-south2-aiplatform.googleapis.com/', 'asia-southeast1': 'https://asia-southeast1-aiplatform.googleapis.com/', 'asia-southeast2': 'https://asia-southeast2-aiplatform.googleapis.com/', 'australia-southeast1': 'https://australia-southeast1-aiplatform.googleapis.com/', 'australia-southeast2': 'https://australia-southeast2-aiplatform.googleapis.com/', 'europe-central2': 'https://europe-central2-aiplatform.googleapis.com/', 'europe-north1': 'https://europe-north1-aiplatform.googleapis.com/', 'europe-north2': 'https://europe-north2-aiplatform.googleapis.com/', 'europe-southwest1': 'https://europe-southwest1-aiplatform.googleapis.com/', 'europe-west1': 'https://europe-west1-aiplatform.googleapis.com/', 'europe-west10': 'https://europe-west10-aiplatform.googleapis.com/', 'europe-west15': 'https://europe-west15-aiplatform.googleapis.com/', 'europe-west2': 'https://europe-west2-aiplatform.googleapis.com/', 'europe-west3': 'https://europe-west3-aiplatform.googleapis.com/', 'europe-west4': 'https://europe-west4-aiplatform.googleapis.com/', 'europe-west6': 'https://europe-west6-aiplatform.googleapis.com/', 'europe-west8': 'https://europe-west8-aiplatform.googleapis.com/', 'europe-west9': 'https://europe-west9-aiplatform.googleapis.com/', 'europe-west12': 'https://europe-west12-aiplatform.googleapis.com/', 'me-central1': 'https://me-central1-aiplatform.googleapis.com/', 'me-central2': 'https://me-central2-aiplatform.googleapis.com/', 'me-west1': 'https://me-west1-aiplatform.googleapis.com/', 'northamerica-northeast1': 'https://northamerica-northeast1-aiplatform.googleapis.com/', 'northamerica-northeast2': 'https://northamerica-northeast2-aiplatform.googleapis.com/', 'southamerica-east1': 'https://southamerica-east1-aiplatform.googleapis.com/', 'southamerica-west1': 'https://southamerica-west1-aiplatform.googleapis.com/', 'us-central1': 'https://us-central1-aiplatform.googleapis.com/', 'us-central2': 'https://us-central2-aiplatform.googleapis.com/', 'us-east1': 'https://us-east1-aiplatform.googleapis.com/', 'us-east4': 'https://us-east4-aiplatform.googleapis.com/', 'us-east7': 'https://us-east7-aiplatform.googleapis.com/', 'us-south1': 'https://us-south1-aiplatform.googleapis.com/', 'us-west1': 'https://us-west1-aiplatform.googleapis.com/', 'us-west2': 'https://us-west2-aiplatform.googleapis.com/', 'us-west3': 'https://us-west3-aiplatform.googleapis.com/', 'us-west4': 'https://us-west4-aiplatform.googleapis.com/', 'us-east5': 'https://us-east5-aiplatform.googleapis.com/', 'us': 'https://aiplatform.us.rep.googleapis.com/', 'eu': 'https://aiplatform.eu.rep.googleapis.com/'},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.aiplatform.v1beta1', 'aiplatform_v1beta1_client.AiplatformV1beta1', 'aiplatform_v1beta1_messages', 'https://aiplatform.googleapis.com/'),
            ('googlecloudsdk.generated_clients.gapic_wrappers.aiplatform.v1beta1',),
            True,
            True,
            '',
            {'africa-south1': 'https://africa-south1-aiplatform.googleapis.com/', 'asia-east1': 'https://asia-east1-aiplatform.googleapis.com/', 'asia-east2': 'https://asia-east2-aiplatform.googleapis.com/', 'asia-northeast1': 'https://asia-northeast1-aiplatform.googleapis.com/', 'asia-northeast2': 'https://asia-northeast2-aiplatform.googleapis.com/', 'asia-northeast3': 'https://asia-northeast3-aiplatform.googleapis.com/', 'asia-south1': 'https://asia-south1-aiplatform.googleapis.com/', 'asia-south2': 'https://asia-south2-aiplatform.googleapis.com/', 'asia-southeast1': 'https://asia-southeast1-aiplatform.googleapis.com/', 'asia-southeast2': 'https://asia-southeast2-aiplatform.googleapis.com/', 'australia-southeast1': 'https://australia-southeast1-aiplatform.googleapis.com/', 'australia-southeast2': 'https://australia-southeast2-aiplatform.googleapis.com/', 'europe-central2': 'https://europe-central2-aiplatform.googleapis.com/', 'europe-north1': 'https://europe-north1-aiplatform.googleapis.com/', 'europe-north2': 'https://europe-north2-aiplatform.googleapis.com/', 'europe-southwest1': 'https://europe-southwest1-aiplatform.googleapis.com/', 'europe-west1': 'https://europe-west1-aiplatform.googleapis.com/', 'europe-west10': 'https://europe-west10-aiplatform.googleapis.com/', 'europe-west15': 'https://europe-west15-aiplatform.googleapis.com/', 'europe-west2': 'https://europe-west2-aiplatform.googleapis.com/', 'europe-west3': 'https://europe-west3-aiplatform.googleapis.com/', 'europe-west4': 'https://europe-west4-aiplatform.googleapis.com/', 'europe-west6': 'https://europe-west6-aiplatform.googleapis.com/', 'europe-west8': 'https://europe-west8-aiplatform.googleapis.com/', 'europe-west9': 'https://europe-west9-aiplatform.googleapis.com/', 'europe-west12': 'https://europe-west12-aiplatform.googleapis.com/', 'me-central1': 'https://me-central1-aiplatform.googleapis.com/', 'me-central2': 'https://me-central2-aiplatform.googleapis.com/', 'me-west1': 'https://me-west1-aiplatform.googleapis.com/', 'northamerica-northeast1': 'https://northamerica-northeast1-aiplatform.googleapis.com/', 'northamerica-northeast2': 'https://northamerica-northeast2-aiplatform.googleapis.com/', 'southamerica-east1': 'https://southamerica-east1-aiplatform.googleapis.com/', 'southamerica-west1': 'https://southamerica-west1-aiplatform.googleapis.com/', 'us-central1': 'https://us-central1-aiplatform.googleapis.com/', 'us-central2': 'https://us-central2-aiplatform.googleapis.com/', 'us-east1': 'https://us-east1-aiplatform.googleapis.com/', 'us-east4': 'https://us-east4-aiplatform.googleapis.com/', 'us-east7': 'https://us-east7-aiplatform.googleapis.com/', 'us-south1': 'https://us-south1-aiplatform.googleapis.com/', 'us-west1': 'https://us-west1-aiplatform.googleapis.com/', 'us-west2': 'https://us-west2-aiplatform.googleapis.com/', 'us-west3': 'https://us-west3-aiplatform.googleapis.com/', 'us-west4': 'https://us-west4-aiplatform.googleapis.com/', 'us-east5': 'https://us-east5-aiplatform.googleapis.com/', 'us-west8': 'https://us-west8-aiplatform.googleapis.com/', 'us': 'https://aiplatform.us.rep.googleapis.com/', 'eu': 'https://aiplatform.eu.rep.googleapis.com/'},
        ),
    },
    'alloydb': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.alloydb.v1', 'alloydb_v1_client.AlloydbV1', 'alloydb_v1_messages', 'https://alloydb.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us-central2': 'https://alloydb.us-central2.rep.googleapis.com/', 'us-east7': 'https://alloydb.us-east7.rep.googleapis.com/', 'northamerica-northeast1': 'https://alloydb.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://alloydb.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://alloydb.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://alloydb.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://alloydb.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://alloydb.us-central1.rep.googleapis.com/', 'us-east1': 'https://alloydb.us-east1.rep.googleapis.com/', 'us-east4': 'https://alloydb.us-east4.rep.googleapis.com/', 'us-east5': 'https://alloydb.us-east5.rep.googleapis.com/', 'us-south1': 'https://alloydb.us-south1.rep.googleapis.com/', 'us-west1': 'https://alloydb.us-west1.rep.googleapis.com/', 'us-west2': 'https://alloydb.us-west2.rep.googleapis.com/', 'us-west3': 'https://alloydb.us-west3.rep.googleapis.com/', 'us-west4': 'https://alloydb.us-west4.rep.googleapis.com/', 'europe-central2': 'https://alloydb.europe-central2.rep.googleapis.com/', 'europe-southwest1': 'https://alloydb.europe-southwest1.rep.googleapis.com/', 'europe-north1': 'https://alloydb.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://alloydb.europe-north2.rep.googleapis.com/', 'europe-west1': 'https://alloydb.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://alloydb.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://alloydb.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://alloydb.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://alloydb.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://alloydb.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://alloydb.europe-west9.rep.googleapis.com/', 'europe-west10': 'https://alloydb.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://alloydb.europe-west12.rep.googleapis.com/', 'asia-east1': 'https://alloydb.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://alloydb.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://alloydb.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://alloydb.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://alloydb.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://alloydb.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://alloydb.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://alloydb.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://alloydb.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://alloydb.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://alloydb.australia-southeast2.rep.googleapis.com/', 'me-central1': 'https://alloydb.me-central1.rep.googleapis.com/', 'me-central2': 'https://alloydb.me-central2.rep.googleapis.com/', 'me-west1': 'https://alloydb.me-west1.rep.googleapis.com/', 'africa-south1': 'https://alloydb.africa-south1.rep.googleapis.com/'},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.alloydb.v1alpha', 'alloydb_v1alpha_client.AlloydbV1alpha', 'alloydb_v1alpha_messages', 'https://alloydb.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-central2': 'https://alloydb.us-central2.rep.googleapis.com/', 'us-east7': 'https://alloydb.us-east7.rep.googleapis.com/', 'northamerica-northeast1': 'https://alloydb.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://alloydb.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://alloydb.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://alloydb.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://alloydb.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://alloydb.us-central1.rep.googleapis.com/', 'us-east1': 'https://alloydb.us-east1.rep.googleapis.com/', 'us-east4': 'https://alloydb.us-east4.rep.googleapis.com/', 'us-east5': 'https://alloydb.us-east5.rep.googleapis.com/', 'us-south1': 'https://alloydb.us-south1.rep.googleapis.com/', 'us-west1': 'https://alloydb.us-west1.rep.googleapis.com/', 'us-west2': 'https://alloydb.us-west2.rep.googleapis.com/', 'us-west3': 'https://alloydb.us-west3.rep.googleapis.com/', 'us-west4': 'https://alloydb.us-west4.rep.googleapis.com/', 'europe-central2': 'https://alloydb.europe-central2.rep.googleapis.com/', 'europe-southwest1': 'https://alloydb.europe-southwest1.rep.googleapis.com/', 'europe-north1': 'https://alloydb.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://alloydb.europe-north2.rep.googleapis.com/', 'europe-west1': 'https://alloydb.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://alloydb.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://alloydb.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://alloydb.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://alloydb.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://alloydb.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://alloydb.europe-west9.rep.googleapis.com/', 'europe-west10': 'https://alloydb.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://alloydb.europe-west12.rep.googleapis.com/', 'asia-east1': 'https://alloydb.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://alloydb.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://alloydb.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://alloydb.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://alloydb.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://alloydb.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://alloydb.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://alloydb.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://alloydb.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://alloydb.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://alloydb.australia-southeast2.rep.googleapis.com/', 'me-central1': 'https://alloydb.me-central1.rep.googleapis.com/', 'me-central2': 'https://alloydb.me-central2.rep.googleapis.com/', 'me-west1': 'https://alloydb.me-west1.rep.googleapis.com/', 'africa-south1': 'https://alloydb.africa-south1.rep.googleapis.com/'},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.alloydb.v1beta', 'alloydb_v1beta_client.AlloydbV1beta', 'alloydb_v1beta_messages', 'https://alloydb.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-central2': 'https://alloydb.us-central2.rep.googleapis.com/', 'us-east7': 'https://alloydb.us-east7.rep.googleapis.com/', 'northamerica-northeast1': 'https://alloydb.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://alloydb.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://alloydb.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://alloydb.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://alloydb.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://alloydb.us-central1.rep.googleapis.com/', 'us-east1': 'https://alloydb.us-east1.rep.googleapis.com/', 'us-east4': 'https://alloydb.us-east4.rep.googleapis.com/', 'us-east5': 'https://alloydb.us-east5.rep.googleapis.com/', 'us-south1': 'https://alloydb.us-south1.rep.googleapis.com/', 'us-west1': 'https://alloydb.us-west1.rep.googleapis.com/', 'us-west2': 'https://alloydb.us-west2.rep.googleapis.com/', 'us-west3': 'https://alloydb.us-west3.rep.googleapis.com/', 'us-west4': 'https://alloydb.us-west4.rep.googleapis.com/', 'europe-central2': 'https://alloydb.europe-central2.rep.googleapis.com/', 'europe-southwest1': 'https://alloydb.europe-southwest1.rep.googleapis.com/', 'europe-north1': 'https://alloydb.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://alloydb.europe-north2.rep.googleapis.com/', 'europe-west1': 'https://alloydb.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://alloydb.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://alloydb.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://alloydb.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://alloydb.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://alloydb.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://alloydb.europe-west9.rep.googleapis.com/', 'europe-west10': 'https://alloydb.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://alloydb.europe-west12.rep.googleapis.com/', 'asia-east1': 'https://alloydb.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://alloydb.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://alloydb.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://alloydb.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://alloydb.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://alloydb.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://alloydb.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://alloydb.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://alloydb.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://alloydb.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://alloydb.australia-southeast2.rep.googleapis.com/', 'me-central1': 'https://alloydb.me-central1.rep.googleapis.com/', 'me-central2': 'https://alloydb.me-central2.rep.googleapis.com/', 'me-west1': 'https://alloydb.me-west1.rep.googleapis.com/', 'africa-south1': 'https://alloydb.africa-south1.rep.googleapis.com/'},
        ),
    },
    'anthosevents': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.anthosevents.v1', 'anthosevents_v1_client.AnthoseventsV1', 'anthosevents_v1_messages', 'https://anthosevents.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.anthosevents.v1alpha1', 'anthosevents_v1alpha1_client.AnthoseventsV1alpha1', 'anthosevents_v1alpha1_messages', 'https://anthosevents.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.anthosevents.v1beta1', 'anthosevents_v1beta1_client.AnthoseventsV1beta1', 'anthosevents_v1beta1_messages', 'https://anthosevents.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'anthospolicycontrollerstatus_pa': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.anthospolicycontrollerstatus_pa.v1alpha', 'anthospolicycontrollerstatus_pa_v1alpha_client.AnthospolicycontrollerstatusPaV1alpha', 'anthospolicycontrollerstatus_pa_v1alpha_messages', 'https://anthospolicycontrollerstatus-pa.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'apigateway': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.apigateway.v1', 'apigateway_v1_client.ApigatewayV1', 'apigateway_v1_messages', 'https://apigateway.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.apigateway.v1alpha1', 'apigateway_v1alpha1_client.ApigatewayV1alpha1', 'apigateway_v1alpha1_messages', 'https://apigateway.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.apigateway.v1beta', 'apigateway_v1beta_client.ApigatewayV1beta', 'apigateway_v1beta_messages', 'https://apigateway.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'apigee': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.apigee.v1', 'apigee_v1_client.ApigeeV1', 'apigee_v1_messages', 'https://apigee.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us': 'https://apigee.us.rep.googleapis.com/', 'eu': 'https://apigee.eu.rep.googleapis.com/', 'in': 'https://apigee.in.rep.googleapis.com/', 'sa': 'https://apigee.sa.rep.googleapis.com/'},
        ),
        'v2alpha': (
            ('googlecloudsdk.generated_clients.apis.apigee.v2alpha', 'apigee_v2alpha_client.ApigeeV2alpha', 'apigee_v2alpha_messages', 'https://apigee.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'apihub': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.apihub.v1', 'apihub_v1_client.ApihubV1', 'apihub_v1_messages', 'https://apihub.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'asia-east1': 'https://apihub.asia-east1.rep.googleapis.com/', 'asia-south1': 'https://apihub.asia-south1.rep.googleapis.com/', 'asia-southeast1': 'https://apihub.asia-southeast1.rep.googleapis.com/', 'europe-north1': 'https://apihub.europe-north1.rep.googleapis.com/', 'europe-west1': 'https://apihub.europe-west1.rep.googleapis.com/', 'europe-west9': 'https://apihub.europe-west9.rep.googleapis.com/', 'us-central1': 'https://apihub.us-central1.rep.googleapis.com/', 'us-east1': 'https://apihub.us-east1.rep.googleapis.com/', 'us-west1': 'https://apihub.us-west1.rep.googleapis.com/'},
        ),
    },
    'apikeys': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.apikeys.v2', 'apikeys_v2_client.ApikeysV2', 'apikeys_v2_messages', 'https://apikeys.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'appengine': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.appengine.v1', 'appengine_v1_client.AppengineV1', 'appengine_v1_messages', 'https://appengine.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.appengine.v1alpha', 'appengine_v1alpha_client.AppengineV1alpha', 'appengine_v1alpha_messages', 'https://appengine.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.appengine.v1beta', 'appengine_v1beta_client.AppengineV1beta', 'appengine_v1beta_messages', 'https://appengine.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'apphub': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.apphub.v1', 'apphub_v1_client.ApphubV1', 'apphub_v1_messages', 'https://apphub.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.apphub.v1alpha', 'apphub_v1alpha_client.ApphubV1alpha', 'apphub_v1alpha_messages', 'https://apphub.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'appoptimize': {
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.appoptimize.v1beta', 'appoptimize_v1beta_client.AppoptimizeV1beta', 'appoptimize_v1beta_messages', 'https://appoptimize.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'artifactregistry': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.artifactregistry.v1', 'artifactregistry_v1_client.ArtifactregistryV1', 'artifactregistry_v1_messages', 'https://artifactregistry.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://artifactregistry.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://artifactregistry.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://artifactregistry.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://artifactregistry.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://artifactregistry.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://artifactregistry.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://artifactregistry.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://artifactregistry.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://artifactregistry.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://artifactregistry.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://artifactregistry.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://artifactregistry.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://artifactregistry.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://artifactregistry.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://artifactregistry.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://artifactregistry.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://artifactregistry.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://artifactregistry.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://artifactregistry.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://artifactregistry.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://artifactregistry.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://artifactregistry.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://artifactregistry.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://artifactregistry.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://artifactregistry.europe-west9.rep.googleapis.com/', 'me-central1': 'https://artifactregistry.me-central1.rep.googleapis.com/', 'me-west1': 'https://artifactregistry.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://artifactregistry.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://artifactregistry.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://artifactregistry.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://artifactregistry.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://artifactregistry.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://artifactregistry.us-central1.rep.googleapis.com/', 'us-central2': 'https://artifactregistry.us-central2.rep.googleapis.com/', 'us-east1': 'https://artifactregistry.us-east1.rep.googleapis.com/', 'us-east4': 'https://artifactregistry.us-east4.rep.googleapis.com/', 'us-east5': 'https://artifactregistry.us-east5.rep.googleapis.com/', 'us-south1': 'https://artifactregistry.us-south1.rep.googleapis.com/', 'us-west1': 'https://artifactregistry.us-west1.rep.googleapis.com/', 'us-west2': 'https://artifactregistry.us-west2.rep.googleapis.com/', 'us-west3': 'https://artifactregistry.us-west3.rep.googleapis.com/', 'us-west4': 'https://artifactregistry.us-west4.rep.googleapis.com/', 'us-west8': 'https://artifactregistry.us-west8.rep.googleapis.com/', 'me-central2': 'https://artifactregistry.me-central2.rep.googleapis.com/', 'us-east7': 'https://artifactregistry.us-east7.rep.googleapis.com/', 'us': 'https://artifactregistry.us.rep.googleapis.com/', 'eu': 'https://artifactregistry.eu.rep.googleapis.com/'},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.artifactregistry.v1beta1', 'artifactregistry_v1beta1_client.ArtifactregistryV1beta1', 'artifactregistry_v1beta1_messages', 'https://artifactregistry.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://artifactregistry.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://artifactregistry.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://artifactregistry.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://artifactregistry.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://artifactregistry.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://artifactregistry.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://artifactregistry.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://artifactregistry.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://artifactregistry.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://artifactregistry.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://artifactregistry.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://artifactregistry.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://artifactregistry.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://artifactregistry.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://artifactregistry.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://artifactregistry.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://artifactregistry.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://artifactregistry.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://artifactregistry.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://artifactregistry.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://artifactregistry.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://artifactregistry.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://artifactregistry.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://artifactregistry.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://artifactregistry.europe-west9.rep.googleapis.com/', 'me-central1': 'https://artifactregistry.me-central1.rep.googleapis.com/', 'me-west1': 'https://artifactregistry.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://artifactregistry.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://artifactregistry.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://artifactregistry.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://artifactregistry.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://artifactregistry.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://artifactregistry.us-central1.rep.googleapis.com/', 'us-central2': 'https://artifactregistry.us-central2.rep.googleapis.com/', 'us-east1': 'https://artifactregistry.us-east1.rep.googleapis.com/', 'us-east4': 'https://artifactregistry.us-east4.rep.googleapis.com/', 'us-east5': 'https://artifactregistry.us-east5.rep.googleapis.com/', 'us-south1': 'https://artifactregistry.us-south1.rep.googleapis.com/', 'us-west1': 'https://artifactregistry.us-west1.rep.googleapis.com/', 'us-west2': 'https://artifactregistry.us-west2.rep.googleapis.com/', 'us-west3': 'https://artifactregistry.us-west3.rep.googleapis.com/', 'us-west4': 'https://artifactregistry.us-west4.rep.googleapis.com/', 'us-west8': 'https://artifactregistry.us-west8.rep.googleapis.com/', 'me-central2': 'https://artifactregistry.me-central2.rep.googleapis.com/', 'us-east7': 'https://artifactregistry.us-east7.rep.googleapis.com/', 'us': 'https://artifactregistry.us.rep.googleapis.com/', 'eu': 'https://artifactregistry.eu.rep.googleapis.com/'},
        ),
        'v1beta2': (
            ('googlecloudsdk.generated_clients.apis.artifactregistry.v1beta2', 'artifactregistry_v1beta2_client.ArtifactregistryV1beta2', 'artifactregistry_v1beta2_messages', 'https://artifactregistry.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://artifactregistry.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://artifactregistry.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://artifactregistry.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://artifactregistry.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://artifactregistry.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://artifactregistry.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://artifactregistry.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://artifactregistry.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://artifactregistry.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://artifactregistry.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://artifactregistry.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://artifactregistry.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://artifactregistry.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://artifactregistry.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://artifactregistry.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://artifactregistry.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://artifactregistry.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://artifactregistry.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://artifactregistry.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://artifactregistry.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://artifactregistry.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://artifactregistry.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://artifactregistry.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://artifactregistry.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://artifactregistry.europe-west9.rep.googleapis.com/', 'me-central1': 'https://artifactregistry.me-central1.rep.googleapis.com/', 'me-west1': 'https://artifactregistry.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://artifactregistry.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://artifactregistry.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://artifactregistry.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://artifactregistry.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://artifactregistry.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://artifactregistry.us-central1.rep.googleapis.com/', 'us-central2': 'https://artifactregistry.us-central2.rep.googleapis.com/', 'us-east1': 'https://artifactregistry.us-east1.rep.googleapis.com/', 'us-east4': 'https://artifactregistry.us-east4.rep.googleapis.com/', 'us-east5': 'https://artifactregistry.us-east5.rep.googleapis.com/', 'us-south1': 'https://artifactregistry.us-south1.rep.googleapis.com/', 'us-west1': 'https://artifactregistry.us-west1.rep.googleapis.com/', 'us-west2': 'https://artifactregistry.us-west2.rep.googleapis.com/', 'us-west3': 'https://artifactregistry.us-west3.rep.googleapis.com/', 'us-west4': 'https://artifactregistry.us-west4.rep.googleapis.com/', 'us-west8': 'https://artifactregistry.us-west8.rep.googleapis.com/', 'me-central2': 'https://artifactregistry.me-central2.rep.googleapis.com/', 'us-east7': 'https://artifactregistry.us-east7.rep.googleapis.com/', 'us': 'https://artifactregistry.us.rep.googleapis.com/', 'eu': 'https://artifactregistry.eu.rep.googleapis.com/'},
        ),
    },
    'artifactscanguard': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.artifactscanguard.v1alpha', 'artifactscanguard_v1alpha_client.ArtifactscanguardV1alpha', 'artifactscanguard_v1alpha_messages', 'https://artifactscanguard.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'assuredworkloads': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.assuredworkloads.v1', 'assuredworkloads_v1_client.AssuredworkloadsV1', 'assuredworkloads_v1_messages', 'https://assuredworkloads.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.assuredworkloads.v1beta1', 'assuredworkloads_v1beta1_client.AssuredworkloadsV1beta1', 'assuredworkloads_v1beta1_messages', 'https://assuredworkloads.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'auditmanager': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.auditmanager.v1', 'auditmanager_v1_client.AuditmanagerV1', 'auditmanager_v1_messages', 'https://auditmanager.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.auditmanager.v1alpha', 'auditmanager_v1alpha_client.AuditmanagerV1alpha', 'auditmanager_v1alpha_messages', 'https://auditmanager.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'authztoolkit': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.authztoolkit.v1', 'authztoolkit_v1_client.AuthztoolkitV1', 'authztoolkit_v1_messages', 'https://authztoolkit.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.authztoolkit.v1alpha', 'authztoolkit_v1alpha_client.AuthztoolkitV1alpha', 'authztoolkit_v1alpha_messages', 'https://authztoolkit.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'backupdr': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.backupdr.v1', 'backupdr_v1_client.BackupdrV1', 'backupdr_v1_messages', 'https://backupdr.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://backupdr.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://backupdr.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://backupdr.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://backupdr.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://backupdr.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://backupdr.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://backupdr.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://backupdr.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://backupdr.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://backupdr.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://backupdr.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://backupdr.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://backupdr.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://backupdr.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://backupdr.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://backupdr.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://backupdr.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://backupdr.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://backupdr.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://backupdr.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://backupdr.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://backupdr.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://backupdr.europe-west9.rep.googleapis.com/', 'europe-west10': 'https://backupdr.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://backupdr.europe-west12.rep.googleapis.com/', 'me-central1': 'https://backupdr.me-central1.rep.googleapis.com/', 'me-central2': 'https://backupdr.me-central2.rep.googleapis.com/', 'me-west1': 'https://backupdr.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://backupdr.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://backupdr.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://backupdr.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://backupdr.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://backupdr.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://backupdr.us-central1.rep.googleapis.com/', 'us-central2': 'https://backupdr.us-central2.rep.googleapis.com/', 'us-east1': 'https://backupdr.us-east1.rep.googleapis.com/', 'us-east4': 'https://backupdr.us-east4.rep.googleapis.com/', 'us-east5': 'https://backupdr.us-east5.rep.googleapis.com/', 'us-east7': 'https://backupdr.us-east7.rep.googleapis.com/', 'us-south1': 'https://backupdr.us-south1.rep.googleapis.com/', 'us-west1': 'https://backupdr.us-west1.rep.googleapis.com/', 'us-west2': 'https://backupdr.us-west2.rep.googleapis.com/', 'us-west3': 'https://backupdr.us-west3.rep.googleapis.com/', 'us-west4': 'https://backupdr.us-west4.rep.googleapis.com/', 'us-west8': 'https://backupdr.us-west8.rep.googleapis.com/', 'us': 'https://backupdr.us.rep.googleapis.com/', 'eu': 'https://backupdr.eu.rep.googleapis.com/'},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.backupdr.v1alpha', 'backupdr_v1alpha_client.BackupdrV1alpha', 'backupdr_v1alpha_messages', 'https://backupdr.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://backupdr.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://backupdr.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://backupdr.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://backupdr.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://backupdr.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://backupdr.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://backupdr.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://backupdr.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://backupdr.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://backupdr.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://backupdr.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://backupdr.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://backupdr.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://backupdr.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://backupdr.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://backupdr.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://backupdr.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://backupdr.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://backupdr.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://backupdr.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://backupdr.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://backupdr.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://backupdr.europe-west9.rep.googleapis.com/', 'europe-west10': 'https://backupdr.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://backupdr.europe-west12.rep.googleapis.com/', 'me-central1': 'https://backupdr.me-central1.rep.googleapis.com/', 'me-central2': 'https://backupdr.me-central2.rep.googleapis.com/', 'me-west1': 'https://backupdr.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://backupdr.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://backupdr.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://backupdr.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://backupdr.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://backupdr.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://backupdr.us-central1.rep.googleapis.com/', 'us-central2': 'https://backupdr.us-central2.rep.googleapis.com/', 'us-east1': 'https://backupdr.us-east1.rep.googleapis.com/', 'us-east4': 'https://backupdr.us-east4.rep.googleapis.com/', 'us-east5': 'https://backupdr.us-east5.rep.googleapis.com/', 'us-east7': 'https://backupdr.us-east7.rep.googleapis.com/', 'us-south1': 'https://backupdr.us-south1.rep.googleapis.com/', 'us-west1': 'https://backupdr.us-west1.rep.googleapis.com/', 'us-west2': 'https://backupdr.us-west2.rep.googleapis.com/', 'us-west3': 'https://backupdr.us-west3.rep.googleapis.com/', 'us-west4': 'https://backupdr.us-west4.rep.googleapis.com/', 'us-west8': 'https://backupdr.us-west8.rep.googleapis.com/', 'us': 'https://backupdr.us.rep.googleapis.com/', 'eu': 'https://backupdr.eu.rep.googleapis.com/'},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.backupdr.v1beta', 'backupdr_v1beta_client.BackupdrV1beta', 'backupdr_v1beta_messages', 'https://backupdr.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://backupdr.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://backupdr.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://backupdr.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://backupdr.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://backupdr.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://backupdr.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://backupdr.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://backupdr.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://backupdr.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://backupdr.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://backupdr.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://backupdr.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://backupdr.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://backupdr.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://backupdr.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://backupdr.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://backupdr.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://backupdr.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://backupdr.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://backupdr.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://backupdr.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://backupdr.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://backupdr.europe-west9.rep.googleapis.com/', 'europe-west10': 'https://backupdr.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://backupdr.europe-west12.rep.googleapis.com/', 'me-central1': 'https://backupdr.me-central1.rep.googleapis.com/', 'me-central2': 'https://backupdr.me-central2.rep.googleapis.com/', 'me-west1': 'https://backupdr.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://backupdr.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://backupdr.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://backupdr.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://backupdr.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://backupdr.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://backupdr.us-central1.rep.googleapis.com/', 'us-central2': 'https://backupdr.us-central2.rep.googleapis.com/', 'us-east1': 'https://backupdr.us-east1.rep.googleapis.com/', 'us-east4': 'https://backupdr.us-east4.rep.googleapis.com/', 'us-east5': 'https://backupdr.us-east5.rep.googleapis.com/', 'us-east7': 'https://backupdr.us-east7.rep.googleapis.com/', 'us-south1': 'https://backupdr.us-south1.rep.googleapis.com/', 'us-west1': 'https://backupdr.us-west1.rep.googleapis.com/', 'us-west2': 'https://backupdr.us-west2.rep.googleapis.com/', 'us-west3': 'https://backupdr.us-west3.rep.googleapis.com/', 'us-west4': 'https://backupdr.us-west4.rep.googleapis.com/', 'us-west8': 'https://backupdr.us-west8.rep.googleapis.com/', 'us': 'https://backupdr.us.rep.googleapis.com/', 'eu': 'https://backupdr.eu.rep.googleapis.com/'},
        ),
    },
    'baremetalsolution': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.baremetalsolution.v1', 'baremetalsolution_v1_client.BaremetalsolutionV1', 'baremetalsolution_v1_messages', 'https://baremetalsolution.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.baremetalsolution.v2', 'baremetalsolution_v2_client.BaremetalsolutionV2', 'baremetalsolution_v2_messages', 'https://baremetalsolution.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'batch': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.batch.v1', 'batch_v1_client.BatchV1', 'batch_v1_messages', 'https://batch.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.batch.v1alpha', 'batch_v1alpha_client.BatchV1alpha', 'batch_v1alpha_messages', 'https://batch.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.batch.v1alpha1', 'batch_v1alpha1_client.BatchV1alpha1', 'batch_v1alpha1_messages', 'https://batch.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'beyondcorp': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.beyondcorp.v1', 'beyondcorp_v1_client.BeyondcorpV1', 'beyondcorp_v1_messages', 'https://beyondcorp.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.beyondcorp.v1alpha', 'beyondcorp_v1alpha_client.BeyondcorpV1alpha', 'beyondcorp_v1alpha_messages', 'https://beyondcorp.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'biglake': {
        'data_product_sharing_v1alpha': (
            ('googlecloudsdk.generated_clients.apis.biglake.data_product_sharing_v1alpha', 'biglake_data_product_sharing_v1alpha_client.BiglakeDataProductSharingV1alpha', 'biglake_data_product_sharing_v1alpha_messages', 'https://biglake.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'delta_v1': (
            ('googlecloudsdk.generated_clients.apis.biglake.delta_v1', 'biglake_delta_v1_client.BiglakeDeltaV1', 'biglake_delta_v1_messages', 'https://biglake.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'delta_v1alpha': (
            ('googlecloudsdk.generated_clients.apis.biglake.delta_v1alpha', 'biglake_delta_v1alpha_client.BiglakeDeltaV1alpha', 'biglake_delta_v1alpha_messages', 'https://biglake.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1': (
            ('googlecloudsdk.generated_clients.apis.biglake.v1', 'biglake_v1_client.BiglakeV1', 'biglake_v1_messages', 'https://biglake.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.biglake.v1beta', 'biglake_v1beta_client.BiglakeV1beta', 'biglake_v1beta_messages', 'https://biglake.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'bigquery': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.bigquery.v2', 'bigquery_v2_client.BigqueryV2', 'bigquery_v2_messages', 'https://bigquery.googleapis.com/bigquery/v2/'),
            None,
            True,
            True,
            'https://bigquery.mtls.googleapis.com/bigquery/v2/',
            {'asia-south1': 'https://bigquery.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://bigquery.asia-south2.rep.googleapis.com/', 'europe-west1': 'https://bigquery.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://bigquery.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://bigquery.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://bigquery.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://bigquery.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://bigquery.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://bigquery.europe-west9.rep.googleapis.com/', 'me-central2': 'https://bigquery.me-central2.rep.googleapis.com/', 'northamerica-northeast1': 'https://bigquery.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://bigquery.northamerica-northeast2.rep.googleapis.com/', 'us-central1': 'https://bigquery.us-central1.rep.googleapis.com/', 'us-central2': 'https://bigquery.us-central2.rep.googleapis.com/', 'us-east1': 'https://bigquery.us-east1.rep.googleapis.com/', 'us-east4': 'https://bigquery.us-east4.rep.googleapis.com/', 'us-east5': 'https://bigquery.us-east5.rep.googleapis.com/', 'us-east7': 'https://bigquery.us-east7.rep.googleapis.com/', 'us-south1': 'https://bigquery.us-south1.rep.googleapis.com/', 'us-west1': 'https://bigquery.us-west1.rep.googleapis.com/', 'us-west2': 'https://bigquery.us-west2.rep.googleapis.com/', 'us-west3': 'https://bigquery.us-west3.rep.googleapis.com/', 'us-west4': 'https://bigquery.us-west4.rep.googleapis.com/', 'us-west8': 'https://bigquery.us-west8.rep.googleapis.com/'},
        ),
    },
    'bigquerydatatransfer': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.bigquerydatatransfer.v1', 'bigquerydatatransfer_v1_client.BigquerydatatransferV1', 'bigquerydatatransfer_v1_messages', 'https://bigquerydatatransfer.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'asia-south1': 'https://bigquerydatatransfer.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://bigquerydatatransfer.asia-south2.rep.googleapis.com/', 'europe-west1': 'https://bigquerydatatransfer.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://bigquerydatatransfer.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://bigquerydatatransfer.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://bigquerydatatransfer.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://bigquerydatatransfer.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://bigquerydatatransfer.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://bigquerydatatransfer.europe-west9.rep.googleapis.com/', 'me-central2': 'https://bigquerydatatransfer.me-central2.rep.googleapis.com/', 'northamerica-northeast1': 'https://bigquerydatatransfer.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://bigquerydatatransfer.northamerica-northeast2.rep.googleapis.com/', 'us-central1': 'https://bigquerydatatransfer.us-central1.rep.googleapis.com/', 'us-central2': 'https://bigquerydatatransfer.us-central2.rep.googleapis.com/', 'us-east1': 'https://bigquerydatatransfer.us-east1.rep.googleapis.com/', 'us-east4': 'https://bigquerydatatransfer.us-east4.rep.googleapis.com/', 'us-east5': 'https://bigquerydatatransfer.us-east5.rep.googleapis.com/', 'us-east7': 'https://bigquerydatatransfer.us-east7.rep.googleapis.com/', 'us-south1': 'https://bigquerydatatransfer.us-south1.rep.googleapis.com/', 'us-west1': 'https://bigquerydatatransfer.us-west1.rep.googleapis.com/', 'us-west2': 'https://bigquerydatatransfer.us-west2.rep.googleapis.com/', 'us-west3': 'https://bigquerydatatransfer.us-west3.rep.googleapis.com/', 'us-west4': 'https://bigquerydatatransfer.us-west4.rep.googleapis.com/', 'us-west8': 'https://bigquerydatatransfer.us-west8.rep.googleapis.com/'},
        ),
    },
    'bigquerymigration': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.bigquerymigration.v2', 'bigquerymigration_v2_client.BigquerymigrationV2', 'bigquerymigration_v2_messages', 'https://bigquerymigration.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'asia-northeast1': 'https://bigquerymigration.asia-northeast1.rep.googleapis.com/', 'asia-south1': 'https://bigquerymigration.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://bigquerymigration.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://bigquerymigration.asia-southeast1.rep.googleapis.com/', 'australia-southeast1': 'https://bigquerymigration.australia-southeast1.rep.googleapis.com/', 'europe-west1': 'https://bigquerymigration.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://bigquerymigration.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://bigquerymigration.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://bigquerymigration.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://bigquerymigration.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://bigquerymigration.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://bigquerymigration.europe-west9.rep.googleapis.com/', 'me-central2': 'https://bigquerymigration.me-central2.rep.googleapis.com/', 'northamerica-northeast1': 'https://bigquerymigration.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://bigquerymigration.northamerica-northeast2.rep.googleapis.com/', 'southamerica-east1': 'https://bigquerymigration.southamerica-east1.rep.googleapis.com/', 'us-central1': 'https://bigquerymigration.us-central1.rep.googleapis.com/', 'us-central2': 'https://bigquerymigration.us-central2.rep.googleapis.com/', 'us-east1': 'https://bigquerymigration.us-east1.rep.googleapis.com/', 'us-east4': 'https://bigquerymigration.us-east4.rep.googleapis.com/', 'us-east5': 'https://bigquerymigration.us-east5.rep.googleapis.com/', 'us-east7': 'https://bigquerymigration.us-east7.rep.googleapis.com/', 'us-south1': 'https://bigquerymigration.us-south1.rep.googleapis.com/', 'us-west1': 'https://bigquerymigration.us-west1.rep.googleapis.com/', 'us-west2': 'https://bigquerymigration.us-west2.rep.googleapis.com/', 'us-west3': 'https://bigquerymigration.us-west3.rep.googleapis.com/', 'us-west4': 'https://bigquerymigration.us-west4.rep.googleapis.com/', 'us-west8': 'https://bigquerymigration.us-west8.rep.googleapis.com/'},
        ),
    },
    'bigtableadmin': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.bigtableadmin.v2', 'bigtableadmin_v2_client.BigtableadminV2', 'bigtableadmin_v2_messages', 'https://bigtableadmin.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'billingbudgets': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.billingbudgets.v1', 'billingbudgets_v1_client.BillingbudgetsV1', 'billingbudgets_v1_messages', 'https://billingbudgets.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.billingbudgets.v1beta1', 'billingbudgets_v1beta1_client.BillingbudgetsV1beta1', 'billingbudgets_v1beta1_messages', 'https://billingbudgets.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'binaryauthorization': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.binaryauthorization.v1', 'binaryauthorization_v1_client.BinaryauthorizationV1', 'binaryauthorization_v1_messages', 'https://binaryauthorization.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.binaryauthorization.v1alpha2', 'binaryauthorization_v1alpha2_client.BinaryauthorizationV1alpha2', 'binaryauthorization_v1alpha2_messages', 'https://binaryauthorization.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.binaryauthorization.v1beta1', 'binaryauthorization_v1beta1_client.BinaryauthorizationV1beta1', 'binaryauthorization_v1beta1_messages', 'https://binaryauthorization.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'blockchainnodeengine': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.blockchainnodeengine.v1', 'blockchainnodeengine_v1_client.BlockchainnodeengineV1', 'blockchainnodeengine_v1_messages', 'https://blockchainnodeengine.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'blockchainvalidatormanager': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.blockchainvalidatormanager.v1', 'blockchainvalidatormanager_v1_client.BlockchainvalidatormanagerV1', 'blockchainvalidatormanager_v1_messages', 'https://blockchainvalidatormanager.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.blockchainvalidatormanager.v1alpha', 'blockchainvalidatormanager_v1alpha_client.BlockchainvalidatormanagerV1alpha', 'blockchainvalidatormanager_v1alpha_messages', 'https://blockchainvalidatormanager.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'certificatemanager': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.certificatemanager.v1', 'certificatemanager_v1_client.CertificatemanagerV1', 'certificatemanager_v1_messages', 'https://certificatemanager.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'cloudaicompanion': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudaicompanion.v1', 'cloudaicompanion_v1_client.CloudaicompanionV1', 'cloudaicompanion_v1_messages', 'https://cloudaicompanion.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.cloudaicompanion.v1alpha', 'cloudaicompanion_v1alpha_client.CloudaicompanionV1alpha', 'cloudaicompanion_v1alpha_messages', 'https://cloudaicompanion.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'cloudapiregistry': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudapiregistry.v1', 'cloudapiregistry_v1_client.CloudapiregistryV1', 'cloudapiregistry_v1_messages', 'https://cloudapiregistry.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.cloudapiregistry.v1alpha', 'cloudapiregistry_v1alpha_client.CloudapiregistryV1alpha', 'cloudapiregistry_v1alpha_messages', 'https://cloudapiregistry.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.cloudapiregistry.v1beta', 'cloudapiregistry_v1beta_client.CloudapiregistryV1beta', 'cloudapiregistry_v1beta_messages', 'https://cloudapiregistry.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'cloudasset': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudasset.v1', 'cloudasset_v1_client.CloudassetV1', 'cloudasset_v1_messages', 'https://cloudasset.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1p1beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudasset.v1p1beta1', 'cloudasset_v1p1beta1_client.CloudassetV1p1beta1', 'cloudasset_v1p1beta1_messages', 'https://cloudasset.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1p2beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudasset.v1p2beta1', 'cloudasset_v1p2beta1_client.CloudassetV1p2beta1', 'cloudasset_v1p2beta1_messages', 'https://cloudasset.googleapis.com/'),
            None,
            False,
            True,
            'https://cloudasset.mtls.googleapis.com/',
            {},
        ),
        'v1p4alpha1': (
            ('googlecloudsdk.generated_clients.apis.cloudasset.v1p4alpha1', 'cloudasset_v1p4alpha1_client.CloudassetV1p4alpha1', 'cloudasset_v1p4alpha1_messages', 'https://cloudasset.googleapis.com/'),
            None,
            False,
            True,
            'https://cloudasset.mtls.googleapis.com/',
            {},
        ),
        'v1p5beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudasset.v1p5beta1', 'cloudasset_v1p5beta1_client.CloudassetV1p5beta1', 'cloudasset_v1p5beta1_messages', 'https://cloudasset.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1p7beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudasset.v1p7beta1', 'cloudasset_v1p7beta1_client.CloudassetV1p7beta1', 'cloudasset_v1p7beta1_messages', 'https://cloudasset.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'cloudbilling': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudbilling.v1', 'cloudbilling_v1_client.CloudbillingV1', 'cloudbilling_v1_messages', 'https://cloudbilling.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'cloudbuild': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudbuild.v1', 'cloudbuild_v1_client.CloudbuildV1', 'cloudbuild_v1_messages', 'https://cloudbuild.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://cloudbuild.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://cloudbuild.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://cloudbuild.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://cloudbuild.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://cloudbuild.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://cloudbuild.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://cloudbuild.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://cloudbuild.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://cloudbuild.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://cloudbuild.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://cloudbuild.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://cloudbuild.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://cloudbuild.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://cloudbuild.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://cloudbuild.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://cloudbuild.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://cloudbuild.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://cloudbuild.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://cloudbuild.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://cloudbuild.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://cloudbuild.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://cloudbuild.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://cloudbuild.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://cloudbuild.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://cloudbuild.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://cloudbuild.europe-west9.rep.googleapis.com/', 'europe-west15': 'https://cloudbuild.europe-west15.rep.googleapis.com/', 'me-central1': 'https://cloudbuild.me-central1.rep.googleapis.com/', 'me-central2': 'https://cloudbuild.me-central2.rep.googleapis.com/', 'me-west1': 'https://cloudbuild.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://cloudbuild.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://cloudbuild.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://cloudbuild.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://cloudbuild.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://cloudbuild.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://cloudbuild.us-central1.rep.googleapis.com/', 'us-central2': 'https://cloudbuild.us-central2.rep.googleapis.com/', 'us-east1': 'https://cloudbuild.us-east1.rep.googleapis.com/', 'us-east4': 'https://cloudbuild.us-east4.rep.googleapis.com/', 'us-east5': 'https://cloudbuild.us-east5.rep.googleapis.com/', 'us-east7': 'https://cloudbuild.us-east7.rep.googleapis.com/', 'us-south1': 'https://cloudbuild.us-south1.rep.googleapis.com/', 'us-west1': 'https://cloudbuild.us-west1.rep.googleapis.com/', 'us-west2': 'https://cloudbuild.us-west2.rep.googleapis.com/', 'us-west3': 'https://cloudbuild.us-west3.rep.googleapis.com/', 'us-west4': 'https://cloudbuild.us-west4.rep.googleapis.com/', 'us-west8': 'https://cloudbuild.us-west8.rep.googleapis.com/'},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.cloudbuild.v1alpha1', 'cloudbuild_v1alpha1_client.CloudbuildV1alpha1', 'cloudbuild_v1alpha1_messages', 'https://cloudbuild.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.cloudbuild.v1alpha2', 'cloudbuild_v1alpha2_client.CloudbuildV1alpha2', 'cloudbuild_v1alpha2_messages', 'https://cloudbuild.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudbuild.v1beta1', 'cloudbuild_v1beta1_client.CloudbuildV1beta1', 'cloudbuild_v1beta1_messages', 'https://cloudbuild.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.cloudbuild.v2', 'cloudbuild_v2_client.CloudbuildV2', 'cloudbuild_v2_messages', 'https://cloudbuild.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://cloudbuild.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://cloudbuild.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://cloudbuild.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://cloudbuild.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://cloudbuild.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://cloudbuild.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://cloudbuild.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://cloudbuild.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://cloudbuild.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://cloudbuild.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://cloudbuild.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://cloudbuild.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://cloudbuild.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://cloudbuild.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://cloudbuild.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://cloudbuild.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://cloudbuild.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://cloudbuild.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://cloudbuild.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://cloudbuild.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://cloudbuild.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://cloudbuild.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://cloudbuild.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://cloudbuild.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://cloudbuild.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://cloudbuild.europe-west9.rep.googleapis.com/', 'europe-west15': 'https://cloudbuild.europe-west15.rep.googleapis.com/', 'me-central1': 'https://cloudbuild.me-central1.rep.googleapis.com/', 'me-central2': 'https://cloudbuild.me-central2.rep.googleapis.com/', 'me-west1': 'https://cloudbuild.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://cloudbuild.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://cloudbuild.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://cloudbuild.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://cloudbuild.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://cloudbuild.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://cloudbuild.us-central1.rep.googleapis.com/', 'us-central2': 'https://cloudbuild.us-central2.rep.googleapis.com/', 'us-east1': 'https://cloudbuild.us-east1.rep.googleapis.com/', 'us-east4': 'https://cloudbuild.us-east4.rep.googleapis.com/', 'us-east5': 'https://cloudbuild.us-east5.rep.googleapis.com/', 'us-east7': 'https://cloudbuild.us-east7.rep.googleapis.com/', 'us-south1': 'https://cloudbuild.us-south1.rep.googleapis.com/', 'us-west1': 'https://cloudbuild.us-west1.rep.googleapis.com/', 'us-west2': 'https://cloudbuild.us-west2.rep.googleapis.com/', 'us-west3': 'https://cloudbuild.us-west3.rep.googleapis.com/', 'us-west4': 'https://cloudbuild.us-west4.rep.googleapis.com/', 'us-west8': 'https://cloudbuild.us-west8.rep.googleapis.com/'},
        ),
    },
    'cloudcommerceconsumerprocurement': {
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.cloudcommerceconsumerprocurement.v1alpha1', 'cloudcommerceconsumerprocurement_v1alpha1_client.CloudcommerceconsumerprocurementV1alpha1', 'cloudcommerceconsumerprocurement_v1alpha1_messages', 'https://cloudcommerceconsumerprocurement.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'clouddebugger': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.clouddebugger.v2', 'clouddebugger_v2_client.ClouddebuggerV2', 'clouddebugger_v2_messages', 'https://clouddebugger.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'clouddeploy': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.clouddeploy.v1', 'clouddeploy_v1_client.ClouddeployV1', 'clouddeploy_v1_messages', 'https://clouddeploy.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'clouderrorreporting': {
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.clouderrorreporting.v1beta1', 'clouderrorreporting_v1beta1_client.ClouderrorreportingV1beta1', 'clouderrorreporting_v1beta1_messages', 'https://clouderrorreporting.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us': 'https://clouderrorreporting.us.rep.googleapis.com/', 'africa-south1': 'https://clouderrorreporting.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://clouderrorreporting.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://clouderrorreporting.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://clouderrorreporting.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://clouderrorreporting.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://clouderrorreporting.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://clouderrorreporting.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://clouderrorreporting.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://clouderrorreporting.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://clouderrorreporting.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://clouderrorreporting.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://clouderrorreporting.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://clouderrorreporting.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://clouderrorreporting.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://clouderrorreporting.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://clouderrorreporting.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://clouderrorreporting.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://clouderrorreporting.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://clouderrorreporting.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://clouderrorreporting.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://clouderrorreporting.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://clouderrorreporting.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://clouderrorreporting.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://clouderrorreporting.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://clouderrorreporting.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://clouderrorreporting.europe-west9.rep.googleapis.com/', 'me-central1': 'https://clouderrorreporting.me-central1.rep.googleapis.com/', 'me-central2': 'https://clouderrorreporting.me-central2.rep.googleapis.com/', 'me-west1': 'https://clouderrorreporting.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://clouderrorreporting.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://clouderrorreporting.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://clouderrorreporting.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://clouderrorreporting.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://clouderrorreporting.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://clouderrorreporting.us-central1.rep.googleapis.com/', 'us-central2': 'https://clouderrorreporting.us-central2.rep.googleapis.com/', 'us-east1': 'https://clouderrorreporting.us-east1.rep.googleapis.com/', 'us-east4': 'https://clouderrorreporting.us-east4.rep.googleapis.com/', 'us-east5': 'https://clouderrorreporting.us-east5.rep.googleapis.com/', 'us-east7': 'https://clouderrorreporting.us-east7.rep.googleapis.com/', 'us-south1': 'https://clouderrorreporting.us-south1.rep.googleapis.com/', 'us-west1': 'https://clouderrorreporting.us-west1.rep.googleapis.com/', 'us-west2': 'https://clouderrorreporting.us-west2.rep.googleapis.com/', 'us-west3': 'https://clouderrorreporting.us-west3.rep.googleapis.com/', 'us-west4': 'https://clouderrorreporting.us-west4.rep.googleapis.com/', 'us-west8': 'https://clouderrorreporting.us-west8.rep.googleapis.com/'},
        ),
    },
    'cloudfunctions': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudfunctions.v1', 'cloudfunctions_v1_client.CloudfunctionsV1', 'cloudfunctions_v1_messages', 'https://cloudfunctions.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.cloudfunctions.v2', 'cloudfunctions_v2_client.CloudfunctionsV2', 'cloudfunctions_v2_messages', 'https://cloudfunctions.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2alpha': (
            ('googlecloudsdk.generated_clients.apis.cloudfunctions.v2alpha', 'cloudfunctions_v2alpha_client.CloudfunctionsV2alpha', 'cloudfunctions_v2alpha_messages', 'https://cloudfunctions.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2beta': (
            ('googlecloudsdk.generated_clients.apis.cloudfunctions.v2beta', 'cloudfunctions_v2beta_client.CloudfunctionsV2beta', 'cloudfunctions_v2beta_messages', 'https://cloudfunctions.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'cloudidentity': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudidentity.v1', 'cloudidentity_v1_client.CloudidentityV1', 'cloudidentity_v1_messages', 'https://cloudidentity.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.cloudidentity.v1alpha1', 'cloudidentity_v1alpha1_client.CloudidentityV1alpha1', 'cloudidentity_v1alpha1_messages', 'https://cloudidentity.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudidentity.v1beta1', 'cloudidentity_v1beta1_client.CloudidentityV1beta1', 'cloudidentity_v1beta1_messages', 'https://cloudidentity.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'cloudkms': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudkms.v1', 'cloudkms_v1_client.CloudkmsV1', 'cloudkms_v1_messages', 'https://cloudkms.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'europe-west8': 'https://cloudkms.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://cloudkms.europe-west9.rep.googleapis.com/', 'me-central2': 'https://cloudkms.me-central2.rep.googleapis.com/', 'us-east1': 'https://cloudkms.us-east1.rep.googleapis.com/', 'us-east4': 'https://cloudkms.us-east4.rep.googleapis.com/', 'us-west2': 'https://cloudkms.us-west2.rep.googleapis.com/', 'us-west1': 'https://cloudkms.us-west1.rep.googleapis.com/', 'us-central1': 'https://cloudkms.us-central1.rep.googleapis.com/', 'us-west3': 'https://cloudkms.us-west3.rep.googleapis.com/', 'us-central2': 'https://cloudkms.us-central2.rep.googleapis.com/', 'us-west4': 'https://cloudkms.us-west4.rep.googleapis.com/', 'us-east5': 'https://cloudkms.us-east5.rep.googleapis.com/', 'us-south1': 'https://cloudkms.us-south1.rep.googleapis.com/', 'us-east7': 'https://cloudkms.us-east7.rep.googleapis.com/', 'europe-west3': 'https://cloudkms.europe-west3.rep.googleapis.com/', 'us-west8': 'https://cloudkms.us-west8.rep.googleapis.com/', 'northamerica-northeast1': 'https://cloudkms.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://cloudkms.northamerica-northeast2.rep.googleapis.com/', 'us': 'https://cloudkms.us.rep.googleapis.com/', 'in': 'https://cloudkms.in.rep.googleapis.com/', 'ca': 'https://cloudkms.ca.rep.googleapis.com/'},
        ),
    },
    'cloudlocationfinder': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudlocationfinder.v1', 'cloudlocationfinder_v1_client.CloudlocationfinderV1', 'cloudlocationfinder_v1_messages', 'https://cloudlocationfinder.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.cloudlocationfinder.v1alpha', 'cloudlocationfinder_v1alpha_client.CloudlocationfinderV1alpha', 'cloudlocationfinder_v1alpha_messages', 'https://cloudlocationfinder.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'cloudnumberregistry': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.cloudnumberregistry.v1alpha', 'cloudnumberregistry_v1alpha_client.CloudnumberregistryV1alpha', 'cloudnumberregistry_v1alpha_messages', 'https://cloudnumberregistry.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'cloudquotas': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudquotas.v1', 'cloudquotas_v1_client.CloudquotasV1', 'cloudquotas_v1_messages', 'https://cloudquotas.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.cloudquotas.v1alpha', 'cloudquotas_v1alpha_client.CloudquotasV1alpha', 'cloudquotas_v1alpha_messages', 'https://cloudquotas.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.cloudquotas.v1beta', 'cloudquotas_v1beta_client.CloudquotasV1beta', 'cloudquotas_v1beta_messages', 'https://cloudquotas.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'cloudresourcemanager': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudresourcemanager.v1', 'cloudresourcemanager_v1_client.CloudresourcemanagerV1', 'cloudresourcemanager_v1_messages', 'https://cloudresourcemanager.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudresourcemanager.v1beta1', 'cloudresourcemanager_v1beta1_client.CloudresourcemanagerV1beta1', 'cloudresourcemanager_v1beta1_messages', 'https://cloudresourcemanager.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.cloudresourcemanager.v2', 'cloudresourcemanager_v2_client.CloudresourcemanagerV2', 'cloudresourcemanager_v2_messages', 'https://cloudresourcemanager.googleapis.com/'),
            None,
            False,
            True,
            'https://cloudresourcemanager.mtls.googleapis.com/',
            {},
        ),
        'v2alpha1': (
            ('googlecloudsdk.generated_clients.apis.cloudresourcemanager.v2alpha1', 'cloudresourcemanager_v2alpha1_client.CloudresourcemanagerV2alpha1', 'cloudresourcemanager_v2alpha1_messages', 'https://cloudresourcemanager.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudresourcemanager.v2beta1', 'cloudresourcemanager_v2beta1_client.CloudresourcemanagerV2beta1', 'cloudresourcemanager_v2beta1_messages', 'https://cloudresourcemanager.googleapis.com/'),
            None,
            False,
            True,
            'https://cloudresourcemanager.mtls.googleapis.com/',
            {},
        ),
        'v3': (
            ('googlecloudsdk.generated_clients.apis.cloudresourcemanager.v3', 'cloudresourcemanager_v3_client.CloudresourcemanagerV3', 'cloudresourcemanager_v3_messages', 'https://cloudresourcemanager.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'cloudscheduler': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudscheduler.v1', 'cloudscheduler_v1_client.CloudschedulerV1', 'cloudscheduler_v1_messages', 'https://cloudscheduler.googleapis.com/'),
            None,
            True,
            True,
            'https://cloudscheduler.mtls.googleapis.com/',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.cloudscheduler.v1alpha1', 'cloudscheduler_v1alpha1_client.CloudschedulerV1alpha1', 'cloudscheduler_v1alpha1_messages', 'https://cloudscheduler.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudscheduler.v1beta1', 'cloudscheduler_v1beta1_client.CloudschedulerV1beta1', 'cloudscheduler_v1beta1_messages', 'https://cloudscheduler.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'cloudsecuritycompliance': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudsecuritycompliance.v1', 'cloudsecuritycompliance_v1_client.CloudsecuritycomplianceV1', 'cloudsecuritycompliance_v1_messages', 'https://cloudsecuritycompliance.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us': 'https://cloudsecuritycompliance.us.rep.googleapis.com/', 'us-east4': 'https://cloudsecuritycompliance.us-east4.rep.googleapis.com/'},
        ),
    },
    'cloudshell': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.cloudshell.v1', 'cloudshell_v1_client.CloudshellV1', 'cloudshell_v1_messages', 'https://cloudshell.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.cloudshell.v1alpha1', 'cloudshell_v1alpha1_client.CloudshellV1alpha1', 'cloudshell_v1alpha1_messages', 'https://cloudshell.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'cloudtasks': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.cloudtasks.v2', 'cloudtasks_v2_client.CloudtasksV2', 'cloudtasks_v2_messages', 'https://cloudtasks.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v2beta2': (
            ('googlecloudsdk.generated_clients.apis.cloudtasks.v2beta2', 'cloudtasks_v2beta2_client.CloudtasksV2beta2', 'cloudtasks_v2beta2_messages', 'https://cloudtasks.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2beta3': (
            ('googlecloudsdk.generated_clients.apis.cloudtasks.v2beta3', 'cloudtasks_v2beta3_client.CloudtasksV2beta3', 'cloudtasks_v2beta3_messages', 'https://cloudtasks.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'cloudtrace': {
        'v2beta1': (
            ('googlecloudsdk.generated_clients.apis.cloudtrace.v2beta1', 'cloudtrace_v2beta1_client.CloudtraceV2beta1', 'cloudtrace_v2beta1_messages', 'https://cloudtrace.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://cloudtrace.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://cloudtrace.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://cloudtrace.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://cloudtrace.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://cloudtrace.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://cloudtrace.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://cloudtrace.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://cloudtrace.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://cloudtrace.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://cloudtrace.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://cloudtrace.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://cloudtrace.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://cloudtrace.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://cloudtrace.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://cloudtrace.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://cloudtrace.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://cloudtrace.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://cloudtrace.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://cloudtrace.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://cloudtrace.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://cloudtrace.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://cloudtrace.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://cloudtrace.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://cloudtrace.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://cloudtrace.europe-west9.rep.googleapis.com/', 'me-central1': 'https://cloudtrace.me-central1.rep.googleapis.com/', 'me-central2': 'https://cloudtrace.me-central2.rep.googleapis.com/', 'me-west1': 'https://cloudtrace.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://cloudtrace.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://cloudtrace.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://cloudtrace.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://cloudtrace.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://cloudtrace.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://cloudtrace.us-central1.rep.googleapis.com/', 'us-central2': 'https://cloudtrace.us-central2.rep.googleapis.com/', 'us-east1': 'https://cloudtrace.us-east1.rep.googleapis.com/', 'us-east4': 'https://cloudtrace.us-east4.rep.googleapis.com/', 'us-east5': 'https://cloudtrace.us-east5.rep.googleapis.com/', 'us-east7': 'https://cloudtrace.us-east7.rep.googleapis.com/', 'us-south1': 'https://cloudtrace.us-south1.rep.googleapis.com/', 'us-west1': 'https://cloudtrace.us-west1.rep.googleapis.com/', 'us-west2': 'https://cloudtrace.us-west2.rep.googleapis.com/', 'us-west3': 'https://cloudtrace.us-west3.rep.googleapis.com/', 'us-west4': 'https://cloudtrace.us-west4.rep.googleapis.com/', 'us-west8': 'https://cloudtrace.us-west8.rep.googleapis.com/', 'us': 'https://cloudtrace.us.rep.googleapis.com/', 'eu': 'https://cloudtrace.eu.rep.googleapis.com/'},
        ),
    },
    'composer': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.composer.v1', 'composer_v1_client.ComposerV1', 'composer_v1_messages', 'https://composer.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://composer.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://composer.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://composer.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://composer.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://composer.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://composer.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://composer.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://composer.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://composer.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://composer.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://composer.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://composer.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://composer.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://composer.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://composer.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://composer.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://composer.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://composer.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://composer.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://composer.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://composer.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://composer.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://composer.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://composer.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://composer.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://composer.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://composer.europe-west9.rep.googleapis.com/', 'me-central1': 'https://composer.me-central1.rep.googleapis.com/', 'me-central2': 'https://composer.me-central2.rep.googleapis.com/', 'me-west1': 'https://composer.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://composer.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://composer.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://composer.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://composer.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://composer.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://composer.us-central1.rep.googleapis.com/', 'us-east1': 'https://composer.us-east1.rep.googleapis.com/', 'us-east4': 'https://composer.us-east4.rep.googleapis.com/', 'us-east5': 'https://composer.us-east5.rep.googleapis.com/', 'us-east7': 'https://composer.us-east7.rep.googleapis.com/', 'us-south1': 'https://composer.us-south1.rep.googleapis.com/', 'us-west1': 'https://composer.us-west1.rep.googleapis.com/', 'us-west2': 'https://composer.us-west2.rep.googleapis.com/', 'us-west3': 'https://composer.us-west3.rep.googleapis.com/', 'us-west4': 'https://composer.us-west4.rep.googleapis.com/', 'us-west8': 'https://composer.us-west8.rep.googleapis.com/'},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.composer.v1alpha2', 'composer_v1alpha2_client.ComposerV1alpha2', 'composer_v1alpha2_messages', 'https://composer.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://composer.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://composer.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://composer.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://composer.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://composer.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://composer.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://composer.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://composer.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://composer.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://composer.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://composer.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://composer.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://composer.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://composer.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://composer.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://composer.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://composer.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://composer.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://composer.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://composer.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://composer.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://composer.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://composer.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://composer.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://composer.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://composer.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://composer.europe-west9.rep.googleapis.com/', 'me-central1': 'https://composer.me-central1.rep.googleapis.com/', 'me-central2': 'https://composer.me-central2.rep.googleapis.com/', 'me-west1': 'https://composer.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://composer.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://composer.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://composer.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://composer.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://composer.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://composer.us-central1.rep.googleapis.com/', 'us-east1': 'https://composer.us-east1.rep.googleapis.com/', 'us-east4': 'https://composer.us-east4.rep.googleapis.com/', 'us-east5': 'https://composer.us-east5.rep.googleapis.com/', 'us-east7': 'https://composer.us-east7.rep.googleapis.com/', 'us-south1': 'https://composer.us-south1.rep.googleapis.com/', 'us-west1': 'https://composer.us-west1.rep.googleapis.com/', 'us-west2': 'https://composer.us-west2.rep.googleapis.com/', 'us-west3': 'https://composer.us-west3.rep.googleapis.com/', 'us-west4': 'https://composer.us-west4.rep.googleapis.com/', 'us-west8': 'https://composer.us-west8.rep.googleapis.com/'},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.composer.v1beta1', 'composer_v1beta1_client.ComposerV1beta1', 'composer_v1beta1_messages', 'https://composer.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://composer.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://composer.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://composer.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://composer.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://composer.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://composer.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://composer.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://composer.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://composer.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://composer.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://composer.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://composer.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://composer.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://composer.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://composer.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://composer.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://composer.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://composer.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://composer.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://composer.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://composer.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://composer.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://composer.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://composer.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://composer.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://composer.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://composer.europe-west9.rep.googleapis.com/', 'me-central1': 'https://composer.me-central1.rep.googleapis.com/', 'me-central2': 'https://composer.me-central2.rep.googleapis.com/', 'me-west1': 'https://composer.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://composer.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://composer.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://composer.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://composer.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://composer.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://composer.us-central1.rep.googleapis.com/', 'us-east1': 'https://composer.us-east1.rep.googleapis.com/', 'us-east4': 'https://composer.us-east4.rep.googleapis.com/', 'us-east5': 'https://composer.us-east5.rep.googleapis.com/', 'us-east7': 'https://composer.us-east7.rep.googleapis.com/', 'us-south1': 'https://composer.us-south1.rep.googleapis.com/', 'us-west1': 'https://composer.us-west1.rep.googleapis.com/', 'us-west2': 'https://composer.us-west2.rep.googleapis.com/', 'us-west3': 'https://composer.us-west3.rep.googleapis.com/', 'us-west4': 'https://composer.us-west4.rep.googleapis.com/', 'us-west8': 'https://composer.us-west8.rep.googleapis.com/'},
        ),
    },
    'composerflex': {
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.composerflex.v1alpha1', 'composerflex_v1alpha1_client.ComposerflexV1alpha1', 'composerflex_v1alpha1_messages', 'https://composerflex.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'compute': {
        'alpha': (
            ('googlecloudsdk.generated_clients.apis.compute.alpha', 'compute_alpha_client.ComputeAlpha', 'compute_alpha_messages', 'https://compute.googleapis.com/compute/alpha/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'beta': (
            ('googlecloudsdk.generated_clients.apis.compute.beta', 'compute_beta_client.ComputeBeta', 'compute_beta_messages', 'https://compute.googleapis.com/compute/beta/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'preview': (
            ('googlecloudsdk.generated_clients.apis.compute.preview', 'compute_preview_client.ComputePreview', 'compute_preview_messages', 'https://compute.googleapis.com/compute/v1/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1': (
            ('googlecloudsdk.generated_clients.apis.compute.v1', 'compute_v1_client.ComputeV1', 'compute_v1_messages', 'https://compute.googleapis.com/compute/v1/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'config': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.config.v1', 'config_v1_client.ConfigV1', 'config_v1_messages', 'https://config.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us-south1': 'https://config.us-south1.rep.googleapis.com/', 'us-west3': 'https://config.us-west3.rep.googleapis.com/', 'us-east4': 'https://config.us-east4.rep.googleapis.com/', 'us-west4': 'https://config.us-west4.rep.googleapis.com/', 'us-east5': 'https://config.us-east5.rep.googleapis.com/', 'us-east7': 'https://config.us-east7.rep.googleapis.com/'},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.config.v1alpha2', 'config_v1alpha2_client.ConfigV1alpha2', 'config_v1alpha2_messages', 'https://config.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-south1': 'https://config.us-south1.rep.googleapis.com/', 'us-west3': 'https://config.us-west3.rep.googleapis.com/', 'us-east4': 'https://config.us-east4.rep.googleapis.com/', 'us-west4': 'https://config.us-west4.rep.googleapis.com/', 'us-east5': 'https://config.us-east5.rep.googleapis.com/', 'us-east7': 'https://config.us-east7.rep.googleapis.com/'},
        ),
    },
    'configdelivery': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.configdelivery.v1', 'configdelivery_v1_client.ConfigdeliveryV1', 'configdelivery_v1_messages', 'https://configdelivery.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.configdelivery.v1alpha', 'configdelivery_v1alpha_client.ConfigdeliveryV1alpha', 'configdelivery_v1alpha_messages', 'https://configdelivery.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.configdelivery.v1beta', 'configdelivery_v1beta_client.ConfigdeliveryV1beta', 'configdelivery_v1beta_messages', 'https://configdelivery.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'connectgateway': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.connectgateway.v1', 'connectgateway_v1_client.ConnectgatewayV1', 'connectgateway_v1_messages', 'https://connectgateway.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'asia-south1': 'https://connectgateway.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://connectgateway.asia-south2.rep.googleapis.com/', 'us-central1': 'https://connectgateway.us-central1.rep.googleapis.com/', 'us-central2': 'https://connectgateway.us-central2.rep.googleapis.com/', 'us-east1': 'https://connectgateway.us-east1.rep.googleapis.com/', 'us-east4': 'https://connectgateway.us-east4.rep.googleapis.com/', 'us-east5': 'https://connectgateway.us-east5.rep.googleapis.com/', 'us-east7': 'https://connectgateway.us-east7.rep.googleapis.com/', 'us-south1': 'https://connectgateway.us-south1.rep.googleapis.com/', 'us-west1': 'https://connectgateway.us-west1.rep.googleapis.com/', 'us-west2': 'https://connectgateway.us-west2.rep.googleapis.com/', 'us-west3': 'https://connectgateway.us-west3.rep.googleapis.com/', 'us-west4': 'https://connectgateway.us-west4.rep.googleapis.com/', 'us-west8': 'https://connectgateway.us-west8.rep.googleapis.com/'},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.connectgateway.v1alpha1', 'connectgateway_v1alpha1_client.ConnectgatewayV1alpha1', 'connectgateway_v1alpha1_messages', 'https://connectgateway.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-south1': 'https://connectgateway.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://connectgateway.asia-south2.rep.googleapis.com/', 'us-central1': 'https://connectgateway.us-central1.rep.googleapis.com/', 'us-central2': 'https://connectgateway.us-central2.rep.googleapis.com/', 'us-east1': 'https://connectgateway.us-east1.rep.googleapis.com/', 'us-east4': 'https://connectgateway.us-east4.rep.googleapis.com/', 'us-east5': 'https://connectgateway.us-east5.rep.googleapis.com/', 'us-east7': 'https://connectgateway.us-east7.rep.googleapis.com/', 'us-south1': 'https://connectgateway.us-south1.rep.googleapis.com/', 'us-west1': 'https://connectgateway.us-west1.rep.googleapis.com/', 'us-west2': 'https://connectgateway.us-west2.rep.googleapis.com/', 'us-west3': 'https://connectgateway.us-west3.rep.googleapis.com/', 'us-west4': 'https://connectgateway.us-west4.rep.googleapis.com/', 'us-west8': 'https://connectgateway.us-west8.rep.googleapis.com/'},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.connectgateway.v1beta1', 'connectgateway_v1beta1_client.ConnectgatewayV1beta1', 'connectgateway_v1beta1_messages', 'https://connectgateway.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-south1': 'https://connectgateway.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://connectgateway.asia-south2.rep.googleapis.com/', 'us-central1': 'https://connectgateway.us-central1.rep.googleapis.com/', 'us-central2': 'https://connectgateway.us-central2.rep.googleapis.com/', 'us-east1': 'https://connectgateway.us-east1.rep.googleapis.com/', 'us-east4': 'https://connectgateway.us-east4.rep.googleapis.com/', 'us-east5': 'https://connectgateway.us-east5.rep.googleapis.com/', 'us-east7': 'https://connectgateway.us-east7.rep.googleapis.com/', 'us-south1': 'https://connectgateway.us-south1.rep.googleapis.com/', 'us-west1': 'https://connectgateway.us-west1.rep.googleapis.com/', 'us-west2': 'https://connectgateway.us-west2.rep.googleapis.com/', 'us-west3': 'https://connectgateway.us-west3.rep.googleapis.com/', 'us-west4': 'https://connectgateway.us-west4.rep.googleapis.com/', 'us-west8': 'https://connectgateway.us-west8.rep.googleapis.com/'},
        ),
    },
    'connectors': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.connectors.v1', 'connectors_v1_client.ConnectorsV1', 'connectors_v1_messages', 'https://connectors.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'container': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.container.v1', 'container_v1_client.ContainerV1', 'container_v1_messages', 'https://container.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.container.v1alpha1', 'container_v1alpha1_client.ContainerV1alpha1', 'container_v1alpha1_messages', 'https://container.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.container.v1beta1', 'container_v1beta1_client.ContainerV1beta1', 'container_v1beta1_messages', 'https://container.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'containeranalysis': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.containeranalysis.v1', 'containeranalysis_v1_client.ContaineranalysisV1', 'containeranalysis_v1_messages', 'https://containeranalysis.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-east1': 'https://containeranalysis.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://containeranalysis.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://containeranalysis.asia-northeast1.rep.googleapis.com/', 'asia-northeast3': 'https://containeranalysis.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://containeranalysis.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://containeranalysis.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://containeranalysis.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://containeranalysis.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://containeranalysis.australia-southeast1.rep.googleapis.com/', 'europe-central2': 'https://containeranalysis.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://containeranalysis.europe-north1.rep.googleapis.com/', 'europe-southwest1': 'https://containeranalysis.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://containeranalysis.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://containeranalysis.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://containeranalysis.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://containeranalysis.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://containeranalysis.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://containeranalysis.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://containeranalysis.europe-west9.rep.googleapis.com/', 'me-central1': 'https://containeranalysis.me-central1.rep.googleapis.com/', 'me-central2': 'https://containeranalysis.me-central2.rep.googleapis.com/', 'me-west1': 'https://containeranalysis.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://containeranalysis.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://containeranalysis.northamerica-northeast2.rep.googleapis.com/', 'southamerica-east1': 'https://containeranalysis.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://containeranalysis.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://containeranalysis.us-central1.rep.googleapis.com/', 'us-central2': 'https://containeranalysis.us-central2.rep.googleapis.com/', 'us-east1': 'https://containeranalysis.us-east1.rep.googleapis.com/', 'us-east4': 'https://containeranalysis.us-east4.rep.googleapis.com/', 'us-east5': 'https://containeranalysis.us-east5.rep.googleapis.com/', 'us-east7': 'https://containeranalysis.us-east7.rep.googleapis.com/', 'us-south1': 'https://containeranalysis.us-south1.rep.googleapis.com/', 'us-west1': 'https://containeranalysis.us-west1.rep.googleapis.com/', 'us-west2': 'https://containeranalysis.us-west2.rep.googleapis.com/', 'us-west3': 'https://containeranalysis.us-west3.rep.googleapis.com/', 'us-west4': 'https://containeranalysis.us-west4.rep.googleapis.com/', 'africa-south1': 'https://containeranalysis.africa-south1.rep.googleapis.com/', 'asia-northeast2': 'https://containeranalysis.asia-northeast2.rep.googleapis.com/', 'australia-southeast2': 'https://containeranalysis.australia-southeast2.rep.googleapis.com/', 'europe-west10': 'https://containeranalysis.europe-west10.rep.googleapis.com/', 'us': 'https://containeranalysis.us.rep.googleapis.com/', 'eu': 'https://containeranalysis.eu.rep.googleapis.com/'},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.containeranalysis.v1alpha1', 'containeranalysis_v1alpha1_client.ContaineranalysisV1alpha1', 'containeranalysis_v1alpha1_messages', 'https://containeranalysis.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'asia-east1': 'https://containeranalysis.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://containeranalysis.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://containeranalysis.asia-northeast1.rep.googleapis.com/', 'asia-northeast3': 'https://containeranalysis.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://containeranalysis.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://containeranalysis.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://containeranalysis.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://containeranalysis.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://containeranalysis.australia-southeast1.rep.googleapis.com/', 'europe-central2': 'https://containeranalysis.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://containeranalysis.europe-north1.rep.googleapis.com/', 'europe-southwest1': 'https://containeranalysis.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://containeranalysis.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://containeranalysis.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://containeranalysis.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://containeranalysis.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://containeranalysis.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://containeranalysis.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://containeranalysis.europe-west9.rep.googleapis.com/', 'me-central1': 'https://containeranalysis.me-central1.rep.googleapis.com/', 'me-central2': 'https://containeranalysis.me-central2.rep.googleapis.com/', 'me-west1': 'https://containeranalysis.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://containeranalysis.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://containeranalysis.northamerica-northeast2.rep.googleapis.com/', 'southamerica-east1': 'https://containeranalysis.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://containeranalysis.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://containeranalysis.us-central1.rep.googleapis.com/', 'us-central2': 'https://containeranalysis.us-central2.rep.googleapis.com/', 'us-east1': 'https://containeranalysis.us-east1.rep.googleapis.com/', 'us-east4': 'https://containeranalysis.us-east4.rep.googleapis.com/', 'us-east5': 'https://containeranalysis.us-east5.rep.googleapis.com/', 'us-east7': 'https://containeranalysis.us-east7.rep.googleapis.com/', 'us-south1': 'https://containeranalysis.us-south1.rep.googleapis.com/', 'us-west1': 'https://containeranalysis.us-west1.rep.googleapis.com/', 'us-west2': 'https://containeranalysis.us-west2.rep.googleapis.com/', 'us-west3': 'https://containeranalysis.us-west3.rep.googleapis.com/', 'us-west4': 'https://containeranalysis.us-west4.rep.googleapis.com/', 'africa-south1': 'https://containeranalysis.africa-south1.rep.googleapis.com/', 'asia-northeast2': 'https://containeranalysis.asia-northeast2.rep.googleapis.com/', 'australia-southeast2': 'https://containeranalysis.australia-southeast2.rep.googleapis.com/', 'europe-west10': 'https://containeranalysis.europe-west10.rep.googleapis.com/', 'us': 'https://containeranalysis.us.rep.googleapis.com/', 'eu': 'https://containeranalysis.eu.rep.googleapis.com/'},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.containeranalysis.v1beta1', 'containeranalysis_v1beta1_client.ContaineranalysisV1beta1', 'containeranalysis_v1beta1_messages', 'https://containeranalysis.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-east1': 'https://containeranalysis.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://containeranalysis.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://containeranalysis.asia-northeast1.rep.googleapis.com/', 'asia-northeast3': 'https://containeranalysis.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://containeranalysis.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://containeranalysis.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://containeranalysis.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://containeranalysis.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://containeranalysis.australia-southeast1.rep.googleapis.com/', 'europe-central2': 'https://containeranalysis.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://containeranalysis.europe-north1.rep.googleapis.com/', 'europe-southwest1': 'https://containeranalysis.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://containeranalysis.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://containeranalysis.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://containeranalysis.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://containeranalysis.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://containeranalysis.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://containeranalysis.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://containeranalysis.europe-west9.rep.googleapis.com/', 'me-central1': 'https://containeranalysis.me-central1.rep.googleapis.com/', 'me-central2': 'https://containeranalysis.me-central2.rep.googleapis.com/', 'me-west1': 'https://containeranalysis.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://containeranalysis.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://containeranalysis.northamerica-northeast2.rep.googleapis.com/', 'southamerica-east1': 'https://containeranalysis.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://containeranalysis.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://containeranalysis.us-central1.rep.googleapis.com/', 'us-central2': 'https://containeranalysis.us-central2.rep.googleapis.com/', 'us-east1': 'https://containeranalysis.us-east1.rep.googleapis.com/', 'us-east4': 'https://containeranalysis.us-east4.rep.googleapis.com/', 'us-east5': 'https://containeranalysis.us-east5.rep.googleapis.com/', 'us-east7': 'https://containeranalysis.us-east7.rep.googleapis.com/', 'us-south1': 'https://containeranalysis.us-south1.rep.googleapis.com/', 'us-west1': 'https://containeranalysis.us-west1.rep.googleapis.com/', 'us-west2': 'https://containeranalysis.us-west2.rep.googleapis.com/', 'us-west3': 'https://containeranalysis.us-west3.rep.googleapis.com/', 'us-west4': 'https://containeranalysis.us-west4.rep.googleapis.com/', 'africa-south1': 'https://containeranalysis.africa-south1.rep.googleapis.com/', 'asia-northeast2': 'https://containeranalysis.asia-northeast2.rep.googleapis.com/', 'australia-southeast2': 'https://containeranalysis.australia-southeast2.rep.googleapis.com/', 'europe-west10': 'https://containeranalysis.europe-west10.rep.googleapis.com/', 'us': 'https://containeranalysis.us.rep.googleapis.com/', 'eu': 'https://containeranalysis.eu.rep.googleapis.com/'},
        ),
    },
    'datacatalog': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.datacatalog.v1', 'datacatalog_v1_client.DatacatalogV1', 'datacatalog_v1_messages', 'https://datacatalog.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha3': (
            ('googlecloudsdk.generated_clients.apis.datacatalog.v1alpha3', 'datacatalog_v1alpha3_client.DatacatalogV1alpha3', 'datacatalog_v1alpha3_messages', 'https://datacatalog.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.datacatalog.v1beta1', 'datacatalog_v1beta1_client.DatacatalogV1beta1', 'datacatalog_v1beta1_messages', 'https://datacatalog.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'dataflow': {
        'v1b3': (
            ('googlecloudsdk.generated_clients.apis.dataflow.v1b3', 'dataflow_v1b3_client.DataflowV1b3', 'dataflow_v1b3_messages', 'https://dataflow.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://dataflow.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://dataflow.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://dataflow.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://dataflow.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://dataflow.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://dataflow.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://dataflow.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://dataflow.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://dataflow.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://dataflow.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://dataflow.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://dataflow.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://dataflow.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://dataflow.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://dataflow.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://dataflow.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://dataflow.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://dataflow.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://dataflow.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://dataflow.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://dataflow.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://dataflow.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://dataflow.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://dataflow.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://dataflow.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://dataflow.europe-west9.rep.googleapis.com/', 'me-central1': 'https://dataflow.me-central1.rep.googleapis.com/', 'me-central2': 'https://dataflow.me-central2.rep.googleapis.com/', 'me-west1': 'https://dataflow.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://dataflow.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://dataflow.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://dataflow.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://dataflow.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://dataflow.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://dataflow.us-central1.rep.googleapis.com/', 'us-central2': 'https://dataflow.us-central2.rep.googleapis.com/', 'us-east1': 'https://dataflow.us-east1.rep.googleapis.com/', 'us-east4': 'https://dataflow.us-east4.rep.googleapis.com/', 'us-east5': 'https://dataflow.us-east5.rep.googleapis.com/', 'us-east7': 'https://dataflow.us-east7.rep.googleapis.com/', 'us-south1': 'https://dataflow.us-south1.rep.googleapis.com/', 'us-west1': 'https://dataflow.us-west1.rep.googleapis.com/', 'us-west2': 'https://dataflow.us-west2.rep.googleapis.com/', 'us-west3': 'https://dataflow.us-west3.rep.googleapis.com/', 'us-west4': 'https://dataflow.us-west4.rep.googleapis.com/', 'us-west8': 'https://dataflow.us-west8.rep.googleapis.com/'},
        ),
    },
    'dataform': {
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.dataform.v1beta1', 'dataform_v1beta1_client.DataformV1beta1', 'dataform_v1beta1_messages', 'https://dataform.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://dataform.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://dataform.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://dataform.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://dataform.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://dataform.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://dataform.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://dataform.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://dataform.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://dataform.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://dataform.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://dataform.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://dataform.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://dataform.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://dataform.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://dataform.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://dataform.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://dataform.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://dataform.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://dataform.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://dataform.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://dataform.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://dataform.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://dataform.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://dataform.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://dataform.europe-west9.rep.googleapis.com/', 'me-central1': 'https://dataform.me-central1.rep.googleapis.com/', 'me-central2': 'https://dataform.me-central2.rep.googleapis.com/', 'me-west1': 'https://dataform.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://dataform.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://dataform.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://dataform.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://dataform.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://dataform.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://dataform.us-central1.rep.googleapis.com/', 'us-east1': 'https://dataform.us-east1.rep.googleapis.com/', 'us-east4': 'https://dataform.us-east4.rep.googleapis.com/', 'us-east5': 'https://dataform.us-east5.rep.googleapis.com/', 'us-east7': 'https://dataform.us-east7.rep.googleapis.com/', 'us-south1': 'https://dataform.us-south1.rep.googleapis.com/', 'us-west1': 'https://dataform.us-west1.rep.googleapis.com/', 'us-west2': 'https://dataform.us-west2.rep.googleapis.com/', 'us-west3': 'https://dataform.us-west3.rep.googleapis.com/', 'us-west4': 'https://dataform.us-west4.rep.googleapis.com/'},
        ),
    },
    'datafusion': {
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.datafusion.v1beta1', 'datafusion_v1beta1_client.DatafusionV1beta1', 'datafusion_v1beta1_messages', 'https://datafusion.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://datafusion.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://datafusion.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://datafusion.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://datafusion.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://datafusion.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://datafusion.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://datafusion.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://datafusion.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://datafusion.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://datafusion.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://datafusion.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://datafusion.australia-southeast2.rep.googleapis.com/', 'europe-north1': 'https://datafusion.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://datafusion.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://datafusion.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://datafusion.europe-west1.rep.googleapis.com/', 'europe-west12': 'https://datafusion.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://datafusion.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://datafusion.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://datafusion.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://datafusion.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://datafusion.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://datafusion.europe-west9.rep.googleapis.com/', 'me-central1': 'https://datafusion.me-central1.rep.googleapis.com/', 'me-central2': 'https://datafusion.me-central2.rep.googleapis.com/', 'me-west1': 'https://datafusion.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://datafusion.northamerica-northeast1.rep.googleapis.com/', 'northamerica-south1': 'https://datafusion.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://datafusion.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://datafusion.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://datafusion.us-central1.rep.googleapis.com/', 'us-east1': 'https://datafusion.us-east1.rep.googleapis.com/', 'us-east4': 'https://datafusion.us-east4.rep.googleapis.com/', 'us-east5': 'https://datafusion.us-east5.rep.googleapis.com/', 'us-east7': 'https://datafusion.us-east7.rep.googleapis.com/', 'us-south1': 'https://datafusion.us-south1.rep.googleapis.com/', 'us-west1': 'https://datafusion.us-west1.rep.googleapis.com/', 'us-west2': 'https://datafusion.us-west2.rep.googleapis.com/'},
        ),
    },
    'datamigration': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.datamigration.v1', 'datamigration_v1_client.DatamigrationV1', 'datamigration_v1_messages', 'https://datamigration.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://datamigration.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://datamigration.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://datamigration.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://datamigration.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://datamigration.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://datamigration.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://datamigration.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://datamigration.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://datamigration.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://datamigration.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://datamigration.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://datamigration.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://datamigration.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://datamigration.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://datamigration.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://datamigration.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://datamigration.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://datamigration.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://datamigration.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://datamigration.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://datamigration.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://datamigration.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://datamigration.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://datamigration.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://datamigration.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://datamigration.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://datamigration.europe-west9.rep.googleapis.com/', 'me-central1': 'https://datamigration.me-central1.rep.googleapis.com/', 'me-central2': 'https://datamigration.me-central2.rep.googleapis.com/', 'me-west1': 'https://datamigration.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://datamigration.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://datamigration.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://datamigration.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://datamigration.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://datamigration.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://datamigration.us-central1.rep.googleapis.com/', 'us-central2': 'https://datamigration.us-central2.rep.googleapis.com/', 'us-east1': 'https://datamigration.us-east1.rep.googleapis.com/', 'us-east4': 'https://datamigration.us-east4.rep.googleapis.com/', 'us-east5': 'https://datamigration.us-east5.rep.googleapis.com/', 'us-east7': 'https://datamigration.us-east7.rep.googleapis.com/', 'us-south1': 'https://datamigration.us-south1.rep.googleapis.com/', 'us-west1': 'https://datamigration.us-west1.rep.googleapis.com/', 'us-west2': 'https://datamigration.us-west2.rep.googleapis.com/', 'us-west3': 'https://datamigration.us-west3.rep.googleapis.com/', 'us-west4': 'https://datamigration.us-west4.rep.googleapis.com/', 'us-west8': 'https://datamigration.us-west8.rep.googleapis.com/'},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.datamigration.v1alpha2', 'datamigration_v1alpha2_client.DatamigrationV1alpha2', 'datamigration_v1alpha2_messages', 'https://datamigration.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://datamigration.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://datamigration.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://datamigration.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://datamigration.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://datamigration.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://datamigration.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://datamigration.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://datamigration.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://datamigration.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://datamigration.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://datamigration.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://datamigration.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://datamigration.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://datamigration.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://datamigration.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://datamigration.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://datamigration.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://datamigration.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://datamigration.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://datamigration.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://datamigration.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://datamigration.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://datamigration.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://datamigration.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://datamigration.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://datamigration.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://datamigration.europe-west9.rep.googleapis.com/', 'me-central1': 'https://datamigration.me-central1.rep.googleapis.com/', 'me-central2': 'https://datamigration.me-central2.rep.googleapis.com/', 'me-west1': 'https://datamigration.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://datamigration.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://datamigration.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://datamigration.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://datamigration.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://datamigration.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://datamigration.us-central1.rep.googleapis.com/', 'us-central2': 'https://datamigration.us-central2.rep.googleapis.com/', 'us-east1': 'https://datamigration.us-east1.rep.googleapis.com/', 'us-east4': 'https://datamigration.us-east4.rep.googleapis.com/', 'us-east5': 'https://datamigration.us-east5.rep.googleapis.com/', 'us-east7': 'https://datamigration.us-east7.rep.googleapis.com/', 'us-south1': 'https://datamigration.us-south1.rep.googleapis.com/', 'us-west1': 'https://datamigration.us-west1.rep.googleapis.com/', 'us-west2': 'https://datamigration.us-west2.rep.googleapis.com/', 'us-west3': 'https://datamigration.us-west3.rep.googleapis.com/', 'us-west4': 'https://datamigration.us-west4.rep.googleapis.com/', 'us-west8': 'https://datamigration.us-west8.rep.googleapis.com/'},
        ),
    },
    'datapipelines': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.datapipelines.v1', 'datapipelines_v1_client.DatapipelinesV1', 'datapipelines_v1_messages', 'https://datapipelines.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'dataplex': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.dataplex.v1', 'dataplex_v1_client.DataplexV1', 'dataplex_v1_messages', 'https://dataplex.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://dataplex.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://dataplex.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://dataplex.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://dataplex.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://dataplex.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://dataplex.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://dataplex.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://dataplex.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://dataplex.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://dataplex.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://dataplex.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://dataplex.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://dataplex.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://dataplex.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://dataplex.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://dataplex.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://dataplex.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://dataplex.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://dataplex.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://dataplex.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://dataplex.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://dataplex.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://dataplex.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://dataplex.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://dataplex.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://dataplex.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://dataplex.europe-west9.rep.googleapis.com/', 'me-central1': 'https://dataplex.me-central1.rep.googleapis.com/', 'me-central2': 'https://dataplex.me-central2.rep.googleapis.com/', 'me-west1': 'https://dataplex.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://dataplex.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://dataplex.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://dataplex.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://dataplex.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://dataplex.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://dataplex.us-central1.rep.googleapis.com/', 'us-central2': 'https://dataplex.us-central2.rep.googleapis.com/', 'us-east1': 'https://dataplex.us-east1.rep.googleapis.com/', 'us-east4': 'https://dataplex.us-east4.rep.googleapis.com/', 'us-east5': 'https://dataplex.us-east5.rep.googleapis.com/', 'us-east7': 'https://dataplex.us-east7.rep.googleapis.com/', 'us-south1': 'https://dataplex.us-south1.rep.googleapis.com/', 'us-west1': 'https://dataplex.us-west1.rep.googleapis.com/', 'us-west2': 'https://dataplex.us-west2.rep.googleapis.com/', 'us-west3': 'https://dataplex.us-west3.rep.googleapis.com/', 'us-west4': 'https://dataplex.us-west4.rep.googleapis.com/', 'us-west8': 'https://dataplex.us-west8.rep.googleapis.com/', 'us': 'https://dataplex.us.rep.googleapis.com/', 'eu': 'https://dataplex.eu.rep.googleapis.com/'},
        ),
    },
    'dataproc': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.dataproc.v1', 'dataproc_v1_client.DataprocV1', 'dataproc_v1_messages', 'https://dataproc.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'europe-west3': 'https://dataproc.europe-west3.rep.googleapis.com/', 'europe-west9': 'https://dataproc.europe-west9.rep.googleapis.com/', 'us-central1': 'https://dataproc.us-central1.rep.googleapis.com/', 'us-central2': 'https://dataproc.us-central2.rep.googleapis.com/', 'us-east1': 'https://dataproc.us-east1.rep.googleapis.com/', 'us-east4': 'https://dataproc.us-east4.rep.googleapis.com/', 'us-east5': 'https://dataproc.us-east5.rep.googleapis.com/', 'us-east7': 'https://dataproc.us-east7.rep.googleapis.com/', 'us-south1': 'https://dataproc.us-south1.rep.googleapis.com/', 'us-west1': 'https://dataproc.us-west1.rep.googleapis.com/', 'us-west2': 'https://dataproc.us-west2.rep.googleapis.com/', 'us-west3': 'https://dataproc.us-west3.rep.googleapis.com/', 'us-west8': 'https://dataproc.us-west8.rep.googleapis.com/', 'europe-west8': 'https://dataproc.europe-west8.rep.googleapis.com/', 'asia-south1': 'https://dataproc.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://dataproc.asia-south2.rep.googleapis.com/', 'me-central2': 'https://dataproc.me-central2.rep.googleapis.com/'},
        ),
    },
    'dataprocgdc': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.dataprocgdc.v1', 'dataprocgdc_v1_client.DataprocgdcV1', 'dataprocgdc_v1_messages', 'https://dataprocgdc.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.dataprocgdc.v1alpha1', 'dataprocgdc_v1alpha1_client.DataprocgdcV1alpha1', 'dataprocgdc_v1alpha1_messages', 'https://dataprocgdc.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'datastore': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.datastore.v1', 'datastore_v1_client.DatastoreV1', 'datastore_v1_messages', 'https://datastore.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://batch-datastore.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://batch-datastore.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://batch-datastore.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://batch-datastore.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://batch-datastore.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://batch-datastore.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://batch-datastore.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://batch-datastore.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://batch-datastore.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://batch-datastore.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://batch-datastore.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://batch-datastore.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://batch-datastore.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://batch-datastore.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://batch-datastore.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://batch-datastore.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://batch-datastore.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://batch-datastore.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://batch-datastore.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://batch-datastore.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://batch-datastore.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://batch-datastore.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://batch-datastore.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://batch-datastore.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://batch-datastore.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://batch-datastore.europe-west9.rep.googleapis.com/', 'me-central1': 'https://batch-datastore.me-central1.rep.googleapis.com/', 'me-central2': 'https://batch-datastore.me-central2.rep.googleapis.com/', 'me-west1': 'https://batch-datastore.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://batch-datastore.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://batch-datastore.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://batch-datastore.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://batch-datastore.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://batch-datastore.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://batch-datastore.us-central1.rep.googleapis.com/', 'us-east1': 'https://batch-datastore.us-east1.rep.googleapis.com/', 'us-east4': 'https://batch-datastore.us-east4.rep.googleapis.com/', 'us-east5': 'https://batch-datastore.us-east5.rep.googleapis.com/', 'us-south1': 'https://batch-datastore.us-south1.rep.googleapis.com/', 'us-west1': 'https://batch-datastore.us-west1.rep.googleapis.com/', 'us-west2': 'https://batch-datastore.us-west2.rep.googleapis.com/', 'us-west3': 'https://batch-datastore.us-west3.rep.googleapis.com/', 'us-west4': 'https://batch-datastore.us-west4.rep.googleapis.com/', 'eu': 'https://batch-datastore.eu.rep.googleapis.com/', 'us': 'https://batch-datastore.us.rep.googleapis.com/'},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.datastore.v1beta1', 'datastore_v1beta1_client.DatastoreV1beta1', 'datastore_v1beta1_messages', 'https://datastore.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://batch-datastore.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://batch-datastore.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://batch-datastore.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://batch-datastore.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://batch-datastore.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://batch-datastore.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://batch-datastore.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://batch-datastore.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://batch-datastore.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://batch-datastore.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://batch-datastore.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://batch-datastore.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://batch-datastore.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://batch-datastore.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://batch-datastore.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://batch-datastore.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://batch-datastore.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://batch-datastore.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://batch-datastore.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://batch-datastore.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://batch-datastore.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://batch-datastore.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://batch-datastore.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://batch-datastore.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://batch-datastore.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://batch-datastore.europe-west9.rep.googleapis.com/', 'me-central1': 'https://batch-datastore.me-central1.rep.googleapis.com/', 'me-central2': 'https://batch-datastore.me-central2.rep.googleapis.com/', 'me-west1': 'https://batch-datastore.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://batch-datastore.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://batch-datastore.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://batch-datastore.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://batch-datastore.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://batch-datastore.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://batch-datastore.us-central1.rep.googleapis.com/', 'us-east1': 'https://batch-datastore.us-east1.rep.googleapis.com/', 'us-east4': 'https://batch-datastore.us-east4.rep.googleapis.com/', 'us-east5': 'https://batch-datastore.us-east5.rep.googleapis.com/', 'us-south1': 'https://batch-datastore.us-south1.rep.googleapis.com/', 'us-west1': 'https://batch-datastore.us-west1.rep.googleapis.com/', 'us-west2': 'https://batch-datastore.us-west2.rep.googleapis.com/', 'us-west3': 'https://batch-datastore.us-west3.rep.googleapis.com/', 'us-west4': 'https://batch-datastore.us-west4.rep.googleapis.com/', 'eu': 'https://batch-datastore.eu.rep.googleapis.com/', 'us': 'https://batch-datastore.us.rep.googleapis.com/'},
        ),
    },
    'datastream': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.datastream.v1', 'datastream_v1_client.DatastreamV1', 'datastream_v1_messages', 'https://datastream.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://datastream.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://datastream.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://datastream.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://datastream.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://datastream.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://datastream.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://datastream.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://datastream.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://datastream.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://datastream.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://datastream.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://datastream.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://datastream.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://datastream.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://datastream.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://datastream.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://datastream.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://datastream.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://datastream.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://datastream.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://datastream.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://datastream.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://datastream.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://datastream.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://datastream.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://datastream.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://datastream.europe-west9.rep.googleapis.com/', 'me-central1': 'https://datastream.me-central1.rep.googleapis.com/', 'me-central2': 'https://datastream.me-central2.rep.googleapis.com/', 'me-west1': 'https://datastream.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://datastream.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://datastream.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://datastream.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://datastream.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://datastream.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://datastream.us-central1.rep.googleapis.com/', 'us-central2': 'https://datastream.us-central2.rep.googleapis.com/', 'us-east1': 'https://datastream.us-east1.rep.googleapis.com/', 'us-east4': 'https://datastream.us-east4.rep.googleapis.com/', 'us-east5': 'https://datastream.us-east5.rep.googleapis.com/', 'us-east7': 'https://datastream.us-east7.rep.googleapis.com/', 'us-south1': 'https://datastream.us-south1.rep.googleapis.com/', 'us-west1': 'https://datastream.us-west1.rep.googleapis.com/', 'us-west2': 'https://datastream.us-west2.rep.googleapis.com/', 'us-west3': 'https://datastream.us-west3.rep.googleapis.com/', 'us-west4': 'https://datastream.us-west4.rep.googleapis.com/', 'us-west8': 'https://datastream.us-west8.rep.googleapis.com/'},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.datastream.v1alpha1', 'datastream_v1alpha1_client.DatastreamV1alpha1', 'datastream_v1alpha1_messages', 'https://datastream.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://datastream.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://datastream.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://datastream.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://datastream.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://datastream.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://datastream.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://datastream.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://datastream.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://datastream.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://datastream.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://datastream.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://datastream.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://datastream.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://datastream.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://datastream.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://datastream.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://datastream.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://datastream.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://datastream.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://datastream.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://datastream.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://datastream.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://datastream.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://datastream.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://datastream.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://datastream.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://datastream.europe-west9.rep.googleapis.com/', 'me-central1': 'https://datastream.me-central1.rep.googleapis.com/', 'me-central2': 'https://datastream.me-central2.rep.googleapis.com/', 'me-west1': 'https://datastream.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://datastream.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://datastream.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://datastream.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://datastream.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://datastream.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://datastream.us-central1.rep.googleapis.com/', 'us-central2': 'https://datastream.us-central2.rep.googleapis.com/', 'us-east1': 'https://datastream.us-east1.rep.googleapis.com/', 'us-east4': 'https://datastream.us-east4.rep.googleapis.com/', 'us-east5': 'https://datastream.us-east5.rep.googleapis.com/', 'us-east7': 'https://datastream.us-east7.rep.googleapis.com/', 'us-south1': 'https://datastream.us-south1.rep.googleapis.com/', 'us-west1': 'https://datastream.us-west1.rep.googleapis.com/', 'us-west2': 'https://datastream.us-west2.rep.googleapis.com/', 'us-west3': 'https://datastream.us-west3.rep.googleapis.com/', 'us-west4': 'https://datastream.us-west4.rep.googleapis.com/', 'us-west8': 'https://datastream.us-west8.rep.googleapis.com/'},
        ),
    },
    'deploymentmanager': {
        'alpha': (
            ('googlecloudsdk.generated_clients.apis.deploymentmanager.alpha', 'deploymentmanager_alpha_client.DeploymentmanagerAlpha', 'deploymentmanager_alpha_messages', 'https://deploymentmanager.googleapis.com/'),
            None,
            False,
            True,
            'https://www.mtls.googleapis.com/deploymentmanager/alpha/',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.deploymentmanager.v2', 'deploymentmanager_v2_client.DeploymentmanagerV2', 'deploymentmanager_v2_messages', 'https://deploymentmanager.googleapis.com/'),
            None,
            True,
            True,
            'https://www.mtls.googleapis.com/deploymentmanager/v2/',
            {},
        ),
        'v2beta': (
            ('googlecloudsdk.generated_clients.apis.deploymentmanager.v2beta', 'deploymentmanager_v2beta_client.DeploymentmanagerV2beta', 'deploymentmanager_v2beta_messages', 'https://deploymentmanager.googleapis.com/'),
            None,
            False,
            True,
            'https://www.mtls.googleapis.com/deploymentmanager/v2beta/',
            {},
        ),
    },
    'designcenter': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.designcenter.v1', 'designcenter_v1_client.DesigncenterV1', 'designcenter_v1_messages', 'https://designcenter.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.designcenter.v1alpha', 'designcenter_v1alpha_client.DesigncenterV1alpha', 'designcenter_v1alpha_messages', 'https://designcenter.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'developerconnect': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.developerconnect.v1', 'developerconnect_v1_client.DeveloperconnectV1', 'developerconnect_v1_messages', 'https://developerconnect.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us-central1': 'https://developerconnect.us-central1.rep.googleapis.com/', 'europe-west1': 'https://developerconnect.europe-west1.rep.googleapis.com/', 'asia-east1': 'https://developerconnect.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://developerconnect.asia-east2.rep.googleapis.com/', 'europe-west4': 'https://developerconnect.europe-west4.rep.googleapis.com/', 'us-east4': 'https://developerconnect.us-east4.rep.googleapis.com/', 'us-east5': 'https://developerconnect.us-east5.rep.googleapis.com/', 'asia-southeast1': 'https://developerconnect.asia-southeast1.rep.googleapis.com/', 'us-west1': 'https://developerconnect.us-west1.rep.googleapis.com/', 'us-west2': 'https://developerconnect.us-west2.rep.googleapis.com/'},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.developerconnect.v1alpha', 'developerconnect_v1alpha_client.DeveloperconnectV1alpha', 'developerconnect_v1alpha_messages', 'https://developerconnect.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-central1': 'https://developerconnect.us-central1.rep.googleapis.com/', 'europe-west1': 'https://developerconnect.europe-west1.rep.googleapis.com/', 'asia-east1': 'https://developerconnect.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://developerconnect.asia-east2.rep.googleapis.com/', 'europe-west4': 'https://developerconnect.europe-west4.rep.googleapis.com/', 'us-east4': 'https://developerconnect.us-east4.rep.googleapis.com/', 'us-east5': 'https://developerconnect.us-east5.rep.googleapis.com/', 'asia-southeast1': 'https://developerconnect.asia-southeast1.rep.googleapis.com/', 'us-west1': 'https://developerconnect.us-west1.rep.googleapis.com/', 'us-west2': 'https://developerconnect.us-west2.rep.googleapis.com/'},
        ),
    },
    'dialogflow': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.dialogflow.v2', 'dialogflow_v2_client.DialogflowV2', 'dialogflow_v2_messages', 'https://dialogflow.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'discovery': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.discovery.v1', 'discovery_v1_client.DiscoveryV1', 'discovery_v1_messages', 'https://www.googleapis.com/discovery/v1/'),
            None,
            True,
            True,
            'https://www.mtls.googleapis.com/discovery/v1/',
            {},
        ),
    },
    'dlp': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.dlp.v2', 'dlp_v2_client.DlpV2', 'dlp_v2_messages', 'https://dlp.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://dlp.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://dlp.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://dlp.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://dlp.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://dlp.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://dlp.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://dlp.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://dlp.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://dlp.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://dlp.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://dlp.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://dlp.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://dlp.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://dlp.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://dlp.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://dlp.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://dlp.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://dlp.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://dlp.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://dlp.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://dlp.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://dlp.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://dlp.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://dlp.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://dlp.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://dlp.europe-west9.rep.googleapis.com/', 'me-central1': 'https://dlp.me-central1.rep.googleapis.com/', 'me-central2': 'https://dlp.me-central2.rep.googleapis.com/', 'me-west1': 'https://dlp.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://dlp.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://dlp.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://dlp.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://dlp.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://dlp.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://dlp.us-central1.rep.googleapis.com/', 'us-central2': 'https://dlp.us-central2.rep.googleapis.com/', 'us-east1': 'https://dlp.us-east1.rep.googleapis.com/', 'us-east4': 'https://dlp.us-east4.rep.googleapis.com/', 'us-east5': 'https://dlp.us-east5.rep.googleapis.com/', 'us-south1': 'https://dlp.us-south1.rep.googleapis.com/', 'us-west1': 'https://dlp.us-west1.rep.googleapis.com/', 'us-west2': 'https://dlp.us-west2.rep.googleapis.com/', 'us-west3': 'https://dlp.us-west3.rep.googleapis.com/', 'us-west4': 'https://dlp.us-west4.rep.googleapis.com/', 'us-west8': 'https://dlp.us-west8.rep.googleapis.com/', 'us': 'https://dlp.us.rep.googleapis.com/', 'eu': 'https://dlp.eu.rep.googleapis.com/', 'in': 'https://dlp.in.rep.googleapis.com/'},
        ),
    },
    'dns': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.dns.v1', 'dns_v1_client.DnsV1', 'dns_v1_messages', 'https://dns.googleapis.com/dns/v1/'),
            None,
            True,
            True,
            'https://dns.mtls.googleapis.com/dns/v1/',
            {},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.dns.v1alpha2', 'dns_v1alpha2_client.DnsV1alpha2', 'dns_v1alpha2_messages', 'https://dns.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta2': (
            ('googlecloudsdk.generated_clients.apis.dns.v1beta2', 'dns_v1beta2_client.DnsV1beta2', 'dns_v1beta2_messages', 'https://dns.googleapis.com/dns/v1beta2/'),
            None,
            False,
            True,
            'https://dns.mtls.googleapis.com/dns/v1beta2/',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.dns.v2', 'dns_v2_client.DnsV2', 'dns_v2_messages', 'https://dns.googleapis.com/'),
            None,
            False,
            True,
            'https://dns.mtls.googleapis.com/',
            {},
        ),
    },
    'documentai': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.documentai.v1', 'documentai_v1_client.DocumentaiV1', 'documentai_v1_messages', 'https://documentai.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us': 'https://documentai.us.rep.googleapis.com/', 'eu': 'https://documentai.eu.rep.googleapis.com/', 'asia-south1': 'https://documentai.asia-south1.rep.googleapis.com/', 'asia-southeast1': 'https://documentai.asia-southeast1.rep.googleapis.com/', 'northamerica-northeast1': 'https://documentai.northamerica-northeast1.rep.googleapis.com/', 'australia-southeast1': 'https://documentai.australia-southeast1.rep.googleapis.com/', 'europe-west2': 'https://documentai.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://documentai.europe-west3.rep.googleapis.com/'},
        ),
    },
    'domains': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.domains.v1', 'domains_v1_client.DomainsV1', 'domains_v1_messages', 'https://domains.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.domains.v1alpha2', 'domains_v1alpha2_client.DomainsV1alpha2', 'domains_v1alpha2_messages', 'https://domains.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.domains.v1beta1', 'domains_v1beta1_client.DomainsV1beta1', 'domains_v1beta1_messages', 'https://domains.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'edgecontainer': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.edgecontainer.v1', 'edgecontainer_v1_client.EdgecontainerV1', 'edgecontainer_v1_messages', 'https://edgecontainer.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.edgecontainer.v1alpha', 'edgecontainer_v1alpha_client.EdgecontainerV1alpha', 'edgecontainer_v1alpha_messages', 'https://edgecontainer.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.edgecontainer.v1beta', 'edgecontainer_v1beta_client.EdgecontainerV1beta', 'edgecontainer_v1beta_messages', 'https://edgecontainer.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'edgenetwork': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.edgenetwork.v1', 'edgenetwork_v1_client.EdgenetworkV1', 'edgenetwork_v1_messages', 'https://edgenetwork.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.edgenetwork.v1alpha1', 'edgenetwork_v1alpha1_client.EdgenetworkV1alpha1', 'edgenetwork_v1alpha1_messages', 'https://edgenetwork.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'essentialcontacts': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.essentialcontacts.v1', 'essentialcontacts_v1_client.EssentialcontactsV1', 'essentialcontacts_v1_messages', 'https://essentialcontacts.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.essentialcontacts.v1alpha1', 'essentialcontacts_v1alpha1_client.EssentialcontactsV1alpha1', 'essentialcontacts_v1alpha1_messages', 'https://essentialcontacts.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.essentialcontacts.v1beta1', 'essentialcontacts_v1beta1_client.EssentialcontactsV1beta1', 'essentialcontacts_v1beta1_messages', 'https://essentialcontacts.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'eventarc': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.eventarc.v1', 'eventarc_v1_client.EventarcV1', 'eventarc_v1_messages', 'https://eventarc.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://eventarc.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://eventarc.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://eventarc.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://eventarc.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://eventarc.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://eventarc.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://eventarc.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://eventarc.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://eventarc.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://eventarc.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://eventarc.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://eventarc.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://eventarc.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://eventarc.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://eventarc.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://eventarc.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://eventarc.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://eventarc.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://eventarc.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://eventarc.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://eventarc.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://eventarc.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://eventarc.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://eventarc.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://eventarc.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://eventarc.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://eventarc.europe-west9.rep.googleapis.com/', 'me-central1': 'https://eventarc.me-central1.rep.googleapis.com/', 'me-central2': 'https://eventarc.me-central2.rep.googleapis.com/', 'me-west1': 'https://eventarc.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://eventarc.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://eventarc.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://eventarc.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://eventarc.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://eventarc.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://eventarc.us-central1.rep.googleapis.com/', 'us-central2': 'https://eventarc.us-central2.rep.googleapis.com/', 'us-east1': 'https://eventarc.us-east1.rep.googleapis.com/', 'us-east4': 'https://eventarc.us-east4.rep.googleapis.com/', 'us-east5': 'https://eventarc.us-east5.rep.googleapis.com/', 'us-east7': 'https://eventarc.us-east7.rep.googleapis.com/', 'us-south1': 'https://eventarc.us-south1.rep.googleapis.com/', 'us-west1': 'https://eventarc.us-west1.rep.googleapis.com/', 'us-west2': 'https://eventarc.us-west2.rep.googleapis.com/', 'us-west3': 'https://eventarc.us-west3.rep.googleapis.com/', 'us-west4': 'https://eventarc.us-west4.rep.googleapis.com/', 'us-west8': 'https://eventarc.us-west8.rep.googleapis.com/', 'us': 'https://eventarc.us.rep.googleapis.com/', 'eu': 'https://eventarc.eu.rep.googleapis.com/'},
        ),
    },
    'eventarcpublishing': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.eventarcpublishing.v1', 'eventarcpublishing_v1_client.EventarcpublishingV1', 'eventarcpublishing_v1_messages', 'https://eventarcpublishing.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://eventarcpublishing.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://eventarcpublishing.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://eventarcpublishing.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://eventarcpublishing.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://eventarcpublishing.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://eventarcpublishing.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://eventarcpublishing.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://eventarcpublishing.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://eventarcpublishing.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://eventarcpublishing.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://eventarcpublishing.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://eventarcpublishing.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://eventarcpublishing.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://eventarcpublishing.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://eventarcpublishing.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://eventarcpublishing.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://eventarcpublishing.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://eventarcpublishing.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://eventarcpublishing.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://eventarcpublishing.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://eventarcpublishing.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://eventarcpublishing.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://eventarcpublishing.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://eventarcpublishing.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://eventarcpublishing.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://eventarcpublishing.europe-west9.rep.googleapis.com/', 'me-central1': 'https://eventarcpublishing.me-central1.rep.googleapis.com/', 'me-central2': 'https://eventarcpublishing.me-central2.rep.googleapis.com/', 'me-west1': 'https://eventarcpublishing.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://eventarcpublishing.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://eventarcpublishing.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://eventarcpublishing.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://eventarcpublishing.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://eventarcpublishing.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://eventarcpublishing.us-central1.rep.googleapis.com/', 'us-central2': 'https://eventarcpublishing.us-central2.rep.googleapis.com/', 'us-east1': 'https://eventarcpublishing.us-east1.rep.googleapis.com/', 'us-east4': 'https://eventarcpublishing.us-east4.rep.googleapis.com/', 'us-east5': 'https://eventarcpublishing.us-east5.rep.googleapis.com/', 'us-east7': 'https://eventarcpublishing.us-east7.rep.googleapis.com/', 'us-south1': 'https://eventarcpublishing.us-south1.rep.googleapis.com/', 'us-west1': 'https://eventarcpublishing.us-west1.rep.googleapis.com/', 'us-west2': 'https://eventarcpublishing.us-west2.rep.googleapis.com/', 'us-west3': 'https://eventarcpublishing.us-west3.rep.googleapis.com/', 'us-west4': 'https://eventarcpublishing.us-west4.rep.googleapis.com/', 'us-west8': 'https://eventarcpublishing.us-west8.rep.googleapis.com/'},
        ),
    },
    'eventflow': {
        'v1beta2': (
            ('googlecloudsdk.generated_clients.apis.eventflow.v1beta2', 'eventflow_v1beta2_client.EventflowV1beta2', 'eventflow_v1beta2_messages', 'https://eventflow.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'externalexposure': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.externalexposure.v1alpha', 'externalexposure_v1alpha_client.ExternalexposureV1alpha', 'externalexposure_v1alpha_messages', 'https://externalexposure.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'faulttesting': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.faulttesting.v1alpha', 'faulttesting_v1alpha_client.FaulttestingV1alpha', 'faulttesting_v1alpha_messages', 'https://faulttesting.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'file': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.file.v1', 'file_v1_client.FileV1', 'file_v1_messages', 'https://file.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.file.v1beta1', 'file_v1beta1_client.FileV1beta1', 'file_v1beta1_messages', 'https://file.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1p1alpha1': (
            ('googlecloudsdk.generated_clients.apis.file.v1p1alpha1', 'file_v1p1alpha1_client.FileV1p1alpha1', 'file_v1p1alpha1_messages', 'https://file.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'firebasedataconnect': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.firebasedataconnect.v1alpha', 'firebasedataconnect_v1alpha_client.FirebasedataconnectV1alpha', 'firebasedataconnect_v1alpha_messages', 'https://firebasedataconnect.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.firebasedataconnect.v1beta', 'firebasedataconnect_v1beta_client.FirebasedataconnectV1beta', 'firebasedataconnect_v1beta_messages', 'https://firebasedataconnect.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'firestore': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.firestore.v1', 'firestore_v1_client.FirestoreV1', 'firestore_v1_messages', 'https://firestore.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://batch-firestore.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://batch-firestore.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://batch-firestore.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://batch-firestore.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://batch-firestore.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://batch-firestore.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://batch-firestore.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://batch-firestore.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://batch-firestore.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://batch-firestore.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://batch-firestore.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://batch-firestore.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://batch-firestore.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://batch-firestore.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://batch-firestore.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://batch-firestore.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://batch-firestore.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://batch-firestore.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://batch-firestore.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://batch-firestore.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://batch-firestore.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://batch-firestore.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://batch-firestore.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://batch-firestore.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://batch-firestore.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://batch-firestore.europe-west9.rep.googleapis.com/', 'me-central1': 'https://batch-firestore.me-central1.rep.googleapis.com/', 'me-central2': 'https://batch-firestore.me-central2.rep.googleapis.com/', 'me-west1': 'https://batch-firestore.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://batch-firestore.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://batch-firestore.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://batch-firestore.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://batch-firestore.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://batch-firestore.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://batch-firestore.us-central1.rep.googleapis.com/', 'us-east1': 'https://batch-firestore.us-east1.rep.googleapis.com/', 'us-east4': 'https://batch-firestore.us-east4.rep.googleapis.com/', 'us-east5': 'https://batch-firestore.us-east5.rep.googleapis.com/', 'us-south1': 'https://batch-firestore.us-south1.rep.googleapis.com/', 'us-west1': 'https://batch-firestore.us-west1.rep.googleapis.com/', 'us-west2': 'https://batch-firestore.us-west2.rep.googleapis.com/', 'us-west3': 'https://batch-firestore.us-west3.rep.googleapis.com/', 'us-west4': 'https://batch-firestore.us-west4.rep.googleapis.com/', 'eu': 'https://batch-firestore.eu.rep.googleapis.com/', 'us': 'https://batch-firestore.us.rep.googleapis.com/'},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.firestore.v1beta1', 'firestore_v1beta1_client.FirestoreV1beta1', 'firestore_v1beta1_messages', 'https://firestore.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://batch-firestore.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://batch-firestore.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://batch-firestore.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://batch-firestore.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://batch-firestore.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://batch-firestore.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://batch-firestore.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://batch-firestore.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://batch-firestore.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://batch-firestore.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://batch-firestore.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://batch-firestore.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://batch-firestore.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://batch-firestore.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://batch-firestore.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://batch-firestore.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://batch-firestore.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://batch-firestore.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://batch-firestore.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://batch-firestore.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://batch-firestore.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://batch-firestore.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://batch-firestore.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://batch-firestore.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://batch-firestore.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://batch-firestore.europe-west9.rep.googleapis.com/', 'me-central1': 'https://batch-firestore.me-central1.rep.googleapis.com/', 'me-central2': 'https://batch-firestore.me-central2.rep.googleapis.com/', 'me-west1': 'https://batch-firestore.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://batch-firestore.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://batch-firestore.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://batch-firestore.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://batch-firestore.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://batch-firestore.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://batch-firestore.us-central1.rep.googleapis.com/', 'us-east1': 'https://batch-firestore.us-east1.rep.googleapis.com/', 'us-east4': 'https://batch-firestore.us-east4.rep.googleapis.com/', 'us-east5': 'https://batch-firestore.us-east5.rep.googleapis.com/', 'us-south1': 'https://batch-firestore.us-south1.rep.googleapis.com/', 'us-west1': 'https://batch-firestore.us-west1.rep.googleapis.com/', 'us-west2': 'https://batch-firestore.us-west2.rep.googleapis.com/', 'us-west3': 'https://batch-firestore.us-west3.rep.googleapis.com/', 'us-west4': 'https://batch-firestore.us-west4.rep.googleapis.com/', 'eu': 'https://batch-firestore.eu.rep.googleapis.com/', 'us': 'https://batch-firestore.us.rep.googleapis.com/'},
        ),
        'v1beta2': (
            ('googlecloudsdk.generated_clients.apis.firestore.v1beta2', 'firestore_v1beta2_client.FirestoreV1beta2', 'firestore_v1beta2_messages', 'https://firestore.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://batch-firestore.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://batch-firestore.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://batch-firestore.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://batch-firestore.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://batch-firestore.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://batch-firestore.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://batch-firestore.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://batch-firestore.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://batch-firestore.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://batch-firestore.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://batch-firestore.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://batch-firestore.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://batch-firestore.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://batch-firestore.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://batch-firestore.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://batch-firestore.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://batch-firestore.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://batch-firestore.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://batch-firestore.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://batch-firestore.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://batch-firestore.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://batch-firestore.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://batch-firestore.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://batch-firestore.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://batch-firestore.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://batch-firestore.europe-west9.rep.googleapis.com/', 'me-central1': 'https://batch-firestore.me-central1.rep.googleapis.com/', 'me-central2': 'https://batch-firestore.me-central2.rep.googleapis.com/', 'me-west1': 'https://batch-firestore.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://batch-firestore.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://batch-firestore.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://batch-firestore.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://batch-firestore.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://batch-firestore.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://batch-firestore.us-central1.rep.googleapis.com/', 'us-east1': 'https://batch-firestore.us-east1.rep.googleapis.com/', 'us-east4': 'https://batch-firestore.us-east4.rep.googleapis.com/', 'us-east5': 'https://batch-firestore.us-east5.rep.googleapis.com/', 'us-south1': 'https://batch-firestore.us-south1.rep.googleapis.com/', 'us-west1': 'https://batch-firestore.us-west1.rep.googleapis.com/', 'us-west2': 'https://batch-firestore.us-west2.rep.googleapis.com/', 'us-west3': 'https://batch-firestore.us-west3.rep.googleapis.com/', 'us-west4': 'https://batch-firestore.us-west4.rep.googleapis.com/', 'eu': 'https://batch-firestore.eu.rep.googleapis.com/', 'us': 'https://batch-firestore.us.rep.googleapis.com/'},
        ),
    },
    'geminicloudassist': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.geminicloudassist.v1', 'geminicloudassist_v1_client.GeminicloudassistV1', 'geminicloudassist_v1_messages', 'https://geminicloudassist.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.geminicloudassist.v1alpha', 'geminicloudassist_v1alpha_client.GeminicloudassistV1alpha', 'geminicloudassist_v1alpha_messages', 'https://geminicloudassist.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'genomics': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.genomics.v1', 'genomics_v1_client.GenomicsV1', 'genomics_v1_messages', 'https://genomics.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.genomics.v1alpha2', 'genomics_v1alpha2_client.GenomicsV1alpha2', 'genomics_v1alpha2_messages', 'https://genomics.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2alpha1': (
            ('googlecloudsdk.generated_clients.apis.genomics.v2alpha1', 'genomics_v2alpha1_client.GenomicsV2alpha1', 'genomics_v2alpha1_messages', 'https://genomics.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'gkebackup': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.gkebackup.v1', 'gkebackup_v1_client.GkebackupV1', 'gkebackup_v1_messages', 'https://gkebackup.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'gkehub': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.gkehub.v1', 'gkehub_v1_client.GkehubV1', 'gkehub_v1_messages', 'https://gkehub.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'asia-south1': 'https://gkehub.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://gkehub.asia-south2.rep.googleapis.com/', 'us-central1': 'https://gkehub.us-central1.rep.googleapis.com/', 'us-central2': 'https://gkehub.us-central2.rep.googleapis.com/', 'us-east1': 'https://gkehub.us-east1.rep.googleapis.com/', 'us-east4': 'https://gkehub.us-east4.rep.googleapis.com/', 'us-east5': 'https://gkehub.us-east5.rep.googleapis.com/', 'us-east7': 'https://gkehub.us-east7.rep.googleapis.com/', 'us-south1': 'https://gkehub.us-south1.rep.googleapis.com/', 'us-west1': 'https://gkehub.us-west1.rep.googleapis.com/', 'us-west2': 'https://gkehub.us-west2.rep.googleapis.com/', 'us-west3': 'https://gkehub.us-west3.rep.googleapis.com/', 'us-west4': 'https://gkehub.us-west4.rep.googleapis.com/', 'us-west8': 'https://gkehub.us-west8.rep.googleapis.com/'},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.gkehub.v1alpha', 'gkehub_v1alpha_client.GkehubV1alpha', 'gkehub_v1alpha_messages', 'https://gkehub.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-south1': 'https://gkehub.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://gkehub.asia-south2.rep.googleapis.com/', 'us-central1': 'https://gkehub.us-central1.rep.googleapis.com/', 'us-central2': 'https://gkehub.us-central2.rep.googleapis.com/', 'us-east1': 'https://gkehub.us-east1.rep.googleapis.com/', 'us-east4': 'https://gkehub.us-east4.rep.googleapis.com/', 'us-east5': 'https://gkehub.us-east5.rep.googleapis.com/', 'us-east7': 'https://gkehub.us-east7.rep.googleapis.com/', 'us-south1': 'https://gkehub.us-south1.rep.googleapis.com/', 'us-west1': 'https://gkehub.us-west1.rep.googleapis.com/', 'us-west2': 'https://gkehub.us-west2.rep.googleapis.com/', 'us-west3': 'https://gkehub.us-west3.rep.googleapis.com/', 'us-west4': 'https://gkehub.us-west4.rep.googleapis.com/', 'us-west8': 'https://gkehub.us-west8.rep.googleapis.com/'},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.gkehub.v1alpha1', 'gkehub_v1alpha1_client.GkehubV1alpha1', 'gkehub_v1alpha1_messages', 'https://gkehub.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-south1': 'https://gkehub.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://gkehub.asia-south2.rep.googleapis.com/', 'us-central1': 'https://gkehub.us-central1.rep.googleapis.com/', 'us-central2': 'https://gkehub.us-central2.rep.googleapis.com/', 'us-east1': 'https://gkehub.us-east1.rep.googleapis.com/', 'us-east4': 'https://gkehub.us-east4.rep.googleapis.com/', 'us-east5': 'https://gkehub.us-east5.rep.googleapis.com/', 'us-east7': 'https://gkehub.us-east7.rep.googleapis.com/', 'us-south1': 'https://gkehub.us-south1.rep.googleapis.com/', 'us-west1': 'https://gkehub.us-west1.rep.googleapis.com/', 'us-west2': 'https://gkehub.us-west2.rep.googleapis.com/', 'us-west3': 'https://gkehub.us-west3.rep.googleapis.com/', 'us-west4': 'https://gkehub.us-west4.rep.googleapis.com/', 'us-west8': 'https://gkehub.us-west8.rep.googleapis.com/'},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.gkehub.v1alpha2', 'gkehub_v1alpha2_client.GkehubV1alpha2', 'gkehub_v1alpha2_messages', 'https://gkehub.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.gkehub.v1beta', 'gkehub_v1beta_client.GkehubV1beta', 'gkehub_v1beta_messages', 'https://gkehub.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-south1': 'https://gkehub.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://gkehub.asia-south2.rep.googleapis.com/', 'us-central1': 'https://gkehub.us-central1.rep.googleapis.com/', 'us-central2': 'https://gkehub.us-central2.rep.googleapis.com/', 'us-east1': 'https://gkehub.us-east1.rep.googleapis.com/', 'us-east4': 'https://gkehub.us-east4.rep.googleapis.com/', 'us-east5': 'https://gkehub.us-east5.rep.googleapis.com/', 'us-east7': 'https://gkehub.us-east7.rep.googleapis.com/', 'us-south1': 'https://gkehub.us-south1.rep.googleapis.com/', 'us-west1': 'https://gkehub.us-west1.rep.googleapis.com/', 'us-west2': 'https://gkehub.us-west2.rep.googleapis.com/', 'us-west3': 'https://gkehub.us-west3.rep.googleapis.com/', 'us-west4': 'https://gkehub.us-west4.rep.googleapis.com/', 'us-west8': 'https://gkehub.us-west8.rep.googleapis.com/'},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.gkehub.v1beta1', 'gkehub_v1beta1_client.GkehubV1beta1', 'gkehub_v1beta1_messages', 'https://gkehub.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-south1': 'https://gkehub.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://gkehub.asia-south2.rep.googleapis.com/', 'us-central1': 'https://gkehub.us-central1.rep.googleapis.com/', 'us-central2': 'https://gkehub.us-central2.rep.googleapis.com/', 'us-east1': 'https://gkehub.us-east1.rep.googleapis.com/', 'us-east4': 'https://gkehub.us-east4.rep.googleapis.com/', 'us-east5': 'https://gkehub.us-east5.rep.googleapis.com/', 'us-east7': 'https://gkehub.us-east7.rep.googleapis.com/', 'us-south1': 'https://gkehub.us-south1.rep.googleapis.com/', 'us-west1': 'https://gkehub.us-west1.rep.googleapis.com/', 'us-west2': 'https://gkehub.us-west2.rep.googleapis.com/', 'us-west3': 'https://gkehub.us-west3.rep.googleapis.com/', 'us-west4': 'https://gkehub.us-west4.rep.googleapis.com/', 'us-west8': 'https://gkehub.us-west8.rep.googleapis.com/'},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.gkehub.v2', 'gkehub_v2_client.GkehubV2', 'gkehub_v2_messages', 'https://gkehub.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-south1': 'https://gkehub.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://gkehub.asia-south2.rep.googleapis.com/', 'us-central1': 'https://gkehub.us-central1.rep.googleapis.com/', 'us-central2': 'https://gkehub.us-central2.rep.googleapis.com/', 'us-east1': 'https://gkehub.us-east1.rep.googleapis.com/', 'us-east4': 'https://gkehub.us-east4.rep.googleapis.com/', 'us-east5': 'https://gkehub.us-east5.rep.googleapis.com/', 'us-east7': 'https://gkehub.us-east7.rep.googleapis.com/', 'us-south1': 'https://gkehub.us-south1.rep.googleapis.com/', 'us-west1': 'https://gkehub.us-west1.rep.googleapis.com/', 'us-west2': 'https://gkehub.us-west2.rep.googleapis.com/', 'us-west3': 'https://gkehub.us-west3.rep.googleapis.com/', 'us-west4': 'https://gkehub.us-west4.rep.googleapis.com/', 'us-west8': 'https://gkehub.us-west8.rep.googleapis.com/'},
        ),
        'v2alpha': (
            ('googlecloudsdk.generated_clients.apis.gkehub.v2alpha', 'gkehub_v2alpha_client.GkehubV2alpha', 'gkehub_v2alpha_messages', 'https://gkehub.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-south1': 'https://gkehub.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://gkehub.asia-south2.rep.googleapis.com/', 'us-central1': 'https://gkehub.us-central1.rep.googleapis.com/', 'us-central2': 'https://gkehub.us-central2.rep.googleapis.com/', 'us-east1': 'https://gkehub.us-east1.rep.googleapis.com/', 'us-east4': 'https://gkehub.us-east4.rep.googleapis.com/', 'us-east5': 'https://gkehub.us-east5.rep.googleapis.com/', 'us-east7': 'https://gkehub.us-east7.rep.googleapis.com/', 'us-south1': 'https://gkehub.us-south1.rep.googleapis.com/', 'us-west1': 'https://gkehub.us-west1.rep.googleapis.com/', 'us-west2': 'https://gkehub.us-west2.rep.googleapis.com/', 'us-west3': 'https://gkehub.us-west3.rep.googleapis.com/', 'us-west4': 'https://gkehub.us-west4.rep.googleapis.com/', 'us-west8': 'https://gkehub.us-west8.rep.googleapis.com/'},
        ),
        'v2beta': (
            ('googlecloudsdk.generated_clients.apis.gkehub.v2beta', 'gkehub_v2beta_client.GkehubV2beta', 'gkehub_v2beta_messages', 'https://gkehub.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-south1': 'https://gkehub.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://gkehub.asia-south2.rep.googleapis.com/', 'us-central1': 'https://gkehub.us-central1.rep.googleapis.com/', 'us-central2': 'https://gkehub.us-central2.rep.googleapis.com/', 'us-east1': 'https://gkehub.us-east1.rep.googleapis.com/', 'us-east4': 'https://gkehub.us-east4.rep.googleapis.com/', 'us-east5': 'https://gkehub.us-east5.rep.googleapis.com/', 'us-east7': 'https://gkehub.us-east7.rep.googleapis.com/', 'us-south1': 'https://gkehub.us-south1.rep.googleapis.com/', 'us-west1': 'https://gkehub.us-west1.rep.googleapis.com/', 'us-west2': 'https://gkehub.us-west2.rep.googleapis.com/', 'us-west3': 'https://gkehub.us-west3.rep.googleapis.com/', 'us-west4': 'https://gkehub.us-west4.rep.googleapis.com/', 'us-west8': 'https://gkehub.us-west8.rep.googleapis.com/'},
        ),
    },
    'gkemulticloud': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.gkemulticloud.v1', 'gkemulticloud_v1_client.GkemulticloudV1', 'gkemulticloud_v1_messages', 'https://gkemulticloud.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'gkeonprem': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.gkeonprem.v1', 'gkeonprem_v1_client.GkeonpremV1', 'gkeonprem_v1_messages', 'https://gkeonprem.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'gkerecommender': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.gkerecommender.v1', 'gkerecommender_v1_client.GkerecommenderV1', 'gkerecommender_v1_messages', 'https://gkerecommender.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.gkerecommender.v1alpha1', 'gkerecommender_v1alpha1_client.GkerecommenderV1alpha1', 'gkerecommender_v1alpha1_messages', 'https://gkerecommender.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'gsuiteaddons': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.gsuiteaddons.v1', 'gsuiteaddons_v1_client.GsuiteaddonsV1', 'gsuiteaddons_v1_messages', 'https://gsuiteaddons.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'healthcare': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.healthcare.v1', 'healthcare_v1_client.HealthcareV1', 'healthcare_v1_messages', 'https://healthcare.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.healthcare.v1alpha2', 'healthcare_v1alpha2_client.HealthcareV1alpha2', 'healthcare_v1alpha2_messages', 'https://healthcare.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.healthcare.v1beta1', 'healthcare_v1beta1_client.HealthcareV1beta1', 'healthcare_v1beta1_messages', 'https://healthcare.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'hypercomputecluster': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.hypercomputecluster.v1', 'hypercomputecluster_v1_client.HypercomputeclusterV1', 'hypercomputecluster_v1_messages', 'https://hypercomputecluster.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.hypercomputecluster.v1alpha', 'hypercomputecluster_v1alpha_client.HypercomputeclusterV1alpha', 'hypercomputecluster_v1alpha_messages', 'https://hypercomputecluster.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.hypercomputecluster.v1beta', 'hypercomputecluster_v1beta_client.HypercomputeclusterV1beta', 'hypercomputecluster_v1beta_messages', 'https://hypercomputecluster.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'iam': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.iam.v1', 'iam_v1_client.IamV1', 'iam_v1_messages', 'https://iam.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.iam.v1beta', 'iam_v1beta_client.IamV1beta', 'iam_v1beta_messages', 'https://iam.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.iam.v2', 'iam_v2_client.IamV2', 'iam_v2_messages', 'https://iam.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2alpha': (
            ('googlecloudsdk.generated_clients.apis.iam.v2alpha', 'iam_v2alpha_client.IamV2alpha', 'iam_v2alpha_messages', 'https://iam.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2beta': (
            ('googlecloudsdk.generated_clients.apis.iam.v2beta', 'iam_v2beta_client.IamV2beta', 'iam_v2beta_messages', 'https://iam.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v3': (
            ('googlecloudsdk.generated_clients.apis.iam.v3', 'iam_v3_client.IamV3', 'iam_v3_messages', 'https://iam.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v3alpha': (
            ('googlecloudsdk.generated_clients.apis.iam.v3alpha', 'iam_v3alpha_client.IamV3alpha', 'iam_v3alpha_messages', 'https://iam.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v3beta': (
            ('googlecloudsdk.generated_clients.apis.iam.v3beta', 'iam_v3beta_client.IamV3beta', 'iam_v3beta_messages', 'https://iam.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'iamconnectors': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.iamconnectors.v1alpha', 'iamconnectors_v1alpha_client.IamconnectorsV1alpha', 'iamconnectors_v1alpha_messages', 'https://iamconnectors.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'iamcredentials': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.iamcredentials.v1', 'iamcredentials_v1_client.IamcredentialsV1', 'iamcredentials_v1_messages', 'https://iamcredentials.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'asia-east1': 'https://iamcredentials.asia-east1.rep.googleapis.com/', 'europe-west1': 'https://iamcredentials.europe-west1.rep.googleapis.com/', 'us-central1': 'https://iamcredentials.us-central1.rep.googleapis.com/', 'us-east1': 'https://iamcredentials.us-east1.rep.googleapis.com/', 'us-east7': 'https://iamcredentials.us-east7.rep.googleapis.com/', 'us-west1': 'https://iamcredentials.us-west1.rep.googleapis.com/'},
        ),
    },
    'iap': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.iap.v1', 'iap_v1_client.IapV1', 'iap_v1_messages', 'https://iap.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.iap.v1beta1', 'iap_v1beta1_client.IapV1beta1', 'iap_v1beta1_messages', 'https://iap.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'ids': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.ids.v1', 'ids_v1_client.IdsV1', 'ids_v1_messages', 'https://ids.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'kmsinventory': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.kmsinventory.v1', 'kmsinventory_v1_client.KmsinventoryV1', 'kmsinventory_v1_messages', 'https://kmsinventory.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'krmapihosting': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.krmapihosting.v1', 'krmapihosting_v1_client.KrmapihostingV1', 'krmapihosting_v1_messages', 'https://krmapihosting.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.krmapihosting.v1alpha1', 'krmapihosting_v1alpha1_client.KrmapihostingV1alpha1', 'krmapihosting_v1alpha1_messages', 'https://krmapihosting.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'language': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.language.v1', 'language_v1_client.LanguageV1', 'language_v1_messages', 'https://language.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta2': (
            ('googlecloudsdk.generated_clients.apis.language.v1beta2', 'language_v1beta2_client.LanguageV1beta2', 'language_v1beta2_messages', 'https://language.googleapis.com/'),
            None,
            False,
            True,
            'https://language.mtls.googleapis.com/',
            {},
        ),
    },
    'logging': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.logging.v2', 'logging_v2_client.LoggingV2', 'logging_v2_messages', 'https://logging.googleapis.com/'),
            ('googlecloudsdk.generated_clients.gapic_wrappers.logging.v2',),
            True,
            True,
            '',
            {'africa-south1': 'https://logging.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://logging.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://logging.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://logging.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://logging.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://logging.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://logging.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://logging.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://logging.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://logging.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://logging.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://logging.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://logging.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://logging.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://logging.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://logging.europe-north2.rep.googleapis.com/', 'europe-north3': 'https://logging.europe-north3.rep.googleapis.com/', 'europe-southwest1': 'https://logging.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://logging.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://logging.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://logging.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://logging.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://logging.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://logging.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://logging.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://logging.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://logging.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://logging.europe-west9.rep.googleapis.com/', 'me-central1': 'https://logging.me-central1.rep.googleapis.com/', 'me-central2': 'https://logging.me-central2.rep.googleapis.com/', 'me-west1': 'https://logging.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://logging.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://logging.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://logging.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://logging.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://logging.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://logging.us-central1.rep.googleapis.com/', 'us-central2': 'https://logging.us-central2.rep.googleapis.com/', 'us-east1': 'https://logging.us-east1.rep.googleapis.com/', 'us-east4': 'https://logging.us-east4.rep.googleapis.com/', 'us-east5': 'https://logging.us-east5.rep.googleapis.com/', 'us-east7': 'https://logging.us-east7.rep.googleapis.com/', 'us-south1': 'https://logging.us-south1.rep.googleapis.com/', 'us-west1': 'https://logging.us-west1.rep.googleapis.com/', 'us-west2': 'https://logging.us-west2.rep.googleapis.com/', 'us-west3': 'https://logging.us-west3.rep.googleapis.com/', 'us-west4': 'https://logging.us-west4.rep.googleapis.com/', 'us-west8': 'https://logging.us-west8.rep.googleapis.com/', 'ch': 'https://logging.ch.rep.googleapis.com/', 'eu': 'https://logging.eu.rep.googleapis.com/', 'in': 'https://logging.in.rep.googleapis.com/', 'us': 'https://logging.us.rep.googleapis.com/'},
        ),
    },
    'looker': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.looker.v1', 'looker_v1_client.LookerV1', 'looker_v1_messages', 'https://looker.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.looker.v1alpha2', 'looker_v1alpha2_client.LookerV1alpha2', 'looker_v1alpha2_messages', 'https://looker.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'lustre': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.lustre.v1', 'lustre_v1_client.LustreV1', 'lustre_v1_messages', 'https://lustre.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.lustre.v1alpha', 'lustre_v1alpha_client.LustreV1alpha', 'lustre_v1alpha_messages', 'https://lustre.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'managedflink': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.managedflink.v1alpha', 'managedflink_v1alpha_client.ManagedflinkV1alpha', 'managedflink_v1alpha_messages', 'https://managedflink.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'managedidentities': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.managedidentities.v1', 'managedidentities_v1_client.ManagedidentitiesV1', 'managedidentities_v1_messages', 'https://managedidentities.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.managedidentities.v1alpha1', 'managedidentities_v1alpha1_client.ManagedidentitiesV1alpha1', 'managedidentities_v1alpha1_messages', 'https://managedidentities.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.managedidentities.v1beta1', 'managedidentities_v1beta1_client.ManagedidentitiesV1beta1', 'managedidentities_v1beta1_messages', 'https://managedidentities.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'managedkafka': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.managedkafka.v1', 'managedkafka_v1_client.ManagedkafkaV1', 'managedkafka_v1_messages', 'https://managedkafka.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://managedkafka.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://managedkafka.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://managedkafka.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://managedkafka.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://managedkafka.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://managedkafka.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://managedkafka.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://managedkafka.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://managedkafka.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://managedkafka.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://managedkafka.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://managedkafka.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://managedkafka.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://managedkafka.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://managedkafka.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://managedkafka.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://managedkafka.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://managedkafka.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://managedkafka.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://managedkafka.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://managedkafka.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://managedkafka.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://managedkafka.europe-west9.rep.googleapis.com/', 'europe-west10': 'https://managedkafka.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://managedkafka.europe-west12.rep.googleapis.com/', 'me-west1': 'https://managedkafka.me-west1.rep.googleapis.com/', 'me-central1': 'https://managedkafka.me-central1.rep.googleapis.com/', 'me-central2': 'https://managedkafka.me-central2.rep.googleapis.com/', 'northamerica-northeast1': 'https://managedkafka.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://managedkafka.northamerica-northeast2.rep.googleapis.com/', 'southamerica-east1': 'https://managedkafka.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://managedkafka.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://managedkafka.us-central1.rep.googleapis.com/', 'us-east1': 'https://managedkafka.us-east1.rep.googleapis.com/', 'us-east4': 'https://managedkafka.us-east4.rep.googleapis.com/', 'us-east5': 'https://managedkafka.us-east5.rep.googleapis.com/', 'us-east7': 'https://managedkafka.us-east7.rep.googleapis.com/', 'us-south1': 'https://managedkafka.us-south1.rep.googleapis.com/', 'us-west1': 'https://managedkafka.us-west1.rep.googleapis.com/', 'us-west2': 'https://managedkafka.us-west2.rep.googleapis.com/', 'us-west3': 'https://managedkafka.us-west3.rep.googleapis.com/', 'us-west4': 'https://managedkafka.us-west4.rep.googleapis.com/'},
        ),
    },
    'marketplacesolutions': {
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.marketplacesolutions.v1alpha1', 'marketplacesolutions_v1alpha1_client.MarketplacesolutionsV1alpha1', 'marketplacesolutions_v1alpha1_messages', 'https://marketplacesolutions.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'mediaasset': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.mediaasset.v1alpha', 'mediaasset_v1alpha_client.MediaassetV1alpha', 'mediaasset_v1alpha_messages', 'https://mediaasset.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'memcache': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.memcache.v1', 'memcache_v1_client.MemcacheV1', 'memcache_v1_messages', 'https://memcache.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta2': (
            ('googlecloudsdk.generated_clients.apis.memcache.v1beta2', 'memcache_v1beta2_client.MemcacheV1beta2', 'memcache_v1beta2_messages', 'https://memcache.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'memorystore': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.memorystore.v1', 'memorystore_v1_client.MemorystoreV1', 'memorystore_v1_messages', 'https://memorystore.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.memorystore.v1alpha', 'memorystore_v1alpha_client.MemorystoreV1alpha', 'memorystore_v1alpha_messages', 'https://memorystore.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.memorystore.v1beta', 'memorystore_v1beta_client.MemorystoreV1beta', 'memorystore_v1beta_messages', 'https://memorystore.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'messagestreams': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.messagestreams.v1alpha', 'messagestreams_v1alpha_client.MessagestreamsV1alpha', 'messagestreams_v1alpha_messages', 'https://messagestreams.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'metastore': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.metastore.v1', 'metastore_v1_client.MetastoreV1', 'metastore_v1_messages', 'https://metastore.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.metastore.v1alpha', 'metastore_v1alpha_client.MetastoreV1alpha', 'metastore_v1alpha_messages', 'https://metastore.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.metastore.v1beta', 'metastore_v1beta_client.MetastoreV1beta', 'metastore_v1beta_messages', 'https://metastore.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'microservices': {
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.microservices.v1alpha1', 'microservices_v1alpha1_client.MicroservicesV1alpha1', 'microservices_v1alpha1_messages', 'https://microservices.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'ml': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.ml.v1', 'ml_v1_client.MlV1', 'ml_v1_messages', 'https://ml.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'modelarmor': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.modelarmor.v1', 'modelarmor_v1_client.ModelarmorV1', 'modelarmor_v1_messages', 'https://modelarmor.us.rep.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us-central1': 'https://modelarmor.us-central1.rep.googleapis.com/', 'us-east1': 'https://modelarmor.us-east1.rep.googleapis.com/', 'us-east7': 'https://modelarmor.us-east7.rep.googleapis.com/', 'us-west1': 'https://modelarmor.us-west1.rep.googleapis.com/', 'europe-west1': 'https://modelarmor.europe-west1.rep.googleapis.com/', 'europe-west4': 'https://modelarmor.europe-west4.rep.googleapis.com/', 'us-east4': 'https://modelarmor.us-east4.rep.googleapis.com/', 'asia-southeast1': 'https://modelarmor.asia-southeast1.rep.googleapis.com/', 'europe-west2': 'https://modelarmor.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://modelarmor.europe-west3.rep.googleapis.com/', 'asia-south1': 'https://modelarmor.asia-south1.rep.googleapis.com/', 'europe-southwest1': 'https://modelarmor.europe-southwest1.rep.googleapis.com/', 'asia-northeast1': 'https://modelarmor.asia-northeast1.rep.googleapis.com/', 'asia-northeast3': 'https://modelarmor.asia-northeast3.rep.googleapis.com/', 'australia-southeast1': 'https://modelarmor.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://modelarmor.australia-southeast2.rep.googleapis.com/', 'northamerica-northeast1': 'https://modelarmor.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://modelarmor.northamerica-northeast2.rep.googleapis.com/', 'europe-west9': 'https://modelarmor.europe-west9.rep.googleapis.com/', 'us': 'https://modelarmor.us.rep.googleapis.com/', 'eu': 'https://modelarmor.eu.rep.googleapis.com/'},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.modelarmor.v1alpha', 'modelarmor_v1alpha_client.ModelarmorV1alpha', 'modelarmor_v1alpha_messages', 'https://modelarmor.us.rep.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-central1': 'https://modelarmor.us-central1.rep.googleapis.com/', 'us-east1': 'https://modelarmor.us-east1.rep.googleapis.com/', 'us-east7': 'https://modelarmor.us-east7.rep.googleapis.com/', 'us-west1': 'https://modelarmor.us-west1.rep.googleapis.com/', 'europe-west1': 'https://modelarmor.europe-west1.rep.googleapis.com/', 'europe-west4': 'https://modelarmor.europe-west4.rep.googleapis.com/', 'us-east4': 'https://modelarmor.us-east4.rep.googleapis.com/', 'asia-southeast1': 'https://modelarmor.asia-southeast1.rep.googleapis.com/', 'europe-west2': 'https://modelarmor.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://modelarmor.europe-west3.rep.googleapis.com/', 'asia-south1': 'https://modelarmor.asia-south1.rep.googleapis.com/', 'europe-southwest1': 'https://modelarmor.europe-southwest1.rep.googleapis.com/', 'asia-northeast1': 'https://modelarmor.asia-northeast1.rep.googleapis.com/', 'asia-northeast3': 'https://modelarmor.asia-northeast3.rep.googleapis.com/', 'australia-southeast1': 'https://modelarmor.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://modelarmor.australia-southeast2.rep.googleapis.com/', 'northamerica-northeast1': 'https://modelarmor.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://modelarmor.northamerica-northeast2.rep.googleapis.com/', 'europe-west9': 'https://modelarmor.europe-west9.rep.googleapis.com/', 'us': 'https://modelarmor.us.rep.googleapis.com/', 'eu': 'https://modelarmor.eu.rep.googleapis.com/'},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.modelarmor.v1beta', 'modelarmor_v1beta_client.ModelarmorV1beta', 'modelarmor_v1beta_messages', 'https://modelarmor.us.rep.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-central1': 'https://modelarmor.us-central1.rep.googleapis.com/', 'us-east1': 'https://modelarmor.us-east1.rep.googleapis.com/', 'us-east7': 'https://modelarmor.us-east7.rep.googleapis.com/', 'us-west1': 'https://modelarmor.us-west1.rep.googleapis.com/', 'europe-west1': 'https://modelarmor.europe-west1.rep.googleapis.com/', 'europe-west4': 'https://modelarmor.europe-west4.rep.googleapis.com/', 'us-east4': 'https://modelarmor.us-east4.rep.googleapis.com/', 'asia-southeast1': 'https://modelarmor.asia-southeast1.rep.googleapis.com/', 'europe-west2': 'https://modelarmor.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://modelarmor.europe-west3.rep.googleapis.com/', 'asia-south1': 'https://modelarmor.asia-south1.rep.googleapis.com/', 'europe-southwest1': 'https://modelarmor.europe-southwest1.rep.googleapis.com/', 'asia-northeast1': 'https://modelarmor.asia-northeast1.rep.googleapis.com/', 'asia-northeast3': 'https://modelarmor.asia-northeast3.rep.googleapis.com/', 'australia-southeast1': 'https://modelarmor.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://modelarmor.australia-southeast2.rep.googleapis.com/', 'northamerica-northeast1': 'https://modelarmor.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://modelarmor.northamerica-northeast2.rep.googleapis.com/', 'europe-west9': 'https://modelarmor.europe-west9.rep.googleapis.com/', 'us': 'https://modelarmor.us.rep.googleapis.com/', 'eu': 'https://modelarmor.eu.rep.googleapis.com/'},
        ),
    },
    'monitoring': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.monitoring.v1', 'monitoring_v1_client.MonitoringV1', 'monitoring_v1_messages', 'https://monitoring.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v3': (
            ('googlecloudsdk.generated_clients.apis.monitoring.v3', 'monitoring_v3_client.MonitoringV3', 'monitoring_v3_messages', 'https://monitoring.googleapis.com/'),
            None,
            True,
            True,
            'https://monitoring.mtls.googleapis.com/',
            {},
        ),
    },
    'netapp': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.netapp.v1', 'netapp_v1_client.NetappV1', 'netapp_v1_messages', 'https://netapp.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://netapp.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://netapp.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://netapp.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://netapp.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://netapp.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://netapp.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://netapp.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://netapp.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://netapp.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://netapp.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://netapp.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://netapp.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://netapp.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://netapp.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://netapp.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://netapp.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://netapp.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://netapp.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://netapp.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://netapp.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://netapp.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://netapp.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://netapp.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://netapp.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://netapp.europe-west9.rep.googleapis.com/', 'me-central1': 'https://netapp.me-central1.rep.googleapis.com/', 'me-central2': 'https://netapp.me-central2.rep.googleapis.com/', 'me-west1': 'https://netapp.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://netapp.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://netapp.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://netapp.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://netapp.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://netapp.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://netapp.us-central1.rep.googleapis.com/', 'us-east1': 'https://netapp.us-east1.rep.googleapis.com/', 'us-east4': 'https://netapp.us-east4.rep.googleapis.com/', 'us-east5': 'https://netapp.us-east5.rep.googleapis.com/', 'us-east7': 'https://netapp.us-east7.rep.googleapis.com/', 'us-south1': 'https://netapp.us-south1.rep.googleapis.com/', 'us-west1': 'https://netapp.us-west1.rep.googleapis.com/', 'us-west2': 'https://netapp.us-west2.rep.googleapis.com/', 'us-west3': 'https://netapp.us-west3.rep.googleapis.com/', 'us-west4': 'https://netapp.us-west4.rep.googleapis.com/'},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.netapp.v1alpha1', 'netapp_v1alpha1_client.NetappV1alpha1', 'netapp_v1alpha1_messages', 'https://netapp.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://netapp.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://netapp.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://netapp.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://netapp.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://netapp.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://netapp.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://netapp.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://netapp.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://netapp.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://netapp.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://netapp.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://netapp.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://netapp.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://netapp.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://netapp.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://netapp.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://netapp.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://netapp.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://netapp.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://netapp.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://netapp.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://netapp.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://netapp.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://netapp.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://netapp.europe-west9.rep.googleapis.com/', 'me-central1': 'https://netapp.me-central1.rep.googleapis.com/', 'me-central2': 'https://netapp.me-central2.rep.googleapis.com/', 'me-west1': 'https://netapp.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://netapp.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://netapp.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://netapp.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://netapp.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://netapp.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://netapp.us-central1.rep.googleapis.com/', 'us-east1': 'https://netapp.us-east1.rep.googleapis.com/', 'us-east4': 'https://netapp.us-east4.rep.googleapis.com/', 'us-east5': 'https://netapp.us-east5.rep.googleapis.com/', 'us-east7': 'https://netapp.us-east7.rep.googleapis.com/', 'us-south1': 'https://netapp.us-south1.rep.googleapis.com/', 'us-west1': 'https://netapp.us-west1.rep.googleapis.com/', 'us-west2': 'https://netapp.us-west2.rep.googleapis.com/', 'us-west3': 'https://netapp.us-west3.rep.googleapis.com/', 'us-west4': 'https://netapp.us-west4.rep.googleapis.com/'},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.netapp.v1beta1', 'netapp_v1beta1_client.NetappV1beta1', 'netapp_v1beta1_messages', 'https://netapp.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'africa-south1': 'https://netapp.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://netapp.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://netapp.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://netapp.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://netapp.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://netapp.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://netapp.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://netapp.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://netapp.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://netapp.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://netapp.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://netapp.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://netapp.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://netapp.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://netapp.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://netapp.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://netapp.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://netapp.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://netapp.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://netapp.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://netapp.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://netapp.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://netapp.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://netapp.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://netapp.europe-west9.rep.googleapis.com/', 'me-central1': 'https://netapp.me-central1.rep.googleapis.com/', 'me-central2': 'https://netapp.me-central2.rep.googleapis.com/', 'me-west1': 'https://netapp.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://netapp.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://netapp.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://netapp.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://netapp.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://netapp.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://netapp.us-central1.rep.googleapis.com/', 'us-east1': 'https://netapp.us-east1.rep.googleapis.com/', 'us-east4': 'https://netapp.us-east4.rep.googleapis.com/', 'us-east5': 'https://netapp.us-east5.rep.googleapis.com/', 'us-east7': 'https://netapp.us-east7.rep.googleapis.com/', 'us-south1': 'https://netapp.us-south1.rep.googleapis.com/', 'us-west1': 'https://netapp.us-west1.rep.googleapis.com/', 'us-west2': 'https://netapp.us-west2.rep.googleapis.com/', 'us-west3': 'https://netapp.us-west3.rep.googleapis.com/', 'us-west4': 'https://netapp.us-west4.rep.googleapis.com/'},
        ),
    },
    'networkconnectivity': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.networkconnectivity.v1', 'networkconnectivity_v1_client.NetworkconnectivityV1', 'networkconnectivity_v1_messages', 'https://networkconnectivity.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.networkconnectivity.v1alpha1', 'networkconnectivity_v1alpha1_client.NetworkconnectivityV1alpha1', 'networkconnectivity_v1alpha1_messages', 'https://networkconnectivity.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.networkconnectivity.v1beta', 'networkconnectivity_v1beta_client.NetworkconnectivityV1beta', 'networkconnectivity_v1beta_messages', 'https://networkconnectivity.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'networkmanagement': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.networkmanagement.v1', 'networkmanagement_v1_client.NetworkmanagementV1', 'networkmanagement_v1_messages', 'https://networkmanagement.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.networkmanagement.v1alpha1', 'networkmanagement_v1alpha1_client.NetworkmanagementV1alpha1', 'networkmanagement_v1alpha1_messages', 'https://networkmanagement.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.networkmanagement.v1beta1', 'networkmanagement_v1beta1_client.NetworkmanagementV1beta1', 'networkmanagement_v1beta1_messages', 'https://networkmanagement.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'networksecurity': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.networksecurity.v1', 'networksecurity_v1_client.NetworksecurityV1', 'networksecurity_v1_messages', 'https://networksecurity.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.networksecurity.v1alpha1', 'networksecurity_v1alpha1_client.NetworksecurityV1alpha1', 'networksecurity_v1alpha1_messages', 'https://networksecurity.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.networksecurity.v1beta1', 'networksecurity_v1beta1_client.NetworksecurityV1beta1', 'networksecurity_v1beta1_messages', 'https://networksecurity.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'networkservices': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.networkservices.v1', 'networkservices_v1_client.NetworkservicesV1', 'networkservices_v1_messages', 'https://networkservices.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.networkservices.v1alpha1', 'networkservices_v1alpha1_client.NetworkservicesV1alpha1', 'networkservices_v1alpha1_messages', 'https://networkservices.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.networkservices.v1beta1', 'networkservices_v1beta1_client.NetworkservicesV1beta1', 'networkservices_v1beta1_messages', 'https://networkservices.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'notebooks': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.notebooks.v1', 'notebooks_v1_client.NotebooksV1', 'notebooks_v1_messages', 'https://notebooks.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.notebooks.v1beta1', 'notebooks_v1beta1_client.NotebooksV1beta1', 'notebooks_v1beta1_messages', 'https://notebooks.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.notebooks.v2', 'notebooks_v2_client.NotebooksV2', 'notebooks_v2_messages', 'https://notebooks.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'observability': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.observability.v1', 'observability_v1_client.ObservabilityV1', 'observability_v1_messages', 'https://observability.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://observability.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://observability.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://observability.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://observability.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://observability.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://observability.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://observability.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://observability.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://observability.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://observability.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://observability.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://observability.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://observability.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://observability.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://observability.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://observability.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://observability.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://observability.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://observability.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://observability.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://observability.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://observability.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://observability.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://observability.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://observability.europe-west8.rep.googleapis.com/', 'me-central1': 'https://observability.me-central1.rep.googleapis.com/', 'me-central2': 'https://observability.me-central2.rep.googleapis.com/', 'me-west1': 'https://observability.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://observability.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://observability.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://observability.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://observability.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://observability.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://observability.us-central1.rep.googleapis.com/', 'us-central2': 'https://observability.us-central2.rep.googleapis.com/', 'us-east1': 'https://observability.us-east1.rep.googleapis.com/', 'us-east4': 'https://observability.us-east4.rep.googleapis.com/', 'us-east5': 'https://observability.us-east5.rep.googleapis.com/', 'us-south1': 'https://observability.us-south1.rep.googleapis.com/', 'us-west1': 'https://observability.us-west1.rep.googleapis.com/', 'us-west2': 'https://observability.us-west2.rep.googleapis.com/', 'us-west3': 'https://observability.us-west3.rep.googleapis.com/', 'us-west4': 'https://observability.us-west4.rep.googleapis.com/', 'us': 'https://observability.us.rep.googleapis.com/', 'eu': 'https://observability.eu.rep.googleapis.com/'},
        ),
    },
    'ondemandscanning': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.ondemandscanning.v1', 'ondemandscanning_v1_client.OndemandscanningV1', 'ondemandscanning_v1_messages', 'https://ondemandscanning.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.ondemandscanning.v1beta1', 'ondemandscanning_v1beta1_client.OndemandscanningV1beta1', 'ondemandscanning_v1beta1_messages', 'https://ondemandscanning.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'oracledatabase': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.oracledatabase.v1', 'oracledatabase_v1_client.OracledatabaseV1', 'oracledatabase_v1_messages', 'https://oracledatabase.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'asia-northeast2': 'https://oracledatabase.asia-northeast2.rep.googleapis.com/', 'asia-south2': 'https://oracledatabase.asia-south2.rep.googleapis.com/', 'asia-south1': 'https://oracledatabase.asia-south1.rep.googleapis.com/', 'australia-southeast2': 'https://oracledatabase.australia-southeast2.rep.googleapis.com/', 'europe-west8': 'https://oracledatabase.europe-west8.rep.googleapis.com/', 'northamerica-northeast2': 'https://oracledatabase.northamerica-northeast2.rep.googleapis.com/'},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.oracledatabase.v1alpha', 'oracledatabase_v1alpha_client.OracledatabaseV1alpha', 'oracledatabase_v1alpha_messages', 'https://oracledatabase.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'asia-northeast2': 'https://oracledatabase.asia-northeast2.rep.googleapis.com/', 'asia-south2': 'https://oracledatabase.asia-south2.rep.googleapis.com/', 'asia-south1': 'https://oracledatabase.asia-south1.rep.googleapis.com/', 'australia-southeast2': 'https://oracledatabase.australia-southeast2.rep.googleapis.com/', 'europe-west8': 'https://oracledatabase.europe-west8.rep.googleapis.com/', 'northamerica-northeast2': 'https://oracledatabase.northamerica-northeast2.rep.googleapis.com/'},
        ),
    },
    'orglifecycle': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.orglifecycle.v1', 'orglifecycle_v1_client.OrglifecycleV1', 'orglifecycle_v1_messages', 'https://orglifecycle.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'orgpolicy': {
        'v2': (
            ('googlecloudsdk.generated_clients.apis.orgpolicy.v2', 'orgpolicy_v2_client.OrgpolicyV2', 'orgpolicy_v2_messages', 'https://orgpolicy.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'osconfig': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.osconfig.v1', 'osconfig_v1_client.OsconfigV1', 'osconfig_v1_messages', 'https://osconfig.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us-east7': 'https://osconfig.us-east7.rep.googleapis.com/'},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.osconfig.v1alpha', 'osconfig_v1alpha_client.OsconfigV1alpha', 'osconfig_v1alpha_messages', 'https://osconfig.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-east7': 'https://osconfig.us-east7.rep.googleapis.com/'},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.osconfig.v1beta', 'osconfig_v1beta_client.OsconfigV1beta', 'osconfig_v1beta_messages', 'https://osconfig.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-east7': 'https://osconfig.us-east7.rep.googleapis.com/'},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.osconfig.v2', 'osconfig_v2_client.OsconfigV2', 'osconfig_v2_messages', 'https://osconfig.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-east7': 'https://osconfig.us-east7.rep.googleapis.com/'},
        ),
        'v2alpha': (
            ('googlecloudsdk.generated_clients.apis.osconfig.v2alpha', 'osconfig_v2alpha_client.OsconfigV2alpha', 'osconfig_v2alpha_messages', 'https://osconfig.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-east7': 'https://osconfig.us-east7.rep.googleapis.com/'},
        ),
        'v2beta': (
            ('googlecloudsdk.generated_clients.apis.osconfig.v2beta', 'osconfig_v2beta_client.OsconfigV2beta', 'osconfig_v2beta_messages', 'https://osconfig.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-east7': 'https://osconfig.us-east7.rep.googleapis.com/'},
        ),
    },
    'oslogin': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.oslogin.v1', 'oslogin_v1_client.OsloginV1', 'oslogin_v1_messages', 'https://oslogin.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.oslogin.v1alpha', 'oslogin_v1alpha_client.OsloginV1alpha', 'oslogin_v1alpha_messages', 'https://oslogin.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.oslogin.v1beta', 'oslogin_v1beta_client.OsloginV1beta', 'oslogin_v1beta_messages', 'https://oslogin.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'parallelstore': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.parallelstore.v1', 'parallelstore_v1_client.ParallelstoreV1', 'parallelstore_v1_messages', 'https://parallelstore.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.parallelstore.v1alpha', 'parallelstore_v1alpha_client.ParallelstoreV1alpha', 'parallelstore_v1alpha_messages', 'https://parallelstore.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.parallelstore.v1beta', 'parallelstore_v1beta_client.ParallelstoreV1beta', 'parallelstore_v1beta_messages', 'https://parallelstore.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'parametermanager': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.parametermanager.v1', 'parametermanager_v1_client.ParametermanagerV1', 'parametermanager_v1_messages', 'https://parametermanager.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us-central1': 'https://parametermanager.us-central1.rep.googleapis.com/', 'europe-west1': 'https://parametermanager.europe-west1.rep.googleapis.com/', 'europe-west4': 'https://parametermanager.europe-west4.rep.googleapis.com/', 'us-east4': 'https://parametermanager.us-east4.rep.googleapis.com/', 'europe-west2': 'https://parametermanager.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://parametermanager.europe-west3.rep.googleapis.com/', 'us-east7': 'https://parametermanager.us-east7.rep.googleapis.com/', 'us-central2': 'https://parametermanager.us-central2.rep.googleapis.com/', 'us-east1': 'https://parametermanager.us-east1.rep.googleapis.com/', 'us-east5': 'https://parametermanager.us-east5.rep.googleapis.com/', 'us-south1': 'https://parametermanager.us-south1.rep.googleapis.com/', 'us-west1': 'https://parametermanager.us-west1.rep.googleapis.com/', 'us-west2': 'https://parametermanager.us-west2.rep.googleapis.com/', 'us-west3': 'https://parametermanager.us-west3.rep.googleapis.com/', 'us-west4': 'https://parametermanager.us-west4.rep.googleapis.com/', 'asia-northeast1': 'https://parametermanager.asia-northeast1.rep.googleapis.com/', 'australia-southeast1': 'https://parametermanager.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://parametermanager.australia-southeast2.rep.googleapis.com/', 'europe-west6': 'https://parametermanager.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://parametermanager.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://parametermanager.europe-west9.rep.googleapis.com/', 'me-central2': 'https://parametermanager.me-central2.rep.googleapis.com/', 'me-west1': 'https://parametermanager.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://parametermanager.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://parametermanager.northamerica-northeast2.rep.googleapis.com/', 'europe-west12': 'https://parametermanager.europe-west12.rep.googleapis.com/', 'africa-south1': 'https://parametermanager.africa-south1.rep.googleapis.com/', 'asia-southeast1': 'https://parametermanager.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://parametermanager.asia-southeast2.rep.googleapis.com/', 'me-central1': 'https://parametermanager.me-central1.rep.googleapis.com/', 'southamerica-east1': 'https://parametermanager.southamerica-east1.rep.googleapis.com/', 'asia-south1': 'https://parametermanager.asia-south1.rep.googleapis.com/', 'europe-west10': 'https://parametermanager.europe-west10.rep.googleapis.com/', 'europe-north1': 'https://parametermanager.europe-north1.rep.googleapis.com/', 'europe-central2': 'https://parametermanager.europe-central2.rep.googleapis.com/', 'europe-southwest1': 'https://parametermanager.europe-southwest1.rep.googleapis.com/', 'asia-south2': 'https://parametermanager.asia-south2.rep.googleapis.com/', 'asia-east1': 'https://parametermanager.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://parametermanager.asia-east2.rep.googleapis.com/', 'asia-northeast2': 'https://parametermanager.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://parametermanager.asia-northeast3.rep.googleapis.com/', 'northamerica-south1': 'https://parametermanager.northamerica-south1.rep.googleapis.com/', 'southamerica-west1': 'https://parametermanager.southamerica-west1.rep.googleapis.com/', 'europe-north2': 'https://parametermanager.europe-north2.rep.googleapis.com/', 'europe-west15': 'https://parametermanager.europe-west15.rep.googleapis.com/', 'us': 'https://parametermanager.us.rep.googleapis.com/', 'eu': 'https://parametermanager.eu.rep.googleapis.com/', 'ca': 'https://parametermanager.ca.rep.googleapis.com/', 'in': 'https://parametermanager.in.rep.googleapis.com/'},
        ),
    },
    'policyanalyzer': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.policyanalyzer.v1', 'policyanalyzer_v1_client.PolicyanalyzerV1', 'policyanalyzer_v1_messages', 'https://policyanalyzer.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.policyanalyzer.v1beta1', 'policyanalyzer_v1beta1_client.PolicyanalyzerV1beta1', 'policyanalyzer_v1beta1_messages', 'https://policyanalyzer.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'policysimulator': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.policysimulator.v1', 'policysimulator_v1_client.PolicysimulatorV1', 'policysimulator_v1_messages', 'https://policysimulator.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.policysimulator.v1alpha', 'policysimulator_v1alpha_client.PolicysimulatorV1alpha', 'policysimulator_v1alpha_messages', 'https://policysimulator.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.policysimulator.v1beta', 'policysimulator_v1beta_client.PolicysimulatorV1beta', 'policysimulator_v1beta_messages', 'https://policysimulator.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'policytroubleshooter': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.policytroubleshooter.v1', 'policytroubleshooter_v1_client.PolicytroubleshooterV1', 'policytroubleshooter_v1_messages', 'https://policytroubleshooter.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.policytroubleshooter.v1beta', 'policytroubleshooter_v1beta_client.PolicytroubleshooterV1beta', 'policytroubleshooter_v1beta_messages', 'https://policytroubleshooter.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2alpha1': (
            ('googlecloudsdk.generated_clients.apis.policytroubleshooter.v2alpha1', 'policytroubleshooter_v2alpha1_client.PolicytroubleshooterV2alpha1', 'policytroubleshooter_v2alpha1_messages', 'https://policytroubleshooter.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v3': (
            ('googlecloudsdk.generated_clients.apis.policytroubleshooter.v3', 'policytroubleshooter_v3_client.PolicytroubleshooterV3', 'policytroubleshooter_v3_messages', 'https://policytroubleshooter.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v3alpha': (
            ('googlecloudsdk.generated_clients.apis.policytroubleshooter.v3alpha', 'policytroubleshooter_v3alpha_client.PolicytroubleshooterV3alpha', 'policytroubleshooter_v3alpha_messages', 'https://policytroubleshooter.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v3beta': (
            ('googlecloudsdk.generated_clients.apis.policytroubleshooter.v3beta', 'policytroubleshooter_v3beta_client.PolicytroubleshooterV3beta', 'policytroubleshooter_v3beta_messages', 'https://policytroubleshooter.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'privateca': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.privateca.v1', 'privateca_v1_client.PrivatecaV1', 'privateca_v1_messages', 'https://privateca.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'privilegedaccessmanager': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.privilegedaccessmanager.v1', 'privilegedaccessmanager_v1_client.PrivilegedaccessmanagerV1', 'privilegedaccessmanager_v1_messages', 'https://privilegedaccessmanager.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.privilegedaccessmanager.v1alpha', 'privilegedaccessmanager_v1alpha_client.PrivilegedaccessmanagerV1alpha', 'privilegedaccessmanager_v1alpha_messages', 'https://privilegedaccessmanager.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.privilegedaccessmanager.v1beta', 'privilegedaccessmanager_v1beta_client.PrivilegedaccessmanagerV1beta', 'privilegedaccessmanager_v1beta_messages', 'https://privilegedaccessmanager.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'publicca': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.publicca.v1', 'publicca_v1_client.PubliccaV1', 'publicca_v1_messages', 'https://publicca.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.publicca.v1alpha1', 'publicca_v1alpha1_client.PubliccaV1alpha1', 'publicca_v1alpha1_messages', 'https://publicca.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.publicca.v1beta1', 'publicca_v1beta1_client.PubliccaV1beta1', 'publicca_v1beta1_messages', 'https://publicca.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'pubsub': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.pubsub.v1', 'pubsub_v1_client.PubsubV1', 'pubsub_v1_messages', 'https://pubsub.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://pubsub.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://pubsub.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://pubsub.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://pubsub.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://pubsub.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://pubsub.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://pubsub.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://pubsub.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://pubsub.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://pubsub.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://pubsub.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://pubsub.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://pubsub.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://pubsub.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://pubsub.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://pubsub.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://pubsub.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://pubsub.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://pubsub.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://pubsub.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://pubsub.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://pubsub.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://pubsub.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://pubsub.europe-west9.rep.googleapis.com/', 'europe-west10': 'https://pubsub.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://pubsub.europe-west12.rep.googleapis.com/', 'me-central1': 'https://pubsub.me-central1.rep.googleapis.com/', 'me-central2': 'https://pubsub.me-central2.rep.googleapis.com/', 'me-west1': 'https://pubsub.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://pubsub.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://pubsub.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://pubsub.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://pubsub.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://pubsub.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://pubsub.us-central1.rep.googleapis.com/', 'us-central2': 'https://pubsub.us-central2.rep.googleapis.com/', 'us-east1': 'https://pubsub.us-east1.rep.googleapis.com/', 'us-east4': 'https://pubsub.us-east4.rep.googleapis.com/', 'us-east5': 'https://pubsub.us-east5.rep.googleapis.com/', 'us-east7': 'https://pubsub.us-east7.rep.googleapis.com/', 'us-south1': 'https://pubsub.us-south1.rep.googleapis.com/', 'us-west1': 'https://pubsub.us-west1.rep.googleapis.com/', 'us-west2': 'https://pubsub.us-west2.rep.googleapis.com/', 'us-west3': 'https://pubsub.us-west3.rep.googleapis.com/', 'us-west4': 'https://pubsub.us-west4.rep.googleapis.com/', 'us-west8': 'https://pubsub.us-west8.rep.googleapis.com/'},
        ),
    },
    'pubsublite': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.pubsublite.v1', 'pubsublite_v1_client.PubsubliteV1', 'pubsublite_v1_messages', 'https://pubsublite.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'recaptchaenterprise': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.recaptchaenterprise.v1', 'recaptchaenterprise_v1_client.RecaptchaenterpriseV1', 'recaptchaenterprise_v1_messages', 'https://recaptchaenterprise.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'recommender': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.recommender.v1', 'recommender_v1_client.RecommenderV1', 'recommender_v1_messages', 'https://recommender.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha2': (
            ('googlecloudsdk.generated_clients.apis.recommender.v1alpha2', 'recommender_v1alpha2_client.RecommenderV1alpha2', 'recommender_v1alpha2_messages', 'https://recommender.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.recommender.v1beta1', 'recommender_v1beta1_client.RecommenderV1beta1', 'recommender_v1beta1_messages', 'https://recommender.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'redis': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.redis.v1', 'redis_v1_client.RedisV1', 'redis_v1_messages', 'https://redis.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.redis.v1alpha1', 'redis_v1alpha1_client.RedisV1alpha1', 'redis_v1alpha1_messages', 'https://redis.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.redis.v1beta1', 'redis_v1beta1_client.RedisV1beta1', 'redis_v1beta1_messages', 'https://redis.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'remotebuildexecution': {
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.remotebuildexecution.v1alpha', 'remotebuildexecution_v1alpha_client.RemotebuildexecutionV1alpha', 'remotebuildexecution_v1alpha_messages', 'https://admin-remotebuildexecution.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'run': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.run.v1', 'run_v1_client.RunV1', 'run_v1_messages', 'https://run.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://run.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://run.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://run.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://run.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://run.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://run.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://run.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://run.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://run.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://run.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://run.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://run.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://run.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://run.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://run.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://run.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://run.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://run.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://run.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://run.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://run.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://run.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://run.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://run.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://run.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://run.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://run.europe-west9.rep.googleapis.com/', 'me-central1': 'https://run.me-central1.rep.googleapis.com/', 'me-central2': 'https://run.me-central2.rep.googleapis.com/', 'me-west1': 'https://run.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://run.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://run.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://run.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://run.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://run.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://run.us-central1.rep.googleapis.com/', 'us-central2': 'https://run.us-central2.rep.googleapis.com/', 'us-east1': 'https://run.us-east1.rep.googleapis.com/', 'us-east4': 'https://run.us-east4.rep.googleapis.com/', 'us-east5': 'https://run.us-east5.rep.googleapis.com/', 'us-east7': 'https://run.us-east7.rep.googleapis.com/', 'us-south1': 'https://run.us-south1.rep.googleapis.com/', 'us-west1': 'https://run.us-west1.rep.googleapis.com/', 'us-west2': 'https://run.us-west2.rep.googleapis.com/', 'us-west3': 'https://run.us-west3.rep.googleapis.com/', 'us-west4': 'https://run.us-west4.rep.googleapis.com/', 'us-west8': 'https://run.us-west8.rep.googleapis.com/'},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.run.v1alpha1', 'run_v1alpha1_client.RunV1alpha1', 'run_v1alpha1_messages', 'https://run.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.run.v2', 'run_v2_client.RunV2', 'run_v2_messages', 'https://run.googleapis.com/'),
            ('googlecloudsdk.generated_clients.gapic_wrappers.run.v2',),
            False,
            True,
            '',
            {'africa-south1': 'https://run.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://run.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://run.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://run.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://run.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://run.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://run.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://run.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://run.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://run.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://run.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://run.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://run.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://run.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://run.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://run.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://run.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://run.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://run.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://run.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://run.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://run.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://run.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://run.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://run.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://run.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://run.europe-west9.rep.googleapis.com/', 'me-central1': 'https://run.me-central1.rep.googleapis.com/', 'me-central2': 'https://run.me-central2.rep.googleapis.com/', 'me-west1': 'https://run.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://run.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://run.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://run.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://run.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://run.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://run.us-central1.rep.googleapis.com/', 'us-central2': 'https://run.us-central2.rep.googleapis.com/', 'us-east1': 'https://run.us-east1.rep.googleapis.com/', 'us-east4': 'https://run.us-east4.rep.googleapis.com/', 'us-east5': 'https://run.us-east5.rep.googleapis.com/', 'us-east7': 'https://run.us-east7.rep.googleapis.com/', 'us-south1': 'https://run.us-south1.rep.googleapis.com/', 'us-west1': 'https://run.us-west1.rep.googleapis.com/', 'us-west2': 'https://run.us-west2.rep.googleapis.com/', 'us-west3': 'https://run.us-west3.rep.googleapis.com/', 'us-west4': 'https://run.us-west4.rep.googleapis.com/', 'us-west8': 'https://run.us-west8.rep.googleapis.com/'},
        ),
    },
    'runapps': {
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.runapps.v1alpha1', 'runapps_v1alpha1_client.RunappsV1alpha1', 'runapps_v1alpha1_messages', 'https://runapps.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'runtimeconfig': {
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.runtimeconfig.v1beta1', 'runtimeconfig_v1beta1_client.RuntimeconfigV1beta1', 'runtimeconfig_v1beta1_messages', 'https://runtimeconfig.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'saasservicemgmt': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.saasservicemgmt.v1', 'saasservicemgmt_v1_client.SaasservicemgmtV1', 'saasservicemgmt_v1_messages', 'https://saasservicemgmt.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.saasservicemgmt.v1alpha1', 'saasservicemgmt_v1alpha1_client.SaasservicemgmtV1alpha1', 'saasservicemgmt_v1alpha1_messages', 'https://saasservicemgmt.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.saasservicemgmt.v1beta1', 'saasservicemgmt_v1beta1_client.SaasservicemgmtV1beta1', 'saasservicemgmt_v1beta1_messages', 'https://saasservicemgmt.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'sasportal': {
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.sasportal.v1alpha1', 'sasportal_v1alpha1_client.SasportalV1alpha1', 'sasportal_v1alpha1_messages', 'https://sasportal.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'sddc': {
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.sddc.v1alpha1', 'sddc_v1alpha1_client.SddcV1alpha1', 'sddc_v1alpha1_messages', 'https://sddc.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'seclm': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.seclm.v1', 'seclm_v1_client.SeclmV1', 'seclm_v1_messages', 'https://seclm.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.seclm.v1alpha', 'seclm_v1alpha_client.SeclmV1alpha', 'seclm_v1alpha_messages', 'https://seclm.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'secretmanager': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.secretmanager.v1', 'secretmanager_v1_client.SecretmanagerV1', 'secretmanager_v1_messages', 'https://secretmanager.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'me-central2': 'https://secretmanager.me-central2.rep.googleapis.com/', 'africa-south1': 'https://secretmanager.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://secretmanager.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://secretmanager.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://secretmanager.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://secretmanager.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://secretmanager.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://secretmanager.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://secretmanager.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://secretmanager.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://secretmanager.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://secretmanager.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://secretmanager.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://secretmanager.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://secretmanager.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://secretmanager.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://secretmanager.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://secretmanager.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://secretmanager.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://secretmanager.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://secretmanager.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://secretmanager.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://secretmanager.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://secretmanager.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://secretmanager.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://secretmanager.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://secretmanager.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://secretmanager.europe-west9.rep.googleapis.com/', 'me-central1': 'https://secretmanager.me-central1.rep.googleapis.com/', 'me-west1': 'https://secretmanager.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://secretmanager.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://secretmanager.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://secretmanager.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://secretmanager.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://secretmanager.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://secretmanager.us-central1.rep.googleapis.com/', 'us-central2': 'https://secretmanager.us-central2.rep.googleapis.com/', 'us-east1': 'https://secretmanager.us-east1.rep.googleapis.com/', 'us-east4': 'https://secretmanager.us-east4.rep.googleapis.com/', 'us-east5': 'https://secretmanager.us-east5.rep.googleapis.com/', 'us-east7': 'https://secretmanager.us-east7.rep.googleapis.com/', 'us-south1': 'https://secretmanager.us-south1.rep.googleapis.com/', 'us-west1': 'https://secretmanager.us-west1.rep.googleapis.com/', 'us-west2': 'https://secretmanager.us-west2.rep.googleapis.com/', 'us-west3': 'https://secretmanager.us-west3.rep.googleapis.com/', 'us-west4': 'https://secretmanager.us-west4.rep.googleapis.com/', 'us': 'https://secretmanager.us.rep.googleapis.com/', 'eu': 'https://secretmanager.eu.rep.googleapis.com/', 'ca': 'https://secretmanager.ca.rep.googleapis.com/', 'in': 'https://secretmanager.in.rep.googleapis.com/'},
        ),
        'v1beta2': (
            ('googlecloudsdk.generated_clients.apis.secretmanager.v1beta2', 'secretmanager_v1beta2_client.SecretmanagerV1beta2', 'secretmanager_v1beta2_messages', 'https://secretmanager.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'me-central2': 'https://secretmanager.me-central2.rep.googleapis.com/', 'africa-south1': 'https://secretmanager.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://secretmanager.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://secretmanager.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://secretmanager.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://secretmanager.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://secretmanager.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://secretmanager.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://secretmanager.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://secretmanager.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://secretmanager.asia-southeast2.rep.googleapis.com/', 'asia-southeast3': 'https://secretmanager.asia-southeast3.rep.googleapis.com/', 'australia-southeast1': 'https://secretmanager.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://secretmanager.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://secretmanager.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://secretmanager.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://secretmanager.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://secretmanager.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://secretmanager.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://secretmanager.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://secretmanager.europe-west12.rep.googleapis.com/', 'europe-west15': 'https://secretmanager.europe-west15.rep.googleapis.com/', 'europe-west2': 'https://secretmanager.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://secretmanager.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://secretmanager.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://secretmanager.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://secretmanager.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://secretmanager.europe-west9.rep.googleapis.com/', 'me-central1': 'https://secretmanager.me-central1.rep.googleapis.com/', 'me-west1': 'https://secretmanager.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://secretmanager.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://secretmanager.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://secretmanager.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://secretmanager.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://secretmanager.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://secretmanager.us-central1.rep.googleapis.com/', 'us-central2': 'https://secretmanager.us-central2.rep.googleapis.com/', 'us-east1': 'https://secretmanager.us-east1.rep.googleapis.com/', 'us-east4': 'https://secretmanager.us-east4.rep.googleapis.com/', 'us-east5': 'https://secretmanager.us-east5.rep.googleapis.com/', 'us-east7': 'https://secretmanager.us-east7.rep.googleapis.com/', 'us-south1': 'https://secretmanager.us-south1.rep.googleapis.com/', 'us-west1': 'https://secretmanager.us-west1.rep.googleapis.com/', 'us-west2': 'https://secretmanager.us-west2.rep.googleapis.com/', 'us-west3': 'https://secretmanager.us-west3.rep.googleapis.com/', 'us-west4': 'https://secretmanager.us-west4.rep.googleapis.com/', 'us': 'https://secretmanager.us.rep.googleapis.com/', 'eu': 'https://secretmanager.eu.rep.googleapis.com/', 'ca': 'https://secretmanager.ca.rep.googleapis.com/', 'in': 'https://secretmanager.in.rep.googleapis.com/'},
        ),
    },
    'securesourcemanager': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.securesourcemanager.v1', 'securesourcemanager_v1_client.SecuresourcemanagerV1', 'securesourcemanager_v1_messages', 'https://securesourcemanager.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'asia-east1': 'https://securesourcemanager.asia-east1.rep.googleapis.com/', 'asia-northeast1': 'https://securesourcemanager.asia-northeast1.rep.googleapis.com/', 'asia-northeast3': 'https://securesourcemanager.asia-northeast3.rep.googleapis.com/', 'australia-southeast1': 'https://securesourcemanager.australia-southeast1.rep.googleapis.com/', 'europe-west2': 'https://securesourcemanager.europe-west2.rep.googleapis.com/', 'europe-west4': 'https://securesourcemanager.europe-west4.rep.googleapis.com/', 'me-central2': 'https://securesourcemanager.me-central2.rep.googleapis.com/', 'me-west1': 'https://securesourcemanager.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://securesourcemanager.northamerica-northeast1.rep.googleapis.com/', 'us-central1': 'https://securesourcemanager.us-central1.rep.googleapis.com/', 'us-east1': 'https://securesourcemanager.us-east1.rep.googleapis.com/'},
        ),
    },
    'securitycenter': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.securitycenter.v1', 'securitycenter_v1_client.SecuritycenterV1', 'securitycenter_v1_messages', 'https://securitycenter.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'me-central2': 'https://securitycenter.me-central2.rep.googleapis.com/', 'us': 'https://securitycenter.us.rep.googleapis.com/', 'eu': 'https://securitycenter.eu.rep.googleapis.com/'},
        ),
        'v1beta2': (
            ('googlecloudsdk.generated_clients.apis.securitycenter.v1beta2', 'securitycenter_v1beta2_client.SecuritycenterV1beta2', 'securitycenter_v1beta2_messages', 'https://securitycenter.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'me-central2': 'https://securitycenter.me-central2.rep.googleapis.com/', 'us': 'https://securitycenter.us.rep.googleapis.com/', 'eu': 'https://securitycenter.eu.rep.googleapis.com/'},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.securitycenter.v2', 'securitycenter_v2_client.SecuritycenterV2', 'securitycenter_v2_messages', 'https://securitycenter.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'me-central2': 'https://securitycenter.me-central2.rep.googleapis.com/', 'us': 'https://securitycenter.us.rep.googleapis.com/', 'eu': 'https://securitycenter.eu.rep.googleapis.com/'},
        ),
    },
    'securitycentermanagement': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.securitycentermanagement.v1', 'securitycentermanagement_v1_client.SecuritycentermanagementV1', 'securitycentermanagement_v1_messages', 'https://securitycentermanagement.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'securityposture': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.securityposture.v1', 'securityposture_v1_client.SecuritypostureV1', 'securityposture_v1_messages', 'https://securityposture.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.securityposture.v1alpha', 'securityposture_v1alpha_client.SecuritypostureV1alpha', 'securityposture_v1alpha_messages', 'https://securityposture.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'serviceconsumermanagement': {
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.serviceconsumermanagement.v1beta1', 'serviceconsumermanagement_v1beta1_client.ServiceconsumermanagementV1beta1', 'serviceconsumermanagement_v1beta1_messages', 'https://serviceconsumermanagement.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'servicedirectory': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.servicedirectory.v1', 'servicedirectory_v1_client.ServicedirectoryV1', 'servicedirectory_v1_messages', 'https://servicedirectory.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.servicedirectory.v1beta1', 'servicedirectory_v1beta1_client.ServicedirectoryV1beta1', 'servicedirectory_v1beta1_messages', 'https://servicedirectory.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'servicehealth': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.servicehealth.v1', 'servicehealth_v1_client.ServicehealthV1', 'servicehealth_v1_messages', 'https://servicehealth.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.servicehealth.v1beta', 'servicehealth_v1beta_client.ServicehealthV1beta', 'servicehealth_v1beta_messages', 'https://servicehealth.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'servicemanagement': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.servicemanagement.v1', 'servicemanagement_v1_client.ServicemanagementV1', 'servicemanagement_v1_messages', 'https://servicemanagement.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'servicenetworking': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.servicenetworking.v1', 'servicenetworking_v1_client.ServicenetworkingV1', 'servicenetworking_v1_messages', 'https://servicenetworking.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.servicenetworking.v1beta', 'servicenetworking_v1beta_client.ServicenetworkingV1beta', 'servicenetworking_v1beta_messages', 'https://servicenetworking.googleapis.com/'),
            None,
            False,
            True,
            'https://servicenetworking.mtls.googleapis.com/',
            {},
        ),
    },
    'serviceusage': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.serviceusage.v1', 'serviceusage_v1_client.ServiceusageV1', 'serviceusage_v1_messages', 'https://serviceusage.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.serviceusage.v1alpha', 'serviceusage_v1alpha_client.ServiceusageV1alpha', 'serviceusage_v1alpha_messages', 'https://serviceusage.googleapis.com/'),
            None,
            False,
            True,
            'https://serviceusage.mtls.googleapis.com/',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.serviceusage.v1beta1', 'serviceusage_v1beta1_client.ServiceusageV1beta1', 'serviceusage_v1beta1_messages', 'https://serviceusage.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2alpha': (
            ('googlecloudsdk.generated_clients.apis.serviceusage.v2alpha', 'serviceusage_v2alpha_client.ServiceusageV2alpha', 'serviceusage_v2alpha_messages', 'https://serviceusage.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2beta': (
            ('googlecloudsdk.generated_clients.apis.serviceusage.v2beta', 'serviceusage_v2beta_client.ServiceusageV2beta', 'serviceusage_v2beta_messages', 'https://serviceusage.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'source': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.source.v1', 'source_v1_client.SourceV1', 'source_v1_messages', 'https://source.googleapis.com/'),
            None,
            True,
            True,
            'https://source.mtls.googleapis.com/',
            {},
        ),
    },
    'sourcerepo': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.sourcerepo.v1', 'sourcerepo_v1_client.SourcerepoV1', 'sourcerepo_v1_messages', 'https://sourcerepo.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'spanner': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.spanner.v1', 'spanner_v1_client.SpannerV1', 'spanner_v1_messages', 'https://spanner.googleapis.com/'),
            ('googlecloudsdk.generated_clients.gapic_wrappers.spanner.v1',),
            True,
            True,
            '',
            {'europe-west8': 'https://spanner.europe-west8.rep.googleapis.com/', 'me-central2': 'https://spanner.me-central2.rep.googleapis.com/', 'us-central1': 'https://spanner.us-central1.rep.googleapis.com/', 'us-central2': 'https://spanner.us-central2.rep.googleapis.com/', 'us-east1': 'https://spanner.us-east1.rep.googleapis.com/', 'us-east4': 'https://spanner.us-east4.rep.googleapis.com/', 'us-east5': 'https://spanner.us-east5.rep.googleapis.com/', 'us-south1': 'https://spanner.us-south1.rep.googleapis.com/', 'us-west1': 'https://spanner.us-west1.rep.googleapis.com/', 'us-west2': 'https://spanner.us-west2.rep.googleapis.com/', 'us-west3': 'https://spanner.us-west3.rep.googleapis.com/', 'us-west4': 'https://spanner.us-west4.rep.googleapis.com/', 'us-west8': 'https://spanner.us-west8.rep.googleapis.com/', 'us-east7': 'https://spanner.us-east7.rep.googleapis.com/'},
        ),
    },
    'speech': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.speech.v1', 'speech_v1_client.SpeechV1', 'speech_v1_messages', 'https://speech.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us-central1': 'https://speech.us-central1.rep.googleapis.com/', 'us-west1': 'https://speech.us-west1.rep.googleapis.com/', 'me-west1': 'https://speech.me-west1.rep.googleapis.com/', 'europe-west1': 'https://speech.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://speech.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://speech.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://speech.europe-west4.rep.googleapis.com/'},
        ),
        'v1p1beta1': (
            ('googlecloudsdk.generated_clients.apis.speech.v1p1beta1', 'speech_v1p1beta1_client.SpeechV1p1beta1', 'speech_v1p1beta1_messages', 'https://speech.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-central1': 'https://speech.us-central1.rep.googleapis.com/', 'us-west1': 'https://speech.us-west1.rep.googleapis.com/', 'me-west1': 'https://speech.me-west1.rep.googleapis.com/', 'europe-west1': 'https://speech.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://speech.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://speech.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://speech.europe-west4.rep.googleapis.com/'},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.speech.v2', 'speech_v2_client.SpeechV2', 'speech_v2_messages', 'https://speech.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us-central1': 'https://speech.us-central1.rep.googleapis.com/', 'us-west1': 'https://speech.us-west1.rep.googleapis.com/', 'me-west1': 'https://speech.me-west1.rep.googleapis.com/', 'europe-west1': 'https://speech.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://speech.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://speech.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://speech.europe-west4.rep.googleapis.com/'},
        ),
    },
    'sqladmin': {
        'v1beta4': (
            ('googlecloudsdk.generated_clients.apis.sqladmin.v1beta4', 'sqladmin_v1beta4_client.SqladminV1beta4', 'sqladmin_v1beta4_messages', 'https://sqladmin.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us-east7': 'https://sqladmin.us-east7.rep.googleapis.com/', 'northamerica-northeast1': 'https://sqladmin.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://sqladmin.northamerica-northeast2.rep.googleapis.com/', 'europe-north1': 'https://sqladmin.europe-north1.rep.googleapis.com/', 'us-west2': 'https://sqladmin.us-west2.rep.googleapis.com/', 'asia-east2': 'https://sqladmin.asia-east2.rep.googleapis.com/', 'europe-west3': 'https://sqladmin.europe-west3.rep.googleapis.com/', 'us-east1': 'https://sqladmin.us-east1.rep.googleapis.com/', 'asia-east1': 'https://sqladmin.asia-east1.rep.googleapis.com/', 'asia-northeast2': 'https://sqladmin.asia-northeast2.rep.googleapis.com/', 'me-central1': 'https://sqladmin.me-central1.rep.googleapis.com/', 'europe-central2': 'https://sqladmin.europe-central2.rep.googleapis.com/', 'northamerica-south1': 'https://sqladmin.northamerica-south1.rep.googleapis.com/', 'us-west8': 'https://sqladmin.us-west8.rep.googleapis.com/', 'me-west1': 'https://sqladmin.me-west1.rep.googleapis.com/', 'asia-northeast3': 'https://sqladmin.asia-northeast3.rep.googleapis.com/', 'us-west1': 'https://sqladmin.us-west1.rep.googleapis.com/', 'europe-west9': 'https://sqladmin.europe-west9.rep.googleapis.com/', 'asia-southeast3': 'https://sqladmin.asia-southeast3.rep.googleapis.com/', 'europe-west1': 'https://sqladmin.europe-west1.rep.googleapis.com/', 'asia-southeast1': 'https://sqladmin.asia-southeast1.rep.googleapis.com/', 'us-west4': 'https://sqladmin.us-west4.rep.googleapis.com/', 'europe-west12': 'https://sqladmin.europe-west12.rep.googleapis.com/', 'asia-south2': 'https://sqladmin.asia-south2.rep.googleapis.com/', 'australia-southeast1': 'https://sqladmin.australia-southeast1.rep.googleapis.com/', 'europe-west6': 'https://sqladmin.europe-west6.rep.googleapis.com/', 'us-east4': 'https://sqladmin.us-east4.rep.googleapis.com/', 'asia-southeast2': 'https://sqladmin.asia-southeast2.rep.googleapis.com/', 'europe-southwest1': 'https://sqladmin.europe-southwest1.rep.googleapis.com/', 'europe-west8': 'https://sqladmin.europe-west8.rep.googleapis.com/', 'africa-south1': 'https://sqladmin.africa-south1.rep.googleapis.com/', 'me-central2': 'https://sqladmin.me-central2.rep.googleapis.com/', 'us-central1': 'https://sqladmin.us-central1.rep.googleapis.com/', 'us-central2': 'https://sqladmin.us-central2.rep.googleapis.com/', 'europe-north2': 'https://sqladmin.europe-north2.rep.googleapis.com/', 'asia-northeast1': 'https://sqladmin.asia-northeast1.rep.googleapis.com/', 'europe-west2': 'https://sqladmin.europe-west2.rep.googleapis.com/', 'southamerica-east1': 'https://sqladmin.southamerica-east1.rep.googleapis.com/', 'us-east5': 'https://sqladmin.us-east5.rep.googleapis.com/', 'asia-south1': 'https://sqladmin.asia-south1.rep.googleapis.com/', 'europe-west4': 'https://sqladmin.europe-west4.rep.googleapis.com/', 'us-west3': 'https://sqladmin.us-west3.rep.googleapis.com/', 'australia-southeast2': 'https://sqladmin.australia-southeast2.rep.googleapis.com/', 'southamerica-west1': 'https://sqladmin.southamerica-west1.rep.googleapis.com/', 'europe-west10': 'https://sqladmin.europe-west10.rep.googleapis.com/'},
        ),
    },
    'storage': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.storage.v1', 'storage_v1_client.StorageV1', 'storage_v1_messages', 'https://storage.googleapis.com/storage/v1/'),
            None,
            True,
            True,
            '',
            {'africa-south1': 'https://storage.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://storage.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://storage.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://storage.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://storage.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://storage.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://storage.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://storage.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://storage.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://storage.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://storage.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://storage.australia-southeast2.rep.googleapis.com/', 'eu': 'https://storage.eu.rep.googleapis.com/', 'europe-central2': 'https://storage.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://storage.europe-north1.rep.googleapis.com/', 'europe-southwest1': 'https://storage.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://storage.europe-west1.rep.googleapis.com/', 'europe-west2': 'https://storage.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://storage.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://storage.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://storage.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://storage.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://storage.europe-west9.rep.googleapis.com/', 'europe-west10': 'https://storage.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://storage.europe-west12.rep.googleapis.com/', 'me-central2': 'https://storage.me-central2.rep.googleapis.com/', 'me-west1': 'https://storage.me-west1.rep.googleapis.com/', 'us': 'https://storage.us.rep.googleapis.com/', 'us-central1': 'https://storage.us-central1.rep.googleapis.com/', 'us-east1': 'https://storage.us-east1.rep.googleapis.com/', 'us-east4': 'https://storage.us-east4.rep.googleapis.com/', 'us-east5': 'https://storage.us-east5.rep.googleapis.com/', 'us-south1': 'https://storage.us-south1.rep.googleapis.com/', 'us-west1': 'https://storage.us-west1.rep.googleapis.com/', 'us-west2': 'https://storage.us-west2.rep.googleapis.com/', 'us-west3': 'https://storage.us-west3.rep.googleapis.com/', 'us-west4': 'https://storage.us-west4.rep.googleapis.com/', 'northamerica-northeast2': 'https://storage.northamerica-northeast2.rep.googleapis.com/', 'southamerica-east1': 'https://storage.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://storage.southamerica-west1.rep.googleapis.com/', 'me-central1': 'https://storage.me-central1.rep.googleapis.com/', 'northamerica-northeast1': 'https://storage.northamerica-northeast1.rep.googleapis.com/', 'europe-north2': 'https://storage.europe-north2.rep.googleapis.com/', 'us-west8': 'https://storage.us-west8.rep.googleapis.com/', 'northamerica-south1': 'https://storage.northamerica-south1.rep.googleapis.com/'},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.storage.v2', 'storage_v2_client.StorageV2', 'storage_v2_messages', 'https://storage.googleapis.com/'),
            ('googlecloudsdk.generated_clients.gapic_wrappers.storage.v2',),
            False,
            True,
            '',
            {'africa-south1': 'https://storage.africa-south1.rep.googleapis.com/', 'asia-east1': 'https://storage.asia-east1.rep.googleapis.com/', 'asia-east2': 'https://storage.asia-east2.rep.googleapis.com/', 'asia-northeast1': 'https://storage.asia-northeast1.rep.googleapis.com/', 'asia-northeast2': 'https://storage.asia-northeast2.rep.googleapis.com/', 'asia-northeast3': 'https://storage.asia-northeast3.rep.googleapis.com/', 'asia-south1': 'https://storage.asia-south1.rep.googleapis.com/', 'asia-south2': 'https://storage.asia-south2.rep.googleapis.com/', 'asia-southeast1': 'https://storage.asia-southeast1.rep.googleapis.com/', 'asia-southeast2': 'https://storage.asia-southeast2.rep.googleapis.com/', 'australia-southeast1': 'https://storage.australia-southeast1.rep.googleapis.com/', 'australia-southeast2': 'https://storage.australia-southeast2.rep.googleapis.com/', 'europe-central2': 'https://storage.europe-central2.rep.googleapis.com/', 'europe-north1': 'https://storage.europe-north1.rep.googleapis.com/', 'europe-north2': 'https://storage.europe-north2.rep.googleapis.com/', 'europe-southwest1': 'https://storage.europe-southwest1.rep.googleapis.com/', 'europe-west1': 'https://storage.europe-west1.rep.googleapis.com/', 'europe-west10': 'https://storage.europe-west10.rep.googleapis.com/', 'europe-west12': 'https://storage.europe-west12.rep.googleapis.com/', 'europe-west2': 'https://storage.europe-west2.rep.googleapis.com/', 'europe-west3': 'https://storage.europe-west3.rep.googleapis.com/', 'europe-west4': 'https://storage.europe-west4.rep.googleapis.com/', 'europe-west6': 'https://storage.europe-west6.rep.googleapis.com/', 'europe-west8': 'https://storage.europe-west8.rep.googleapis.com/', 'europe-west9': 'https://storage.europe-west9.rep.googleapis.com/', 'me-central1': 'https://storage.me-central1.rep.googleapis.com/', 'me-central2': 'https://storage.me-central2.rep.googleapis.com/', 'me-west1': 'https://storage.me-west1.rep.googleapis.com/', 'northamerica-northeast1': 'https://storage.northamerica-northeast1.rep.googleapis.com/', 'northamerica-northeast2': 'https://storage.northamerica-northeast2.rep.googleapis.com/', 'northamerica-south1': 'https://storage.northamerica-south1.rep.googleapis.com/', 'southamerica-east1': 'https://storage.southamerica-east1.rep.googleapis.com/', 'southamerica-west1': 'https://storage.southamerica-west1.rep.googleapis.com/', 'us-central1': 'https://storage.us-central1.rep.googleapis.com/', 'us-central2': 'https://storage.us-central2.rep.googleapis.com/', 'us-east1': 'https://storage.us-east1.rep.googleapis.com/', 'us-east4': 'https://storage.us-east4.rep.googleapis.com/', 'us-east5': 'https://storage.us-east5.rep.googleapis.com/', 'us-east7': 'https://storage.us-east7.rep.googleapis.com/', 'us-south1': 'https://storage.us-south1.rep.googleapis.com/', 'us-west1': 'https://storage.us-west1.rep.googleapis.com/', 'us-west2': 'https://storage.us-west2.rep.googleapis.com/', 'us-west3': 'https://storage.us-west3.rep.googleapis.com/', 'us-west4': 'https://storage.us-west4.rep.googleapis.com/', 'us-west8': 'https://storage.us-west8.rep.googleapis.com/', 'eu': 'https://storage.eu.rep.googleapis.com/', 'us': 'https://storage.us.rep.googleapis.com/'},
        ),
    },
    'storagebatchoperations': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.storagebatchoperations.v1', 'storagebatchoperations_v1_client.StoragebatchoperationsV1', 'storagebatchoperations_v1_messages', 'https://storagebatchoperations.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'storageinsights': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.storageinsights.v1', 'storageinsights_v1_client.StorageinsightsV1', 'storageinsights_v1_messages', 'https://storageinsights.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'storagetransfer': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.storagetransfer.v1', 'storagetransfer_v1_client.StoragetransferV1', 'storagetransfer_v1_messages', 'https://storagetransfer.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'stream': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.stream.v1', 'stream_v1_client.StreamV1', 'stream_v1_messages', 'https://stream.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.stream.v1alpha1', 'stream_v1alpha1_client.StreamV1alpha1', 'stream_v1alpha1_messages', 'https://stream.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'telcoautomation': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.telcoautomation.v1', 'telcoautomation_v1_client.TelcoautomationV1', 'telcoautomation_v1_messages', 'https://telcoautomation.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.telcoautomation.v1alpha1', 'telcoautomation_v1alpha1_client.TelcoautomationV1alpha1', 'telcoautomation_v1alpha1_messages', 'https://telcoautomation.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'testing': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.testing.v1', 'testing_v1_client.TestingV1', 'testing_v1_messages', 'https://testing.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'toolresults': {
        'v1beta3': (
            ('googlecloudsdk.generated_clients.apis.toolresults.v1beta3', 'toolresults_v1beta3_client.ToolresultsV1beta3', 'toolresults_v1beta3_messages', 'https://toolresults.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'tpu': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.tpu.v1', 'tpu_v1_client.TpuV1', 'tpu_v1_messages', 'https://tpu.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.tpu.v1alpha1', 'tpu_v1alpha1_client.TpuV1alpha1', 'tpu_v1alpha1_messages', 'https://tpu.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v2': (
            ('googlecloudsdk.generated_clients.apis.tpu.v2', 'tpu_v2_client.TpuV2', 'tpu_v2_messages', 'https://tpu.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v2alpha1': (
            ('googlecloudsdk.generated_clients.apis.tpu.v2alpha1', 'tpu_v2alpha1_client.TpuV2alpha1', 'tpu_v2alpha1_messages', 'https://tpu.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'transcoder': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.transcoder.v1', 'transcoder_v1_client.TranscoderV1', 'transcoder_v1_messages', 'https://transcoder.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'transferappliance': {
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.transferappliance.v1alpha1', 'transferappliance_v1alpha1_client.TransferapplianceV1alpha1', 'transferappliance_v1alpha1_messages', 'https://transferappliance.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'translate': {
        'v3': (
            ('googlecloudsdk.generated_clients.apis.translate.v3', 'translate_v3_client.TranslateV3', 'translate_v3_messages', 'https://translation.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v3beta1': (
            ('googlecloudsdk.generated_clients.apis.translate.v3beta1', 'translate_v3beta1_client.TranslateV3beta1', 'translate_v3beta1_messages', 'https://translation.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'vectorsearch': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.vectorsearch.v1', 'vectorsearch_v1_client.VectorsearchV1', 'vectorsearch_v1_messages', 'https://vectorsearch.googleapis.com/'),
            None,
            True,
            True,
            '',
            {'us': 'https://vectorsearch.us.rep.googleapis.com/'},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.vectorsearch.v1beta', 'vectorsearch_v1beta_client.VectorsearchV1beta', 'vectorsearch_v1beta_messages', 'https://vectorsearch.googleapis.com/'),
            None,
            False,
            True,
            '',
            {'us': 'https://vectorsearch.us.rep.googleapis.com/'},
        ),
    },
    'videointelligence': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.videointelligence.v1', 'videointelligence_v1_client.VideointelligenceV1', 'videointelligence_v1_messages', 'https://videointelligence.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'vision': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.vision.v1', 'vision_v1_client.VisionV1', 'vision_v1_messages', 'https://vision.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'vmmigration': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.vmmigration.v1', 'vmmigration_v1_client.VmmigrationV1', 'vmmigration_v1_messages', 'https://vmmigration.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.vmmigration.v1alpha1', 'vmmigration_v1alpha1_client.VmmigrationV1alpha1', 'vmmigration_v1alpha1_messages', 'https://vmmigration.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'vmwareengine': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.vmwareengine.v1', 'vmwareengine_v1_client.VmwareengineV1', 'vmwareengine_v1_messages', 'https://vmwareengine.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'vpcaccess': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.vpcaccess.v1', 'vpcaccess_v1_client.VpcaccessV1', 'vpcaccess_v1_messages', 'https://vpcaccess.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.vpcaccess.v1alpha1', 'vpcaccess_v1alpha1_client.VpcaccessV1alpha1', 'vpcaccess_v1alpha1_messages', 'https://vpcaccess.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta1': (
            ('googlecloudsdk.generated_clients.apis.vpcaccess.v1beta1', 'vpcaccess_v1beta1_client.VpcaccessV1beta1', 'vpcaccess_v1beta1_messages', 'https://vpcaccess.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'websecurityscanner': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.websecurityscanner.v1', 'websecurityscanner_v1_client.WebsecurityscannerV1', 'websecurityscanner_v1_messages', 'https://websecurityscanner.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.websecurityscanner.v1beta', 'websecurityscanner_v1beta_client.WebsecurityscannerV1beta', 'websecurityscanner_v1beta_messages', 'https://websecurityscanner.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
    },
    'workflowexecutions': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.workflowexecutions.v1', 'workflowexecutions_v1_client.WorkflowexecutionsV1', 'workflowexecutions_v1_messages', 'https://workflowexecutions.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.workflowexecutions.v1alpha1', 'workflowexecutions_v1alpha1_client.WorkflowexecutionsV1alpha1', 'workflowexecutions_v1alpha1_messages', 'https://workflowexecutions.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.workflowexecutions.v1beta', 'workflowexecutions_v1beta_client.WorkflowexecutionsV1beta', 'workflowexecutions_v1beta_messages', 'https://workflowexecutions.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'workflows': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.workflows.v1', 'workflows_v1_client.WorkflowsV1', 'workflows_v1_messages', 'https://workflows.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha1': (
            ('googlecloudsdk.generated_clients.apis.workflows.v1alpha1', 'workflows_v1alpha1_client.WorkflowsV1alpha1', 'workflows_v1alpha1_messages', 'https://workflows.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.workflows.v1beta', 'workflows_v1beta_client.WorkflowsV1beta', 'workflows_v1beta_messages', 'https://workflows.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'workloadidentity': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.workloadidentity.v1', 'workloadidentity_v1_client.WorkloadidentityV1', 'workloadidentity_v1_messages', 'https://workloadidentity.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1alpha': (
            ('googlecloudsdk.generated_clients.apis.workloadidentity.v1alpha', 'workloadidentity_v1alpha_client.WorkloadidentityV1alpha', 'workloadidentity_v1alpha_messages', 'https://workloadidentity.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
    'workstations': {
        'v1': (
            ('googlecloudsdk.generated_clients.apis.workstations.v1', 'workstations_v1_client.WorkstationsV1', 'workstations_v1_messages', 'https://workstations.googleapis.com/'),
            None,
            True,
            True,
            '',
            {},
        ),
        'v1beta': (
            ('googlecloudsdk.generated_clients.apis.workstations.v1beta', 'workstations_v1beta_client.WorkstationsV1beta', 'workstations_v1beta_messages', 'https://workstations.googleapis.com/'),
            None,
            False,
            True,
            '',
            {},
        ),
    },
})
