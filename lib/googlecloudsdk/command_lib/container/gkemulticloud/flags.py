# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Helpers for flags in commands working with GKE Multi-cloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import util as api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties


def _ToCamelCase(name):
  """Converts hyphen-case name to CamelCase."""
  parts = name.split('-')
  return ''.join(x.title() for x in parts)


def _InvalidValueError(value, flag, detail):
  return arg_parsers.ArgumentTypeError(
      'Invalid value [{}] for argument {}. {}'.format(value, flag, detail))


_TAINT_EFFECT_ENUM_MAPPER = arg_utils.ChoiceEnumMapper(
    '--node-taints',
    api_util.GetMessagesModule().GoogleCloudGkemulticloudV1NodeTaint
    .EffectValueValuesEnum,
    include_filter=lambda effect: 'UNSPECIFIED' not in effect)

_TAINT_FORMAT_HELP = 'Node taint is of format key=value:effect.'

_TAINT_EFFECT_HELP = 'Effect must be one of: {}.'.format(', '.join(
    [_ToCamelCase(e) for e in _TAINT_EFFECT_ENUM_MAPPER.choices]))

_REPLICAPLACEMENT_FORMAT_HELP = (
    'Replica placement is of format subnetid:zone, for example subnetid12345:1')

_LOGGING_CHOICES = [constants.SYSTEM, constants.WORKLOAD]


def AddRegion(parser):
  """Add the --location flag."""
  parser.add_argument(
      '--location', help='Anthos GKE Multi-cloud location.', required=True)


def AddPodAddressCidrBlocks(parser):
  """Adds the --pod-address-cidr-blocks flag."""
  parser.add_argument(
      '--pod-address-cidr-blocks',
      required=True,
      help=('IP address range for the pods in this cluster in CIDR '
            'notation (e.g. 10.0.0.0/8).'))


def GetPodAddressCidrBlocks(args):
  """Gets the value of --pod-address-cidr-blocks flag."""
  cidr_blocks = getattr(args, 'pod_address_cidr_blocks', None)
  return [cidr_blocks] if cidr_blocks else []


def AddServiceAddressCidrBlocks(parser):
  """Add the --service-address-cidr-blocks flag."""
  parser.add_argument(
      '--service-address-cidr-blocks',
      required=True,
      help=('IP address range for the services IPs in CIDR notation '
            '(e.g. 10.0.0.0/8).'))


def GetServiceAddressCidrBlocks(args):
  """Gets the value of --service-address-cidr-blocks flag."""
  cidr_blocks = getattr(args, 'service_address_cidr_blocks', None)
  return [cidr_blocks] if cidr_blocks else []


def AddSubnetID(parser, help_text, required=True):
  """Add the --subnet-id flag."""
  parser.add_argument(
      '--subnet-id',
      required=required,
      help='Subnet ID of an existing VNET to use for {}.'.format(help_text))


def GetSubnetID(args):
  return getattr(args, 'subnet_id', None)


def AddOutputFile(parser, help_action):
  """Add an output file argument.

  Args:
    parser: The argparse.parser to add the output file argument to.
    help_action: str, describes the action of what will be stored.
  """
  parser.add_argument(
      '--output-file', help='Path to the output file {}.'.format(help_action))


def AddValidateOnly(parser, help_action):
  """Add the --validate-only argument.

  Args:
    parser: The argparse.parser to add the argument to.
    help_action: str, describes the action that will be validated.
  """
  parser.add_argument(
      '--validate-only',
      action='store_true',
      help='Validate the {}, but don\'t actually perform it.'.format(
          help_action))


def GetValidateOnly(args):
  return getattr(args, 'validate_only', None)


def AddClusterVersion(parser, required=True):
  parser.add_argument(
      '--cluster-version',
      required=required,
      help='Kubernetes version to use for the cluster.')


def GetClusterVersion(args):
  return getattr(args, 'cluster_version', None)


def AddDescription(parser, required=False):
  parser.add_argument(
      '--description',
      required=required,
      help='Description for the cluster.')


def GetDescription(args):
  return getattr(args, 'description', None)


def AddClearDescription(parser):
  """Adds the --clear-description flag.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  parser.add_argument(
      '--clear-description',
      action='store_true',
      default=None,
      help='Clear the description for the cluster.')


def AddDescriptionForUpdate(parser):
  """Adds description related flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  group = parser.add_group('Description', mutex=True)
  AddDescription(group)
  AddClearDescription(group)


def AddAnnotations(parser, noun='cluster'):
  parser.add_argument(
      '--annotations',
      type=arg_parsers.ArgDict(min_length=1),
      metavar='ANNOTATION',
      help='Annotations for the {}.'.format(noun))


def AddClearAnnotations(parser, noun):
  """Adds flag for clearing the annotations.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flag is applicable.
  """
  parser.add_argument(
      '--clear-annotations',
      action='store_true',
      default=None,
      help='Clear the annotations for the {}.'.format(noun))


def GetAnnotations(args):
  return getattr(args, 'annotations', None) or {}


def AddAnnotationsForUpdate(parser, noun):
  """Adds annotations related flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flag is applicable.
  """
  group = parser.add_group('Annotations', mutex=True)
  AddAnnotations(group, noun)
  AddClearAnnotations(group, noun)


def AddNodeVersion(parser, required=True):
  parser.add_argument(
      '--node-version',
      required=required,
      help='Kubernetes version to use for the node pool.')


def GetNodeVersion(args):
  return getattr(args, 'node_version', None)


def AddAutoscaling(parser, required=True):
  """Adds node pool autoscaling flags.

  Args:
    parser: The argparse.parser to add the arguments to.
    required: bool, whether autoscaling flags are required.
  """

  group = parser.add_argument_group('Node pool autoscaling')
  group.add_argument(
      '--min-nodes',
      required=required,
      type=int,
      help='Minimum number of nodes in the node pool.')
  group.add_argument(
      '--max-nodes',
      required=required,
      type=int,
      help='Maximum number of nodes in the node pool.')


def GetAutoscalingParams(args):
  min_nodes = 0
  max_nodes = 0
  min_nodes = args.min_nodes
  max_nodes = args.max_nodes

  return (min_nodes, max_nodes)


def GetMinNodes(args):
  return getattr(args, 'min_nodes', None)


def GetMaxNodes(args):
  return getattr(args, 'max_nodes', None)


def AddMaxPodsPerNode(parser):
  parser.add_argument(
      '--max-pods-per-node', type=int, help='Maximum number of pods per node.')


def GetMaxPodsPerNode(args):
  return getattr(args, 'max_pods_per_node', None)


def AddAzureAvailabilityZone(parser):
  parser.add_argument(
      '--azure-availability-zone',
      help='Azure availability zone where the node pool will be created.')


def GetAzureAvailabilityZone(args):
  return getattr(args, 'azure_availability_zone', None)


def AddVMSize(parser):
  parser.add_argument(
      '--vm-size', help='Azure Virtual Machine Size (e.g. Standard_DS1_v).')


def GetVMSize(args):
  return getattr(args, 'vm_size', None)


def AddSSHPublicKey(parser, required=True):
  parser.add_argument(
      '--ssh-public-key',
      required=required,
      help='SSH public key to use for authentication.')


def GetSSHPublicKey(args):
  return getattr(args, 'ssh_public_key', None)


def AddRootVolumeSize(parser):
  parser.add_argument(
      '--root-volume-size',
      type=arg_parsers.BinarySize(
          suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB'],
          default_unit='Gi'),
      help="""
        Size of the root volume. The value must be a whole number
        followed by a size unit of ``GB'' for gigabyte, or ``TB'' for
        terabyte. If no size unit is specified, GB is assumed.
        """)


def GetRootVolumeSize(args):
  size = getattr(args, 'root_volume_size', None)
  if not size:
    return None

  # Volume sizes are currently in GB, argument is in B.
  return int(size) >> 30


def AddMainVolumeSize(parser):
  parser.add_argument(
      '--main-volume-size',
      type=arg_parsers.BinarySize(
          suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB'],
          default_unit='Gi'),
      help="""
        Size of the main volume. The value must be a whole number
        followed by a size unit of ``GB'' for gigabyte, or ``TB'' for
        terabyte. If no size unit is specified, GB is assumed.
        """)


def GetMainVolumeSize(args):
  size = getattr(args, 'main_volume_size', None)
  if not size:
    return None

  # Volume sizes are currently in GB, argument is in B.
  return int(size) >> 30


def AddTags(parser, noun):
  help_text = """\
  Applies the given tags (comma separated) on the {0}. Example:

    $ {{command}} EXAMPLE_{1} --tags=tag1=one,tag2=two
  """.format(noun,
             noun.replace(' ', '_').upper())

  parser.add_argument(
      '--tags',
      type=arg_parsers.ArgDict(min_length=1),
      metavar='TAG',
      help=help_text)


def AddClearTags(parser, noun):
  """Adds flag for clearing the tags.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flag is applicable.
  """

  parser.add_argument(
      '--clear-tags',
      action='store_true',
      default=None,
      help='Clear any tags associated with the {}\'s nodes. '.format(noun))


def AddTagsForUpdate(parser, noun):
  """Adds tags related flags for update.

  Args:
    parser: The argparse.parser to add the arguments to.
    noun: The resource type to which the flags are applicable.
  """
  group = parser.add_group('Tags', mutex=True)
  AddTags(group, noun)
  AddClearTags(group, noun)


def GetTags(args):
  return getattr(args, 'tags', None) or {}


def AddCluster(parser, help_action):
  parser.add_argument(
      '--cluster',
      required=True,
      help='Name of the cluster to {} node pools with.'.format(help_action))


def AddDatabaseEncryption(parser):
  """Adds database encryption flags.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  parser.add_argument(
      '--database-encryption-key-id',
      help=('URL the of the Azure Key Vault key (with its version) '
            'to use to encrypt / decrypt cluster secrets.'))


def GetDatabaseEncryptionKeyId(args):
  return getattr(args, 'database_encryption_key_id', None)


def AddConfigEncryption(parser):
  """Adds config encryption flags.

  Args:
    parser: The argparse.parser to add the arguments to.
  """
  parser.add_argument(
      '--config-encryption-key-id',
      help=('URL the of the Azure Key Vault key (with its version) '
            'to use to encrypt / decrypt config data.'))
  parser.add_argument(
      '--config-encryption-public-key',
      help=('RSA key of the Azure Key Vault public key to use for encrypting '
            'config data.'))


def GetConfigEncryptionKeyId(args):
  return getattr(args, 'config_encryption_key_id', None)


def GetConfigEncryptionPublicKey(args):
  return getattr(args, 'config_encryption_public_key', None)


def AddNodeLabels(parser):
  parser.add_argument(
      '--node-labels',
      type=arg_parsers.ArgDict(min_length=1),
      metavar='NODE_LABEL',
      help='Labels assigned to nodes of the node pool.')


def GetNodeLabels(args):
  return getattr(args, 'node_labels', None) or {}


def _ValidateNodeTaintFormat(taint):
  """Validates the node taint format.

  Node taint is of format key=value:effect.

  Args:
    taint: Node taint.

  Returns:
    The node taint value and effect if the format is valid.

  Raises:
    ArgumentError: If the node taint format is invalid.
  """
  strs = taint.split(':')
  if len(strs) != 2:
    raise _InvalidValueError(taint, '--node-taints', _TAINT_FORMAT_HELP)
  value, effect = strs[0], strs[1]
  return value, effect


def _ValidateNodeTaint(taint):
  """Validates the node taint.

  Node taint is of format key=value:effect. Valid values for effect include
  NoExecute, NoSchedule, PreferNoSchedule.

  Args:
    taint: Node taint.

  Returns:
    The node taint if it is valid.

  Raises:
    ArgumentError: If the node taint is invalid.
  """
  unused_value, effect = _ValidateNodeTaintFormat(taint)
  effects = [_ToCamelCase(e) for e in _TAINT_EFFECT_ENUM_MAPPER.choices]
  if effect not in effects:
    raise _InvalidValueError(effect, '--node-taints', _TAINT_EFFECT_HELP)
  return taint


def AddNodeTaints(parser):
  parser.add_argument(
      '--node-taints',
      type=arg_parsers.ArgDict(min_length=1, value_type=_ValidateNodeTaint),
      metavar='NODE_TAINT',
      help=('Taints assigned to nodes of the node pool. '
            '{} {}'.format(_TAINT_FORMAT_HELP, _TAINT_EFFECT_HELP)))


def GetNodeTaints(args):
  """Gets node taint objects from the arguments.

  Args:
    args: Arguments parsed from the command.

  Returns:
    The list of node taint objects.

  Raises:
    ArgumentError: If the node taint format is invalid.
  """
  taints = []
  taint_effect_map = {
      _ToCamelCase(e): e for e in _TAINT_EFFECT_ENUM_MAPPER.choices
  }
  node_taints = getattr(args, 'node_taints', None)
  if node_taints:
    for k, v in node_taints.items():
      value, effect = _ValidateNodeTaintFormat(v)
      effect = taint_effect_map[effect]
      effect = _TAINT_EFFECT_ENUM_MAPPER.GetEnumForChoice(effect)
      taint = api_util.GetMessagesModule().GoogleCloudGkemulticloudV1NodeTaint(
          key=k, value=value, effect=effect)
      taints.append(taint)
  return taints


def _ReplicaPlacementStrToObject(replicaplacement):
  """Converts a colon-delimited string to a GoogleCloudGkemulticloudV1ReplicaPlacement instance.

  Replica placement is of format subnetid:zone.

  Args:
    replicaplacement: Replica placement.

  Returns:
    An GoogleCloudGkemulticloudV1ReplicaPlacement instance.

  Raises:
    ArgumentError: If the Replica placement format is invalid.
  """
  strs = replicaplacement.split(':')
  if len(strs) != 2:
    raise _InvalidValueError(replicaplacement, '--replica-placements',
                             _REPLICAPLACEMENT_FORMAT_HELP)
  subnetid, zone = strs[0], strs[1]
  return api_util.GetMessagesModule(
  ).GoogleCloudGkemulticloudV1ReplicaPlacement(
      azureAvailabilityZone=zone, subnetId=subnetid)


def AddReplicaPlacements(parser):
  parser.add_argument(
      '--replica-placements',
      type=arg_parsers.ArgList(element_type=_ReplicaPlacementStrToObject),
      metavar='REPLICA_PLACEMENT',
      help=('Placement info for the control plane replicas. '
            '{}'.format(_REPLICAPLACEMENT_FORMAT_HELP)))


def GetReplicaPlacements(args):
  replica_placements = getattr(args, 'replica_placements', None)
  return replica_placements if replica_placements else []


def AddAuthProviderCmdPath(parser):
  parser.add_argument(
      '--auth-provider-cmd-path',
      hidden=True,
      help='Path to the executable for the auth provider field in kubeconfig.')


def AddProxyConfig(parser):
  """Add proxy configuration flags.

  Args:
    parser: The argparse.parser to add the arguments to.
  """

  group = parser.add_argument_group('Proxy config')
  group.add_argument(
      '--proxy-resource-group-id',
      required=True,
      help=('The ARM ID the of the resource group containing proxy keyvault.'))
  group.add_argument(
      '--proxy-secret-id',
      required=True,
      help=('The URL the of the proxy setting secret with its version.'))


def GetProxyResourceGroupId(args):
  return getattr(args, 'proxy_resource_group_id', None)


def GetProxySecretId(args):
  return getattr(args, 'proxy_secret_id', None)


def AddFleetProject(parser):
  parser.add_argument(
      '--fleet-project',
      type=arg_parsers.CustomFunctionValidator(
          project_util.ValidateProjectIdentifier,
          '--fleet-project must be a valid project ID or project number.'),
      required=True,
      help='ID or number of the Fleet host project where the cluster is registered.'
  )


def GetFleetProject(args):
  """Gets and parses the fleet project argument.

  Project ID if specified is converted to project number. The parsed fleet
  project has format projects/<project-number>.

  Args:
    args: Arguments parsed from the command.

  Returns:
    The fleet project in format projects/<project-number>
    or None if the fleet projectnot is not specified.
  """
  p = getattr(args, 'fleet_project', None)
  if not p:
    return None
  if not p.isdigit():
    return 'projects/{}'.format(project_util.GetProjectNumber(p))
  return 'projects/{}'.format(p)


def AddPrivateEndpoint(parser):
  parser.add_argument(
      '--private-endpoint',
      default=False,
      action='store_true',
      help='If set, use private VPC for authentication.')


def AddExecCredential(parser):
  parser.add_argument(
      '--exec-credential',
      default=False,
      action='store_true',
      help='If set, format access token as a Kubernetes execCredential object.')


def AddAdminUsers(parser, create=True):
  help_txt = 'Users that can perform operations as a cluster administrator.'
  if create:
    help_txt += ' If not specified, the value of property core/account is used.'
  parser.add_argument(
      '--admin-users',
      type=arg_parsers.ArgList(min_length=1),
      metavar='USER',
      help=help_txt)


def GetAdminUsers(args):
  if not hasattr(args, 'admin_users'):
    return None
  if args.admin_users:
    return args.admin_users
  # Default to core/account property if not specified.
  return [properties.VALUES.core.account.GetOrFail()]


def AddLogging(parser):
  """Adds the --logging flag."""
  help_text = """
Set the components that have logging enabled.

Examples:

  $ {command} --logging=SYSTEM
  $ {command} --logging=SYSTEM,WORKLOAD
"""
  parser.add_argument(
      '--logging',
      type=arg_parsers.ArgList(min_length=1, choices=_LOGGING_CHOICES),
      metavar='COMPONENT',
      help=help_text)


def GetLogging(args):
  """Parses and validates the value of the --logging flag.

  Args:
    args: Arguments parsed from the command.

  Returns:
    The logging config object as GoogleCloudGkemulticloudV1LoggingConfig.

  Raises:
    ArgumentError: If the value of the --logging flag is invalid.

  """
  logging = getattr(args, 'logging', None)
  if not logging:
    return None

  messages = api_util.GetMessagesModule()
  config = messages.GoogleCloudGkemulticloudV1LoggingComponentConfig()
  enum = config.EnableComponentsValueListEntryValuesEnum
  if constants.SYSTEM not in logging:
    raise _InvalidValueError(
        ','.join(logging), '--logging',
        'Must include SYSTEM logging if any logging is enabled.')
  if constants.SYSTEM in logging:
    config.enableComponents.append(enum.SYSTEM_COMPONENTS)
  if constants.WORKLOAD in logging:
    config.enableComponents.append(enum.WORKLOADS)
  return messages.GoogleCloudGkemulticloudV1LoggingConfig(
      componentConfig=config)


def AddImageType(parser):
  """Adds the --image-type flag."""
  help_text = """
Set the OS image type to use on node pool instances.

Examples:

  $ {command} --image-type=windows
  $ {command} --image-type=ubuntu
"""
  parser.add_argument('--image-type', help=help_text)


def GetImageType(args):
  return getattr(args, 'image_type', None)


def AddAzureRegion(parser):
  parser.add_argument(
      '--azure-region',
      required=True,
      help=('Azure location to deploy the cluster. '
            'Refer to your Azure subscription for available locations.'))


def GetAzureRegion(args):
  return getattr(args, 'azure_region', None)


def AddResourceGroupId(parser):
  parser.add_argument(
      '--resource-group-id',
      required=True,
      help=('ID of the Azure Resource Group '
            'to associate the cluster with.'))


def GetResourceGroupId(args):
  return getattr(args, 'resource_group_id', None)


def AddVnetId(parser):
  parser.add_argument(
      '--vnet-id',
      required=True,
      help=('ID of the Azure Virtual Network '
            'to associate with the cluster.'))


def GetVnetId(args):
  return getattr(args, 'vnet_id', None)


def AddServiceLoadBalancerSubnetId(parser):
  parser.add_argument(
      '--service-load-balancer-subnet-id',
      help=('ARM ID of the subnet where Kubernetes private service type '
            'load balancers are deployed, when the Service lacks a subnet '
            'annotation.'))


def GetServiceLoadBalancerSubnetId(args):
  return getattr(args, 'service_load_balancer_subnet_id', None)


def AddEndpointSubnetId(parser):
  parser.add_argument(
      '--endpoint-subnet-id',
      help=('ARM ID of the subnet where the control plane load balancer '
            'is deployed. When unspecified, it defaults to the control '
            'plane subnet ID.'))


def GetEndpointSubnetId(args):
  return getattr(args, 'endpoint_subnet_id', None)


def AddMonitoringConfig(parser):
  parser.add_argument(
      '--enable-managed-prometheus',
      action='store_true',
      help=('Enable managed collection for Managed Service for Prometheus.'))


def GetMonitoringConfig(args):
  """Parses and validates the value of the --enable-managed-prometheus flag.

  Args:
    args: Arguments parsed from the command.

  Returns:
    The monitoring config object as GoogleCloudGkemulticloudV1MonitoringConfig.
    None if enable_managed_prometheus is None.

  """
  prometheus = getattr(args, 'enable_managed_prometheus', None)
  if not prometheus:
    return None

  messages = api_util.GetMessagesModule()
  config = messages.GoogleCloudGkemulticloudV1ManagedPrometheusConfig()
  config.enabled = True
  return messages.GoogleCloudGkemulticloudV1MonitoringConfig(
      managedPrometheusConfig=config)

