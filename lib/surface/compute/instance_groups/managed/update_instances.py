# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for updating instances of managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.managed_instance_groups import update_instances_utils
from googlecloudsdk.core.util import times


def _AddArgs(parser):
  """Adds args."""
  parser.add_argument('--type',
                      choices={
                          'opportunistic': 'Replace instances when needed.',
                          'proactive': 'Replace instances proactively.',
                      },
                      default='proactive',
                      category=base.COMMONLY_USED_FLAGS,
                      help='Desired update type.')
  parser.add_argument('--action',
                      choices={
                          'replace': 'Replace instances by new ones',
                          'restart': 'Restart existing instances.',
                      },
                      default='replace',
                      category=base.COMMONLY_USED_FLAGS,
                      help='Desired action.')
  parser.add_argument('--max-surge',
                      type=str,
                      default='1',
                      help=('Maximum additional number of instances that '
                            'can be created during the update process. '
                            'This can be a fixed number (e.g. 5) or '
                            'a percentage of size to the managed instance '
                            'group (e.g. 10%)'))
  parser.add_argument('--max-unavailable',
                      type=str,
                      default='1',
                      help=('Maximum number of instances that can be '
                            'unavailable during the update process. '
                            'This can be a fixed number (e.g. 5) or '
                            'a percentage of size to the managed instance '
                            'group (e.g. 10%)'))
  parser.add_argument('--min-ready',
                      type=arg_parsers.Duration(lower_bound='0s'),
                      default='0s',
                      help=('Minimum time for which a newly created instance '
                            'should be ready to be considered available.'))
  parser.add_argument('--version-original',
                      type=arg_parsers.ArgDict(spec={
                          'template': str,
                          'target-size': str,
                      }),
                      category=base.COMMONLY_USED_FLAGS,
                      help=('Original instance template resource to be used. '
                            'Each version has the following format: '
                            'template=TEMPLATE,[target-size=FIXED_OR_PERCENT]'),
                      metavar='VERSION_ORIGINAL')
  parser.add_argument('--version-new',
                      type=arg_parsers.ArgDict(spec={
                          'template': str,
                          'target-size': str,
                      }),
                      category=base.COMMONLY_USED_FLAGS,
                      help=('New instance template resource to be used. '
                            'Each version has the following format: '
                            'template=TEMPLATE,[target-size=FIXED_OR_PERCENT]'),
                      metavar='VERSION_NEW')
  parser.add_argument('--force',
                      action='store_true',
                      help=('If set, accepts any original or new version '
                            'configurations without validation.'))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateInstancesAlpha(base_classes.BaseAsyncMutator):
  """Update instances of managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser)
    instance_groups_flags.ZONAL_INSTANCE_GROUP_MANAGER_ARG.AddArgument(parser)

  @property
  def method(self):
    return 'Patch'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    resource_arg = instance_groups_flags.ZONAL_INSTANCE_GROUP_MANAGER_ARG
    default_scope = flags.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(
        self.compute_client, self.project)
    igm_ref = resource_arg.ResolveAsResource(
        args, self.resources, default_scope=default_scope,
        scope_lister=scope_lister)

    update_instances_utils.ValidateUpdateInstancesArgs(args)
    update_policy_type = update_instances_utils.ParseUpdatePolicyType(
        '--type', args.type, self.messages)
    max_surge = update_instances_utils.ParseFixedOrPercent(
        '--max-surge', 'max-surge', args.max_surge, self.messages)
    max_unavailable = update_instances_utils.ParseFixedOrPercent(
        '--max-unavailable', 'max-unavailable', args.max_unavailable,
        self.messages)

    igm_info = managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, self.project, self.compute, self.http, self.batch_url)
    if args.action == 'replace':
      versions = []
      if args.version_original:
        versions.append(update_instances_utils.ParseVersion(
            '--version-original', args.version_original, self, self.messages))
      versions.append(update_instances_utils.ParseVersion(
          '--version-new', args.version_new, self, self.messages))
      managed_instance_groups_utils.ValidateVersions(
          igm_info, versions, args.force)

      igm_tags = dict((version.instanceTemplate, version.tag)
                      for version in igm_info.versions)
      for version in versions:
        version.tag = igm_tags.get(version.instanceTemplate)
      minimal_action = (self.messages.InstanceGroupManagerUpdatePolicy
                        .MinimalActionValueValuesEnum.REPLACE)
    elif args.action == 'restart' and igm_info.versions is not None:
      versions = (igm_info.versions
                  or [self.messages.InstanceGroupManagerVersion(
                      instanceTemplate=igm_info.instanceTemplate)])
      for version in versions:
        version.tag = str(times.Now(times.UTC))
      minimal_action = (self.messages.InstanceGroupManagerUpdatePolicy
                        .MinimalActionValueValuesEnum.RESTART)
    else:
      raise exceptions.InvalidArgumentException(
          '--action', 'unknown action type.')

    update_policy = self.messages.InstanceGroupManagerUpdatePolicy(
        maxSurge=max_surge,
        maxUnavailable=max_unavailable,
        minReadySec=args.min_ready,
        minimalAction=minimal_action,
        type=update_policy_type,)
    service = self.compute.instanceGroupManagers
    request = (self.messages.ComputeInstanceGroupManagersPatchRequest(
        instanceGroupManager=igm_ref.Name(),
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            instanceTemplate=None,
            updatePolicy=update_policy,
            versions=versions)),
        project=self.project,
        zone=igm_ref.zone))

    return [(service, self.method, request)]


UpdateInstancesAlpha.detailed_help = {
    'brief': 'Updates instances in a managed instance group',
    'DESCRIPTION': """\
        *{command}* updates instances in a managed instance group,
        according to the given versions and the given update policy."""
}
