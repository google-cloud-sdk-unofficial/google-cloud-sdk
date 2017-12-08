# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for creating managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags


def _AddArgs(parser, multizonal):
  """Adds args."""
  parser.add_argument('name', help='Managed instance group name.')
  parser.add_argument(
      '--template',
      required=True,
      help=('Specifies the instance template to use when creating new '
            'instances.'))
  parser.add_argument(
      '--base-instance-name',
      help=('The base name to use for the Compute Engine instances that will '
            'be created with the managed instance group. If not provided '
            'base instance name will be the prefix of instance group name.'))
  parser.add_argument(
      '--size',
      required=True,
      help=('The initial number of instances you want in this group.'))
  parser.add_argument(
      '--description',
      help='An optional description for this group.')
  parser.add_argument(
      '--target-pool',
      type=arg_parsers.ArgList(),
      action=arg_parsers.FloatingListValuesCatcher(),
      metavar='TARGET_POOL',
      help=('Specifies any target pools you want the instances of this '
            'managed instance group to be part of.'))
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    flags.AddRegionFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='create',
        explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='create',
        explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    flags.AddZoneFlag(
        parser,
        resource_type='instance group manager',
        operation_type='create')


def _IsZonalGroup(ref):
  """Checks if reference to instance group is zonal."""
  return ref.Collection() == 'compute.instanceGroupManagers'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base_classes.BaseAsyncCreator, zone_utils.ZoneResourceFetcher,
               base_classes.InstanceGroupManagerDynamicProperiesMixin):
  """Create Google Compute Engine managed instance groups."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=False)

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateGroupReference(self, args):
    group_ref = self.CreateZonalReference(args.name, args.zone)
    self.WarnForZonalCreation([group_ref])
    return group_ref

  def GetRegionForGroup(self, group_ref):
    return utils.ZoneNameToRegionName(group_ref.zone)

  def GetServiceForGroup(self, group_ref):
    return self.compute.instanceGroupManagers

  def CreateResourceRequest(self, group_ref, instance_group_manager):
    instance_group_manager.zone = group_ref.zone
    return self.messages.ComputeInstanceGroupManagersInsertRequest(
        instanceGroupManager=instance_group_manager,
        project=self.project,
        zone=group_ref.zone)

  def ComputeDynamicProperties(self, args, items):
    return (base_classes.InstanceGroupManagerDynamicProperiesMixin
            .ComputeDynamicProperties(self, args, items))

  def CreateRequests(self, args):
    """Creates and returns an instanceGroupManagers.Insert request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      request: a singleton list containing
               ComputeManagedInstanceGroupsInsertRequest message object.
    """
    group_ref = self.CreateGroupReference(args)
    template_ref = self.CreateGlobalReference(args.template,
                                              resource_type='instanceTemplates')
    if args.target_pool:
      region = self.GetRegionForGroup(group_ref)
      pool_refs = self.CreateRegionalReferences(
          args.target_pool, region, resource_type='targetPools')
      pools = [pool_ref.SelfLink() for pool_ref in pool_refs]
    else:
      pools = []

    name = group_ref.Name()
    if args.base_instance_name:
      base_instance_name = args.base_instance_name
    else:
      base_instance_name = name[0:54]

    instance_group_manager = self.messages.InstanceGroupManager(
        name=name,
        description=args.description,
        instanceTemplate=template_ref.SelfLink(),
        baseInstanceName=base_instance_name,
        targetPools=pools,
        targetSize=int(args.size))
    auto_healing_policies = (
        managed_instance_groups_utils.CreateAutohealingPolicies(self, args))
    if auto_healing_policies:
      instance_group_manager.autoHealingPolicies = auto_healing_policies

    request = self.CreateResourceRequest(group_ref, instance_group_manager)
    service = self.GetServiceForGroup(group_ref)
    return [(service, self.method, request)]


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateBeta(CreateGA):
  """Create Google Compute Engine managed instance groups."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=True)
    managed_instance_groups_utils.AddAutohealingArgs(parser)

  def CreateGroupReference(self, args):
    group_ref = instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.name, region=args.region, zone=args.zone)
    if _IsZonalGroup(group_ref):
      self.WarnForZonalCreation([group_ref])
    return group_ref

  def GetRegionForGroup(self, group_ref):
    if _IsZonalGroup(group_ref):
      return utils.ZoneNameToRegionName(group_ref.zone)
    else:
      return group_ref.region

  def GetServiceForGroup(self, group_ref):
    if _IsZonalGroup(group_ref):
      return self.compute.instanceGroupManagers
    else:
      return self.compute.regionInstanceGroupManagers

  def CreateResourceRequest(self, group_ref, instance_group_manager):
    if _IsZonalGroup(group_ref):
      instance_group_manager.zone = group_ref.zone
      return self.messages.ComputeInstanceGroupManagersInsertRequest(
          instanceGroupManager=instance_group_manager,
          project=self.project,
          zone=group_ref.zone)
    else:
      region_link = self.CreateRegionalReference(
          group_ref.region, group_ref.region, resource_type='regions')
      instance_group_manager.region = region_link.SelfLink()
      instance_group_manager.failoverAction = (
          self.messages.InstanceGroupManager.FailoverActionValueValuesEnum
          .NO_FAILOVER)
      return self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
          instanceGroupManager=instance_group_manager,
          project=self.project,
          region=group_ref.region)


DETAILED_HELP = {
    'brief': 'Create a Compute Engine managed instance group',
    'DESCRIPTION': """\
        *{command}* creates a Google Compute Engine managed instance group.

For example, running:

        $ {command} example-managed-instance-group --zone us-central1-a --template example-instance-template --size 1

will create one managed instance group called 'example-managed-instance-group'
in the ``us-central1-a'' zone.
""",
}
CreateGA.detailed_help = DETAILED_HELP
CreateBeta.detailed_help = DETAILED_HELP
