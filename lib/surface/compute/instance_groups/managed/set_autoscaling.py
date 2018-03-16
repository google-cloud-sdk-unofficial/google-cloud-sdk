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
"""Command for configuring autoscaling of a managed instance group."""

import json
import re

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def _IsZonalGroup(ref):
  """Checks if reference to instance group is zonal."""
  return ref.Collection() == 'compute.instanceGroupManagers'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetAutoscaling(base.Command):
  """Set autoscaling parameters of a managed instance group."""

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(
        parser=parser, queue_scaling_enabled=False)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def CreateGroupReference(self, client, resources, args):
    resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(client)
    return resource_arg.ResolveAsResource(
        args, resources, default_scope=default_scope,
        scope_lister=scope_lister)

  def GetAutoscalerServiceForGroup(self, client, group_ref):
    if _IsZonalGroup(group_ref):
      return client.apitools_client.autoscalers
    else:
      return client.apitools_client.regionAutoscalers

  def CreateAutoscalerResource(self, client, resources, igm_ref, args):
    autoscaler = managed_instance_groups_utils.AutoscalerForMigByRef(
        client, resources, igm_ref)
    autoscaler_name = getattr(autoscaler, 'name', None)
    new_one = autoscaler_name is None
    autoscaler_name = autoscaler_name or args.name
    autoscaler_resource = managed_instance_groups_utils.BuildAutoscaler(
        args, client.messages, igm_ref, autoscaler_name, autoscaler)
    return autoscaler_resource, new_one

  def ScopeRequest(self, request, igm_ref):
    if _IsZonalGroup(igm_ref):
      request.zone = igm_ref.zone
    else:
      request.region = igm_ref.region

  def _PromptToDeleteAutoscaler(
      self, client, igm_ref, existing_autoscaler_name, prompt_message):
    if not console_io.PromptContinue(message=prompt_message):
      raise exceptions.ToolException('Deletion aborted by user.')
    service = self.GetAutoscalerServiceForGroup(client, igm_ref)
    request = service.GetRequestType('Delete')(
        project=igm_ref.project,
        autoscaler=existing_autoscaler_name)
    self.ScopeRequest(request, igm_ref)
    return client.MakeRequests([(service, 'Delete', request)])

  def _InsertAutoscaler(self, client, igm_ref, autoscaler_resource):
    service = self.GetAutoscalerServiceForGroup(client, igm_ref)
    request = service.GetRequestType('Insert')(
        project=igm_ref.project,
        autoscaler=autoscaler_resource,
    )
    self.ScopeRequest(request, igm_ref)
    return client.MakeRequests([(service, 'Insert', request)])

  def _UpdateAutoscaler(self, client, igm_ref, autoscaler_resource):
    service = self.GetAutoscalerServiceForGroup(client, igm_ref)
    request = service.GetRequestType('Update')(
        project=igm_ref.project,
        autoscaler=autoscaler_resource.name,
        autoscalerResource=autoscaler_resource,
    )
    self.ScopeRequest(request, igm_ref)
    return client.MakeRequests([(service, 'Update', request)])

  def _SetAutoscalerFromFile(
      self, autoscaling_file, client, igm_ref, existing_autoscaler_name):
    with open(autoscaling_file) as f:
      new_autoscaler = json.load(f)
    if new_autoscaler is None:
      if existing_autoscaler_name is None:
        log.info('Configuration specifies no autoscaling and there is no '
                 'autoscaling configured. Nothing to do.')
        return
      else:
        return self._PromptToDeleteAutoscaler(
            client, igm_ref, existing_autoscaler_name,
            prompt_message=(
                'Configuration specifies no autoscaling configuration. '
                'Continuing will delete the existing autoscaler '
                'configuration. Do you want to continue?')
        )

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      new_autoscaler = encoding.DictToMessage(
          new_autoscaler, client.messages.Autoscaler)
    else:
      new_autoscaler = encoding.DictToMessage(
          new_autoscaler, client.messages.RegionAutoscaler)
    if existing_autoscaler_name is None:
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          new_autoscaler, igm_ref)
      return  self._InsertAutoscaler(client, igm_ref, new_autoscaler)

    if (getattr(new_autoscaler, 'name', None) and
        getattr(new_autoscaler, 'name') != existing_autoscaler_name):
      self._PromptToDeleteAutoscaler(
          client, igm_ref, existing_autoscaler_name,
          prompt_message=(
              'Configuration specifies autoscaling configuration with a '
              'different name than existing. Continuing will delete '
              'existing autoscaler and create new one with a different name. '
              'Do you want to continue?')
      )
      return  self._InsertAutoscaler(client, igm_ref, new_autoscaler)

    new_autoscaler.name = existing_autoscaler_name
    return  self._UpdateAutoscaler(client, igm_ref, new_autoscaler)

  def _PromptToAutoscaleGKENodeGroup(self, args):
    if re.match(r'^gke-.*-[0-9a-f]{1,8}-grp$', args.name):
      prompt_message = (
          'You should not use Compute Engine\'s autoscaling feature '
          'on instance groups created by Kubernetes Engine. '
          'Do you want to continue?')
      if not console_io.PromptContinue(message=prompt_message, default=False):
        raise exceptions.ToolException('Setting autoscaling aborted by user.')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    managed_instance_groups_utils.ValidateAutoscalerArgs(args)

    igm_ref = self.CreateGroupReference(client, holder.resources, args)

    # Assert that Instance Group Manager exists.
    managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, client)

    # Require confirmation if autoscaling a GKE node group.
    self._PromptToAutoscaleGKENodeGroup(args)

    autoscaler_resource, is_new = self.CreateAutoscalerResource(
        client, holder.resources, igm_ref, args)

    if is_new:
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          autoscaler_resource, igm_ref)
      return self._InsertAutoscaler(client, igm_ref, autoscaler_resource)
    return self._UpdateAutoscaler(client, igm_ref, autoscaler_resource)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SetAutoscalingBeta(SetAutoscaling):
  """Set autoscaling parameters of a managed instance group."""

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(
        parser=parser, autoscaling_file_enabled=True,
        stackdriver_metrics_flags=True)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    managed_instance_groups_utils.ValidateAutoscalerArgs(args)
    managed_instance_groups_utils.ValidateStackdriverMetricsFlags(args)
    managed_instance_groups_utils.ValidateConflictsWithAutoscalingFile(
        args,
        (managed_instance_groups_utils.
         ARGS_CONFLICTING_WITH_AUTOSCALING_FILE_BETA))
    igm_ref = self.CreateGroupReference(client, holder.resources, args)

    # Assert that Instance Group Manager exists.
    managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, client)

    autoscaler_resource, is_new = self.CreateAutoscalerResource(
        client, holder.resources, igm_ref, args)

    managed_instance_groups_utils.ValidateGeneratedAutoscalerIsValid(
        args, autoscaler_resource)

    if args.IsSpecified('autoscaling_file'):
      if is_new:
        existing_autoscaler_name = None
      else:
        existing_autoscaler_name = autoscaler_resource.name
      return self._SetAutoscalerFromFile(
          args.autoscaling_file, client, igm_ref, existing_autoscaler_name)

    if is_new:
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          autoscaler_resource, igm_ref)
      return self._InsertAutoscaler(client, igm_ref, autoscaler_resource)
    return self._UpdateAutoscaler(client, igm_ref, autoscaler_resource)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetAutoscalingAlpha(SetAutoscaling):
  """Set autoscaling parameters of a managed instance group."""

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(
        parser=parser, queue_scaling_enabled=True,
        autoscaling_file_enabled=True, stackdriver_metrics_flags=True)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    managed_instance_groups_utils.ValidateAutoscalerArgs(args)
    managed_instance_groups_utils.ValidateStackdriverMetricsFlags(args)
    managed_instance_groups_utils.ValidateConflictsWithAutoscalingFile(
        args,
        (managed_instance_groups_utils.
         ARGS_CONFLICTING_WITH_AUTOSCALING_FILE_ALPHA))
    igm_ref = self.CreateGroupReference(client, holder.resources, args)

    # Assert that Instance Group Manager exists.
    managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, client)

    autoscaler_resource, is_new = self.CreateAutoscalerResource(
        client, holder.resources, igm_ref, args)

    managed_instance_groups_utils.ValidateGeneratedAutoscalerIsValid(
        args, autoscaler_resource)

    if args.IsSpecified('autoscaling_file'):
      if is_new:
        existing_autoscaler_name = None
      else:
        existing_autoscaler_name = autoscaler_resource.name
      return self._SetAutoscalerFromFile(
          args.autoscaling_file, client, igm_ref, existing_autoscaler_name)

    if is_new:
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          autoscaler_resource, igm_ref)
      return self._InsertAutoscaler(client, igm_ref, autoscaler_resource)
    return self._UpdateAutoscaler(client, igm_ref, autoscaler_resource)

SetAutoscaling.detailed_help = {
    'brief': 'Set autoscaling parameters of a managed instance group',
    'DESCRIPTION': """\
        *{command}* sets autoscaling parameters of specified managed instance
group.

Autoscalers can use one or more policies listed below. Information on using
multiple policies can be found here: [](https://cloud.google.com/compute/docs/autoscaler/multiple-policies)
        """,
}
SetAutoscalingAlpha.detailed_help = SetAutoscaling.detailed_help
SetAutoscalingBeta.detailed_help = SetAutoscaling.detailed_help
