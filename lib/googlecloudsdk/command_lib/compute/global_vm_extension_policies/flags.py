# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Flags for the compute global vm extension policies commands."""

import textwrap
from typing import Any, List, Optional

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.vm_extension_policies import flags as vm_extension_policies_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import resources


def ResolveGlobalVmExtensionPolicyResource(
    args: parser_extensions.Namespace,
    holder: Any,
    policy_arg: compute_flags.ResourceArgument,
    client: Any = None,
) -> resources.Resource:
  """Resolves the global VM extension policy resource for project, folder, or organization."""
  name = args.name or ''
  if (
      args.IsKnownAndSpecified('folder')
      or name.startswith('folders/')
      or '/folders/' in name
  ):
    folder = args.folder if args.IsKnownAndSpecified('folder') else None
    return holder.resources.Parse(
        args.name,
        params={'folder': folder},
        collection='compute.folderGlobalVmExtensionPolicies',
    )
  if (
      args.IsKnownAndSpecified('organization')
      or name.startswith('organizations/')
      or '/organizations/' in name
  ):
    organization = (
        args.organization if args.IsKnownAndSpecified('organization') else None
    )
    return holder.resources.Parse(
        args.name,
        params={'organization': organization},
        collection='compute.organizationGlobalVmExtensionPolicies',
    )
  scope_lister = (
      compute_flags.GetDefaultScopeLister(client) if client else None
  )
  return policy_arg.ResolveAsResource(
      args,
      holder.resources,
      scope_lister=scope_lister,
  )


def AddRolloutPredefinedPlan(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds the --rollout-predefined-plan flag."""
  parser.add_argument(
      '--rollout-predefined-plan',
      choices=[
          'fast_rollout',
          'slow_rollout'
      ],
      default=None,
      action=arg_parsers.StoreOnceAction,
      required=False,
      help=textwrap.dedent("""\
      Provide the name of a predefined rollout plan from
      [fast_rollout, slow_rollout] to be used for the rollout.

      One of either --rollout-predefined-plan or --rollout-custom-plan must be specified,
      but not both.
      """),
  )


def AddRolloutCustomPlan(parser: parser_arguments.ArgumentInterceptor) -> None:
  """Adds the --rollout-custom-plan flag."""
  parser.add_argument(
      '--rollout-custom-plan',
      default='',
      action=arg_parsers.StoreOnceAction,
      required=False,
      help=textwrap.dedent("""\
      Provide the name of a custom rollout plan to be used for the rollout.

      One of either --rollout-predefined-plan or --rollout-custom-plan must be specified,
      but not both.
      """),
  )


def AddRolloutConflictBehavior(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds the --rollout-conflict-behavior flag."""
  parser.add_argument(
      '--rollout-conflict-behavior',
      default='',
      action=arg_parsers.StoreOnceAction,
      required=False,
      help=textwrap.dedent("""\
      Specifies the behavior of a rollout if a conflict is detected between
      a zonal policy and a global policy. See gcloud compute
      zone-vm-extension-policies for more details on zonal policies.

      The possible values are:
      * `""`: The zonal policy value is used in case of a conflict. This is the default behavior.
      * `overwrite`: The global policy overwrites the zonal policy.

      If you set `--rollout-conflict-behavior` to `overwrite` and want to revert to the default behavior,
      use the update command and omit the `--rollout-conflict-behavior`
      flag.
      """),
  )


def AddRolloutRetryUUID(parser: parser_arguments.ArgumentInterceptor) -> None:
  """Adds the --rollout-retry-uuid flag."""
  parser.add_argument(
      '--rollout-retry-uuid',
      default='',
      action=arg_parsers.StoreOnceAction,
      required=False,
      help=textwrap.dedent("""\
      The UUID of the rollout retry action. Only set it if this is a retry
      for an existing resource.
      """),
  )


def MakeGlobalVmExtensionPolicyArg() -> compute_flags.ResourceArgument:
  return compute_flags.ResourceArgument(
      resource_name='global vm extension policy',
      global_collection='compute.globalVmExtensionPolicies',
      required=True,
      plural=False,
  )


def AddExtensionPolicyArgs(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds the flags for a global VM extension policy."""
  vm_extension_policies_flags.AddExtensionPolicyArgs(
      parser, target_vms='the project/folder'
  )
  AddRolloutPlanArgs(parser)


def AddRolloutPlanArgs(parser: parser_arguments.ArgumentInterceptor) -> None:
  """Adds the flags for a rollout plan."""
  AddRolloutPredefinedPlan(parser)
  AddRolloutCustomPlan(parser)


def ParseRolloutPlan(
    rollout_predefined_plan: Optional[str], rollout_custom_plan: Optional[str]
) -> None:
  """Parses the rollout plan."""
  if rollout_predefined_plan and rollout_custom_plan:
    raise exceptions.BadArgumentException(
        '--rollout-predefined-plan and --rollout-custom-plan',
        'Only one of --rollout-predefined-plan and --rollout-custom-plan can be'
        ' specified.',
    )
  if not rollout_predefined_plan and not rollout_custom_plan:
    raise exceptions.BadArgumentException(
        '--rollout-predefined-plan and --rollout-custom-plan',
        'One of --rollout-predefined-plan and --rollout-custom-plan'
        ' must be specified.',
    )


def InsertRetryUuid(
    args: parser_extensions.Namespace,
    policy: Optional[Any] = None,
    rollout_operation_input: Optional[Any] = None,
) -> None:
  """Inserts the retry UUID into the resource if it exists."""
  # This function is used by Update and Delete. The Update command uses a
  # policy resource, and the Delete command uses a rollout_operation_input
  # resource.
  if policy and rollout_operation_input:
    raise exceptions.BadArgumentException(
        '--rollout-retry-uuid',
        'Only one of policy and rollout_operation_input can be set.',
    )
  if args.rollout_retry_uuid:
    if policy:
      policy.rolloutOperation.rolloutInput.retryUuid = (
          args.rollout_retry_uuid
      )
    elif rollout_operation_input:
      rollout_operation_input.retryUuid = args.rollout_retry_uuid


def BuildRolloutOperationInput(
    args: parser_extensions.Namespace, messages: Any
) -> Any:
  """Builds the RolloutOperation input resource given the resource reference and args."""

  ParseRolloutPlan(args.rollout_predefined_plan, args.rollout_custom_plan)
  rollout_predefined_plan = None
  if args.rollout_predefined_plan:
    rollout_predefined_plan = messages.GlobalVmExtensionPolicyRolloutOperationRolloutInput.PredefinedRolloutPlanValueValuesEnum(
        args.rollout_predefined_plan.upper()
    )

  conflict_behavior = (
      args.rollout_conflict_behavior
      if args.IsKnownAndSpecified('rollout_conflict_behavior')
      else None
  )
  return messages.GlobalVmExtensionPolicyRolloutOperationRolloutInput(
      predefinedRolloutPlan=rollout_predefined_plan,
      name=args.rollout_custom_plan or None,
      conflictBehavior=conflict_behavior or None,
  )


def BuildGlobalVmExtensionPolicy(
    resource_ref: resources.Resource,
    args: parser_extensions.Namespace,
    messages: Any,
) -> Any:
  """Builds the VmExtensionPolicy resource given the resource reference and args."""

  def BuildInclusionLabelsValue(inclusion_labels: str) -> List[Any]:
    return [
        messages.GlobalVmExtensionPolicyLabelSelector.InclusionLabelsValue.AdditionalProperty(
            key=key,
            value=value,
        )
        for key, value in (
            labels_util.ValidateAndParseLabels(inclusion_labels.split(','))
            or {}
        ).items()
    ]

  def BuildExtensionPoliciesValue() -> List[Any]:
    configs = vm_extension_policies_flags.GetConfigs(args)
    return [
        messages.GlobalVmExtensionPolicy.ExtensionPoliciesValue.AdditionalProperty(
            key=extension,
            value=messages.GlobalVmExtensionPolicyExtensionPolicy(
                stringConfig=configs.get(extension),
                pinnedVersion=(args.version or {}).get(extension),
            ),
        )
        for extension in args.extensions
    ]

  vm_extension_policies_flags.ParseExtensionConfigs(
      args.extensions, args.config, args.config_from_file
  )
  vm_extension_policies_flags.ParseExtensionVersions(
      args.extensions, args.version
  )

  return messages.GlobalVmExtensionPolicy(
      name=resource_ref.Name(),
      description=args.description,
      priority=args.priority,
      extensionPolicies=messages.GlobalVmExtensionPolicy.ExtensionPoliciesValue(
          additionalProperties=BuildExtensionPoliciesValue()
      ),
      instanceSelectors=[
          messages.GlobalVmExtensionPolicyInstanceSelector(
              labelSelector=messages.GlobalVmExtensionPolicyLabelSelector(
                  inclusionLabels=messages.GlobalVmExtensionPolicyLabelSelector.InclusionLabelsValue(
                      additionalProperties=BuildInclusionLabelsValue(
                          inclusion_label
                      )
                  ),
              )
          )
          for inclusion_label in args.inclusion_labels
      ],
      rolloutOperation=messages.GlobalVmExtensionPolicyRolloutOperation(
          rolloutInput=BuildRolloutOperationInput(args, messages)
      ),
  )
