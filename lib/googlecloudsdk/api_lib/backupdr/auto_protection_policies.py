# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Cloud AutoProtectionPolicies client."""

from typing import Any, Dict, List, Optional

from googlecloudsdk.api_lib.backupdr import util


class AutoProtectionPoliciesClient(util.BackupDrClientBase):
  """Cloud AutoProtectionPolicies client."""

  def __init__(self, api_version=util.DEFAULT_API_VERSION):
    super(AutoProtectionPoliciesClient, self).__init__(api_version=api_version)
    self.service = self.client.projects_locations_autoProtectionPolicies

  def Create(
      self,
      resource: Any,
      description: str,
      criteria_label: Dict[str, str],
      backup_plan_details: Optional[List[Dict[str, str]]] = None,
  ):
    """Creates a AutoProtectionPolicy."""
    parent = resource.Parent().RelativeName()
    policy_id = resource.Name()
    policy = self.messages.AutoProtectionPolicy(description=description)

    if criteria_label:
      policy.criteria = self.messages.Criteria(
          matchingConditions=[
              self.messages.MatchingCondition(
                  labelCondition=self.messages.KeyValuePair(
                      key=criteria_label['key'],
                      values=[criteria_label['value']]
                  )
              )
          ]
      )

    if backup_plan_details:
      policy.backupPlanDetails = [
          self.messages.BackupPlanDetail(
              resourceType=detail['resource-type'],
              backupPlan=detail['backup-plan']
          ) for detail in backup_plan_details
      ]

    request = self.messages.BackupdrProjectsLocationsAutoProtectionPoliciesCreateRequest(
        parent=parent,
        autoProtectionPolicyId=policy_id,
        autoProtectionPolicy=policy,
    )
    return self.service.Create(request)

  def Patch(
      self,
      resource: Any,
      description: Optional[str],
      criteria_label: Optional[Dict[str, str]],
      backup_plan_details: Optional[List[Dict[str, str]]],
  ):
    """Updates an AutoProtectionPolicy.

    Args:
      resource: The resource reference of the AutoProtectionPolicy to update.
      description: The description of the AutoProtectionPolicy.
      criteria_label: The criteria label of the AutoProtectionPolicy.
      backup_plan_details: A list of dicts with 'resource-type' and
        'backup-plan' containing the details of the backup plans to be applied
        to the resources matching the criteria.

    Returns:
      The long-running operation.
    """
    policy = self.messages.AutoProtectionPolicy()
    update_mask = []

    if description is not None:
      policy.description = description
      update_mask.append('description')

    if criteria_label is not None:
      policy.criteria = self.messages.Criteria(
          matchingConditions=[
              self.messages.MatchingCondition(
                  labelCondition=self.messages.KeyValuePair(
                      key=criteria_label['key'],
                      values=[criteria_label['value']]
                  )
              )
          ]
      )
      update_mask.append('criteria')

    if backup_plan_details is not None:
      # If provided, ensure we send the entire object
      # to the patch endpoint
      policy.backupPlanDetails = []
      for detail in backup_plan_details:
        policy.backupPlanDetails.append(
            self.messages.BackupPlanDetail(
                resourceType=detail['resource-type'],
                backupPlan=detail['backup-plan']
            )
        )
      update_mask.append('backupPlanDetails')

    request = self.messages.BackupdrProjectsLocationsAutoProtectionPoliciesPatchRequest(
        name=resource.RelativeName(),
        autoProtectionPolicy=policy,
        updateMask=','.join(update_mask)
    )
    return self.service.Patch(request)
