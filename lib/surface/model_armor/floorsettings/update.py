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

import json

from googlecloudsdk.api_lib.model_armor import api as model_armor_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.model_armor import args as model_armor_args
from googlecloudsdk.command_lib.model_armor import util as model_armor_util


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
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
        help_text='Enable or disable the floor setting enforcement',
    )
    model_armor_args.AddMaliciousUriFilterSettingsEnforcement(parser)
    model_armor_args.AddPIJBFilterSettingsGroup(parser)
    model_armor_args.AddSDPFilterBasicConfigGroup(parser)
    model_armor_args.AddRaiFilterSettingsGroup(parser)

  def _GetEnumValue(self, value):
    return value.upper().replace('-', '_')

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
      ]

      raise exceptions.MinimumArgumentException(
          possible_args,
          self.NO_CHANGES_MESSAGE.format(floor_setting=args.full_uri),
      )

    if 'filter_config.rai_settings' in update_mask:
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
        for item in json.loads(args.remove_rai_settings_filters):
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

    if 'filter_config.pi_and_jailbreak_filter_settings' in update_mask:
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
        else:
          floor_setting_updated.filterConfig.piAndJailbreakFilterSettings.confidenceLevel = messages.PiAndJailbreakFilterSettings.ConfidenceLevelValueValuesEnum(
              pi_and_jailbreak_filter_settings_confidence_level
          )

    if 'filter_config.malicious_uri_filter_settings' in update_mask:
      if args.IsSpecified('malicious_uri_filter_settings_enforcement'):
        if (
            floor_setting_updated.filterConfig.maliciousUriFilterSettings
            is None
        ):
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

    if 'filter_config.sdp_settings' in update_mask:
      if args.IsSpecified('basic_config_filter_enforcement'):
        if floor_setting_updated.filterConfig.sdpSettings is None:
          floor_setting_updated.filterConfig.sdpSettings = messages.SdpFilterSettings(
              basicConfig=messages.SdpBasicConfig(
                  filterEnforcement=(
                      messages.SdpBasicConfig.FilterEnforcementValueValuesEnum(
                          self._GetEnumValue(
                              args.basic_config_filter_enforcement
                          )
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
          floor_setting_updated.filterConfig.sdpSettings = messages.SdpFilterSettings(
              advancedConfig=messages.SdpAdvancedConfig(
                  deidentifyTemplate=args.advanced_config_deidentify_template
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

    if 'enable_floor_setting_enforcement' in update_mask:
      if args.IsSpecified('enable_floor_setting_enforcement'):
        floor_setting_updated.enableFloorSettingEnforcement = (
            args.enable_floor_setting_enforcement.lower() == 'true'
        )
    return api_client.Update(
        name=args.full_uri,
        floor_setting=floor_setting_updated,
        update_mask=update_mask,
    )

  def Run(self, args):
    api_version = model_armor_api.GetApiFromTrack(self.ReleaseTrack())
    full_uri = args.full_uri
    original = model_armor_api.FloorSettings(api_version=api_version).Get(
        full_uri
    )
    res = self._RunUpdate(original, args)
    return res


# TODO(b/455024265): Remove this class once GA is ready and merge into
# Update.
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpdateAlphaBeta(Update):
  """Update the FloorSetting resource.

  Updates the floor setting resource with the given name.
  """

  NO_CHANGES_MESSAGE = 'There are no changes to the floor setting for update.'

  @staticmethod
  def Args(parser):

    Update.Args(parser)
    model_armor_args.AddIntegratedServices(parser)
    model_armor_args.AddVertexAiFloorSetting(parser)
    model_armor_args.AddMultiLanguageDetection(parser)

  def _GetEnumValue(self, value):
    return value.upper().replace('-', '_')

  def _validateEnforcementType(self, enforcement_type):
    if (
        enforcement_type == 'INSPECT_ONLY'
        or enforcement_type == 'INSPECT_AND_BLOCK'
    ):
      return
    raise exceptions.InvalidArgumentException(
        'vertex-ai-enforcement-type',
        'argument --vertex-ai-enforcement-type: Invalid choice:'
        f" '{enforcement_type}'. Valid choices are [INSPECT_AND_BLOCK,"
        ' INSPECT_ONLY].',
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
    for service in args.remove_integrated_services:
      if service == 'VERTEX_AI':
        if args.IsSpecified('vertex_ai_enforcement_type'):
          raise exceptions.ConflictingArgumentsException(
              '--remove-integrated-services=VERTEX_AI',
              '--vertex-ai-enforcement-type',
          )
        if args.IsSpecified('enable_vertex_ai_cloud_logging'):
          raise exceptions.ConflictingArgumentsException(
              '--remove-integrated-services=VERTEX_AI',
              '--enable-vertex-ai-cloud-logging',
          )

  def _validateClearIntegratedServices(self, args):
    """Validate the arguments for clearing integrated services."""
    if args.IsSpecified('vertex_ai_enforcement_type'):
      raise exceptions.ConflictingArgumentsException(
          '--clear-integrated-services',
          '--vertex-ai-enforcement-type',
      )
    if args.IsSpecified('enable_vertex_ai_cloud_logging'):
      raise exceptions.ConflictingArgumentsException(
          '--clear-integrated-services',
          '--enable-vertex-ai-cloud-logging',
      )

  def _handleEnforcementType(self, arg_enforcement_type, service_floor_setting):
    """Handle the enforcement type for Integreated Services."""
    if arg_enforcement_type == 'INSPECT_ONLY':
      service_floor_setting.inspectOnly = True
      service_floor_setting.inspectAndBlock = False
    elif arg_enforcement_type == 'INSPECT_AND_BLOCK':
      service_floor_setting.inspectOnly = False
      service_floor_setting.inspectAndBlock = True

  def _validateArgs(self, messages, args):
    """Validate the arguments."""
    # Call parent validation for GA flags
    super(UpdateAlphaBeta, self)._validateArgs(messages, args)

    if args.IsSpecified('add_integrated_services'):
      self._validateIntegratedServices(messages, args.add_integrated_services)
    if args.IsSpecified('remove_integrated_services'):
      self._validateRemoveIntegratedServices(messages, args)
    if args.IsSpecified('clear_integrated_services'):
      self._validateClearIntegratedServices(args)
    if args.IsSpecified('vertex_ai_enforcement_type'):
      self._validateEnforcementType(args.vertex_ai_enforcement_type)

  def _RunUpdate(self, original, args):
    api_version = model_armor_api.GetApiFromTrack(self.ReleaseTrack())
    api_client = model_armor_api.FloorSettings(api_version=api_version)
    messages = api_client.GetMessages()
    self._validateArgs(messages, args)
    floor_setting_updated = original
    vertex_ai_enforcement_defaulted = False

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
    if args.IsSpecified('enable_vertex_ai_cloud_logging'):
      update_mask.append('ai_platform_floor_setting.enable_cloud_logging')
    if args.IsSpecified('vertex_ai_enforcement_type'):
      if args.vertex_ai_enforcement_type == 'INSPECT_ONLY':
        update_mask.append('ai_platform_floor_setting.inspect_only')
      elif args.vertex_ai_enforcement_type == 'INSPECT_AND_BLOCK':
        update_mask.append('ai_platform_floor_setting.inspect_and_block')
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
          '--enable-multi-language-detection',
      ]

      raise exceptions.MinimumArgumentException(
          possible_args,
          self.NO_CHANGES_MESSAGE.format(floor_setting=args.full_uri),
      )

    if args.IsSpecified('clear_integrated_services'):
      if (
          floor_setting_updated.aiPlatformFloorSetting is not None
          and messages.FloorSetting.IntegratedServicesValueListEntryValuesEnum.AI_PLATFORM
          in floor_setting_updated.integratedServices
      ):
        floor_setting_updated.aiPlatformFloorSetting = None
        update_mask.append('ai_platform_floor_setting')
      floor_setting_updated.integratedServices = []
    if args.IsSpecified('add_integrated_services') or args.IsSpecified(
        'remove_integrated_services'
    ):
      integrated_services = []
      if floor_setting_updated.integratedServices is not None:
        integrated_services = list(floor_setting_updated.integratedServices)

      if args.IsSpecified('add_integrated_services'):
        for service in args.add_integrated_services:
          if service == 'VERTEX_AI':
            service = 'AI_PLATFORM'
          arg_service = (
              messages.FloorSetting.IntegratedServicesValueListEntryValuesEnum(
                  self._GetEnumValue(service)
              )
          )
          # if no enforcement type is specified, set it to INSPECT_ONLY.
          if (
              arg_service
              == messages.FloorSetting.IntegratedServicesValueListEntryValuesEnum.AI_PLATFORM
              and not args.IsSpecified('vertex_ai_enforcement_type')
          ):
            vertex_ai_enforcement_defaulted = True
            update_mask.append('ai_platform_floor_setting.inspect_only')
            if floor_setting_updated.aiPlatformFloorSetting is None:
              floor_setting_updated.aiPlatformFloorSetting = (
                  messages.AiPlatformFloorSetting()
              )
            floor_setting_updated.aiPlatformFloorSetting.inspectOnly = True

          if arg_service not in integrated_services:
            integrated_services.append(arg_service)

      if args.IsSpecified('remove_integrated_services'):
        for service in args.remove_integrated_services:
          if service == 'VERTEX_AI':
            service = 'AI_PLATFORM'
          arg_service = (
              messages.FloorSetting.IntegratedServicesValueListEntryValuesEnum(
                  self._GetEnumValue(service)
              )
          )
          if arg_service in integrated_services:
            integrated_services.remove(arg_service)
            if (
                arg_service
                == messages.FloorSetting.IntegratedServicesValueListEntryValuesEnum.AI_PLATFORM
            ):
              floor_setting_updated.aiPlatformFloorSetting = None
              update_mask.append('ai_platform_floor_setting')
      floor_setting_updated.integratedServices = integrated_services

    if args.IsSpecified('enable_vertex_ai_cloud_logging') or args.IsSpecified(
        'vertex_ai_enforcement_type'
    ):
      if floor_setting_updated.aiPlatformFloorSetting is None:
        floor_setting_updated.aiPlatformFloorSetting = (
            messages.AiPlatformFloorSetting()
        )
      if args.IsSpecified('enable_vertex_ai_cloud_logging'):
        floor_setting_updated.aiPlatformFloorSetting.enableCloudLogging = (
            args.enable_vertex_ai_cloud_logging
        )
      if args.IsSpecified('vertex_ai_enforcement_type'):
        arg_enforcement_type = self._GetEnumValue(
            args.vertex_ai_enforcement_type
        )
        self._handleEnforcementType(
            arg_enforcement_type, floor_setting_updated.aiPlatformFloorSetting
        )
    if args.IsSpecified('enable_multi_language_detection'):
      if floor_setting_updated.floorSettingMetadata is None:
        floor_setting_updated.floorSettingMetadata = (
            messages.FloorSettingMetadata()
        )
      if (
          floor_setting_updated.floorSettingMetadata.multiLanguageDetection
          is None
      ):
        floor_setting_updated.floorSettingMetadata.multiLanguageDetection = messages.FloorSettingFloorSettingMetadataMultiLanguageDetection(
            enableMultiLanguageDetection=args.enable_multi_language_detection
        )
      else:
        floor_setting_updated.floorSettingMetadata.multiLanguageDetection.enableMultiLanguageDetection = (
            args.enable_multi_language_detection
        )
    if 'filter_config.rai_settings' in update_mask:
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
        for item in json.loads(args.remove_rai_settings_filters):
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

    if 'filter_config.pi_and_jailbreak_filter_settings' in update_mask:
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
        else:
          floor_setting_updated.filterConfig.piAndJailbreakFilterSettings.confidenceLevel = messages.PiAndJailbreakFilterSettings.ConfidenceLevelValueValuesEnum(
              pi_and_jailbreak_filter_settings_confidence_level
          )

    if 'filter_config.malicious_uri_filter_settings' in update_mask:
      if args.IsSpecified('malicious_uri_filter_settings_enforcement'):
        if (
            floor_setting_updated.filterConfig.maliciousUriFilterSettings
            is None
        ):
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

    if 'filter_config.sdp_settings' in update_mask:
      if args.IsSpecified('basic_config_filter_enforcement'):
        if floor_setting_updated.filterConfig.sdpSettings is None:
          floor_setting_updated.filterConfig.sdpSettings = messages.SdpFilterSettings(
              basicConfig=messages.SdpBasicConfig(
                  filterEnforcement=(
                      messages.SdpBasicConfig.FilterEnforcementValueValuesEnum(
                          self._GetEnumValue(
                              args.basic_config_filter_enforcement
                          )
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
          floor_setting_updated.filterConfig.sdpSettings = messages.SdpFilterSettings(
              advancedConfig=messages.SdpAdvancedConfig(
                  deidentifyTemplate=args.advanced_config_deidentify_template
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
        vertex_ai_enforcement_defaulted,
    )

  def Run(self, args):
    api_version = model_armor_api.GetApiFromTrack(self.ReleaseTrack())
    full_uri = args.full_uri
    original = model_armor_api.FloorSettings(api_version=api_version).Get(
        full_uri
    )
    res, vertex_ai_enforcement_defaulted = self._RunUpdate(original, args)
    if vertex_ai_enforcement_defaulted:
      print(
          'Vertex AI enforcement type defaulted to INSPECT_ONLY. This means '
          'that malicious traffic will be inspected but not blocked. To block '
          'malicious traffic, please specify '
          '"--vertex-ai-enforcement-type=INSPECT_AND_BLOCK".'
      )
    return res
