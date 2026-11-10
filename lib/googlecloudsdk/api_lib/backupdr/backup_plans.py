# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Cloud Backup Plans client."""


import collections

from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.backupdr import util as command_util
from googlecloudsdk.core import properties


# TODO: b/416214401 - Add type annotations.


class BackupPlansClient(util.BackupDrClientBase):
  """Cloud Backup Plans client."""

  def __init__(self, api_version=util.DEFAULT_API_VERSION):
    super(BackupPlansClient, self).__init__(api_version=api_version)
    self.service = self.client.projects_locations_backupPlans

  def _ParseStorageTier(self, storage_tier):
    if not isinstance(storage_tier, str) or storage_tier not in (
        'STANDARD',
        'ARCHIVE',
    ):
      raise exceptions.InvalidArgumentException(
          'storage-tier',
          f'Invalid storage-tier value: {storage_tier}. Must be one of:'
          ' STANDARD, ARCHIVE.',
      )
    return self.messages.BackupRule.StorageTierValueValuesEnum(storage_tier)

  def _PreserveStorageTier(
      self, rebuilt_rules, backup_rule_args, current_backup_plan
  ):
    """Preserves existing storageTier on rules where storage-tier is unset."""
    if current_backup_plan is None or not current_backup_plan.backupRules:
      return
    existing_tier_by_id = {
        rule.ruleId: rule.storageTier
        for rule in current_backup_plan.backupRules
        if getattr(rule, 'storageTier', None) is not None
    }
    for rebuilt_rule, rule_args in zip(rebuilt_rules, backup_rule_args):
      # Matches _ParseBackupRules, which also treats a null value as unset.
      if rule_args.get('storage-tier') is None:
        existing_tier = existing_tier_by_id.get(rebuilt_rule.ruleId)
        if existing_tier is not None:
          rebuilt_rule.storageTier = existing_tier

  def _ParseBackupRules(self, backup_rules):
    backup_rules_message = []
    if backup_rules is None:
      return []
    for backup_rule in backup_rules:
      standard_schedule = self.messages.StandardSchedule()
      standard_schedule.timeZone = (
          'UTC' if 'time-zone' not in backup_rule else backup_rule['time-zone']
      )
      standard_schedule.backupWindow = self.messages.BackupWindow(
          startHourOfDay=backup_rule['backup-window-start'],
          endHourOfDay=backup_rule['backup-window-end'],
      )
      standard_schedule.recurrenceType = (
          self.messages.StandardSchedule.RecurrenceTypeValueValuesEnum(
              backup_rule['recurrence']
          )
      )
      if 'hourly-frequency' in backup_rule:
        standard_schedule.hourlyFrequency = backup_rule['hourly-frequency']
      if 'days-of-week' in backup_rule:
        standard_schedule.daysOfWeek = [
            self.messages.StandardSchedule.DaysOfWeekValueListEntryValuesEnum(
                day
            )
            for day in backup_rule['days-of-week']
        ]
      if 'week-day-of-month' in backup_rule:
        week_day_of_month = backup_rule['week-day-of-month'].split('-')
        standard_schedule.weekDayOfMonth = self.messages.WeekDayOfMonth(
            weekOfMonth=self.messages.WeekDayOfMonth.WeekOfMonthValueValuesEnum(
                week_day_of_month[0]
            ),
            dayOfWeek=self.messages.WeekDayOfMonth.DayOfWeekValueValuesEnum(
                week_day_of_month[1]
            ),
        )
      if 'days-of-month' in backup_rule:
        standard_schedule.daysOfMonth = backup_rule['days-of-month']
      if 'months' in backup_rule:
        standard_schedule.months = [
            self.messages.StandardSchedule.MonthsValueListEntryValuesEnum(month)
            for month in backup_rule['months']
        ]
      backup_rule_message = self.messages.BackupRule(
          ruleId=backup_rule['rule-id'],
          backupRetentionDays=backup_rule['retention-days'],
          standardSchedule=standard_schedule,
      )
      if 'backup-vault' in backup_rule:
        backup_rule_message.backupVault = backup_rule['backup-vault']
      if 'backup-labels' in backup_rule:
        backup_labels_message = self._ParseBackupLabels(
            backup_rule['backup-labels']
        )
        if backup_labels_message is not None:
          backup_rule_message.backupLabels = backup_labels_message
      if (
          'storage-tier' in backup_rule
          and backup_rule['storage-tier'] is not None
      ):
        backup_rule_message.storageTier = self._ParseStorageTier(
            backup_rule['storage-tier']
        )
      backup_rules_message.append(backup_rule_message)
    return backup_rules_message

  def _ParseBackupLabels(self, backup_labels):
    """Parses the per-rule backup labels of a backup rule."""
    if not backup_labels:
      return None
    additional_properties = []
    if isinstance(backup_labels, str):
      seen_keys = set()
      for label_pair in backup_labels.split(';'):
        if not label_pair.strip():
          continue
        key, sep, value = label_pair.partition('=')
        key = key.strip()
        if not sep or not key:
          raise exceptions.InvalidArgumentException(
              'backup-labels',
              'Backup labels must be in the format key=value. Got:'
              f' {label_pair.strip()}',
          )
        if key in seen_keys:
          raise exceptions.InvalidArgumentException(
              'backup-labels',
              f'Backup label [{key}] is specified more than once.',
          )
        seen_keys.add(key)
        additional_properties.append(
            self.messages.BackupRule.BackupLabelsValue.AdditionalProperty(
                key=key, value=value.strip()
            )
        )
    elif isinstance(backup_labels, dict):
      for key, value in backup_labels.items():
        key = str(key).strip()
        if value is None:
          str_value = ''
        elif isinstance(value, bool):
          str_value = 'true' if value else 'false'
        elif isinstance(value, (str, int, float)):
          str_value = str(value).strip()
        else:
          raise exceptions.InvalidArgumentException(
              'backup-labels',
              f'Backup label [{key}] must have a string value. Got: {value}',
          )
        additional_properties.append(
            self.messages.BackupRule.BackupLabelsValue.AdditionalProperty(
                key=key, value=str_value
            )
        )
    else:
      raise exceptions.InvalidArgumentException(
          'backup-labels',
          'Backup labels must be a map or `key=value` pairs separated by `;`.'
          f' Got: {backup_labels}',
      )
    if not additional_properties:
      return None
    return self.messages.BackupRule.BackupLabelsValue(
        additionalProperties=additional_properties
    )

  def _PreserveBackupLabels(
      self, rebuilt_rules, backup_rule_args, current_backup_plan
  ):
    """Carries over existing per-rule backup labels onto rebuilt rules.

    `--backup-rule` and `--backup-rules-from-file` rebuild each rule from the
    command line (or file) and the update is sent with `updateMask=backupRules`,
    which replaces the whole rule list. Without this, labels set on a rule
    through the API would be silently cleared whenever that rule is modified
    with gcloud. Rules that explicitly specify `backup-labels` (including an
    empty value, which clears the labels) are left as specified.

    Args:
      rebuilt_rules: The BackupRule messages built from user input.
      backup_rule_args: The user-provided rule dicts that `rebuilt_rules` were
        built from, in the same order.
      current_backup_plan: The current Backup Plan.
    """
    current_rules_by_id = {
        rule.ruleId: rule for rule in current_backup_plan.backupRules
    }
    for rule, rule_args in zip(rebuilt_rules, backup_rule_args):
      if 'backup-labels' in rule_args:
        continue
      current_rule = current_rules_by_id.get(rule.ruleId)
      if current_rule is not None and current_rule.backupLabels is not None:
        rule.backupLabels = current_rule.backupLabels

  def Create(
      self,
      resource,
      backup_vault,
      resource_type,
      backup_rules,
      log_retention_days,
      description,
      labels,
      max_custom_on_demand_retention_days,
      disk_properties=None,
      compute_instance_properties=None,
  ):
    """Creates a Backup Plan.

    Args:
      resource: The Backup Plan resource.
      backup_vault: The Backup Vault resource.
      resource_type: The resource type of the Backup Plan.
      backup_rules: The backup rules of the Backup Plan.
      log_retention_days: The log retention days of the Backup Plan.
      description: The description of the Backup Plan.
      labels: The labels of the Backup Plan.
      max_custom_on_demand_retention_days: The custom on demand retention days
        limit of the Backup Plan.
      disk_properties: A dictionary containing the disk properties of the
        Backup Plan. Expected keys include:
        'guest-flush': bool, Whether to enable guest flush.
      compute_instance_properties: A dictionary containing the compute instance
        properties of the Backup Plan. Expected keys include:
        'guest-flush': bool, Whether to enable guest flush.

    Returns:
      The created Backup Plan.
    """
    parent = resource.Parent().RelativeName()
    backup_plan_id = resource.Name()
    labels_message = None
    if labels:
      labels_message = self.messages.BackupPlan.LabelsValue(
          additionalProperties=[
              self.messages.BackupPlan.LabelsValue.AdditionalProperty(
                  key=key, value=value
              )
              for key, value in labels.items()
          ]
      )
    disk_props_message = None
    if disk_properties:
      disk_props_message = self.messages.DiskBackupPlanProperties(
          guestFlush=disk_properties.get('guest-flush', False)
      )

    compute_instance_props_message = None
    if compute_instance_properties:
      boot_disk_only = compute_instance_properties.get('boot-disk-only')
      disk_exclusion_labels = compute_instance_properties.get(
          'disk-exclusion-labels'
      )
      if boot_disk_only is not None and disk_exclusion_labels is not None:
        raise exceptions.InvalidArgumentException(
            '--compute-instance-properties',
            'boot-disk-only and disk-exclusion-labels are mutually exclusive'
            ' properties.',
        )

      disk_exclusion_labels_message = None
      if disk_exclusion_labels:
        labels = []
        if isinstance(disk_exclusion_labels, str):
          for label_pair in disk_exclusion_labels.split(';'):
            if not label_pair:
              continue
            if '=' in label_pair:
              k, v = label_pair.split('=', 1)
              labels.append(self.messages.LabelKeyValPair(key=k, value=v))
            else:
              raise exceptions.InvalidArgumentException(
                  '--compute-instance-properties',
                  'Disk exclusion labels must be in the format key=value. Got:'
                  f' {label_pair}',
              )
        elif isinstance(disk_exclusion_labels, dict):
          for k, v in disk_exclusion_labels.items():
            labels.append(self.messages.LabelKeyValPair(key=k, value=v))
        disk_exclusion_labels_message = self.messages.DiskExclusionLabels(
            labels=labels
        )

      kwargs = {
          'guestFlush': compute_instance_properties.get('guest-flush', False),
      }
      if boot_disk_only is not None:
        kwargs['bootDiskOnly'] = boot_disk_only
      if disk_exclusion_labels_message is not None:
        kwargs['diskExclusionLabels'] = disk_exclusion_labels_message

      compute_instance_props_message = (
          self.messages.ComputeInstanceBackupPlanProperties(**kwargs)
      )

    backup_plan = self.messages.BackupPlan(
        resourceType=resource_type,
        backupVault=backup_vault,
        description=description,
        labels=labels_message,
        backupRules=self._ParseBackupRules(backup_rules),
        logRetentionDays=log_retention_days,
        maxCustomOnDemandRetentionDays=(
            int(max_custom_on_demand_retention_days)
            if max_custom_on_demand_retention_days is not None
            else None
        ),
    )
    if disk_props_message and (
        resource_type.endswith('/Disk')
        or resource_type
        == f'compute.{properties.VALUES.core.universe_domain.Get()}/Disk'
    ):
      backup_plan.diskBackupPlanProperties = disk_props_message
    elif compute_instance_props_message and (
        resource_type.endswith('/Instance')
        or resource_type
        == f'compute.{properties.VALUES.core.universe_domain.Get()}/Instance'
    ):
      backup_plan.computeInstanceBackupPlanProperties = (
          compute_instance_props_message
      )

    request = self.messages.BackupdrProjectsLocationsBackupPlansCreateRequest(
        parent=parent,
        backupPlan=backup_plan,
        backupPlanId=backup_plan_id,
    )
    return self.service.Create(request)

  def Describe(self, resource):
    """Describes a Backup Plan.

    Args:
      resource: The Backup Plan resource.

    Returns:
      The described Backup Plan.
    """
    request = self.messages.BackupdrProjectsLocationsBackupPlansGetRequest(
        name=resource.RelativeName()
    )
    return self.service.Get(request)

  def ParseUpdate(
      self,
      description,
      new_backup_rules_from_file,
      update_backup_rules,
      add_backup_rules,
      remove_backup_rules,
      current_backup_plan,
      log_retention_days,
      max_custom_on_demand_retention_days,
      disk_properties=None,
      compute_instance_properties=None,
  ):
    """Parses the update request for a Backup Plan.

    Args:
      description: The description of the Backup Plan.
      new_backup_rules_from_file: The backup rules to update from file in the
        Backup Plan.
      update_backup_rules: The backup rules to update in the Backup Plan.
      add_backup_rules: The backup rules to add to the Backup Plan.
      remove_backup_rules: The backup rules to remove from the Backup Plan.
      current_backup_plan: The current Backup Plan.
      log_retention_days: The log retention days of the Backup Plan.
      max_custom_on_demand_retention_days: The custom on demand retention days
        limit of the Backup Plan.
      disk_properties: A dictionary containing the disk properties of the
        Backup Plan.
      compute_instance_properties: A dictionary containing the compute instance
        properties of the Backup Plan.

    Returns:
      The updated Backup Plan.

    Raises:
      InvalidArgumentException: If the backup rules are invalid.
      ValueError: If the backup plan is not found.
    """
    if current_backup_plan is None:
      raise ValueError('Could not find the backup plan.')
    updated_backup_plan = self.messages.BackupPlan(
        resourceType=current_backup_plan.resourceType
    )
    if description is not None:
      updated_backup_plan.description = description
    if log_retention_days is not None:
      updated_backup_plan.logRetentionDays = log_retention_days
    if max_custom_on_demand_retention_days is not None:
      updated_backup_plan.maxCustomOnDemandRetentionDays = (
          int(max_custom_on_demand_retention_days)
      )
    current_rule_ids = {rule.ruleId for rule in current_backup_plan.backupRules}
    if new_backup_rules_from_file is not None:
      backup_rules_from_file = self._ParseBackupRules(
          new_backup_rules_from_file
      )
      self._PreserveBackupLabels(
          backup_rules_from_file,
          new_backup_rules_from_file,
          current_backup_plan,
      )
      self._PreserveStorageTier(
          backup_rules_from_file,
          new_backup_rules_from_file,
          current_backup_plan,
      )
      updated_backup_plan.backupRules = backup_rules_from_file
    elif update_backup_rules is not None:
      rule_ids = collections.Counter(
          [rule['rule-id'] for rule in update_backup_rules]
      )
      duplicate_rule_ids = [
          rule_id for rule_id, count in rule_ids.items() if count > 1
      ]
      if duplicate_rule_ids:
        raise exceptions.InvalidArgumentException(
            'rule-id',
            f'Rules {duplicate_rule_ids} found in more than one'
            ' --backup-rule flag.',
        )
      not_found_rule_ids = list(set([
          rule['rule-id']
          for rule in update_backup_rules
          if rule['rule-id'] not in current_rule_ids
      ]))
      if not_found_rule_ids:
        raise exceptions.InvalidArgumentException(
            'rule-id',
            f'Rules {not_found_rule_ids} not found in the backup plan.'
            ' The --backup-rule flag can only be used to modify existing'
            ' rules.',
        )
      parsed_update_rules = self._ParseBackupRules(update_backup_rules)
      self._PreserveBackupLabels(
          parsed_update_rules, update_backup_rules, current_backup_plan
      )
      self._PreserveStorageTier(
          parsed_update_rules, update_backup_rules, current_backup_plan
      )
      updated_rules_by_id = {rule.ruleId: rule for rule in parsed_update_rules}
      updated_backup_plan.backupRules = [
          updated_rules_by_id.get(rule.ruleId, rule)
          for rule in current_backup_plan.backupRules
      ]
    else:
      updated_backup_plan.backupRules = current_backup_plan.backupRules
    if add_backup_rules is not None:
      updated_backup_plan.backupRules.extend(
          self._ParseBackupRules(add_backup_rules)
      )
    if remove_backup_rules is not None:
      not_found_rule_ids = list(
          set(
              rule_id
              for rule_id in remove_backup_rules
              if rule_id not in current_rule_ids
          )
      )
      if not_found_rule_ids:
        raise exceptions.InvalidArgumentException(
            'rule-id',
            f'Rules {not_found_rule_ids} not found in the backup plan.',
        )
      updated_backup_plan.backupRules = [
          rule
          for rule in updated_backup_plan.backupRules
          if rule.ruleId not in remove_backup_rules
      ]
    if disk_properties is not None:
      updated_backup_plan.diskBackupPlanProperties = (
          self.messages.DiskBackupPlanProperties(
              guestFlush=disk_properties.get('guest-flush')
          )
      )
    if compute_instance_properties is not None:
      boot_disk_only = compute_instance_properties.get('boot-disk-only')
      disk_exclusion_labels = compute_instance_properties.get(
          'disk-exclusion-labels'
      )
      if boot_disk_only is not None and disk_exclusion_labels is not None:
        raise exceptions.InvalidArgumentException(
            '--compute-instance-properties',
            'boot-disk-only and disk-exclusion-labels are mutually exclusive'
            ' properties.',
        )

      disk_exclusion_labels_message = None
      if disk_exclusion_labels:
        labels = []
        if isinstance(disk_exclusion_labels, str):
          for label_pair in disk_exclusion_labels.split(';'):
            if '=' in label_pair:
              k, v = label_pair.split('=', 1)
              labels.append(self.messages.LabelKeyValPair(key=k, value=v))
        elif isinstance(disk_exclusion_labels, dict):
          for k, v in disk_exclusion_labels.items():
            labels.append(self.messages.LabelKeyValPair(key=k, value=v))
        disk_exclusion_labels_message = self.messages.DiskExclusionLabels(
            labels=labels
        )

      kwargs = {
          'guestFlush': compute_instance_properties.get('guest-flush'),
      }
      if boot_disk_only is not None:
        kwargs['bootDiskOnly'] = boot_disk_only
      if disk_exclusion_labels_message is not None:
        kwargs['diskExclusionLabels'] = disk_exclusion_labels_message

      updated_backup_plan.computeInstanceBackupPlanProperties = (
          self.messages.ComputeInstanceBackupPlanProperties(**kwargs)
      )
    return updated_backup_plan

  def Update(self, resource, backup_plan, update_mask):
    """Updates a Backup Plan.

    Args:
      resource: The Backup Plan resource.
      backup_plan: The updated Backup Plan.
      update_mask: The update mask to edit the Backup Plan.

    Returns:
      The updated Backup Plan.
    """
    request_id = command_util.GenerateRequestId()
    request = self.messages.BackupdrProjectsLocationsBackupPlansPatchRequest(
        backupPlan=backup_plan,
        name=resource.RelativeName(),
        requestId=request_id,
        updateMask=update_mask,
    )
    return self.service.Patch(request)

  def Delete(self, resource):
    """Deletes a Backup Plan.

    Args:
      resource: The Backup Plan resource.

    Returns:
      The deleted Backup Plan.
    """
    request = self.messages.BackupdrProjectsLocationsBackupPlansDeleteRequest(
        name=resource.RelativeName()
    )
    return self.service.Delete(request)
