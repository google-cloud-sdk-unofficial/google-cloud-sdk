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

"""Command for setting instance template of managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


def _AddArgs(parser):
  """Adds args."""
  parser.add_argument(
      '--template',
      required=True,
      help=('Compute Engine instance template resource to be used.'))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetInstanceTemplate(base_classes.BaseAsyncMutator):
  """Set an instances template of managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser)
    instance_groups_flags.ZONAL_INSTANCE_GROUP_MANAGER_ARG.AddArgument(parser)

  @property
  def method(self):
    return 'SetInstanceTemplate'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    template_ref = self.CreateGlobalReference(
        args.template, resource_type='instanceTemplates')
    igm_ref = (instance_groups_flags.ZONAL_INSTANCE_GROUP_MANAGER_ARG.
               ResolveAsResource)(
                   args, self.resources, default_scope=flags.ScopeEnum.ZONE,
                   scope_lister=flags.GetDefaultScopeLister(
                       self.compute_client, self.project))
    request = (
        self.messages.ComputeInstanceGroupManagersSetInstanceTemplateRequest(
            instanceGroupManager=igm_ref.Name(),
            instanceGroupManagersSetInstanceTemplateRequest=(
                self.messages.InstanceGroupManagersSetInstanceTemplateRequest(
                    instanceTemplate=template_ref.SelfLink(),
                )
            ),
            project=self.project,
            zone=igm_ref.zone,)
    )
    return [request]


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class SetInstanceTemplateAlpha(SetInstanceTemplate):
  """Set an instances template of managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def CreateRequests(self, args):
    igm_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.
               ResolveAsResource)(
                   args, self.resources, default_scope=flags.ScopeEnum.ZONE,
                   scope_lister=flags.GetDefaultScopeLister(
                       self.compute_client, self.project))
    template_ref = self.CreateGlobalReference(
        args.template, resource_type='instanceTemplates')

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = self.compute.instanceGroupManagers
      request = (
          self.messages.ComputeInstanceGroupManagersSetInstanceTemplateRequest(
              instanceGroupManager=igm_ref.Name(),
              instanceGroupManagersSetInstanceTemplateRequest=(
                  self.messages.InstanceGroupManagersSetInstanceTemplateRequest(
                      instanceTemplate=template_ref.SelfLink(),
                  )
              ),
              project=self.project,
              zone=igm_ref.zone,)
      )
    else:
      service = self.compute.regionInstanceGroupManagers
      request = (
          self.messages.
          ComputeRegionInstanceGroupManagersSetInstanceTemplateRequest(
              instanceGroupManager=igm_ref.Name(),
              regionInstanceGroupManagersSetTemplateRequest=(
                  self.messages.RegionInstanceGroupManagersSetTemplateRequest(
                      instanceTemplate=template_ref.SelfLink(),
                  )
              ),
              project=self.project,
              region=igm_ref.region,)
      )

    return [(service, self.method, request)]


SetInstanceTemplate.detailed_help = {
    'brief': 'Set instance template for managed instance group.',
    'DESCRIPTION': """
        *{command}* updates the instance template for an existing managed instance group.

The new template won't apply to existing instances in the group unless they are
recreated using the recreate-instances command. But the new template does apply
to all new instances added to the managed instance group.
""",
}
SetInstanceTemplateAlpha.detailed_help = SetInstanceTemplate.detailed_help
