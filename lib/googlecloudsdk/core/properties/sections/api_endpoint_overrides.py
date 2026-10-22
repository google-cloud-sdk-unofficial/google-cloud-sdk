# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Contains the properties for the 'api_endpoint_overrides' section."""

from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.properties.exceptions import InvalidValueError
from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import _VALID_ENDPOINT_OVERRIDE_REGEX
from googlecloudsdk.core.properties.validators import _VALID_STORAGE_GRPC_ENDPOINT_OVERRIDE_REGEX
from googlecloudsdk.generated_clients.apis import apis_map


class _SectionApiEndpointOverrides(_Section):
  """Contains the properties for the 'api-endpoint-overrides' section.

  This overrides what endpoint to use when talking to the given API.
  """

  def __init__(self):
    super(_SectionApiEndpointOverrides, self).__init__('api_endpoint_overrides')
    self.default_universe_domain = 'googleapis.com'
    try:
      active_config = named_configs.ConfigurationStore.ActiveConfig()
      active_config_properties = active_config.GetProperties()
    except Exception:  # pylint: disable=broad-except
      self._universe_domain = self.default_universe_domain
    else:
      self._universe_domain = active_config_properties.get('core', {}).get(
          'universe_domain', self.default_universe_domain
      )

    self.accessapproval = self._Add(
        'accessapproval', command='gcloud access-approval'
    )
    self.accesscontextmanager = self._Add(
        'accesscontextmanager', command='gcloud access-context-manager'
    )
    self.agentidentity = self._Add(
        'agentidentity', command='gcloud agent-identity'
    )
    self.agentregistry = self._Add(
        'agentregistry', command='gcloud agent-registry', hidden=True
    )
    self.ai = self._Add('ai', command='gcloud ai')
    self.aiplatform = self._Add('aiplatform', command='gcloud ai-platform')
    self.alloydb = self._Add('alloydb', command='gcloud alloydb', hidden=True)
    self.anthosevents = self._Add('anthosevents', command='gcloud anthos')
    self.anthospolicycontrollerstatus_pa = self._Add(
        'anthospolicycontrollerstatus_pa',
        command='gcloud container fleet policycontroller',
    )
    self.apigateway = self._Add('apigateway', command='gcloud api-gateway')
    self.apigee = self._Add('apigee', command='gcloud apigee')
    self.apihub = self._Add(
        'apihub', command='gcloud apigeeregistry', hidden=True
    )
    self.apikeys = self._Add(
        'apikeys', command='gcloud services api-keys', hidden=True
    )
    self.appengine = self._Add('appengine', command='gcloud app')
    self.apphub = self._Add('apphub', command='gcloud apphub')
    self.apptopology = self._Add('apptopology', command='gcloud app-topology')
    self.appoptimize = self._Add('appoptimize', command='gcloud app-optimize')
    self.artifactregistry = self._Add(
        'artifactregistry', command='gcloud artifacts'
    )
    self.assuredworkloads = self._Add(
        'assuredworkloads', command='gcloud assured'
    )
    self.auditmanager = self._Add(
        'auditmanager', command='gcloud audit-manager'
    )
    self.authztoolkit = self._Add(
        'authztoolkit', command='gcloud authz-toolkit', hidden=True
    )
    self.backupdr = self._Add(
        'backupdr', command='gcloud backup-dr', hidden=True
    )
    self.baremetalsolution = self._Add(
        'baremetalsolution', command='gcloud bms'
    )
    self.batch = self._Add('batch', command='gcloud batch', hidden=True)
    self.beyondcorp = self._Add('beyondcorp', hidden=True)
    self.biglake = self._Add('biglake', command='gcloud biglake', hidden=True)
    self.bigquery = self._Add('bigquery', hidden=True)
    self.bigquerymigration = self._Add('bigquerymigration', hidden=True)
    self.bigtableadmin = self._Add('bigtableadmin', command='gcloud bigtable')
    self.binaryauthorization = self._Add(
        'binaryauthorization', command='gcloud container binauthz', hidden=True
    )
    self.categorymanager = self._Add('categorymanager', hidden=True)
    self.certificatemanager = self._Add(
        'certificatemanager', command='gcloud certificate-manager'
    )
    self.cloudaicompanion = self._Add('cloudaicompanion', hidden=True)
    self.cloudapiregistry = self._Add(
        'cloudapiregistry', command='gcloud api-registry'
    )
    self.cloudasset = self._Add('cloudasset', command='gcloud asset')
    self.cloudbilling = self._Add('cloudbilling', command='gcloud billing')
    self.cloudbuild = self._Add('cloudbuild', command='gcloud builds')
    self.cloudcommerceconsumerprocurement = self._Add(
        'cloudcommerceconsumerprocurement',
        command='gcloud commerce-procurement',
    )
    self.clouddeploy = self._Add('clouddeploy', command='gcloud deploy')
    self.clouderrorreporting = self._Add(
        'clouderrorreporting', command='gcloud error-reporting'
    )
    self.cloudfunctions = self._Add(
        'cloudfunctions', command='gcloud functions'
    )
    self.cloudidentity = self._Add('cloudidentity', command='gcloud identity')
    self.cloudkms = self._Add('cloudkms', command='gcloud kms')
    self.cloudlocationfinder = self._Add(
        'cloudlocationfinder', command='gcloud cloudlocationfinder'
    )
    self.cloudnumberregistry = self._Add(
        'cloudnumberregistry', command='gcloud cloudnumberregistry', hidden=True
    )
    self.cloudquotas = self._Add(
        'cloudquotas', command='gcloud quotas', hidden=True
    )
    self.cloudresourcemanager = self._Add(
        'cloudresourcemanager', command='gcloud projects'
    )
    self.cloudresourcesearch = self._Add('cloudresourcesearch', hidden=True)
    self.cloudscheduler = self._Add(
        'cloudscheduler', command='gcloud scheduler'
    )
    self.cloudsecuritycompliance = self._Add(
        'cloudsecuritycompliance', command='gcloud compliance-manager'
    )
    self.cloudshell = self._Add(
        'cloudshell', command='gcloud cloud-shell', hidden=True
    )
    self.cloudsupport = self._Add('cloudsupport', command='gcloud support')
    self.cloudtasks = self._Add('cloudtasks', command='gcloud tasks')
    self.cloudtrace = self._Add('cloudtrace', command='gcloud trace')
    self.composer = self._Add('composer', command='gcloud composer')
    self.compute = self._Add(
        'compute',
        help_text=(
            'Overrides API endpoint for `gcloud compute` command group. '
            'For Private Service Connect usage, see '
            'https://cloud.google.com/vpc/docs/configure-private-service-connect-apis#using-endpoints'
        ),
    )
    self.configdelivery = self._Add(
        'configdelivery', command='gcloud container fleet packages', hidden=True
    )
    self.connectgateway = self._Add('connectgateway', hidden=True)
    self.container = self._Add('container', command='gcloud container')
    self.containeranalysis = self._Add('containeranalysis', hidden=True)
    self.datacatalog = self._Add('datacatalog', command='gcloud data-catalog')
    self.dataflow = self._Add('dataflow', command='gcloud dataflow')
    self.datafusion = self._Add('datafusion', command='gcloud data-fusion')
    self.datalineage = self._Add('datalineage', command='gcloud datalineage')
    self.datamigration = self._Add(
        'datamigration', command='gcloud database-migration'
    )
    self.datapol = self._Add('datapol', hidden=True)
    self.datapipelines = self._Add(
        'datapipelines', command='gcloud datapipelines'
    )
    self.dataplex = self._Add('dataplex', command='gcloud dataplex')
    self.dataproc = self._Add('dataproc', command='gcloud dataproc')
    self.dataprocgdc = self._Add('dataprocgdc', hidden=True)
    self.datastore = self._Add('datastore', command='gcloud datastore')
    self.datastream = self._Add('datastream', command='gcloud datastream')
    self.deploymentmanager = self._Add(
        'deploymentmanager', command='gcloud deployment-manager'
    )
    # TODO(b/420912196): Unhide after gcloud client releases to GA.
    self.designcenter = self._Add(
        'designcenter', command='gcloud design-center', hidden=True
    )
    self.developerconnect = self._Add(
        'developerconnect', command='gcloud developer-connect'
    )
    self.developerknowledge = self._Add(
        'developerknowledge', command='gcloud developerknowledge', hidden=True
    )
    self.devicerun = self._Add('devicerun', command='gcloud device-run')
    self.discovery = self._Add('discovery', hidden=True)
    self.dns = self._Add('dns', command='gcloud dns')
    self.domains = self._Add('domains', command='gcloud domains')
    self.edgecontainer = self._Add(
        'edgecontainer', command='gcloud edge-container'
    )
    self.edgenetwork = self._Add(
        'edgenetwork', command='gcloud edge-cloud networking', hidden=True
    )
    self.eventarc = self._Add('eventarc', command='gcloud eventarc')
    self.eventarcpublishing = self._Add(
        'eventarcpublishing', command='gcloud eventarc publish'
    )
    self.externalexposure = self._Add(
        'externalexposure', command='gcloud scc external-exposure', hidden=True
    )
    self.faultinjectiontesting = self._Add(
        'faultinjectiontesting', command='gcloud fault-injection'
    )
    self.faulttesting = self._Add(
        'faulttesting', command='gcloud fault-testing'
    )
    self.file = self._Add('file', command='gcloud filestore')
    self.firebase = self._Add(
        'firebase', command='gcloud firebase', hidden=True)
    self.firebasedataconnect = self._Add(
        'firebasedataconnect', command='gcloud firebase-data-connect'
    )
    self.firebaserules = self._Add(
        'firebaserules', command='gcloud firebaserules', hidden=True)
    self.firestore = self._Add('firestore', command='gcloud firestore')
    self.ftp = self._Add('ftp', command='gcloud storage ftp')
    self.geminicloudassist = self._Add(
        'geminicloudassist', command='gcloud geminicloudassist', hidden=True
    )
    self.gkebackup = self._Add('gkebackup', hidden=True)
    self.gkehub = self._Add('gkehub', hidden=True)
    self.gkerecommender = self._Add('gkerecommender', hidden=True)
    self.hypercomputecluster = self._Add(
        'hypercomputecluster', command='gcloud cluster-director'
    )
    self.iamconnectors = self._Add(
        'iamconnectors', command='gcloud agent-identity'
    )
    self.identitytoolkit = self._Add(
        'identitytoolkit', command='gcloud firebase auth', hidden=True)
    self.meridian = self._Add(
        'meridian', command='gcloud meridian', hidden=True)
    self.observability = self._Add(
        'observability', command='gcloud observability'
    )
    self.servicehealth = self._Add(
        'servicehealth', command='gcloud servicehealth'
    )
    self.softwaredeliverytrust = self._Add(
        'softwaredeliverytrust',
        command='gcloud software-delivery-trust',
        hidden=True,
    )
    self.transcoder = self._Add(
        'transcoder', command='gcloud transcoder', hidden=True
    )
    self.gkemulticloud = self._Add(
        'gkemulticloud',
        help_text=(
            'Overrides API endpoint for `gcloud container aws`, '
            '`gcloud container azure` and `gcloud container attached` '
            'command groups.'
        ),
    )
    # TODO(b/236427906): Unhide after gcloud client releases to GA.
    self.gkeonprem = self._Add('gkeonprem', hidden=True)
    self.healthcare = self._Add('healthcare', command='gcloud healthcare')
    self.iam = self._Add('iam', command='gcloud iam')
    self.iamcredentials = self._Add('iamcredentials', command='gcloud iam')
    self.iap = self._Add('iap', command='gcloud iap')
    self.ids = self._Add('ids', command='gcloud ids')
    self.kmsinventory = self._Add(
        'kmsinventory', command='gcloud kms inventory'
    )
    self.krmapihosting = self._Add(
        'krmapihosting', command='gcloud anthos config controller'
    )
    self.kubernetespolicy = self._Add('kubernetespolicy', hidden=True)
    self.inframanager = self._Add('config', command='gcloud infra-manager')
    self.language = self._Add('language', command='gcloud ml language')
    self.logging = self._Add('logging', command='gcloud logging')
    self.looker = self._Add('looker', command='gcloud looker')
    self.lustre = self._Add('lustre', command='gcloud lustre', hidden=True)
    self.managedidentities = self._Add(
        'managedidentities', command='gcloud active-directory'
    )
    self.managedkafka = self._Add(
        'managedkafka', command='gcloud managed-kafka', hidden=True
    )
    self.manager = self._Add('manager', hidden=True)
    self.marketplacesolutions = self._Add(
        'marketplacesolutions', command='gcloud mps'
    )
    self.mediaasset = self._Add('mediaasset', command='gcloud media')
    self.memcache = self._Add('memcache', command='gcloud memcache')
    self.memorystore = self._Add(
        'memorystore', command='gcloud memorystore', hidden=True
    )
    self.metastore = self._Add('metastore', command='gcloud metastore')
    self.ml = self._Add('ml', hidden=True)
    self.modelarmor = self._Add(
        'modelarmor', command='gcloud modelarmor', hidden=True
    )
    self.monitoring = self._Add('monitoring', command='gcloud monitoring')
    self.netapp = self._Add('netapp', command='gcloud netapp')
    self.networkconnectivity = self._Add(
        'networkconnectivity', command='gcloud network-connectivity'
    )
    self.networkmanagement = self._Add(
        'networkmanagement', command='gcloud network-management'
    )
    self.networksecurity = self._Add(
        'networksecurity', command='gcloud network-security'
    )
    self.networkservices = self._Add(
        'networkservices', command='gcloud network-services'
    )
    self.notebooks = self._Add('notebooks', command='gcloud notebooks')
    self.ondemandscanning = self._Add('ondemandscanning', hidden=True)
    self.oracledatabase = self._Add(
        'oracledatabase', command='gcloud oracle-database', hidden=True
    )
    self.orglifecycle = self._Add(
        'orglifecycle', command='gcloud orglifecycle', hidden=True
    )
    self.orgpolicy = self._Add('orgpolicy', command='gcloud org-policies')
    self.osconfig = self._Add('osconfig', hidden=True)
    self.oslogin = self._Add('oslogin', hidden=True)
    self.parallelstore = self._Add('parallelstore', hidden=True)
    self.parametermanager = self._Add(
        'parametermanager', command='gcloud parameter-manager', hidden=True
    )
    self.policyanalyzer = self._Add(
        'policyanalyzer', command='policy-intelligence'
    )
    self.policysimulator = self._Add('policysimulator', hidden=True)
    self.policytroubleshooter = self._Add('policytroubleshooter', hidden=True)
    self.privateca = self._Add('privateca', command='gcloud privateca')
    self.privilegedaccessmanager = self._Add(
        'privilegedaccessmanager', command='gcloud pam'
    )
    self.publicca = self._Add('publicca', command='gcloud publicca')
    self.pubsub = self._Add('pubsub', command='gcloud pubsub')
    self.pubsublite = self._Add('pubsublite', hidden=True)
    self.recaptcha = self._Add(
        'recaptchaenterprise', command='gcloud recaptcha'
    )
    self.recommender = self._Add('recommender', command='gcloud recommender')
    self.redis = self._Add('redis', command='gcloud redis')
    self.remotebuildexecution = self._Add('remotebuildexecution', hidden=True)
    self.replicapoolupdater = self._Add('replicapoolupdater', hidden=True)
    self.run = self._Add('run', command='gcloud run')
    self.runtimeconfig = self._Add(
        'runtimeconfig', command='gcloud runtime-config'
    )
    self.saasservicemgmt = self._Add(
        'saasservicemgmt', command='gcloud app-lifecycle-manager', hidden=True
    )
    self.sasportal = self._Add('sasportal', hidden=True)
    self.scc = self._Add('securitycenter', command='gcloud scc')
    self.sddc = self._Add('sddc', command='gcloud vmware sddc')
    self.seclm = self._Add('seclm', command='gcloud seclm', hidden=True)
    self.secrets = self._Add('secretmanager', command='gcloud secrets')
    self.securesourcemanager = self._Add('securesourcemanager', hidden=True)
    self.securitycentermanagement = self._Add(
        'securitycentermanagement', command='gcloud scc manage', hidden=True
    )
    self.securityposture = self._Add('securityposture', hidden=True)
    self.servicedirectory = self._Add(
        'servicedirectory', command='gcloud service-directory'
    )
    self.servicemanagement = self._Add(
        'servicemanagement', command='gcloud endpoints'
    )
    self.serviceregistry = self._Add('serviceregistry', hidden=True)
    self.serviceusage = self._Add('serviceusage', hidden=True)
    self.source = self._Add('source', hidden=True)
    self.sourcerepo = self._Add('sourcerepo', command='gcloud source')
    self.spanner = self._Add(
        'spanner',
        help_text=(
            'Overrides API endpoint for `gcloud spanner` command group. '
            'For spanner emulator usage, see '
            'https://cloud.google.com/spanner/docs/emulator#using_the_gcloud_cli_with_the_emulator'
        ),
    )
    self.speech = self._Add('speech', command='gcloud ml speech')
    self.sql = self._Add('sql', command='gcloud sql')
    self.storage = self._Add('storage', command='gcloud storage')
    self.storage_grpc = self._Add(
        'storage_grpc',
        help_text=(
            'Overrides gRPC API endpoint for `gcloud storage` command group.'
            'Note: This is an internal property and should not be used by '
            'external callers.'
        ),
        hidden=True,
        validator=self.StorageGrpcEndpointValidator,
    )
    self.storagebatchoperations = self._Add(
        'storagebatchoperations',
        command='gcloud storage batch-actions',
        hidden=True,
    )
    self.storageinsights = self._Add(
        'storageinsights', command='gcloud storage insights', hidden=True
    )
    self.stream = self._Add('stream', hidden=True)
    self.testing = self._Add('testing', command='gcloud firebase test')
    self.toolresults = self._Add('toolresults', hidden=True)
    self.tpu = self._Add('tpu', hidden=True)
    # Aliased to `storagetransfer` in `api_lib/apis/apis_util.py`.
    self.transfer = self._Add('transfer', command='gcloud transfer')
    self.transferappliance = self._Add(
        'transferappliance', command='gcloud transfer appliances'
    )
    self.useronboarding = self._Add(
        'useronboarding', command='gcloud onboarding'
    )
    self.vectorsearch = self._Add(
        'vectorsearch', command='gcloud vector-search'
    )
    self.vision = self._Add('vision', command='gcloud ml vision')
    self.vmmigration = self._Add('vmmigration', command='gcloud migration vms')
    self.vmwareengine = self._Add('vmwareengine', command='gcloud vmware')
    self.vpcaccess = self._Add('vpcaccess', hidden=True)
    self.workflowexecutions = self._Add(
        'workflowexecutions', command='gcloud workflows executions'
    )
    self.workflows = self._Add('workflows', command='gcloud workflows')
    self.workloadcertificate = self._Add('workloadcertificate', hidden=True)
    self.workloadidentity = self._Add('workloadidentity', hidden=True)
    self.workloadmanager = self._Add(
        'workloadmanager', command='gcloud workload-manager', hidden=True
    )
    self.workspacekeyaccess = self._Add(
        'workspacekeyaccess',
        command='gcloud workspace-key-access',
        hidden=True,
    )
    self.workstations = self._Add('workstations', command='gcloud workstations')

  def StorageGrpcEndpointValidator(self, value):
    """Checks to see if the gRPC endpoint override string is valid."""
    if value is None:
      return
    if not _VALID_STORAGE_GRPC_ENDPOINT_OVERRIDE_REGEX.match(value):
      raise InvalidValueError(
          'The endpoint_overrides property must be an absolute URI (http:// '
          "or https:// ending with '/'), a gRPC Target (dns:///, "
          'google-c2p:///), or a valid hostname:port. '
          '[{value}] is not a valid endpoint override.'.format(value=value)
      )

  def EndpointValidator(self, value):
    """Checks to see if the endpoint override string is valid."""
    if value is None:
      return
    if not _VALID_ENDPOINT_OVERRIDE_REGEX.match(value):
      raise InvalidValueError(
          'The endpoint_overrides property must be an absolute URI beginning '
          "with http:// or https:// and ending with a trailing '/'. "
          '[{value}] is not a valid endpoint override.'.format(value=value)
      )

  def _Add(
      self, name, help_text=None, hidden=False, command=None, validator=None
  ):
    if not help_text and command:
      help_text = ('Overrides API endpoint for `{}` command group.').format(
          command
      )

    default_endpoint = self.GetDefaultEndpoint(name)
    if command and default_endpoint:
      help_text = f'{help_text} Defaults to `{default_endpoint}`'

    return super(_SectionApiEndpointOverrides, self)._Add(
        name,
        help_text=help_text,
        hidden=hidden,
        validator=validator or self.EndpointValidator,
    )

  def _UniversifyHelpTextEndpoint(self, address):
    """Update a URL based on the current universe domain."""
    if (
        address is not None
        and self.default_universe_domain != self._universe_domain
    ):
      address = address.replace(
          self.default_universe_domain, self._universe_domain, 1
      )
    return address

  def GetDefaultEndpoint(self, api_name):
    """Returns the BASE_URL for the respective api and version."""
    api = apis_map.MAP.get(api_name)
    if api:
      for api_version in api:
        api_def = api.get(api_version)
        if api_def.default_version and api_def.apitools:
          return self._UniversifyHelpTextEndpoint(api_def.apitools.base_url)
