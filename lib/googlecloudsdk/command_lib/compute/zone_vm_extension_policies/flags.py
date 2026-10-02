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
"""Flags for the compute zone vm extension policies commands."""

from typing import Any, List

from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.vm_extension_policies import flags as vm_extension_policies_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def ResolveZoneVmExtensionPolicyResource(
    args: parser_extensions.Namespace,
    holder: Any,
    policy_arg: compute_flags.ResourceArgument,
    client: Any = None,
) -> resources.Resource:
  """Resolves the zone VM extension policy resource for project, folder, or organization."""
  name = args.name or ''
  # Pass the property resolver itself rather than invoking it: Parse() only
  # falls back to the params when the name does not already supply the field,
  # so a fully qualified URI still works when compute/zone is unset.
  zone = args.zone or properties.VALUES.compute.zone.GetOrFail
  if (
      args.IsKnownAndSpecified('folder')
      or name.startswith('folders/')
      or '/folders/' in name
  ):
    folder = args.folder if args.IsKnownAndSpecified('folder') else None
    return holder.resources.Parse(
        args.name,
        params={'folder': folder, 'zone': zone},
        collection='compute.folderZoneVmExtensionPolicies',
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
        params={'organization': organization, 'zone': zone},
        collection='compute.organizationZoneVmExtensionPolicies',
    )
  scope_lister = (
      compute_flags.GetDefaultScopeLister(client) if client else None
  )
  return policy_arg.ResolveAsResource(
      args,
      holder.resources,
      scope_lister=scope_lister,
  )


def AddZoneFlag(parser: parser_arguments.ArgumentInterceptor) -> None:
  """Adds the zone flag."""
  parser.add_argument(
      '--zone',
      required=True,
      help="""
      The zone to list the extension policies from.
      """,
  )


def MakeZoneVmExtensionPolicyArg() -> compute_flags.ResourceArgument:
  return compute_flags.ResourceArgument(
      resource_name='zone vm extension policy',
      zonal_collection='compute.zoneVmExtensionPolicies',
      required=True,
      plural=False,
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
  )


def AddExtensionPolicyArgs(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds the flags for a zone VM extension policy."""
  vm_extension_policies_flags.AddExtensionPolicyArgs(
      parser, target_vms='the zone'
  )


def BuildZoneVmExtensionPolicy(
    resource_ref: resources.Resource,
    args: parser_extensions.Namespace,
    messages: Any,
) -> Any:
  """Builds the VmExtensionPolicy resource given the resource reference and args."""

  def BuildInclusionLabelsValue(inclusion_labels: str) -> List[Any]:
    return [
        messages.VmExtensionPolicyLabelSelector.InclusionLabelsValue.AdditionalProperty(
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
        messages.VmExtensionPolicy.ExtensionPoliciesValue.AdditionalProperty(
            key=extension,
            value=messages.VmExtensionPolicyExtensionPolicy(
                stringConfig=configs.get(extension),
                pinnedVersion=(args.version or {}).get(extension),
            ),
        )
        for extension in args.extensions
    ]

  return messages.VmExtensionPolicy(
      name=resource_ref.Name(),
      description=args.description,
      priority=args.priority,
      extensionPolicies=messages.VmExtensionPolicy.ExtensionPoliciesValue(
          additionalProperties=BuildExtensionPoliciesValue()
      ),
      instanceSelectors=[
          messages.VmExtensionPolicyInstanceSelector(
              labelSelector=messages.VmExtensionPolicyLabelSelector(
                  inclusionLabels=messages.VmExtensionPolicyLabelSelector.InclusionLabelsValue(
                      additionalProperties=BuildInclusionLabelsValue(
                          inclusion_label
                      )
                  ),
              )
          )
          for inclusion_label in args.inclusion_labels
      ],
  )
