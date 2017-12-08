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
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute import property_selector
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags as instance_groups_managed_flags
from googlecloudsdk.command_lib.compute.managed_instance_groups import update_instances_utils
from googlecloudsdk.core.util import times


def _AddArgs(parser):
  """Adds args."""
  instance_groups_managed_flags.AddTypeArg(parser)
  parser.add_argument('--action',
                      choices={
                          'replace': 'Replace instances by new ones',
                          'restart': 'Restart existing instances.',
                      },
                      default='replace',
                      category=base.COMMONLY_USED_FLAGS,
                      help='Desired action.')
  instance_groups_managed_flags.AddMaxSurgeArg(parser)
  instance_groups_managed_flags.AddMaxUnavailableArg(parser)
  instance_groups_managed_flags.AddMinReadyArg(parser)
  parser.add_argument('--version-original',
                      type=arg_parsers.ArgDict(spec={
                          'template': str,
                          'target-size': str,
                      }),
                      category=base.COMMONLY_USED_FLAGS,
                      help=('Original instance template resource to be used. '
                            'Each version has the following format: '
                            'template=TEMPLATE,[target-size=FIXED_OR_PERCENT]'))
  parser.add_argument('--version-new',
                      type=arg_parsers.ArgDict(spec={
                          'template': str,
                          'target-size': str,
                      }),
                      category=base.COMMONLY_USED_FLAGS,
                      help=('New instance template resource to be used. '
                            'Each version has the following format: '
                            'template=TEMPLATE,[target-size=FIXED_OR_PERCENT]'))
  instance_groups_managed_flags.AddForceArg(parser)


@base.Deprecate(
    is_removed=False,
    warning='This command is deprecated. Use gcloud alpha compute '
            'instance-groups managed rolling-action command group instead.')
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateInstancesAlpha(base_classes.BaseCommand):
  """Update instances of managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def Run(self, args):
    cleared_fields = []
    (service, method, request) = self.CreateRequest(args, cleared_fields)
    errors = []
    with self.compute_client.apitools_client.IncludeFields(cleared_fields):
      resources = list(request_helper.MakeRequests(
          requests=[(service, method, request)],
          http=self.http,
          batch_url=self.batch_url,
          errors=errors))
    resources = lister.ProcessResults(
        resources=resources,
        field_selector=property_selector.PropertySelector(
            properties=None,
            transformations=self.transformations))
    if errors:
      utils.RaiseToolException(errors)
    return resources

  def CreateRequest(self, args, cleared_fields):
    resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
    default_scope = compute_scope.ScopeEnum.ZONE
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
        igm_ref, self.compute_client)
    if args.action == 'replace':
      versions = []
      if args.version_original:
        versions.append(update_instances_utils.ParseVersion(
            '--version-original', args.version_original, self.resources,
            self.messages))
      versions.append(update_instances_utils.ParseVersion(
          '--version-new', args.version_new, self.resources, self.messages))
      managed_instance_groups_utils.ValidateVersions(
          igm_info, versions, args.force)

      # TODO(user): Decide what we should do when two versions have the same
      #              instance template (this can happen with canary restart
      #              performed using tags).
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
      current_time_str = str(times.Now(times.UTC))
      for i, version in enumerate(versions):
        version.tag = '%d/%s' % (i, current_time_str)
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
        type=update_policy_type)
    igm_resource = self.messages.InstanceGroupManager(
        instanceTemplate=None,
        updatePolicy=update_policy,
        versions=versions)
    if hasattr(igm_ref, 'zone'):
      service = self.compute.instanceGroupManagers
      request = (self.messages.ComputeInstanceGroupManagersPatchRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_resource,
          project=self.project,
          zone=igm_ref.zone))
    elif hasattr(igm_ref, 'region'):
      service = self.compute.regionInstanceGroupManagers
      request = (self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_resource,
          project=self.project,
          region=igm_ref.region))
    # Due to 'Patch' semantics, we have to clear either 'fixed' or 'percent'.
    # Otherwise, we'll get an error that both 'fixed' and 'percent' are set.
    if max_surge is not None:
      cleared_fields.append(
          'updatePolicy.maxSurge.fixed' if max_surge.fixed is None
          else 'updatePolicy.maxSurge.percent')
    if max_unavailable is not None:
      cleared_fields.append(
          'updatePolicy.maxUnavailable.fixed' if max_unavailable.fixed is None
          else 'updatePolicy.maxUnavailable.percent')
    return (service, 'Patch', request)


UpdateInstancesAlpha.detailed_help = {
    'brief': 'Updates instances in a managed instance group',
    'DESCRIPTION': """\
        *{command}* updates instances in a managed instance group,
        according to the given versions and the given update policy."""
}

