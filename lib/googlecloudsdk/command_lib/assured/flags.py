# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the Assured related commands."""


from typing import Any, Optional
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.assured import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def AddListWorkloadsFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds list workloads flags to the given parser."""
  parser.add_argument(
      '--location',
      required=True,
      help=(
          'The location of the Assured Workloads environments. For a '
          'current list of supported LOCATION values, see '
          '[Assured Workloads locations]'
          '(https://cloud.google.com/assured-workloads/docs/locations).'
      ),
  )
  parser.add_argument(
      '--organization',
      required=True,
      help=(
          'The parent organization of the Assured Workloads environments, '
          'provided as an organization ID.'
      ),
  )


def AddListOperationsFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds list operations flags to the given parser."""
  parser.add_argument(
      '--location',
      required=True,
      help=(
          'The location of the Assured Workloads operations. For a '
          'current list of supported LOCATION values, see '
          '[Assured Workloads locations]'
          '(https://cloud.google.com/assured-workloads/docs/locations).'
      ),
  )
  parser.add_argument(
      '--organization',
      required=True,
      help=(
          'The parent organization of the Assured Workloads operations, '
          'provided as an organization ID.'
      ),
  )


def AddCreateWorkloadFlags(
    parser: parser_arguments.ArgumentInterceptor,
    release_track: calliope_base.ReleaseTrack,
) -> None:
  """Adds required flags to the assured workloads create command.

  Args:
    parser: Parser, Parser used to construct the command flags.
    release_track: ReleaseTrack, Release track of the command being called.

  Returns:
    None.
  """
  parser.add_argument(
      '--location',
      required=True,
      help=(
          'The location of the new Assured Workloads environment. For a '
          'current list of supported LOCATION values, see '
          '[Assured Workloads locations]'
          '(https://cloud.google.com/assured-workloads/docs/locations).'
      ),
  )
  parser.add_argument(
      '--organization',
      required=True,
      help=(
          'The parent organization of the new Assured Workloads environment, '
          'provided as an organization ID'
      ),
  )
  parser.add_argument(
      '--external-identifier',
      help='The external identifier of the new Assured Workloads environment',
  )
  parser.add_argument(
      '--display-name',
      required=False,
      help='The display name of the new Assured Workloads environment',
  )
  arg_utils.ChoiceEnumMapper(
      '--compliance-regime',
      message_util.GetComplianceRegimesEnum(release_track),
      include_filter=lambda regime: regime != 'COMPLIANCE_REGIME_UNSPECIFIED',
      required=False,
      help_str='The compliance regime of the new Assured Workloads environment',
  ).choice_arg.AddToParser(parser)
  arg_utils.ChoiceEnumMapper(
      '--partner',
      message_util.GetPartnersEnum(release_track),
      include_filter=lambda regime: regime != 'PARTNER_UNSPECIFIED',
      help_str=(
          'The partner choice when creating a workload managed by local trusted'
          ' partners.'
      ),
  ).choice_arg.AddToParser(parser)
  parser.add_argument(
      '--partner-permissions',
      type=arg_parsers.ArgDict(
          spec={
              'data-logs-viewer': bool,
          }
      ),
      metavar='KEY=VALUE',
      help=(
          'The partner permissions for the partner regime, for example,'
          ' data-logs-viewer=true/false'
      ),
  )
  parser.add_argument(
      '--partner-services-billing-account',
      required=False,
      help=(
          'Billing account necessary for purchasing services from Sovereign'
          ' Partners. This field is required for creating SIA/PSN/CNTXT'
          ' partner workloads. The caller should have'
          " 'billing.resourceAssociations.create' IAM permission on this"
          ' billing-account. The format of this string is'
          ' billingAccounts/AAAAAA-BBBBBB-CCCCCC'
      ),
  )
  parser.add_argument(
      '--billing-account',
      required=False,
      help=(
          'The billing account of the new Assured Workloads environment, for '
          'example, billingAccounts/0000AA-AAA00A-A0A0A0'
      ),
  )
  parser.add_argument(
      '--next-rotation-time',
      help=(
          'The next rotation time of the KMS settings of new Assured '
          'Workloads environment, for example, 2020-12-30T10:15:30.00Z'
      ),
  )
  parser.add_argument(
      '--rotation-period',
      help=(
          'The rotation period of the KMS settings of the new Assured '
          'Workloads environment, for example, 172800s'
      ),
  )
  parser.add_argument(
      '--labels',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE',
      help=(
          'The labels of the new Assured Workloads environment, for example, '
          'LabelKey1=LabelValue1,LabelKey2=LabelValue2'
      ),
  )
  parser.add_argument(
      '--provisioned-resources-parent',
      help=(
          'The parent of the provisioned projects, for example, '
          'folders/{FOLDER_ID}'
      ),
  )
  parser.add_argument(
      '--enable-sovereign-controls',
      type=bool,
      default=False,
      help=(
          'If true, enable sovereign controls for the new Assured Workloads '
          'environment, currently only supported by EU_REGIONS_AND_SUPPORT'
      ),
  )
  _AddResourceSettingsFlag(parser, release_track)


def _AddResourceSettingsFlag(
    parser: parser_arguments.ArgumentInterceptor,
    release_track: calliope_base.ReleaseTrack,
) -> None:
  """Adds the resource settings flag to the assured workloads create command.

  Args:
    parser: Parser, Parser used to construct the command flags.
    release_track: ReleaseTrack, Release track of the command being called.

  Returns:
    None.
  """
  if release_track == calliope_base.ReleaseTrack.GA:
    parser.add_argument(
        '--resource-settings',
        type=arg_parsers.ArgDict(
            spec={
                'consumer-project-id': str,
                'consumer-project-name': str,
                'encryption-keys-project-id': str,
                'encryption-keys-project-name': str,
                'keyring-id': str,
            }
        ),
        metavar='KEY=VALUE',
        help=(
            'A comma-separated, key=value map of custom resource settings such'
            ' as custom project ids, for example:'
            ' consumer-project-id={CONSUMER_PROJECT_ID} Note: Currently only'
            ' consumer-project-id, consumer-project-name,'
            ' encryption-keys-project-id, encryption-keys-project-name and'
            ' keyring-id are supported. The encryption-keys-project-id,'
            ' encryption-keys-project-name and keyring-id settings can be'
            ' specified only if KMS settings are provided'
        ),
    )
  else:
    parser.add_argument(
        '--resource-settings',
        type=arg_parsers.ArgDict(
            spec={
                'encryption-keys-project-id': str,
                'encryption-keys-project-name': str,
                'keyring-id': str,
            }
        ),
        metavar='KEY=VALUE',
        help=(
            'A comma-separated, key=value map of custom resource settings such'
            ' as custom project ids, for example:'
            ' consumer-project-id={CONSUMER_PROJECT_ID} Note: Currently only'
            ' encryption-keys-project-id, encryption-keys-project-name and'
            ' keyring-id are supported. The encryption-keys-project-id,'
            ' encryption-keys-project-name and keyring-id settings can be'
            ' specified only if KMS settings are provided'
        ),
    )


def AddDeleteWorkloadFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  AddWorkloadResourceArgToParser(parser, verb='delete')
  parser.add_argument(
      '--etag',
      help=(
          'The etag acquired by reading the Assured Workloads environment or '
          'AW "resource".'
      ),
  )


def AddDeleteWorkloadV2Flags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds flags to the assured v2 workloads delete command."""
  AddWorkloadResourceArgToParser(parser, verb='delete')
  parser.add_argument(
      '--etag',
      help='The etag acquired by reading the Assured Workloads environment.',
  )
  calliope_base.ASYNC_FLAG.AddToParser(parser)


def AddDescribeWorkloadFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  AddWorkloadResourceArgToParser(parser, verb='describe')


def AddDescribeViolationFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  AddViolationResourceArgToParser(parser, verb='describe')


def AddEnableResourceMonitoringFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  AddWorkloadResourceArgToParser(parser, verb='enable-resource-monitoring')


def AddUpdateWorkloadFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Method to add update workload flags."""
  AddWorkloadResourceArgToParser(parser, verb='update')
  parser.add_argument(
      '--etag',
      help=(
          'The etag acquired by reading the Assured Workloads environment '
          'before updating.'
      ),
  )
  updatable_fields = parser.add_group(
      category='V1 UPDATE FLAGS',
      required=True,
      help='Settings that can be updated on the Assured Workloads environment.',
  )
  updatable_fields.add_argument(
      '--display-name',
      help='The new display name of the Assured Workloads environment.',
  )
  updatable_fields.add_argument(
      '--violation-notifications-enabled',
      help='The notification setting of the Assured Workloads environment.',
  )
  updatable_fields.add_argument(
      '--labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=(
          'The new labels of the Assured Workloads environment, for example, '
          'LabelKey1=LabelValue1,LabelKey2=LabelValue2'
      ),
  )


def AddDescribeOperationFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  concept_parsers.ConceptParser.ForResource(
      'operation',
      resource_args.GetOperationResourceSpec(),
      'The Assured Workloads operation resource to describe.',
      required=True,
  ).AddToParser(parser)


def AddWorkloadResourceArgToParser(
    parser: parser_arguments.ArgumentInterceptor, verb: str
) -> None:
  concept_parsers.ConceptParser.ForResource(
      'workload',
      resource_args.GetWorkloadResourceSpec(),
      'The Assured Workloads environment resource to {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddViolationResourceArgToParser(
    parser: parser_arguments.ArgumentInterceptor, verb: str
) -> None:
  concept_parsers.ConceptParser.ForResource(
      'violation',
      resource_args.GetViolationResourceSpec(),
      'The Assured Workloads violation resource to {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddListViolationsFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Method to add list violations flags."""
  AddListWorkloadsFlags(parser)
  parser.add_argument(
      '--workload',
      required=True,
      help=(
          'The parent workload of the Assured Workloads violations, '
          'provided as workload ID.'
      ),
  )


def AddAcknowledgeViolationsFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Method to add acknowledge violations flags."""
  AddViolationResourceArgToParser(parser, verb='acknowledge')
  parser.add_argument(
      '--comment',
      required=True,
      help='Business justification used added to acknowledge a violation.',
  )
  parser.add_argument(
      '--acknowledge-type',
      help="""the acknowledge type for specified violation, which is one of:
      SINGLE_VIOLATION - to acknowledge specified violation,
      EXISTING_CHILD_RESOURCE_VIOLATIONS - to acknowledge specified org policy
      violation and all associated child resource violations.""",
  )


def AddCreateWorkloadV2Flags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds flags to the assured workloads create command for V2 (ALPHA/BETA)."""
  id_group = parser.add_mutually_exclusive_group()
  id_group.add_argument(
      'workload_id',
      nargs='?',
      default=None,
      help=(
          'User-assigned unique identifier for the workload. If omitted, '
          'generated by the server.'
      ),
  )
  id_group.add_argument(
      '--workload-id',
      dest='flag_workload_id',
      help='User-assigned unique identifier for the workload.',
  )
  id_group.add_argument(
      '--external-identifier',
      dest='external_identifier',
      help='Backwards-compatible alias for --workload-id.',
  )
  parser.add_argument(
      '--location',
      required=True,
      help=(
          'The location of the Assured Workloads environment. For a '
          'current list of supported LOCATION values, see '
          '[Assured Workloads locations]'
          '(https://cloud.google.com/assured-workloads/docs/locations).'
      ),
  )
  parser.add_argument(
      '--organization',
      required=True,
      help=(
          'The parent organization of the Assured Workloads environment, '
          'provided as an organization ID.'
      ),
  )
  parser.add_argument(
      '--description',
      help='User-friendly description for the workload.',
  )

  target_group = parser.add_mutually_exclusive_group(required=True)
  target_group.add_argument(
      '--target-project',
      help=(
          'Existing Project ID or project number to onboard into Assured'
          ' Workloads.'
      ),
  )
  target_group.add_argument(
      '--target-folder',
      help='Existing Folder ID to onboard into Assured Workloads.',
  )
  target_group.add_argument(
      '--new-project-config',
      type=arg_parsers.ArgDict(
          spec={
              'parent': str,
              'display_name': str,
              'billing_account': str,
          }
      ),
      metavar='PROPERTY=VALUE',
      help='JSON/YAML specification for provisioning a new project.',
  )
  target_group.add_argument(
      '--new-folder-config',
      type=arg_parsers.ArgDict(
          spec={
              'parent': str,
              'display_name': str,
          }
      ),
      metavar='PROPERTY=VALUE',
      help='JSON/YAML specification for provisioning a new folder.',
  )

  parser.add_argument(
      '--framework',
      required=True,
      help='Compliance framework resource name or ID (e.g. fedramp-moderate).',
  )
  parser.add_argument(
      '--framework-major-revision',
      type=int,
      help='Major revision ID of the compliance framework.',
  )
  controls_group = parser.add_mutually_exclusive_group()
  controls_group.add_argument(
      '--cloud-control-config',
      action='append',
      type=arg_parsers.ArgDict(),
      metavar='PROPERTY=VALUE',
      help='Repeated inline control configuration.',
  )
  controls_group.add_argument(
      '--cloud-control-configs-from-file',
      help='Path to JSON/YAML file specifying multiple control configurations.',
  )
  parser.add_argument(
      '--cmek-key-ring',
      help='KMS Key Ring resource path for Customer-Managed Encryption Keys.',
  )
  parser.add_argument(
      '--cmek-dedicated-project-config',
      type=arg_parsers.ArgDict(
          spec={
              'project_id': str,
              'billing_account': str,
              'display_name': str,
          }
      ),
      metavar='PROPERTY=VALUE',
      help=(
          'Dedicated KMS project configuration (valid only with folder'
          ' targets).'
      ),
  )
  calliope_base.ASYNC_FLAG.AddToParser(parser)


def AddUpdateWorkloadV2Flags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds flags to the assured workloads update command for V2 (ALPHA/BETA)."""
  AddWorkloadResourceArgToParser(parser, verb='update')
  parser.add_argument(
      '--etag',
      help='ETag for optimistic concurrency control.',
  )
  updatable_group = parser.add_group(
      required=True,
      help='Settings that can be updated on the Assured Workloads environment.',
  )
  controls_group = updatable_group.add_mutually_exclusive_group()
  controls_group.add_argument(
      '--cloud-control-config',
      action='append',
      type=arg_parsers.ArgDict(),
      metavar='PROPERTY=VALUE',
      help='Updated repeated inline control configuration.',
  )
  controls_group.add_argument(
      '--cloud-control-configs-from-file',
      help='Path to JSON/YAML file specifying updated control configurations.',
  )
  calliope_base.ASYNC_FLAG.AddToParser(parser)


def AddVersionFlag(
    parser: parser_arguments.ArgumentInterceptor,
    default: str = 'v1',
) -> None:
  """Adds the --version flag to select between V1 and V2 APIs.

  Args:
    parser: Parser used to construct the command flags.
    default: The default API version ('v1' or 'v2'). Defaults to 'v1'.
  """
  parser.add_argument(
      '--version',
      choices=['v1', 'v2'],
      default=default,
      help=(
          'Assured Workloads API version to use. Options are v1 and v2. '
          f'Defaults to {default}.'
      ),
  )


def GetApiVersion(
    args: Any,
    release_track: Optional[calliope_base.ReleaseTrack] = None,
) -> str:
  """Returns the API version ("v1" or "v2") requested in args."""
  if (
      args.version == 'v2'
      and release_track is not None
      and release_track != calliope_base.ReleaseTrack.GA
  ):
    raise calliope_exceptions.InvalidArgumentException(
        '--version',
        'The --version=v2 flag is only supported on the GA release track.',
    )
  return args.version or 'v1'


V1_ONLY_CREATE_FLAGS = {
    'compliance_regime': (
        '--compliance-regime',
        "Use '--framework' when creating V2 workloads.",
    ),
    'billing_account': (
        '--billing-account',
        (
            "Configure billing within '--new-project-config' or"
            " '--cloud-control-config' when creating V2 workloads."
        ),
    ),
    'provisioned_resources_parent': (
        '--provisioned-resources-parent',
        (
            "Use '--target-folder' or '--target-project' when creating V2"
            ' workloads.'
        ),
    ),
    'resource_settings': (
        '--resource-settings',
        "Use '--cloud-control-config' when creating V2 workloads.",
    ),
    'display_name': (
        '--display-name',
        (
            'Configure folder/project display names within'
            " '--new-folder-config' or '--new-project-config'."
        ),
    ),
    'labels': (
        '--labels',
        'Labels are only supported on V1 workloads.',
    ),
    'partner': (
        '--partner',
        'Partner configurations are only supported on V1 workloads.',
    ),
    'partner_permissions': (
        '--partner-permissions',
        'Partner permissions are only supported on V1 workloads.',
    ),
    'partner_services_billing_account': (
        '--partner-services-billing-account',
        'Partner billing accounts are only supported on V1 workloads.',
    ),
    'next_rotation_time': (
        '--next-rotation-time',
        'KMS rotation settings are only supported on V1 workloads.',
    ),
    'rotation_period': (
        '--rotation-period',
        'KMS rotation settings are only supported on V1 workloads.',
    ),
    'enable_sovereign_controls': (
        '--enable-sovereign-controls',
        'Sovereign controls are only supported on V1 workloads.',
    ),
}

V2_ONLY_CREATE_FLAGS = {
    'framework': (
        '--framework',
        "Use '--compliance-regime' when creating V1 workloads.",
    ),
    'framework_major_revision': (
        '--framework-major-revision',
        'Major revision is only applicable to V2 frameworks.',
    ),
    'target_project': (
        '--target-project',
        'Target resources are only supported in V2 workloads.',
    ),
    'target_folder': (
        '--target-folder',
        'Target resources are only supported in V2 workloads.',
    ),
    'new_project_config': (
        '--new-project-config',
        'New project specifications are only supported in V2 workloads.',
    ),
    'new_folder_config': (
        '--new-folder-config',
        'New folder specifications are only supported in V2 workloads.',
    ),
    'cloud_control_config': (
        '--cloud-control-config',
        "Use '--resource-settings' when creating V1 workloads.",
    ),
    'cloud_control_configs_from_file': (
        '--cloud-control-configs-from-file',
        "Use '--resource-settings' when creating V1 workloads.",
    ),
    'cmek_key_ring': (
        '--cmek-key-ring',
        'CMEK key rings are only supported in V2 workloads.',
    ),
    'cmek_dedicated_project_config': (
        '--cmek-dedicated-project-config',
        'Dedicated CMEK projects are only supported in V2 workloads.',
    ),
    'description': (
        '--description',
        "Use '--display-name' when creating V1 workloads.",
    ),
    'flag_workload_id': (
        '--workload-id',
        'Explicit workload-id is only supported in V2 workloads.',
    ),
    'workload_id': (
        'workload_id',
        (
            'Positional workload ID is only supported in V2 workloads. Use'
            " '--external-identifier' for V1."
        ),
    ),
    'async_': (
        '--async',
        'Asynchronous operations are only supported on V2 workloads.',
    ),
}

V1_ONLY_UPDATE_FLAGS = {
    'display_name': (
        '--display-name',
        'Display name is only supported on V1 workloads.',
    ),
    'labels': (
        '--labels',
        'Labels are only supported on V1 workloads.',
    ),
    'violation_notifications_enabled': (
        '--violation-notifications-enabled',
        'Violation notifications are only supported on V1 workloads.',
    ),
}

V2_ONLY_UPDATE_FLAGS = {
    'framework_major_revision': (
        '--framework-major-revision',
        'Framework major revision is only supported on V2 workloads.',
    ),
    'cloud_control_config': (
        '--cloud-control-config',
        'Cloud control configs are only supported on V2 workloads.',
    ),
    'cloud_control_configs_from_file': (
        '--cloud-control-configs-from-file',
        'Cloud control configs are only supported on V2 workloads.',
    ),
    'async_': (
        '--async',
        'Asynchronous operations are only supported on V2 workloads.',
    ),
}


def _ValidateVersionExclusiveFlags(
    args: Any,
    version: str,
    v1_only_flags: dict[str, tuple[str, str]],
    v2_only_flags: dict[str, tuple[str, str]],
) -> None:
  """Validates that flags exclusive to a specific version are not specified."""
  if version == 'v2':
    for flag_attr, (flag_name, remediation) in v1_only_flags.items():
      if args.IsKnownAndSpecified(flag_attr):
        raise calliope_exceptions.InvalidArgumentException(
            flag_name,
            f'Flag cannot be used with --version=v2. {remediation}',
        )
  elif version == 'v1':
    for flag_attr, (flag_name, remediation) in v2_only_flags.items():
      if args.IsKnownAndSpecified(flag_attr):
        raise calliope_exceptions.InvalidArgumentException(
            flag_name,
            f'Flag cannot be used with --version=v1. {remediation}',
        )


def ValidateCreateWorkloadVersionFlags(args: Any) -> None:
  """Validates mutual exclusivity and required flags between V1 and V2 create workload.

  Args:
    args: The parsed command-line arguments.

  Raises:
    calliope_exceptions.InvalidArgumentException: If mutually exclusive flags
      are used with a conflicting --version value.
    calliope_exceptions.RequiredArgumentException: If required flags for the
      specified version are missing.
  """
  version = GetApiVersion(args)
  _ValidateVersionExclusiveFlags(
      args, version, V1_ONLY_CREATE_FLAGS, V2_ONLY_CREATE_FLAGS
  )
  if version == 'v2':
    if not args.IsKnownAndSpecified('framework'):
      raise calliope_exceptions.RequiredArgumentException(
          '--framework',
          'The compliance framework is required for V2 workloads.',
      )
    if not (
        args.IsKnownAndSpecified('target_project')
        or args.IsKnownAndSpecified('target_folder')
        or args.IsKnownAndSpecified('new_project_config')
        or args.IsKnownAndSpecified('new_folder_config')
    ):
      raise calliope_exceptions.RequiredArgumentException(
          '--target-project',
          'One of --target-project, --target-folder, --new-project-config, or'
          ' --new-folder-config is required for V2 workloads.',
      )
  elif version == 'v1':
    if not args.IsKnownAndSpecified('display_name'):
      raise calliope_exceptions.RequiredArgumentException(
          '--display-name',
          'The display name is required for V1 workloads.',
      )
    if not args.IsKnownAndSpecified('compliance_regime'):
      raise calliope_exceptions.RequiredArgumentException(
          '--compliance-regime',
          'The compliance regime is required for V1 workloads.',
      )
    if not args.IsKnownAndSpecified('billing_account'):
      raise calliope_exceptions.RequiredArgumentException(
          '--billing-account',
          'The billing account is required for V1 workloads.',
      )


def ValidateUpdateWorkloadVersionFlags(args: Any) -> None:
  """Validates mutual exclusivity between V1 and V2 update workload flags.

  Args:
    args: The parsed command-line arguments.

  Raises:
    calliope_exceptions.InvalidArgumentException: If mutually exclusive flags
      are used with a conflicting --version value.
    calliope_exceptions.RequiredArgumentException: If required flags for the
      specified version are missing.
  """
  version = GetApiVersion(args)
  _ValidateVersionExclusiveFlags(
      args, version, V1_ONLY_UPDATE_FLAGS, V2_ONLY_UPDATE_FLAGS
  )

  if version == 'v2':
    if not (
        args.IsKnownAndSpecified('cloud_control_config')
        or args.IsKnownAndSpecified('cloud_control_configs_from_file')
    ):
      raise calliope_exceptions.RequiredArgumentException(
          '--cloud-control-config',
          'One of --cloud-control-config or'
          ' --cloud-control-configs-from-file must be specified when'
          ' updating V2 workloads.',
      )
  elif version == 'v1':
    if not (
        args.IsKnownAndSpecified('display_name')
        or args.IsKnownAndSpecified('labels')
        or args.IsKnownAndSpecified('etag')
        or args.IsKnownAndSpecified('violation_notifications_enabled')
    ):
      raise calliope_exceptions.RequiredArgumentException(
          '--display-name', 'At least one field must be specified for update'
      )


def ValidateDeleteWorkloadVersionFlags(args: Any) -> None:
  """Validates flags for the delete command based on API version.

  Args:
    args: The parsed command-line arguments.

  Raises:
    calliope_exceptions.InvalidArgumentException: If --async is used with
      --version=v1.
  """
  version = GetApiVersion(args)
  if version == 'v1' and args.IsKnownAndSpecified('async_'):
    raise calliope_exceptions.InvalidArgumentException(
        '--async',
        'Flag cannot be used with --version=v1. Asynchronous deletion is only'
        ' supported on V2 workloads.',
    )


OLPC_MODE_MAP = {
    'strict-il5': 'OLPC_MODE_STRICT_IL5',
    'opt-out': 'OLPC_MODE_OPT_OUT',
    'allow-mixed-il5': 'OLPC_MODE_ALLOW_MIXED_IL5',
    'strict-il5-forward': 'OLPC_MODE_STRICT_IL5_FORWARD',
}


def AddOrganizationResourceArgToParser(
    parser: parser_arguments.ArgumentInterceptor, verb: str
) -> None:
  """Adds the organization resource argument for Assured Workloads settings."""
  concept_parsers.ConceptParser.ForResource(
      '--organization',
      resource_args.GetOrganizationResourceSpec(),
      f'The parent organization of the Assured Workloads settings to {verb}.',
      required=True,
  ).AddToParser(parser)


def AddDescribeSettingsFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds flags to the assured settings describe command."""
  AddOrganizationResourceArgToParser(parser, verb='describe')


def AddUpdateSettingsFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds flags to the assured settings update command."""
  AddOrganizationResourceArgToParser(parser, verb='update')
  parser.add_argument(
      '--olpc-mode',
      required=True,
      choices=list(OLPC_MODE_MAP.keys()),
      help='The active OLPC mode to configure for the organization.',
  )
  parser.add_argument(
      '--etag',
      help='ETag for optimistic concurrency control.',
  )


def NormalizeSettingsResourceName(org: str) -> str:
  """Returns the canonical settings resource name for an organization.

  Args:
    org: Organization identifier, path (e.g. 'organizations/12345'), or full
      settings URI (e.g. 'organizations/12345/assuredWorkloadsSettings').

  Returns:
    Resource name in the format
    'organizations/{org_id}/assuredWorkloadsSettings'.
  """
  clean = str(org).strip().rstrip('/')
  if clean.endswith('/assuredWorkloadsSettings'):
    clean = clean[: -len('/assuredWorkloadsSettings')].rstrip('/')
  if clean.startswith('organizations/'):
    clean = clean[len('organizations/') :]
  return f'organizations/{clean}/assuredWorkloadsSettings'


def ParseSettingsResource(args: Any) -> str:
  """Parses and returns the settings resource name from args."""
  if hasattr(args, 'CONCEPTS') and hasattr(args.CONCEPTS, 'organization'):
    try:
      ref = args.CONCEPTS.organization.Parse()
      if ref:
        return NormalizeSettingsResourceName(ref.Name())
    except (calliope_exceptions.Error, AttributeError):
      pass
  org = getattr(args, 'organization', None)
  if not org:
    raise calliope_exceptions.RequiredArgumentException(
        '--organization', 'The organization is required.'
    )
  return NormalizeSettingsResourceName(org)


def AddUnifiedCreateWorkloadFlags(
    parser: parser_arguments.ArgumentInterceptor,
    release_track: calliope_base.ReleaseTrack,
) -> None:
  """Adds flags for both V1 and V2 to the canonical workloads create command."""
  AddVersionFlag(parser)

  parser.add_argument(
      '--location',
      required=True,
      help=(
          'The location of the Assured Workloads environment. For a '
          'current list of supported LOCATION values, see '
          '[Assured Workloads locations]'
          '(https://cloud.google.com/assured-workloads/docs/locations).'
      ),
  )
  parser.add_argument(
      '--organization',
      required=True,
      help=(
          'The parent organization of the Assured Workloads environment, '
          'provided as an organization ID.'
      ),
  )

  id_group = parser.add_mutually_exclusive_group()
  id_group.add_argument(
      'workload_id',
      nargs='?',
      default=None,
      help=(
          'User-assigned unique identifier for the workload. If omitted, '
          'generated by the server.'
      ),
  )
  id_group.add_argument(
      '--workload-id',
      dest='flag_workload_id',
      help='User-assigned unique identifier for the workload.',
  )
  id_group.add_argument(
      '--external-identifier',
      dest='external_identifier',
      help='The external identifier of the Assured Workloads environment.',
  )

  v1_group = parser.add_group(category='V1 CREATION FLAGS')
  v1_group.add_argument(
      '--display-name',
      help='The display name of the new Assured Workloads environment (V1).',
  )
  arg_utils.ChoiceEnumMapper(
      '--compliance-regime',
      message_util.GetComplianceRegimesEnum(release_track),
      include_filter=lambda regime: regime != 'COMPLIANCE_REGIME_UNSPECIFIED',
      required=False,
      help_str=(
          'The compliance regime of the new Assured Workloads environment (V1).'
      ),
  ).choice_arg.AddToParser(v1_group)
  arg_utils.ChoiceEnumMapper(
      '--partner',
      message_util.GetPartnersEnum(release_track),
      include_filter=lambda regime: regime != 'PARTNER_UNSPECIFIED',
      help_str=(
          'The partner choice when creating a workload managed by local trusted'
          ' partners.'
      ),
  ).choice_arg.AddToParser(v1_group)
  v1_group.add_argument(
      '--partner-permissions',
      type=arg_parsers.ArgDict(
          spec={
              'data-logs-viewer': bool,
          }
      ),
      metavar='KEY=VALUE',
      help=(
          'The partner permissions for the partner regime, for example,'
          ' data-logs-viewer=true/false'
      ),
  )
  v1_group.add_argument(
      '--partner-services-billing-account',
      required=False,
      help=(
          'Billing account necessary for purchasing services from Sovereign'
          ' Partners. This field is required for creating SIA/PSN/CNTXT'
          ' partner workloads. The caller should have'
          " 'billing.resourceAssociations.create' IAM permission on this"
          ' billing-account. The format of this string is'
          ' billingAccounts/AAAAAA-BBBBBB-CCCCCC'
      ),
  )
  v1_group.add_argument(
      '--billing-account',
      help=(
          'The billing account of the new Assured Workloads environment, for '
          'example, billingAccounts/0000AA-AAA00A-A0A0A0 (V1).'
      ),
  )
  v1_group.add_argument(
      '--next-rotation-time',
      help=(
          'The next rotation time of the KMS settings of new Assured '
          'Workloads environment, for example, 2020-12-30T10:15:30.00Z'
      ),
  )
  v1_group.add_argument(
      '--rotation-period',
      help=(
          'The rotation period of the KMS settings of the new Assured '
          'Workloads environment, for example, 172800s'
      ),
  )
  v1_group.add_argument(
      '--labels',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE',
      help=(
          'The labels of the new Assured Workloads environment, for example, '
          'LabelKey1=LabelValue1,LabelKey2=LabelValue2'
      ),
  )
  v1_group.add_argument(
      '--provisioned-resources-parent',
      help=(
          'The parent of the provisioned projects, for example, '
          'folders/{FOLDER_ID}'
      ),
  )
  v1_group.add_argument(
      '--enable-sovereign-controls',
      type=bool,
      default=False,
      help=(
          'If true, enable sovereign controls for the new Assured Workloads '
          'environment, currently only supported by EU_REGIONS_AND_SUPPORT'
      ),
  )
  _AddResourceSettingsFlag(v1_group, release_track)

  v2_group = parser.add_group(category='V2 CREATION FLAGS')
  v2_group.add_argument(
      '--description',
      help='User-friendly description for the workload (V2).',
  )
  target_group = v2_group.add_mutually_exclusive_group()
  target_group.add_argument(
      '--target-project',
      help=(
          'Existing Project ID or project number to onboard into Assured'
          ' Workloads (V2).'
      ),
  )
  target_group.add_argument(
      '--target-folder',
      help='Existing Folder ID to onboard into Assured Workloads (V2).',
  )
  target_group.add_argument(
      '--new-project-config',
      type=arg_parsers.ArgDict(
          spec={
              'parent': str,
              'display_name': str,
              'billing_account': str,
          }
      ),
      metavar='PROPERTY=VALUE',
      help='JSON/YAML specification for provisioning a new project (V2).',
  )
  target_group.add_argument(
      '--new-folder-config',
      type=arg_parsers.ArgDict(
          spec={
              'parent': str,
              'display_name': str,
          }
      ),
      metavar='PROPERTY=VALUE',
      help='JSON/YAML specification for provisioning a new folder (V2).',
  )
  v2_group.add_argument(
      '--framework',
      help=(
          'Compliance framework resource name or ID, for example,'
          ' fedramp-moderate (V2).'
      ),
  )
  v2_group.add_argument(
      '--framework-major-revision',
      type=int,
      help='Major revision ID of the compliance framework (V2).',
  )
  controls_group = v2_group.add_mutually_exclusive_group()
  controls_group.add_argument(
      '--cloud-control-config',
      action='append',
      type=arg_parsers.ArgDict(),
      metavar='PROPERTY=VALUE',
      help='Repeated inline control configuration (V2).',
  )
  controls_group.add_argument(
      '--cloud-control-configs-from-file',
      help=(
          'Path to JSON/YAML file specifying multiple control configurations'
          ' (V2).'
      ),
  )
  v2_group.add_argument(
      '--cmek-key-ring',
      help=(
          'KMS Key Ring resource path for Customer-Managed Encryption Keys'
          ' (V2).'
      ),
  )
  v2_group.add_argument(
      '--cmek-dedicated-project-config',
      type=arg_parsers.ArgDict(
          spec={
              'project_id': str,
              'billing_account': str,
              'display_name': str,
          }
      ),
      metavar='PROPERTY=VALUE',
      help=(
          'Dedicated KMS project configuration (valid only with folder'
          ' targets).'
      ),
  )
  calliope_base.ASYNC_FLAG.AddToParser(parser)


def AddUnifiedUpdateWorkloadFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds flags for both V1 and V2 to the canonical workloads update command."""
  AddVersionFlag(parser)
  AddWorkloadResourceArgToParser(parser, verb='update')
  parser.add_argument(
      '--etag',
      help=(
          'The etag acquired by reading the Assured Workloads environment'
          ' before updating.'
      ),
  )
  v2_group = parser.add_group(
      category='V2 UPDATE FLAGS',
  )
  v2_group.add_argument(
      '--framework-major-revision',
      type=int,
      help='Updated major revision ID for the workload (V2).',
  )
  calliope_base.ASYNC_FLAG.AddToParser(parser)
  controls_group = v2_group.add_mutually_exclusive_group()
  controls_group.add_argument(
      '--cloud-control-config',
      action='append',
      type=arg_parsers.ArgDict(),
      metavar='PROPERTY=VALUE',
      help='Updated repeated inline control configuration (V2).',
  )
  controls_group.add_argument(
      '--cloud-control-configs-from-file',
      help=(
          'Path to JSON/YAML file specifying updated control configurations'
          ' (V2).'
      ),
  )
  updatable_fields = parser.add_group(
      category='V1 UPDATE FLAGS',
      required=False,
      help='Settings that can be updated on the Assured Workloads environment.',
  )
  updatable_fields.add_argument(
      '--display-name',
      help='The new display name of the Assured Workloads environment (V1).',
  )
  updatable_fields.add_argument(
      '--violation-notifications-enabled',
      help=(
          'The notification setting of the Assured Workloads environment (V1).'
      ),
  )
  updatable_fields.add_argument(
      '--labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=(
          'The new labels of the Assured Workloads environment, for example,'
          ' LabelKey1=LabelValue1,LabelKey2=LabelValue2 (V1).'
      ),
  )


def AddUnifiedDeleteWorkloadFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds flags for both V1 and V2 to the canonical workloads delete command."""
  AddVersionFlag(parser)
  AddWorkloadResourceArgToParser(parser, verb='delete')
  parser.add_argument(
      '--etag',
      help='The etag acquired by reading the Assured Workloads environment.',
  )
  calliope_base.ASYNC_FLAG.AddToParser(parser)
