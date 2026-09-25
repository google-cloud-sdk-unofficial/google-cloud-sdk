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
"""Utilities for constructing Assured api messages."""


import types
from typing import Any, Dict, List, Optional, Sequence, Union

from googlecloudsdk.api_lib.assured import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import yaml

ReleaseTrack = calliope_base.ReleaseTrack


def GetMessages(release_track):
  return util.GetMessagesModule(release_track)


def GetWorkloadMessage(release_track):
  return WORKLOAD_MAP.get(release_track)


def GetComplianceRegimesEnum(release_track):
  return GetWorkloadMessage(release_track).ComplianceRegimeValueValuesEnum


def GetPartnersEnum(release_track):
  return GetWorkloadMessage(release_track).PartnerValueValuesEnum


def GetKmsSettings(release_track):
  return KMS_SETTINGS_MAP.get(release_track)


def GetResourceSettings(release_track):
  return RESOURCE_SETTINGS_MAP.get(release_track)


def GetPartnerPermissions(release_track):
  return PARTNER_PERMISSIONS_MAP.get(release_track)


def CreateAssuredParent(organization_id, location):
  return 'organizations/{}/locations/{}'.format(organization_id, location)


def CreateAssuredWorkload(
    display_name=None,
    compliance_regime=None,
    partner=None,
    partner_services_billing_account=None,
    partner_permissions=None,
    billing_account=None,
    next_rotation_time=None,
    rotation_period=None,
    labels=None,
    etag=None,
    provisioned_resources_parent=None,
    resource_settings=None,
    enable_sovereign_controls=None,
    violation_notifications_enabled=None,
    release_track=ReleaseTrack.GA,
):
  """Construct an Assured Workload message for Assured Workloads Beta API requests.

  Args:
    display_name: str, display name of the Assured Workloads environment.
    compliance_regime: str, the compliance regime, which is one of:
      FEDRAMP_MODERATE, FEDRAMP_HIGH, IL4 or CJIS.
    partner: str, the partner regime/controls.
    partner_services_billing_account: str, the billing account of the partner
      service in the form: billingAccounts/{BILLING_ACCOUNT_ID}
    partner_permissions: dict, dictionary of permission names and values for the
      partner regime.
    billing_account: str, the billing account of the Assured Workloads
      environment in the form: billingAccounts/{BILLING_ACCOUNT_ID}
    next_rotation_time: str, the next key rotation time for the Assured
      Workloads environment, for example: 2020-12-30T10:15:00.00Z
    rotation_period: str, the time between key rotations, for example: 172800s.
    labels: dict, dictionary of label keys and values of the Assured Workloads
      environment.
    etag: str, the etag of the Assured Workloads environment.
    provisioned_resources_parent: str, parent of provisioned projects, e.g.
      folders/{FOLDER_ID}.
    resource_settings: list of key=value pairs to set customized resource
      settings, which can be one of the following: consumer-project-id,
      consumer-project-name, encryption-keys-project-id,
      encryption-keys-project-name or keyring-id, for example:
      consumer-project-id={ID1},encryption-keys-project-id={ID2}
    enable_sovereign_controls: bool, whether to enable sovereign controls for
      the Assured Workloads environment.
    violation_notifications_enabled: bool, whether email notifications are
      enabled or disabled
    release_track: ReleaseTrack, gcloud release track being used

  Returns:
    A populated Assured Workloads message for the Assured Workloads Beta API.
  """

  workload_message = GetWorkloadMessage(release_track)
  workload = workload_message()
  if etag:
    workload.etag = etag
  if billing_account:
    workload.billingAccount = billing_account
  if display_name:
    workload.displayName = display_name
  if violation_notifications_enabled:
    workload.violationNotificationsEnabled = GetViolationNotificationsEnabled(
        violation_notifications_enabled
    )
  if labels:
    workload.labels = CreateLabels(labels, workload_message)
  if compliance_regime:
    workload.complianceRegime = arg_utils.ChoiceToEnum(
        compliance_regime, GetComplianceRegimesEnum(release_track)
    )
  if partner:
    workload.partner = arg_utils.ChoiceToEnum(
        partner, GetPartnersEnum(release_track)
    )
  if partner_services_billing_account:
    workload.partnerServicesBillingAccount = partner_services_billing_account
  if partner_permissions:
    workload.partnerPermissions = GetPartnerPermissions(release_track)(
        dataLogsViewer=partner_permissions['data-logs-viewer']
    )
  if provisioned_resources_parent:
    workload.provisionedResourcesParent = provisioned_resources_parent
  if next_rotation_time and rotation_period:
    workload.kmsSettings = GetKmsSettings(release_track)(
        nextRotationTime=next_rotation_time, rotationPeriod=rotation_period
    )
  if resource_settings:
    workload.resourceSettings = CreateResourceSettingsList(
        resource_settings, release_track
    )
  if enable_sovereign_controls:
    workload.enableSovereignControls = enable_sovereign_controls
  return workload


def CreateAssuredWorkloadsParent(organization_id, location, workload_id):
  return 'organizations/{}/locations/{}/workloads/{}'.format(
      organization_id, location, workload_id
  )


def GetViolationNotificationsEnabled(violation_notifications_enabled):
  if violation_notifications_enabled.lower() == 'true':
    return True
  if violation_notifications_enabled.lower() == 'false':
    return False
  else:
    return violation_notifications_enabled


def CreateLabels(labels, workload_message):
  workload_labels = []
  for key, value in labels.items():
    new_label = workload_message.LabelsValue.AdditionalProperty(
        key=key, value=value
    )
    workload_labels.append(new_label)
  return workload_message.LabelsValue(additionalProperties=workload_labels)


def CreateResourceSettingsList(resource_settings, release_track):
  """Construct a list of ResourceSettings for Assured Workload object.

  Args:
    resource_settings: a list of key=value pairs of customized resource
      settings.
    release_track: ReleaseTrack, gcloud release track being used.

  Returns:
    A list of ResourceSettings for the Assured Workload object.
  """
  resource_settings_dict = {}
  for key, value in resource_settings.items():
    resource_type = GetResourceType(key, release_track)
    resource_settings = (
        resource_settings_dict[resource_type]
        if resource_type in resource_settings_dict
        else CreateResourceSettings(resource_type, release_track)
    )
    if key.endswith('-id'):
      resource_settings.resourceId = value
    elif key.endswith('-name'):
      resource_settings.displayName = value
    resource_settings_dict[resource_type] = resource_settings
  return list(resource_settings_dict.values())


def GetResourceType(key, release_track):
  """Returns a resource settings type from the key.

  Args:
    key: str, the setting name, which can be one of the following -
      consumer-project-id, consumer-project-name, encryption-keys-project-id,
      encryption-keys-project-name or keyring-id.
    release_track: ReleaseTrack, gcloud release track being used.
  """
  resource_settings_message = GetResourceSettings(release_track)
  if key.startswith('consumer-project'):
    return (
        resource_settings_message.ResourceTypeValueValuesEnum.CONSUMER_PROJECT
    )
  elif key.startswith('encryption-keys-project'):
    return (
        resource_settings_message.ResourceTypeValueValuesEnum.ENCRYPTION_KEYS_PROJECT
    )
  elif key.startswith('keyring'):
    return resource_settings_message.ResourceTypeValueValuesEnum.KEYRING


def CreateResourceSettings(resource_type, release_track):
  resource_settings_message = GetResourceSettings(release_track)
  return resource_settings_message(resourceType=resource_type)


def CreateUpdateMask(display_name, labels, violation_notifications_enabled):
  update_mask = []
  if display_name:
    update_mask.append('workload.display_name')
  if labels:
    update_mask.append('workload.labels')
  if violation_notifications_enabled:
    update_mask.append('workload.violation_notifications_enabled')
  return ','.join(update_mask)


def CreateCreateRequest(
    external_id, parent, workload, release_track=ReleaseTrack.GA
):
  """Construct an Assured Workload Create Request for Assured Workloads API requests.

  Args:
    external_id: str, the identifier that identifies this Assured Workloads
      environment externally.
    parent: str, the parent organization of the Assured Workloads environment to
      be created, in the form: organizations/{ORG_ID}/locations/{LOCATION}.
    workload: Workload, new Assured Workloads environment containing the values
      to be used.
    release_track: ReleaseTrack, gcloud release track being used

  Returns:
    A populated Assured Workloads Update Request for the Assured Workloads API.
  """
  if release_track == ReleaseTrack.GA:
    return util.GetMessagesModule(
        release_track
    ).AssuredworkloadsOrganizationsLocationsWorkloadsCreateRequest(
        externalId=external_id,
        parent=parent,
        googleCloudAssuredworkloadsV1Workload=workload,
    )
  else:
    return util.GetMessagesModule(
        release_track
    ).AssuredworkloadsOrganizationsLocationsWorkloadsCreateRequest(
        externalId=external_id,
        parent=parent,
        googleCloudAssuredworkloadsV1beta1Workload=workload,
    )


def CreateUpdateRequest(
    workload, name, update_mask, release_track=ReleaseTrack.GA
):
  """Construct an Assured Workload Update Request for Assured Workloads API requests.

  Args:
    workload: googleCloudAssuredworkloadsV1beta1Workload, new Assured Workloads
      environment containing the new configuration values to be used.
    name: str, the name for the Assured Workloads environment being updated in
      the form:
      organizations/{ORG_ID}/locations/{LOCATION}/workloads/{WORKLOAD_ID}.
    update_mask: str, list of the fields to be updated, for example,
      workload.display_name,workload.labels
    release_track: ReleaseTrack, gcloud release track being used

  Returns:
    A populated Assured Workloads Update Request for the Assured Workloads API.
  """
  messages = util.GetMessagesModule(release_track)
  if release_track == ReleaseTrack.GA:
    return messages.AssuredworkloadsOrganizationsLocationsWorkloadsPatchRequest(
        googleCloudAssuredworkloadsV1Workload=workload,
        name=name,
        updateMask=update_mask,
    )
  else:
    return messages.AssuredworkloadsOrganizationsLocationsWorkloadsPatchRequest(
        googleCloudAssuredworkloadsV1beta1Workload=workload,
        name=name,
        updateMask=update_mask,
    )


def CreateAcknowledgeRequest(
    name, comment, acknowledge_type=None, release_track=ReleaseTrack.GA
):
  """Construct an Assured Workload Violation Acknowledgement Request.

  Args:
    name: str, the name for the Assured Workloads violation being described in
      the form:
      organizations/{ORG_ID}/locations/{LOCATION}/workloads/{WORKLOAD_ID}/violations/{VIOLATION_ID}.
    comment: str, the business justification which the user wants to add while
      acknowledging a violation.
    acknowledge_type: str, the acknowledge type for specified violation, which
      is one of: SINGLE_VIOLATION - to acknowledge specified violation,
      EXISTING_CHILD_RESOURCE_VIOLATIONS - to acknowledge specified org policy
      violation and all associated child resource violations.
    release_track: ReleaseTrack, gcloud release track being used

  Returns:
    A populated Assured Workloads Violation Acknowledgement Request.
  """
  messages = util.GetMessagesModule(release_track)
  if acknowledge_type:
    acknowledge_type = messages.GoogleCloudAssuredworkloadsV1beta1AcknowledgeViolationRequest.AcknowledgeTypeValueValuesEnum(
        acknowledge_type
    )
  if release_track == ReleaseTrack.GA:
    return messages.AssuredworkloadsOrganizationsLocationsWorkloadsViolationsAcknowledgeRequest(
        googleCloudAssuredworkloadsV1AcknowledgeViolationRequest=messages.GoogleCloudAssuredworkloadsV1AcknowledgeViolationRequest(
            comment=comment
        ),
        name=name,
    )
  else:
    return messages.AssuredworkloadsOrganizationsLocationsWorkloadsViolationsAcknowledgeRequest(
        googleCloudAssuredworkloadsV1beta1AcknowledgeViolationRequest=messages.GoogleCloudAssuredworkloadsV1beta1AcknowledgeViolationRequest(
            comment=comment, acknowledgeType=acknowledge_type
        ),
        name=name,
    )


WORKLOAD_MAP = {
    ReleaseTrack.ALPHA: GetMessages(
        ReleaseTrack.BETA
    ).GoogleCloudAssuredworkloadsV1beta1Workload,
    ReleaseTrack.BETA: GetMessages(
        ReleaseTrack.BETA
    ).GoogleCloudAssuredworkloadsV1beta1Workload,
    ReleaseTrack.GA: GetMessages(
        ReleaseTrack.GA
    ).GoogleCloudAssuredworkloadsV1Workload,
}

KMS_SETTINGS_MAP = {
    ReleaseTrack.ALPHA: GetMessages(
        ReleaseTrack.BETA
    ).GoogleCloudAssuredworkloadsV1beta1WorkloadKMSSettings,
    ReleaseTrack.BETA: GetMessages(
        ReleaseTrack.BETA
    ).GoogleCloudAssuredworkloadsV1beta1WorkloadKMSSettings,
    ReleaseTrack.GA: GetMessages(
        ReleaseTrack.GA
    ).GoogleCloudAssuredworkloadsV1WorkloadKMSSettings,
}

RESOURCE_SETTINGS_MAP = {
    ReleaseTrack.ALPHA: GetMessages(
        ReleaseTrack.BETA
    ).GoogleCloudAssuredworkloadsV1beta1WorkloadResourceSettings,
    ReleaseTrack.BETA: GetMessages(
        ReleaseTrack.BETA
    ).GoogleCloudAssuredworkloadsV1beta1WorkloadResourceSettings,
    ReleaseTrack.GA: GetMessages(
        ReleaseTrack.GA
    ).GoogleCloudAssuredworkloadsV1WorkloadResourceSettings,
}

PARTNER_PERMISSIONS_MAP = {
    ReleaseTrack.ALPHA: GetMessages(
        ReleaseTrack.BETA
    ).GoogleCloudAssuredworkloadsV1beta1WorkloadPartnerPermissions,
    ReleaseTrack.BETA: GetMessages(
        ReleaseTrack.BETA
    ).GoogleCloudAssuredworkloadsV1beta1WorkloadPartnerPermissions,
    ReleaseTrack.GA: GetMessages(
        ReleaseTrack.GA
    ).GoogleCloudAssuredworkloadsV1WorkloadPartnerPermissions,
}


def GetMessagesV2(
    release_track: ReleaseTrack = ReleaseTrack.ALPHA,
) -> types.ModuleType:
  """Returns the v2 messages module for Assured Workloads.

  Args:
    release_track: gcloud release track being used.

  Returns:
    V2 messages module for Assured Workloads.
  """
  return util.GetMessagesModule(release_track=release_track, api_version='v2')


def _IsNonEmpty(target: Any) -> bool:
  """Returns whether the given target resource configuration is non-empty."""
  if target is None:
    return False
  if isinstance(target, str) and not target.strip():
    return False
  return True


def BuildResourceConfig(
    target_project: Optional[str] = None,
    target_folder: Optional[str] = None,
    new_project_dict: Optional[Dict[str, Any]] = None,
    new_folder_dict: Optional[Dict[str, Any]] = None,
    release_track: ReleaseTrack = ReleaseTrack.ALPHA,
) -> Any:
  """Builds a ResourceConfig message for Assured Workloads V2.

  Args:
    target_project: Resource name of an existing GCP project.
    target_folder: Resource name of an existing GCP folder.
    new_project_dict: Configuration to provision a new GCP project.
    new_folder_dict: Configuration to provision a new GCP folder.
    release_track: gcloud release track being used.

  Returns:
    ResourceConfig message for the Assured Workloads environment.

  Raises:
    calliope_exceptions.InvalidArgumentException: If zero or multiple target
      types are provided or required fields are missing.
  """
  targets = [
      t
      for t in [
          target_project,
          target_folder,
          new_project_dict,
          new_folder_dict,
      ]
      if _IsNonEmpty(t)
  ]
  if len(targets) != 1:
    raise calliope_exceptions.InvalidArgumentException(
        'resource_config',
        'Exactly one target resource configuration must be provided (one of'
        ' target_project, target_folder, new_project_dict, or'
        ' new_folder_dict).',
    )

  messages = GetMessagesV2(release_track)

  if target_project is not None:
    return messages.GoogleCloudAssuredworkloadsV2ResourceConfig(
        existingProject=target_project
    )

  if target_folder is not None:
    return messages.GoogleCloudAssuredworkloadsV2ResourceConfig(
        existingFolder=target_folder
    )

  if new_project_dict is not None:
    parent = new_project_dict.get('parent')
    display_name = (
        new_project_dict.get('display_name')
        or new_project_dict.get('displayName')
        or new_project_dict.get('display-name')
    )
    billing_account = (
        new_project_dict.get('billing_account')
        or new_project_dict.get('billingAccount')
        or new_project_dict.get('billing-account')
    )
    if not parent or not display_name or not billing_account:
      raise calliope_exceptions.InvalidArgumentException(
          'new_project_config',
          'new_project_dict must contain parent, display_name, and'
          ' billing_account.',
      )
    new_project = messages.GoogleCloudAssuredworkloadsV2NewProjectConfig(
        parent=parent,
        displayName=display_name,
        billingAccount=billing_account,
    )
    return messages.GoogleCloudAssuredworkloadsV2ResourceConfig(
        newProjectConfig=new_project
    )

  if new_folder_dict is not None:
    parent = new_folder_dict.get('parent')
    display_name = (
        new_folder_dict.get('display_name')
        or new_folder_dict.get('displayName')
        or new_folder_dict.get('display-name')
    )
    if not parent or not display_name:
      raise calliope_exceptions.InvalidArgumentException(
          'new_folder_config',
          'new_folder_dict must contain parent and display_name.',
      )
    new_folder = messages.GoogleCloudAssuredworkloadsV2NewFolderConfig(
        parent=parent,
        displayName=display_name,
    )
    return messages.GoogleCloudAssuredworkloadsV2ResourceConfig(
        newFolderConfig=new_folder
    )


def BuildFrameworkReference(
    framework: str,
    major_revision_id: Optional[Union[int, str]] = None,
    release_track: ReleaseTrack = ReleaseTrack.ALPHA,
) -> Any:
  """Builds a FrameworkReference message for Assured Workloads V2.

  Args:
    framework: Name or resource name of the framework.
    major_revision_id: Optional major version of the framework.
    release_track: gcloud release track being used.

  Returns:
    FrameworkReference message for the Assured Workloads environment.

  Raises:
    calliope_exceptions.InvalidArgumentException: If framework is empty or
      major_revision_id cannot be converted to an integer.
  """
  if not framework:
    raise calliope_exceptions.InvalidArgumentException(
        'framework', 'Framework reference must not be empty.'
    )

  messages = GetMessagesV2(release_track)
  if major_revision_id is not None:
    try:
      revision = int(major_revision_id)
    except (ValueError, TypeError):
      raise calliope_exceptions.InvalidArgumentException(
          'major_revision_id',
          f'Major revision ID must be an integer, got: {major_revision_id}.',
      )
  else:
    revision = None
  return messages.GoogleCloudAssuredworkloadsV2FrameworkReference(
      framework=framework, majorRevisionId=revision
  )


def BuildParamValue(value: Any, messages: types.ModuleType) -> Any:
  """Constructs a GoogleCloudAssuredworkloadsV2ParamValue from a Python value.

  Args:
    value: Raw Python value or existing ParamValue to represent.
    messages: V2 messages module for Assured Workloads.

  Returns:
    ParamValue message representing the given value.

  Raises:
    calliope_exceptions.InvalidArgumentException: If value type is unsupported.
  """
  if isinstance(value, messages.GoogleCloudAssuredworkloadsV2ParamValue):
    return value
  if isinstance(value, bool):
    return messages.GoogleCloudAssuredworkloadsV2ParamValue(boolValue=value)
  elif isinstance(value, (int, float)):
    return messages.GoogleCloudAssuredworkloadsV2ParamValue(
        numberValue=float(value)
    )
  elif isinstance(value, str):
    return messages.GoogleCloudAssuredworkloadsV2ParamValue(stringValue=value)
  elif isinstance(value, (list, tuple)):
    string_list = messages.GoogleCloudAssuredworkloadsV2StringList(
        values=[str(v) for v in value]
    )
    return messages.GoogleCloudAssuredworkloadsV2ParamValue(
        stringListValue=string_list
    )
  elif isinstance(value, dict):
    if 'name' in value and (
        'value' in value
        or 'parameter_value' in value
        or 'parameterValue' in value
    ):
      sub_val = (
          value.get('value')
          if 'value' in value
          else value.get('parameter_value', value.get('parameterValue'))
      )
      sub_param_val = (
          sub_val
          if isinstance(
              sub_val, messages.GoogleCloudAssuredworkloadsV2ParamValue
          )
          else BuildParamValue(sub_val, messages)
      )
      sub_param = messages.GoogleCloudAssuredworkloadsV2Parameter(
          name=value['name'], parameterValue=sub_param_val
      )
      return messages.GoogleCloudAssuredworkloadsV2ParamValue(
          oneofValue=sub_param
      )
    elif 'stringValue' in value or 'string_value' in value:
      s_val = (
          value.get('stringValue')
          if 'stringValue' in value
          else value.get('string_value')
      )
      return messages.GoogleCloudAssuredworkloadsV2ParamValue(stringValue=s_val)
    elif 'boolValue' in value or 'bool_value' in value:
      b_val = (
          value.get('boolValue')
          if 'boolValue' in value
          else value.get('bool_value')
      )
      return messages.GoogleCloudAssuredworkloadsV2ParamValue(boolValue=b_val)
    elif 'numberValue' in value or 'number_value' in value:
      n_val = float(
          value.get('numberValue')
          if 'numberValue' in value
          else value.get('number_value')
      )
      return messages.GoogleCloudAssuredworkloadsV2ParamValue(numberValue=n_val)
    elif 'stringListValue' in value or 'string_list_value' in value:
      raw_list = (
          value.get('stringListValue')
          if 'stringListValue' in value
          else value.get('string_list_value')
      )
      if isinstance(raw_list, dict):
        raw_list = raw_list.get('values', [])
      string_list = messages.GoogleCloudAssuredworkloadsV2StringList(
          values=[str(v) for v in raw_list or []]
      )
      return messages.GoogleCloudAssuredworkloadsV2ParamValue(
          stringListValue=string_list
      )
    else:
      raise calliope_exceptions.InvalidArgumentException(
          'parameter_value', f'Unsupported parameter dict format: {value}'
      )
  else:
    raise calliope_exceptions.InvalidArgumentException(
        'parameter_value', f'Unsupported parameter value type: {type(value)}'
    )


def BuildParameter(
    name: str,
    value: Any,
    release_track: ReleaseTrack = ReleaseTrack.ALPHA,
) -> Any:
  """Constructs a GoogleCloudAssuredworkloadsV2Parameter message.

  Args:
    name: Parameter name.
    value: Parameter value as a ParamValue message or raw Python value.
    release_track: gcloud release track being used.

  Returns:
    Parameter message with the given name and serialized value.
  """
  messages = GetMessagesV2(release_track)
  if isinstance(value, messages.GoogleCloudAssuredworkloadsV2ParamValue):
    param_val = value
  else:
    param_val = BuildParamValue(value, messages)
  return messages.GoogleCloudAssuredworkloadsV2Parameter(
      name=name, parameterValue=param_val
  )


def BuildCloudControlConfigs(
    control_dicts_or_file: Union[Sequence[Dict[str, Any]], Dict[str, Any], str],
    release_track: ReleaseTrack = ReleaseTrack.ALPHA,
) -> List[Any]:
  """Builds a list of CloudControlConfig messages for Assured Workloads V2.

  Args:
    control_dicts_or_file: List of configuration dictionaries or path to a YAML
      file specifying control configurations.
    release_track: gcloud release track being used.

  Returns:
    List of CloudControlConfig messages.

  Raises:
    calliope_exceptions.InvalidArgumentException: If configurations are
      malformed or missing required fields.
  """
  messages = GetMessagesV2(release_track)

  if isinstance(control_dicts_or_file, str):
    raw_data = yaml.load_path(control_dicts_or_file)
  else:
    raw_data = control_dicts_or_file

  if isinstance(raw_data, dict):
    raw_data = [raw_data]

  if not isinstance(raw_data, list):
    raise calliope_exceptions.InvalidArgumentException(
        'cloud_control_configs',
        'Cloud control configs must be a list of configurations or a path to a'
        ' YAML file.',
    )

  cloud_control_configs = []
  enum_type = (
      messages.GoogleCloudAssuredworkloadsV2CloudControlConfig.EnforcementModeValueValuesEnum
  )

  for item in raw_data:
    control_name = (
        item.get('cloud_control')
        or item.get('cloudControl')
        or item.get('cloud-control')
    )
    if not control_name:
      raise calliope_exceptions.InvalidArgumentException(
          'cloud_control', 'Cloud control name is required.'
      )

    revision = (
        item.get('cloud_control_revision')
        or item.get('cloudControlRevision')
        or item.get('cloud-control-revision')
        or item.get('revision')
    )
    if revision is None:
      raise calliope_exceptions.InvalidArgumentException(
          'cloud_control_revision', 'Cloud control revision is required.'
      )

    mode_val = (
        item.get('enforcement_mode')
        or item.get('enforcementMode')
        or item.get('enforcement-mode')
    )
    if not mode_val:
      raise calliope_exceptions.InvalidArgumentException(
          'enforcement_mode', 'Enforcement mode is required.'
      )

    if isinstance(mode_val, str):
      mode_normalized = mode_val.strip().upper().replace('-', '_')
      try:
        enforcement_mode = enum_type(mode_normalized)
      except TypeError as exc:
        raise calliope_exceptions.InvalidArgumentException(
            'enforcement_mode',
            f'Invalid enforcement mode: {mode_val}. Valid options are'
            ' PREVENTIVE, DETECTIVE, AUDIT.',
        ) from exc
    else:
      enforcement_mode = mode_val

    raw_params = item.get('parameters', [])
    param_objs = []
    if isinstance(raw_params, dict):
      for k, v in raw_params.items():
        param_objs.append(BuildParameter(k, v, release_track))
    elif isinstance(raw_params, list):
      for p in raw_params:
        if isinstance(p, dict):
          p_name = p.get('name')
          p_val = (
              p.get('value')
              if 'value' in p
              else p.get('parameter_value', p.get('parameterValue'))
          )
          if p_name is not None and p_val is not None:
            param_objs.append(BuildParameter(p_name, p_val, release_track))
          elif len(p) == 1:
            k, v = next(iter(p.items()))
            param_objs.append(BuildParameter(k, v, release_track))

    try:
      revision_int = int(revision)
    except (ValueError, TypeError):
      raise calliope_exceptions.InvalidArgumentException(
          'cloud_control_revision',
          f'Cloud control revision must be an integer, got: {revision}.',
      )

    config = messages.GoogleCloudAssuredworkloadsV2CloudControlConfig(
        cloudControl=control_name,
        cloudControlRevision=revision_int,
        enforcementMode=enforcement_mode,
        parameters=param_objs,
    )
    cloud_control_configs.append(config)

  return cloud_control_configs


def BuildCmekConfig(
    key_ring_id: str,
    dedicated_project_dict: Optional[Dict[str, Any]] = None,
    is_folder_target: bool = True,
    release_track: ReleaseTrack = ReleaseTrack.ALPHA,
) -> Any:
  """Builds a CmekConfig message for Assured Workloads V2.

  Args:
    key_ring_id: Identifier of the KMS key ring.
    dedicated_project_dict: Optional configuration dictionary for dedicated CMEK
      project creation.
    is_folder_target: Whether the workload target is a folder.
    release_track: gcloud release track being used.

  Returns:
    CmekConfig message for Assured Workloads V2.

  Raises:
    calliope_exceptions.InvalidArgumentException: If key_ring_id is empty or
      dedicated project configuration is used for a non-folder target.
  """
  if not key_ring_id:
    raise calliope_exceptions.InvalidArgumentException(
        'key_ring_id', 'Key ring ID is required for CMEK configuration.'
    )

  messages = GetMessagesV2(release_track)
  dedicated_config = None

  if dedicated_project_dict:
    if not is_folder_target:
      raise calliope_exceptions.InvalidArgumentException(
          'dedicated_project_config',
          'Dedicated CMEK project configuration is only valid when the target'
          ' resource is a folder.',
      )
    billing_account = (
        dedicated_project_dict.get('billing_account')
        or dedicated_project_dict.get('billingAccount')
        or dedicated_project_dict.get('billing-account')
    )
    if not billing_account:
      raise calliope_exceptions.InvalidArgumentException(
          'billing_account',
          'Billing account is required for dedicated CMEK project'
          ' configuration.',
      )
    display_name = (
        dedicated_project_dict.get('display_name')
        or dedicated_project_dict.get('displayName')
        or dedicated_project_dict.get('display-name')
    )
    project_id = (
        dedicated_project_dict.get('project_id')
        or dedicated_project_dict.get('projectId')
        or dedicated_project_dict.get('project-id')
    )
    dedicated_config = (
        messages.GoogleCloudAssuredworkloadsV2CmekProjectCreationConfig(
            billingAccount=billing_account,
            displayName=display_name,
            projectId=project_id,
        )
    )

  return messages.GoogleCloudAssuredworkloadsV2CmekConfig(
      keyRingId=key_ring_id, dedicatedProjectConfig=dedicated_config
  )


def BuildAssuredWorkloadsSettings(
    name: Optional[str] = None,
    olpc_mode: Optional[Union[str, Any]] = None,
    etag: Optional[str] = None,
    release_track: ReleaseTrack = ReleaseTrack.ALPHA,
) -> Any:
  """Builds an AssuredWorkloadsSettings message for Assured Workloads V2.

  Args:
    name: Optional resource name of settings singleton.
    olpc_mode: Optional OLPC mode string or enum value.
    etag: Optional optimistic concurrency control etag.
    release_track: gcloud release track being used.

  Returns:
    AssuredWorkloadsSettings message for the given organization.

  Raises:
    calliope_exceptions.InvalidArgumentException: If olpc_mode is invalid.
  """
  messages = GetMessagesV2(release_track)
  olpc_mode_enum = None

  if olpc_mode:
    enum_type = (
        messages.GoogleCloudAssuredworkloadsV2AssuredWorkloadsSettings.OlpcModeValueValuesEnum
    )
    if isinstance(olpc_mode, str):
      normalized = olpc_mode.strip().upper().replace('-', '_')
      if not normalized.startswith('OLPC_MODE_'):
        normalized = 'OLPC_MODE_' + normalized
      try:
        olpc_mode_enum = enum_type(normalized)
      except TypeError as exc:
        raise calliope_exceptions.InvalidArgumentException(
            'olpc_mode',
            f'Invalid OLPC mode: {olpc_mode}. Valid options are opt-out,'
            ' strict-il5, allow-mixed-il5, strict-il5-forward, unspecified.',
        ) from exc
    else:
      olpc_mode_enum = olpc_mode

  return messages.GoogleCloudAssuredworkloadsV2AssuredWorkloadsSettings(
      name=name, olpcMode=olpc_mode_enum, etag=etag
  )


def CreateAssuredWorkloadV2(
    resource_config: Any,
    framework: Any,
    cloud_control_configs: List[Any],
    description: Optional[str] = None,
    cmek_config: Optional[Any] = None,
    etag: Optional[str] = None,
    release_track: ReleaseTrack = ReleaseTrack.ALPHA,
) -> Any:
  """Constructs an Assured Workloads V2 Workload message.

  Args:
    resource_config: ResourceConfig message for the workload.
    framework: FrameworkReference message for the workload.
    cloud_control_configs: List of CloudControlConfig messages.
    description: Optional description for the workload environment.
    cmek_config: Optional CMEK configuration message.
    etag: Optional optimistic concurrency control etag.
    release_track: gcloud release track being used.

  Returns:
    Workload message for Assured Workloads V2.
  """
  messages = GetMessagesV2(release_track)
  workload = messages.GoogleCloudAssuredworkloadsV2Workload(
      resourceConfig=resource_config,
      framework=framework,
      cloudControlConfigs=cloud_control_configs,
  )
  if description:
    workload.description = description
  if cmek_config:
    workload.cmekConfig = cmek_config
  if etag:
    workload.etag = etag
  return workload


def CreateUpdateMaskV2(
    description: Optional[Any] = None,
    cloud_control_configs: Optional[Any] = None,
) -> str:
  """Constructs a comma-separated update mask for Assured Workloads V2.

  Args:
    description: Indicator if description is being updated.
    cloud_control_configs: Indicator if cloud_control_configs is updated.

  Returns:
    Comma-separated field mask string.
  """
  update_mask = []
  if description is not None:
    update_mask.append('description')
  if cloud_control_configs is not None:
    update_mask.append('cloud_control_configs')
  return ','.join(update_mask)
