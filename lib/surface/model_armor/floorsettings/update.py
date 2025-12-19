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
"""Fetch the FloorSetting resource."""

import dataclasses
import json

from googlecloudsdk.api_lib.model_armor import api as model_armor_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.model_armor import args as model_armor_args
from googlecloudsdk.command_lib.model_armor import util as model_armor_util
from googlecloudsdk.core import log


@dataclasses.dataclass
class ServiceConfig:
  """Configuration for an integrated service."""

  name: str
  enum: ...
  enforcement_type_arg: str
  enforcement_type_flag_name: str
  cloud_logging_arg: str
  service_floor_setting_arg: str
  service_floor_setting_attr: str
  defaulted_enforcement_flag_name: str
  setting_message: ...
  cli_name: str


def _GetServicesConfig(messages):
  """Returns a list of service configurations."""
  return [
      ServiceConfig(
          name='VERTEX_AI',
          enum=(
              messages.FloorSetting.IntegratedServicesValueListEntryValuesEnum.AI_PLATFORM
          ),
          enforcement_type_arg='vertex_ai_enforcement_type',
          enforcement_type_flag_name='--vertex-ai-enforcement-type',
          cloud_logging_arg='enable_vertex_ai_cloud_logging',
          service_floor_setting_arg='ai_platform_floor_setting',
          service_floor_setting_attr='aiPlatformFloorSetting',
          defaulted_enforcement_flag_name='vertex_ai_enforcement_defaulted',
          setting_message=messages.AiPlatformFloorSetting,
          cli_name='vertex-ai',
      ),
      ServiceConfig(
          name='GOOGLE_MCP_SERVER',
          enum=(
              messages.FloorSetting.IntegratedServicesValueListEntryValuesEnum.GOOGLE_MCP_SERVER
          ),
          enforcement_type_arg='google_mcp_server_enforcement_type',
          enforcement_type_flag_name='--google-mcp-server-enforcement-type',
          cloud_logging_arg='enable_google_mcp_server_cloud_logging',
          service_floor_setting_attr='googleMcpServerFloorSetting',
          service_floor_setting_arg='google_mcp_server_floor_setting',
          defaulted_enforcement_flag_name=(
              'google_mcp_server_enforcement_defaulted'
          ),
          setting_message=messages.McpServerFloorSetting,
          cli_name='google-mcp-server',
      ),
  ]


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.Command):
  """Update the FloorSetting resource.

  Updates the floor setting resource with the given name.
  """

  NO_CHANGES_MESSAGE = 'There are no changes to the floor setting for update.'

  @staticmethod
  def Args(parser):
    model_armor_args.AddFullUri(
        parser,
        positional=False,
        required=True,
        help_text='Full uri of the floor setting',
    )
    model_armor_args.AddFloorSettingEnforcement(
        parser,
        positional=False,
        required=False,
    )
    model_armor_args.AddMaliciousUriFilterSettingsEnforcement(parser)
    model_armor_args.AddPIJBFilterSettingsGroup(parser)
    model_armor_args.AddSDPFilterBasicConfigGroup(parser)
    model_armor_args.AddRaiFilterSettingsGroup(parser)
    model_armor_args.AddIntegratedServices(parser)
    model_armor_args.AddVertexAiFloorSetting(parser)
    model_armor_args.AddGoogleMcpServerFloorSetting(parser)
    model_armor_args.AddMultiLanguageDetection(parser)

  def _GetEnumValue(self, value):
    return value.upper().replace('-', '_')

  def _updateMaskForEnforcementType(
      self, *, service_floor_setting_arg, arg_enforcement_type, update_mask
  ):
    """Update the update mask for enforcement type."""
    if arg_enforcement_type == 'INSPECT_ONLY':
      update_mask.append(service_floor_setting_arg + '.inspect_only')
    elif arg_enforcement_type == 'INSPECT_AND_BLOCK':
      update_mask.append(service_floor_setting_arg + '.inspect_and_block')

  def _handleEnforcementType(self, arg_enforcement_type, service_floor_setting):
    """Handle the enforcement type for Integreated Services."""
    # Reset both oneof fields to None before setting the desired one.
    setattr(service_floor_setting, 'inspectOnly', None)
    setattr(service_floor_setting, 'inspectAndBlock', None)

    if arg_enforcement_type == 'INSPECT_ONLY':
      setattr(
          service_floor_setting,
          'inspectOnly',
          True,
      )
    elif arg_enforcement_type == 'INSPECT_AND_BLOCK':
      setattr(
          service_floor_setting,
          'inspectAndBlock',
          True,
      )

  def _validateRaiFilterSettings(self, messages, filters, argument_name):
    for item in [json.loads(f) for f in filters]:
      confidence_level = item['confidenceLevel']
      filter_type = item['filterType']
      model_armor_util.ValidateEnum(
          filter_type,
          messages.RaiFilter.FilterTypeValueValuesEnum,
          argument_name,
          f'Invalid choice : {filter_type}',
      )
      model_armor_util.ValidateEnum(
          confidence_level,
          messages.RaiFilter.ConfidenceLevelValueValuesEnum,
          argument_name,
          f'Invalid choice : {confidence_level}',
      )

  def _validateIntegratedServices(self, messages, services):
    for service in services:
      if service == 'VERTEX_AI':
        service = 'AI_PLATFORM'
      model_armor_util.ValidateEnum(
          service,
          messages.FloorSetting.IntegratedServicesValueListEntryValuesEnum,
          'integrated-services',
          f'{service}',
      )

  def _validateRemoveIntegratedServices(self, messages, args):
    """Validate the arguments for removing integrated services."""
    self._validateIntegratedServices(messages, args.remove_integrated_services)
    services_config = _GetServicesConfig(messages)
    services_config_by_name = {
        service_config.name: service_config
        for service_config in services_config
    }
    for service_name in args.remove_integrated_services:
      if service_name in services_config_by_name:
        service_config = services_config_by_name[service_name]
        if service_name == service_config.name:
          if args.IsSpecified(service_config.enforcement_type_arg):
            raise exceptions.ConflictingArgumentsException(
                f'--remove-integrated-services={service_config.name}',
                f'--{service_config.cli_name}-enforcement-type',
            )
          if args.IsSpecified(service_config.cloud_logging_arg):
            raise exceptions.ConflictingArgumentsException(
                f'--remove-integrated-services={service_config.name}',
                f'--enable-{service_config.cli_name}-cloud-logging',
            )

  def _validateClearIntegratedServices(self, messages, args):
    """Validate the arguments for clearing integrated services."""
    services_config = _GetServicesConfig(messages)
    for service_config in services_config:
      if args.IsSpecified(service_config.enforcement_type_arg):
        raise exceptions.ConflictingArgumentsException(
            '--clear-integrated-services',
            f'--{service_config.cli_name}-enforcement-type',
        )
      if args.IsSpecified(service_config.cloud_logging_arg):
        raise exceptions.ConflictingArgumentsException(
            '--clear-integrated-services',
            f'--enable-{service_config.cli_name}-cloud-logging',
        )

  def _validateEnforcementType(self, enforcement_type, service_name):
    if (
        enforcement_type == 'INSPECT_ONLY'
        or enforcement_type == 'INSPECT_AND_BLOCK'
    ):
      return

    raise exceptions.InvalidArgumentException(
        f'{service_name}-enforcement-type',
        f'argument --{service_name}-enforcement-type: Invalid choice:'
        f' {enforcement_type!r}. Valid choices are [INSPECT_AND_BLOCK,'
        ' INSPECT_ONLY].',
    )

  def _validateArgs(self, messages, args):
    """Validate the arguments."""
    if args.pi_and_jailbreak_filter_settings_confidence_level:
      model_armor_util.ValidateEnum(
          args.pi_and_jailbreak_filter_settings_confidence_level,
          messages.PiAndJailbreakFilterResult.ConfidenceLevelValueValuesEnum,
          'pi-and-jailbreak-filter-settings-confidence-level',
          'Invalid choice :'
          f' {args.pi_and_jailbreak_filter_settings_confidence_level}',
      )
    if args.pi_and_jailbreak_filter_settings_enforcement:
      model_armor_util.ValidateEnum(
          args.pi_and_jailbreak_filter_settings_enforcement,
          messages.PiAndJailbreakFilterSettings.FilterEnforcementValueValuesEnum,
          'pi-and-jailbreak-filter-settings-enforcement',
          'Invalid choice :'
          f' {args.pi_and_jailbreak_filter_settings_enforcement}',
      )
    if args.malicious_uri_filter_settings_enforcement:
      model_armor_util.ValidateEnum(
          args.malicious_uri_filter_settings_enforcement,
          messages.MaliciousUriFilterSettings.FilterEnforcementValueValuesEnum,
          'malicious-uri-filter-settings-enforcement',
          f'Invalid choice : {args.malicious_uri_filter_settings_enforcement}',
      )
    if args.basic_config_filter_enforcement:
      model_armor_util.ValidateEnum(
          args.basic_config_filter_enforcement,
          messages.SdpBasicConfig.FilterEnforcementValueValuesEnum,
          'basic-config-filter-enforcement',
          f'Invalid choice : {args.basic_config_filter_enforcement}',
      )
    if args.rai_settings_filters:
      self._validateRaiFilterSettings(
          messages, args.rai_settings_filters, 'rai-settings-filters'
      )
    if args.add_rai_settings_filters:
      self._validateRaiFilterSettings(
          messages, args.add_rai_settings_filters, 'add-rai-settings-filters'
      )
    if args.remove_rai_settings_filters:
      self._validateRaiFilterSettings(
          messages,
          args.remove_rai_settings_filters,
          'remove-rai-settings-filters',
      )
    if args.IsSpecified('basic_config_filter_enforcement') and ((
        args.IsSpecified('advanced_config_inspect_template')
        or args.IsSpecified('advanced_config_deidentify_template')
    )):
      raise exceptions.ConflictingArgumentsException(
          'basic_config_filter_enforcement', 'sdp_advanced_config_*_template'
      )
    if args.IsSpecified('add_integrated_services'):
      self._validateIntegratedServices(messages, args.add_integrated_services)
    if args.IsSpecified('remove_integrated_services'):
      self._validateRemoveIntegratedServices(messages, args)
    if args.IsSpecified('clear_integrated_services'):
      self._validateClearIntegratedServices(messages, args)
    if args.IsSpecified('vertex_ai_enforcement_type'):
      self._validateEnforcementType(
          args.vertex_ai_enforcement_type, 'vertex-ai'
      )
    if args.IsSpecified('google_mcp_server_enforcement_type'):
      self._validateEnforcementType(
          args.google_mcp_server_enforcement_type, 'google-mcp-server'
      )

  def _RunUpdate(self, original, args):
    api_version = model_armor_api.GetApiFromTrack(self.ReleaseTrack())
    api_client = model_armor_api.FloorSettings(api_version=api_version)
    messages = api_client.GetMessages()
    self._validateArgs(messages, args)
    floor_setting_updated = original

    if floor_setting_updated.filterConfig is None:
      floor_setting_updated.filterConfig = messages.FilterConfig()

    # Collect the list of update masks
    update_mask = []
    if args.IsSpecified(
        'pi_and_jailbreak_filter_settings_enforcement'
    ) or args.IsSpecified('pi_and_jailbreak_filter_settings_confidence_level'):
      update_mask.append('filter_config.pi_and_jailbreak_filter_settings')
    if args.IsSpecified('malicious_uri_filter_settings_enforcement'):
      update_mask.append('filter_config.malicious_uri_filter_settings')
    if (
        args.IsSpecified('basic_config_filter_enforcement')
        or args.IsSpecified('advanced_config_inspect_template')
        or args.IsSpecified('advanced_config_deidentify_template')
    ):
      update_mask.append('filter_config.sdp_settings')
    if (
        args.IsSpecified('add_rai_settings_filters')
        or args.IsSpecified('remove_rai_settings_filters')
        or args.IsSpecified('clear_rai_settings_filters')
        or args.IsSpecified('rai_settings_filters')
    ):
      update_mask.append('filter_config.rai_settings')
    if args.IsSpecified('enable_floor_setting_enforcement'):
      update_mask.append('enable_floor_setting_enforcement')
    if (
        args.IsSpecified('add_integrated_services')
        or args.IsSpecified('remove_integrated_services')
        or args.IsSpecified('clear_integrated_services')
    ):
      update_mask.append('integrated_services')
    if args.IsSpecified('vertex_ai_enforcement_type'):
      self._updateMaskForEnforcementType(
          service_floor_setting_arg='ai_platform_floor_setting',
          arg_enforcement_type=args.vertex_ai_enforcement_type,
          update_mask=update_mask,
      )
    if args.IsSpecified('google_mcp_server_enforcement_type'):
      self._updateMaskForEnforcementType(
          service_floor_setting_arg='google_mcp_server_floor_setting',
          arg_enforcement_type=args.google_mcp_server_enforcement_type,
          update_mask=update_mask,
      )
    if args.IsSpecified('enable_vertex_ai_cloud_logging'):
      update_mask.append('ai_platform_floor_setting.enable_cloud_logging')
    if args.IsSpecified('enable_google_mcp_server_cloud_logging'):
      update_mask.append('google_mcp_server_floor_setting.enable_cloud_logging')
    if args.IsSpecified('enable_multi_language_detection'):
      update_mask.append('floor_setting_metadata.multi_language_detection')

    if not update_mask:
      possible_args = [
          '--pi-and-jailbreak-filter-settings-enforcement',
          '--pi-and-jailbreak-filter-settings-confidence-level',
          '--malicious-uri-filter-settings-enforcement',
          '--basic-config-filter-enforcement',
          '--advanced-config-inspect-template',
          '--advanced-config-deidentify-template',
          '--rai-settings-filters',
          '--add-rai-settings-filters',
          '--remove-rai-settings-filters',
          '--clear-rai-settings-filters',
          '--enable-floor-setting-enforcement',
          '--add-integrated-services',
          '--remove-integrated-services',
          '--clear-integrated-services',
          '--enable-vertex-ai-cloud-logging',
          '--vertex-ai-enforcement-type',
          '--enable-google-mcp-server-cloud-logging',
          '--google-mcp-server-enforcement-type',
          '--enable-multi-language-detection',
      ]

      raise exceptions.MinimumArgumentException(
          possible_args,
          self.NO_CHANGES_MESSAGE.format(floor_setting=args.full_uri),
      )

    if 'filter_config.rai_settings' in update_mask:
      self._UpdateRaiSettings(messages, args, floor_setting_updated)

    if 'filter_config.pi_and_jailbreak_filter_settings' in update_mask:
      self._UpdatePiAndJailbreakSettings(messages, args, floor_setting_updated)

    if 'filter_config.malicious_uri_filter_settings' in update_mask:
      self._UpdateMaliciousUriSettings(messages, args, floor_setting_updated)

    if 'filter_config.sdp_settings' in update_mask:
      self._UpdateSdpSettings(messages, args, floor_setting_updated)

    defaulted_enforcement = {}
    if (
        args.IsSpecified('add_integrated_services')
        or args.IsSpecified('remove_integrated_services')
        or args.IsSpecified('clear_integrated_services')
    ):
      defaulted_enforcement = self._UpdateIntegratedServices(
          messages, args, floor_setting_updated, update_mask
      )

    # Handle Service Specific FloorSettings
    # (e.g., Cloud Logging, Enforcement Type).
    self._UpdateServiceSpecificSettings(messages, args, floor_setting_updated)

    if args.IsSpecified('enable_multi_language_detection'):
      self._UpdateMultiLanguageDetection(messages, args, floor_setting_updated)

    if 'enable_floor_setting_enforcement' in update_mask:
      if args.IsSpecified('enable_floor_setting_enforcement'):
        floor_setting_updated.enableFloorSettingEnforcement = (
            args.enable_floor_setting_enforcement.lower() == 'true'
        )
    return (
        api_client.Update(
            name=args.full_uri,
            floor_setting=floor_setting_updated,
            update_mask=update_mask,
        ),
        defaulted_enforcement,
    )

  def _UpdateRaiSettings(self, messages, args, floor_setting_updated):
    """Updates the RaiFilterSettings in the FloorSetting."""
    rai_filters = []
    if floor_setting_updated.filterConfig.raiSettings is not None:
      rai_filters = floor_setting_updated.filterConfig.raiSettings.raiFilters

    if args.IsSpecified('rai_settings_filters'):
      rai_filters = []
      for item in [json.loads(f) for f in args.rai_settings_filters]:
        arg_filter_type = messages.RaiFilter.FilterTypeValueValuesEnum(
            self._GetEnumValue(item['filterType'])
        )
        arg_confidence_level = (
            messages.RaiFilter.ConfidenceLevelValueValuesEnum(
                self._GetEnumValue(item['confidenceLevel'])
            )
        )
        rai_filters.append(
            messages.RaiFilter(
                filterType=arg_filter_type,
                confidenceLevel=arg_confidence_level,
            )
        )
      floor_setting_updated.filterConfig.raiSettings = (
          messages.RaiFilterSettings(raiFilters=rai_filters)
      )
    if args.IsSpecified('add_rai_settings_filters'):
      for item in [json.loads(f) for f in args.add_rai_settings_filters]:
        already_exists = False
        arg_filter_type = messages.RaiFilter.FilterTypeValueValuesEnum(
            self._GetEnumValue(item['filterType'])
        )
        arg_confidence_level = (
            messages.RaiFilter.ConfidenceLevelValueValuesEnum(
                self._GetEnumValue(item['confidenceLevel'])
            )
        )
        for _, rai_filter in enumerate(rai_filters):
          if arg_filter_type == rai_filter.filterType:
            already_exists = True
            rai_filters.remove(rai_filter)
            rai_filters.append(
                messages.RaiFilter(
                    filterType=arg_filter_type,
                    confidenceLevel=arg_confidence_level,
                )
            )
            break
        if not already_exists:
          rai_filters.append(
              messages.RaiFilter(
                  filterType=arg_filter_type,
                  confidenceLevel=arg_confidence_level,
              )
          )
        floor_setting_updated.filterConfig.raiSettings = (
            messages.RaiFilterSettings(raiFilters=rai_filters)
        )

    if args.IsSpecified('remove_rai_settings_filters'):
      for item in [json.loads(f) for f in args.remove_rai_settings_filters]:
        arg_filter_type = messages.RaiFilter.FilterTypeValueValuesEnum(
            self._GetEnumValue(item['filterType'])
        )
        arg_confidence_level = (
            messages.RaiFilter.ConfidenceLevelValueValuesEnum(
                self._GetEnumValue(item['confidenceLevel'])
            )
        )
        for _, rai_filter in enumerate(rai_filters):
          if (
              messages.RaiFilter.FilterTypeValueValuesEnum(arg_filter_type)
              == rai_filter.filterType
              and messages.RaiFilter.ConfidenceLevelValueValuesEnum(
                  arg_confidence_level
              )
              == rai_filter.confidenceLevel
          ):
            rai_filters.remove(rai_filter)
            break
    if args.IsSpecified('clear_rai_settings_filters'):
      floor_setting_updated.filterConfig.raiSettings = None

  def _UpdatePiAndJailbreakSettings(
      self, messages, args, floor_setting_updated
  ):
    """Updates the PiAndJailbreakFilterSettings in the FloorSetting."""
    if args.IsSpecified('pi_and_jailbreak_filter_settings_enforcement'):
      pi_and_jailbreak_filter_settings_enforcement = self._GetEnumValue(
          args.pi_and_jailbreak_filter_settings_enforcement
      )
      if (
          floor_setting_updated.filterConfig.piAndJailbreakFilterSettings
          is None
      ):
        floor_setting_updated.filterConfig.piAndJailbreakFilterSettings = messages.PiAndJailbreakFilterSettings(
            filterEnforcement=messages.PiAndJailbreakFilterSettings.FilterEnforcementValueValuesEnum(
                pi_and_jailbreak_filter_settings_enforcement
            )
        )
      else:
        floor_setting_updated.filterConfig.piAndJailbreakFilterSettings.filterEnforcement = messages.PiAndJailbreakFilterSettings.FilterEnforcementValueValuesEnum(
            pi_and_jailbreak_filter_settings_enforcement
        )
    if args.IsSpecified('pi_and_jailbreak_filter_settings_confidence_level'):
      pi_and_jailbreak_filter_settings_confidence_level = self._GetEnumValue(
          args.pi_and_jailbreak_filter_settings_confidence_level
      )
      if (
          floor_setting_updated.filterConfig.piAndJailbreakFilterSettings
          is None
      ):
        floor_setting_updated.filterConfig.piAndJailbreakFilterSettings = messages.PiAndJailbreakFilterSettings(
            confidenceLevel=messages.PiAndJailbreakFilterSettings.ConfidenceLevelValueValuesEnum(
                pi_and_jailbreak_filter_settings_confidence_level
            )
        )

  def _UpdateMultiLanguageDetection(
      self, messages, args, floor_setting_updated
  ):
    """Updates the MultiLanguageDetection in the FloorSetting."""
    if floor_setting_updated.floorSettingMetadata is None:
      floor_setting_updated.floorSettingMetadata = (
          messages.FloorSettingMetadata()
      )
    if (
        floor_setting_updated.floorSettingMetadata.multiLanguageDetection
        is None
    ):
      floor_setting_updated.floorSettingMetadata.multiLanguageDetection = (
          messages.FloorSettingFloorSettingMetadataMultiLanguageDetection(
              enableMultiLanguageDetection=args.enable_multi_language_detection
          )
      )
    else:
      (
          floor_setting_updated.floorSettingMetadata.multiLanguageDetection.enableMultiLanguageDetection
      ) = args.enable_multi_language_detection

  def _UpdateServiceSpecificSettings(
      self, messages, args, floor_setting_updated
  ):
    """Handles Cloud Logging and Enforcement Type for Integrated Services."""
    services_config = _GetServicesConfig(messages)
    for service_config in services_config:
      service_attr = service_config.service_floor_setting_attr
      service_setting = getattr(floor_setting_updated, service_attr)
      is_cloud_logging_specified = args.IsSpecified(
          service_config.cloud_logging_arg
      )
      is_enforcement_type_specified = args.IsSpecified(
          service_config.enforcement_type_arg
      )
      if is_cloud_logging_specified or is_enforcement_type_specified:
        if service_setting is None:
          service_setting = service_config.setting_message()
          setattr(floor_setting_updated, service_attr, service_setting)

      if is_cloud_logging_specified:
        service_setting = getattr(floor_setting_updated, service_attr)
        service_setting.enableCloudLogging = getattr(
            args, service_config.cloud_logging_arg
        )

      if is_enforcement_type_specified:
        arg_enforcement_type = self._GetEnumValue(
            getattr(args, service_config.enforcement_type_arg)
        )
        self._handleEnforcementType(arg_enforcement_type, service_setting)

  def _UpdateIntegratedServices(
      self, messages, args, floor_setting_updated, update_mask
  ):
    """Updates the IntegratedServices in the FloorSetting."""
    defaulted_enforcement = {}
    services_config = _GetServicesConfig(messages)
    if args.IsSpecified('clear_integrated_services'):
      for service_config in services_config:
        service_attr = service_config.service_floor_setting_attr
        if (
            getattr(floor_setting_updated, service_attr) is not None
            and service_config.enum in floor_setting_updated.integratedServices
        ):
          setattr(floor_setting_updated, service_attr, None)
          update_mask.append(service_config.service_floor_setting_arg)
      floor_setting_updated.integratedServices = []
    if args.IsSpecified('add_integrated_services') or args.IsSpecified(
        'remove_integrated_services'
    ):
      integrated_services = []
      if floor_setting_updated.integratedServices is not None:
        integrated_services = list(floor_setting_updated.integratedServices)

      services_config_by_name = {
          service_config.name: service_config
          for service_config in services_config
      }
      if args.IsSpecified('add_integrated_services'):
        for service in args.add_integrated_services:
          arg_service = self._GetEnumValue(service)
          if arg_service in services_config_by_name:
            found_config = services_config_by_name[arg_service]
            if found_config.enum in integrated_services:
              continue
            # if no enforcement type is specified, set it to INSPECT_ONLY.
            if not args.IsSpecified(found_config.enforcement_type_arg):
              setting_attr = found_config.service_floor_setting_attr
              service_setting = getattr(
                  floor_setting_updated,
                  setting_attr,
              )
              if service_setting is None:
                service_setting = found_config.setting_message()
                setattr(
                    floor_setting_updated,
                    setting_attr,
                    service_setting,
                )
              self._handleEnforcementType('INSPECT_ONLY', service_setting)
              self._updateMaskForEnforcementType(
                  service_floor_setting_arg=found_config.service_floor_setting_arg,
                  arg_enforcement_type='INSPECT_ONLY',
                  update_mask=update_mask,
              )
              setattr(
                  floor_setting_updated,
                  setting_attr,
                  service_setting,
              )
              defaulted_enforcement[found_config.enforcement_type_flag_name] = (
                  True
              )
            if found_config.enum not in integrated_services:
              integrated_services.append(found_config.enum)

      if args.IsSpecified('remove_integrated_services'):
        for service in args.remove_integrated_services:
          arg_service = self._GetEnumValue(service)
          if arg_service in services_config_by_name:
            found_config = services_config_by_name[arg_service]
            if found_config.enum in integrated_services:
              integrated_services.remove(found_config.enum)
              setattr(
                  floor_setting_updated,
                  found_config.service_floor_setting_attr,
                  None,
              )
              update_mask.append(found_config.service_floor_setting_arg)

      floor_setting_updated.integratedServices = integrated_services
    return defaulted_enforcement

  def _UpdateMaliciousUriSettings(self, messages, args, floor_setting_updated):
    """Updates the MaliciousUriFilterSettings in the FloorSetting."""
    if args.IsSpecified('malicious_uri_filter_settings_enforcement'):
      if floor_setting_updated.filterConfig.maliciousUriFilterSettings is None:
        floor_setting_updated.filterConfig.maliciousUriFilterSettings = messages.MaliciousUriFilterSettings(
            filterEnforcement=messages.MaliciousUriFilterSettings.FilterEnforcementValueValuesEnum(
                self._GetEnumValue(
                    args.malicious_uri_filter_settings_enforcement
                )
            )
        )
      else:
        floor_setting_updated.filterConfig.maliciousUriFilterSettings.filterEnforcement = messages.MaliciousUriFilterSettings.FilterEnforcementValueValuesEnum(
            self._GetEnumValue(args.malicious_uri_filter_settings_enforcement)
        )

  def _UpdateSdpSettings(self, messages, args, floor_setting_updated):
    """Updates the SdpFilterSettings in the FloorSetting."""
    if args.IsSpecified('basic_config_filter_enforcement'):
      if floor_setting_updated.filterConfig.sdpSettings is None:
        floor_setting_updated.filterConfig.sdpSettings = messages.SdpFilterSettings(
            basicConfig=messages.SdpBasicConfig(
                filterEnforcement=(
                    messages.SdpBasicConfig.FilterEnforcementValueValuesEnum(
                        self._GetEnumValue(args.basic_config_filter_enforcement)
                    )
                )
            )
        )
      else:
        floor_setting_updated.filterConfig.sdpSettings.advancedConfig = None
        floor_setting_updated.filterConfig.sdpSettings.basicConfig = messages.SdpBasicConfig(
            filterEnforcement=messages.SdpBasicConfig.FilterEnforcementValueValuesEnum(
                self._GetEnumValue(args.basic_config_filter_enforcement)
            )
        )
    if args.IsSpecified('advanced_config_inspect_template'):
      if floor_setting_updated.filterConfig.sdpSettings is None:
        floor_setting_updated.filterConfig.sdpSettings = (
            messages.SdpFilterSettings(
                advancedConfig=messages.SdpAdvancedConfig(
                    inspectTemplate=args.advanced_config_inspect_template
                )
            )
        )
      else:
        floor_setting_updated.filterConfig.sdpSettings.basicConfig = None
        if (
            floor_setting_updated.filterConfig.sdpSettings.advancedConfig
            is None
        ):
          floor_setting_updated.filterConfig.sdpSettings.advancedConfig = (
              messages.SdpAdvancedConfig(
                  inspectTemplate=args.advanced_config_inspect_template
              )
          )
        else:
          floor_setting_updated.filterConfig.sdpSettings.advancedConfig.inspectTemplate = (
              args.advanced_config_inspect_template
          )
    if args.IsSpecified('advanced_config_deidentify_template'):
      if floor_setting_updated.filterConfig.sdpSettings is None:
        floor_setting_updated.filterConfig.sdpSettings = (
            messages.SdpFilterSettings(
                advancedConfig=messages.SdpAdvancedConfig(
                    deidentifyTemplate=args.advanced_config_deidentify_template
                )
            )
        )
      else:
        floor_setting_updated.filterConfig.sdpSettings.basicConfig = None
        if (
            floor_setting_updated.filterConfig.sdpSettings.advancedConfig
            is None
        ):
          floor_setting_updated.filterConfig.sdpSettings.advancedConfig = (
              messages.SdpAdvancedConfig(
                  deidentifyTemplate=args.advanced_config_deidentify_template
              )
          )
        else:
          floor_setting_updated.filterConfig.sdpSettings.advancedConfig.deidentifyTemplate = (
              args.advanced_config_deidentify_template
          )

  def Run(self, args):
    api_version = model_armor_api.GetApiFromTrack(self.ReleaseTrack())
    full_uri = args.full_uri
    original = model_armor_api.FloorSettings(api_version=api_version).Get(
        full_uri
    )
    (res, defaulted_enforcement) = self._RunUpdate(original, args)
    defaulted_enforcement_services_flags = []
    if defaulted_enforcement:
      for service in defaulted_enforcement.items():
        defaulted_enforcement_services_flags.append(
            f'{service[0]}=INSPECT_AND_BLOCK'
        )

      defaulted_services_str = ' and '.join(
          [f'"{service}"' for service in defaulted_enforcement_services_flags]
      )
      message = (
          'Enforcement type defaulted to INSPECT_ONLY. This means that traffic'
          ' violating Model Armor settings will be inspected but not blocked.'
          f' To block such traffic, please specify {defaulted_services_str}.'
      )
      log.status.Print(message)
    return res
