# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utility for updating Looker instances.

This utility is primarily used for modifying request hooks for update
requests for Looker instances. See go/gcloud-creating-commands#request-hooks
for more details.
"""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io

_MSG_RELEASE_CHANNEL_UPGRADE_WARNING = (
    'Caution: Your instance will be updated to the latest version available in'
    ' the {selected_channel} channel. For more details, review'
    ' https://cloud.google.com/looker/docs/looker-core-release-process#release_channels.'
)

_MSG_RELEASE_CHANNEL_DOWNGRADE_WARNING = (
    'Caution: Your instance will remain on version {looker_version} until this'
    ' version becomes available in the {selected_channel} channel or may update'
    ' instantly if the {selected_channel} channel is on a higher version. For'
    ' more details, review'
    ' https://cloud.google.com/looker/docs/looker-core-release-process#release_channels.'
)

_MSG_RELEASE_CHANNEL_RAPID_MAINTENANCE_WARNING = (
    'Switching to the Rapid channel automatically removes the maintenance'
    ' window and deny maintenance periods for this instance.'
)


def _GetReleaseChannelChangeType(*, current, selected, release_channel_enum):
  """Checks if release channel change is an upgrade or downgrade.

  Args:
    current: The current release channel of the instance.
    selected: The new release channel selected by the user.
    release_channel_enum: The release channel enum from the API messages.

  Returns:
    'upgrade', 'downgrade', or None if the rank is the same.
  """
  current_val = (
      current
      if current is not None
      else release_channel_enum.RELEASE_CHANNEL_UNSPECIFIED
  )

  rank_by_release_channel = {
      release_channel_enum.RELEASE_CHANNEL_UNSPECIFIED: 0.5,
      release_channel_enum.RAPID: 0,
      release_channel_enum.REGULAR: 1,
      release_channel_enum.STABLE: 2,
  }

  current_rank = rank_by_release_channel.get(current_val, 0)
  selected_rank = rank_by_release_channel.get(selected, 0)

  if current_rank == selected_rank:
    return None
  return 'upgrade' if selected_rank < current_rank else 'downgrade'


def _GetReleaseChannelWarningMessage(
    *, current, selected, looker_version, release_channel_enum
):
  """Gets warning message for release channel change.

  Args:
    current: The current release channel of the instance.
    selected: The new release channel selected by the user.
    looker_version: The current version of the Looker instance.
    release_channel_enum: The release channel enum from the API messages.

  Returns:
    A warning message string or None if no warning is needed.
  """
  change_type = _GetReleaseChannelChangeType(
      current=current,
      selected=selected,
      release_channel_enum=release_channel_enum,
  )
  if change_type is None:
    return None

  label_by_release_channel = {
      release_channel_enum.RELEASE_CHANNEL_UNSPECIFIED: 'No Channel',
      release_channel_enum.RAPID: 'Rapid',
      release_channel_enum.REGULAR: 'Regular',
      release_channel_enum.STABLE: 'Stable',
  }

  selected_label = label_by_release_channel.get(selected, str(selected))

  if change_type == 'downgrade':
    warning_msg = _MSG_RELEASE_CHANNEL_DOWNGRADE_WARNING.format(
        looker_version=looker_version, selected_channel=selected_label
    )
  else:
    warning_msg = _MSG_RELEASE_CHANNEL_UPGRADE_WARNING.format(
        selected_channel=selected_label
    )

  if (
      selected == release_channel_enum.RAPID
      and current != release_channel_enum.RAPID
  ):
    warning_msg += '\n\n' + _MSG_RELEASE_CHANNEL_RAPID_MAINTENANCE_WARNING

  return warning_msg


def _WarnForAdminSettingsUpdate():
  """Adds prompt that warns about allowed email domains update."""
  message = 'Change to instance allowed email domain requested. '
  message += (
      'Updating the allowed email domains from cli means the value provided'
      ' will be considered as the entire list and not an amendment to the'
      ' existing list of allowed email domains.'
  )
  console_io.PromptContinue(
      message=message,
      prompt_string='Do you want to proceed with update?',
      cancel_on_no=True,
  )


def _WarnForPscAllowedVpcsUpdate():
  """Adds prompt that warns about allowed vpcs update."""
  message = (
      'Change to instance PSC allowed Virtual Private Cloud networks'
      ' requested. '
  )
  message += (
      'Updating the allowed VPC networks from cli means the value provided'
      ' will be considered as the entire list and not an amendment to the'
      ' existing list of allowed vpcs.'
  )
  console_io.PromptContinue(
      message=message,
      prompt_string='Do you want to proceed with update?',
      cancel_on_no=True,
  )


def _WarnForPscAllowedVpcsRemovalUpdate():
  """Adds prompt that warns about allowed vpcs removal."""
  message = 'Removal of instance PSC allowed vpcs requested. '

  console_io.PromptContinue(
      message=message,
      prompt_string='Do you want to proceed with removal of PSC allowed vpcs?',
      cancel_on_no=True,
  )


def _WarnForPscServiceAttachmentsUpdate():
  """Adds prompt that warns about service attachments update."""
  message = 'Change to instance PSC service attachments requested. '
  message += (
      'Updating the PSC service attachments from cli means the value provided'
      ' will be considered as the entire list and not an amendment to the'
      ' existing list of PSC service attachments'
  )
  console_io.PromptContinue(
      message=message,
      prompt_string='Do you want to proceed with update?',
      cancel_on_no=True,
  )


def _WarnForPscServiceAttachmentsRemovalUpdate():
  """Adds prompt that warns about service attachments removal."""
  message = 'Removal of instance PSC service attachments requested. '

  console_io.PromptContinue(
      message=message,
      prompt_string=(
          'Do you want to proceed with removal of service attachments?'
      ),
      cancel_on_no=True,
  )


def AddFieldToUpdateMask(field, patch_request):
  """Adds fields to the update mask of the patch request.

  Args:
    field: the field of the update mask to patch request for Looker instances.
    patch_request: the request of the actual update command to be modified

  Returns:
    A patch request object to be sent to the server. The object is an instance
    of UpdateInstanceRequest: http://shortn/_yn9MhWaGJx
  """
  update_mask = patch_request.updateMask
  if update_mask:
    fields = set(update_mask.split(','))
    if field not in fields:
      patch_request.updateMask = f'{update_mask},{field}'
  else:
    patch_request.updateMask = field
  return patch_request


def ModifyAllowedEmailDomains(unused_instance_ref, args, patch_request):
  """Python hook to modify allowed email domains in looker instance update request."""
  if args.IsSpecified('allowed_email_domains'):
    # Changing allowed email domains means this list will be overwritten in the
    # DB and not amended and users should be warned before proceeding.
    _WarnForAdminSettingsUpdate()
    patch_request.instance.adminSettings.allowedEmailDomains = (
        args.allowed_email_domains
    )
    patch_request = AddFieldToUpdateMask(
        'admin_settings.allowed_email_domains', patch_request
    )
  return patch_request


def UpdateMaintenanceWindow(unused_instance_ref, args, patch_request):
  """Hook to update maintenance window to the update mask of the request."""
  if args.IsSpecified('maintenance_window_day') or args.IsSpecified(
      'maintenance_window_time'
  ):
    patch_request = AddFieldToUpdateMask('maintenance_window', patch_request)
  return patch_request


def UpdateEnablePublicIpAlpha(unused_instance_ref, args, patch_request):
  """Hook to update public IP to the update mask of the request for alpha."""
  if args.IsSpecified('enable_public_ip'):
    patch_request = AddFieldToUpdateMask('enable_public_ip', patch_request)
  return patch_request


def UpdatePublicIPEnabled(unused_instance_ref, args, patch_request):
  """Hook to update public IP to the update mask of the request fo GA."""
  if args.IsSpecified('public_ip_enabled'):
    patch_request = AddFieldToUpdateMask('public_ip_enabled', patch_request)
  return patch_request


def UpdateOauthClient(unused_instance_ref, args, patch_request):
  """Hook to update Oauth configs to the update mask of the request."""
  if args.IsSpecified('oauth_client_id') and args.IsSpecified(
      'oauth_client_secret'
  ):
    patch_request = AddFieldToUpdateMask(
        'oauth_config.client_id', patch_request
    )
    patch_request = AddFieldToUpdateMask(
        'oauth_config.client_secret', patch_request
    )
    # Disable shared OAuth when updating custom credentials.
    patch_request.instance.oauthConfig.sharedOauthClientEnabled = False
    patch_request = AddFieldToUpdateMask(
        'oauth_config.shared_oauth_client_enabled', patch_request
    )

  return patch_request


def UpdateDenyMaintenancePeriod(unused_instance_ref, args, patch_request):
  """Hook to update deny maintenance period to the update mask of the request."""
  if (
      args.IsSpecified('deny_maintenance_period_start_date')
      or args.IsSpecified('deny_maintenance_period_end_date')
      or args.IsSpecified('deny_maintenance_period_time')
  ):
    patch_request = AddFieldToUpdateMask(
        'deny_maintenance_period', patch_request
    )
  return patch_request


def UpdateUserMetadata(unused_instance_ref, args, patch_request):
  """Hook to update deny user metadata to the update mask of the request."""
  if (
      args.IsSpecified('add_viewer_users')
      or args.IsSpecified('add_standard_users')
      or args.IsSpecified('add_developer_users')
  ):
    patch_request = AddFieldToUpdateMask('user_metadata', patch_request)
  return patch_request


def UpdateCustomDomain(unused_instance_ref, args, patch_request):
  """Hook to update custom domain to the update mask of the request."""
  if args.IsSpecified('custom_domain'):
    patch_request = AddFieldToUpdateMask('custom_domain', patch_request)
  return patch_request


def UpdatePscAllowedVpcs(unused_instance_ref, args, patch_request):
  """Hook to update psc confing allowed vpcs to the update mask of the request."""
  if args.IsSpecified('psc_allowed_vpcs'):
    # Changing allowed email domains means this list will be overwritten in the
    # DB and not amended and users should be warned before proceeding.
    _WarnForPscAllowedVpcsUpdate()
    patch_request.instance.pscConfig.allowedVpcs = args.psc_allowed_vpcs
    patch_request = AddFieldToUpdateMask(
        'psc_config.allowed_vpcs', patch_request
    )
  elif args.IsSpecified('clear_psc_allowed_vpcs'):
    _WarnForPscAllowedVpcsRemovalUpdate()
    patch_request = AddFieldToUpdateMask(
        'psc_config.allowed_vpcs', patch_request
    )
  return patch_request


def UpdatePscServiceAttachments(unused_instance_ref, args, patch_request):
  """Hook to update psc confing service attachments to the update mask of the request."""
  if args.IsSpecified('psc_service_attachment'):
    _WarnForPscServiceAttachmentsUpdate()
    patch_request = AddFieldToUpdateMask(
        'psc_config.service_attachments', patch_request
    )
  elif args.IsSpecified('clear_psc_service_attachments'):
    _WarnForPscServiceAttachmentsRemovalUpdate()
    patch_request = AddFieldToUpdateMask(
        'psc_config.service_attachments', patch_request
    )
  return patch_request


def UpdateGeminiAiConfig(unused_instance_ref, args, patch_request):
  """Hook to update gemini enabled to the update mask of the request."""
  if args.IsSpecified('gemini_enabled'):
    patch_request = AddFieldToUpdateMask('gemini_enabled', patch_request)
  if args.IsSpecified('gemini_preview_tester_enabled'):
    patch_request = AddFieldToUpdateMask(
        'gemini_ai_config.trusted_tester', patch_request
    )
  if args.IsSpecified('gemini_prompt_log_enabled'):
    patch_request = AddFieldToUpdateMask(
        'gemini_ai_config.prompt_logging', patch_request
    )
  return patch_request


def UpdatePeriodicExportConfig(unused_instance_ref, args, patch_request):
  """Hook to handle periodic export config updates."""
  if (
      args.IsSpecified('clear_periodic_export_config')
      or args.IsSpecified('periodic_export_kms_key')
      or args.IsSpecified('periodic_export_gcs_uri')
      or args.IsSpecified('periodic_export_start_time')
  ):
    patch_request = AddFieldToUpdateMask(
        'periodic_export_config', patch_request
    )

  if args.IsSpecified('clear_periodic_export_config'):
    patch_request.instance.periodicExportConfig = None
  return patch_request


def UpdateControlledEgressConfig(unused_instance_ref, args, patch_request):
  """Hook to handle controlled egress config updates."""
  if args.IsSpecified('egress_enabled'):
    patch_request = AddFieldToUpdateMask(
        'controlled_egress_enabled', patch_request
    )
  if args.IsSpecified('marketplace_enabled'):
    if args.marketplace_enabled:
      _WarnForMarketplaceEnabledUpdate()
    patch_request = AddFieldToUpdateMask(
        'controlled_egress_config.marketplace_enabled', patch_request
    )
  if args.IsSpecified('egress_fqdns'):
    patch_request = AddFieldToUpdateMask(
        'controlled_egress_config.egress_fqdns', patch_request
    )
  return patch_request


def UpdateCatalogIntegrationOptOut(unused_instance_ref, args, patch_request):
  """Updates catalog integration opt out in the request update mask."""
  if args.IsSpecified('catalog_integration_opt_out'):
    patch_request = AddFieldToUpdateMask(
        'catalog_integration_opt_out', patch_request
    )
  return patch_request


def UpdateReleaseChannel(instance_ref, args, patch_request):
  """Hook to update release channel to the update mask of the request.

  Args:
    instance_ref: The reference to the instance being updated.
    args: The arguments passed to the update command.
    patch_request: The patch request to be sent to the API.

  Returns:
    The updated patch request.

  Raises:
    exceptions.InvalidArgumentException: If maintenance settings are specified
      when switching to the RAPID release channel.
  """
  if not args.IsSpecified('release_channel'):
    return patch_request

  api_version = instance_ref.GetCollectionInfo().api_version
  messages = apis.GetMessagesModule('looker', api_version)
  instance_msg = getattr(messages, 'Instance')
  release_channel_enum = instance_msg.ReleaseChannelValueValuesEnum

  client = apis.GetClientInstance('looker', api_version)
  service = client.projects_locations_instances

  get_request_class = getattr(
      messages, 'LookerProjectsLocationsInstancesGetRequest'
  )
  current_instance = service.Get(
      get_request_class(name=instance_ref.RelativeName())
  )

  current_channel = current_instance.releaseChannel
  current_version = current_instance.lookerVersion
  new_channel = patch_request.instance.releaseChannel

  if new_channel == release_channel_enum.RAPID:
    maintenance_fields = [
        'maintenance_window_day',
        'maintenance_window_time',
        'deny_maintenance_period_start_date',
        'deny_maintenance_period_end_date',
        'deny_maintenance_period_time',
    ]
    if any(args.IsSpecified(f) for f in maintenance_fields):
      raise exceptions.InvalidArgumentException(
          '--release-channel',
          'Maintenance window and deny maintenance periods are not supported '
          'for instances in the RAPID release channel.',
      )

  warning_msg = _GetReleaseChannelWarningMessage(
      current=current_channel,
      selected=new_channel,
      looker_version=current_version,
      release_channel_enum=release_channel_enum,
  )

  if warning_msg:
    console_io.PromptContinue(
        message=warning_msg,
        prompt_string='Do you want to proceed with the release channel switch?',
        cancel_on_no=True,
    )

  if (
      new_channel == release_channel_enum.RAPID
      and current_channel != release_channel_enum.RAPID
  ):
    patch_request.instance.maintenanceWindow = None
    patch_request.instance.denyMaintenancePeriod = None
    patch_request = AddFieldToUpdateMask('maintenance_window', patch_request)
    patch_request = AddFieldToUpdateMask(
        'deny_maintenance_period', patch_request
    )

  return AddFieldToUpdateMask('release_channel', patch_request)


def UpdateAcceleratedSecurityPatch(unused_instance_ref, args, patch_request):
  """Hook to update accelerated security patch to the update mask of the request."""
  if args.IsSpecified('accelerated_security_patch_enabled'):
    patch_request = AddFieldToUpdateMask(
        'accelerated_security_patch_enabled', patch_request
    )
  return patch_request


def _WarnForMarketplaceEnabledUpdate():
  """Adds prompt that warns about marketplace enabled update."""
  message = 'Change to instance marketplace enabled requested. '
  message += (
      'Enabling connection to the Looker Marketplace will also allow egress to'
      ' github.com.'
  )
  console_io.PromptContinue(
      message=message,
      prompt_string='Do you want to proceed with update?',
      cancel_on_no=True,
  )
