# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Organization Firewall Policy."""


from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log

OP_COLLECTION_NAME = 'compute.globalOrganizationOperations'
API_COLLECTION_NAME = 'compute.firewallPolicies'


class DeletePoller(poller.Poller):

  def GetResult(self, operation):
    # For delete operations, once the operation status is DONE, there is
    # nothing further to fetch.
    return


class OrgFirewallPolicy(object):
  """Abstracts an organization firewall policy resource."""

  def __init__(
      self, ref=None, compute_client=None, resources=None, version='v1'
  ):
    self.ref = ref
    self._compute_client = compute_client
    self._resources = resources
    self._version = 'v1' if version == 'ga' else version
    self._op_has_project = self._HasProject(OP_COLLECTION_NAME)
    self._api_has_project = self._HasProject(API_COLLECTION_NAME)

  def _HasProject(self, collection):
    collection_info = self._resources.GetCollectionInfo(
        collection, self._version
    )
    return (
        'projects' in collection_info.path
        or 'projects' in collection_info.base_url
    )

  @property
  def _client(self):
    return self._compute_client.apitools_client

  @property
  def _messages(self):
    return self._compute_client.messages

  @property
  def _service(self):
    return self._client.firewallPolicies

  def _MakeAddAssociationRequestTuple(
      self, association, firewall_policy_id, replace_existing_association
  ):
    return (
        self._client.firewallPolicies,
        'AddAssociation',
        self._messages.ComputeFirewallPoliciesAddAssociationRequest(
            firewallPolicyAssociation=association,
            firewallPolicy=firewall_policy_id,
            replaceExistingAssociation=replace_existing_association,
        ),
    )

  def _MakeDeleteAssociationRequestTuple(
      self, firewall_policy_id, association_name
  ):
    return (
        self._client.firewallPolicies,
        'RemoveAssociation',
        self._messages.ComputeFirewallPoliciesRemoveAssociationRequest(
            name=association_name, firewallPolicy=firewall_policy_id
        ),
    )

  def _MakeListAssociationsRequestTuple(self, target_resource):
    return (
        self._client.firewallPolicies,
        'ListAssociations',
        self._messages.ComputeFirewallPoliciesListAssociationsRequest(
            targetResource=target_resource
        ),
    )

  def _MakeDeleteRequestTuple(self, fp_id=None):
    return (
        self._client.firewallPolicies,
        'Delete',
        self._messages.ComputeFirewallPoliciesDeleteRequest(
            firewallPolicy=fp_id
        ),
    )

  def _MakeUpdateRequestTuple(self, fp_id=None, firewall_policy=None):
    if fp_id:
      return (
          self._client.firewallPolicies,
          'Patch',
          self._messages.ComputeFirewallPoliciesPatchRequest(
              firewallPolicy=fp_id, firewallPolicyResource=firewall_policy
          ),
      )
    return (
        self._client.firewallPolicies,
        'Patch',
        self._messages.ComputeFirewallPoliciesPatchRequest(
            firewallPolicy=self.ref.Name(),
            firewallPolicyResource=firewall_policy,
        ),
    )

  def _MakeDescribeRequestTuple(self, fp_id=None):
    if fp_id:
      return (
          self._client.firewallPolicies,
          'Get',
          self._messages.ComputeFirewallPoliciesGetRequest(
              firewallPolicy=fp_id
          ),
      )
    return (
        self._client.firewallPolicies,
        'Get',
        self._messages.ComputeFirewallPoliciesGetRequest(
            firewallPolicy=self.ref.Name()
        ),
    )

  def _MakeMoveRequestTuple(self, fp_id=None, parent_id=None):
    return (
        self._client.firewallPolicies,
        'Move',
        self._messages.ComputeFirewallPoliciesMoveRequest(
            firewallPolicy=fp_id, parentId=parent_id
        ),
    )

  def _MakeCloneRulesRequestTuple(
      self, dest_fp_id=None, source_firewall_policy=None
  ):
    return (
        self._client.firewallPolicies,
        'CloneRules',
        self._messages.ComputeFirewallPoliciesCloneRulesRequest(
            firewallPolicy=dest_fp_id,
            sourceFirewallPolicy=source_firewall_policy,
        ),
    )

  def _MakeListRequestTuple(self, parent_id):
    return (
        self._client.firewallPolicies,
        'List',
        self._messages.ComputeFirewallPoliciesListRequest(parentId=parent_id),
    )

  def _MakeCreateRequestTuple(self, firewall_policy, parent_id):
    return (
        self._client.firewallPolicies,
        'Insert',
        self._messages.ComputeFirewallPoliciesInsertRequest(
            parentId=parent_id, firewallPolicy=firewall_policy
        ),
    )

  def _MakeForceStartProgressiveRolloutRequestTuple(self, firewall_policy):
    return (
        self._client.firewallPolicies,
        'ForceStartProgressiveRollout',
        self._messages.ComputeFirewallPoliciesForceStartProgressiveRolloutRequest(
            firewallPolicy=firewall_policy
        ),
    )

  def AddAssociation(
      self,
      association=None,
      firewall_policy_id=None,
      replace_existing_association=False,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to add an association."""

    if batch_mode:
      requests = [
          self._MakeAddAssociationRequestTuple(
              association, firewall_policy_id, replace_existing_association
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.AddAssociation(
        self._MakeAddAssociationRequestTuple(
            association, firewall_policy_id, replace_existing_association
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message='Adding an association for the organization firewall policy.',
        fp_id=firewall_policy_id,
    )

  def DeleteAssociation(
      self,
      firewall_policy_id=None,
      association_name=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to delete an association."""

    if batch_mode:
      requests = [
          self._MakeDeleteAssociationRequestTuple(
              firewall_policy_id, association_name
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.RemoveAssociation(
        self._MakeDeleteAssociationRequestTuple(
            firewall_policy_id, association_name
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message=(
            'Deleting the association for the organization firewall policy.'
        ),
        fp_id=firewall_policy_id,
    )

  def ListAssociations(
      self, target_resource=None, batch_mode=False, only_generate_request=False
  ):
    """Sends request to list all the associations."""

    if batch_mode:
      requests = [self._MakeListAssociationsRequestTuple(target_resource)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    return [
        self._service.ListAssociations(
            self._MakeListAssociationsRequestTuple(target_resource)[2]
        )
    ]

  def Delete(self, fp_id=None, batch_mode=False, only_generate_request=False):
    """Sends request to delete an organization firewall policy."""

    if batch_mode:
      requests = [self._MakeDeleteRequestTuple(fp_id=fp_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.Delete(self._MakeDeleteRequestTuple(fp_id=fp_id)[2])
    operation_poller = DeletePoller(self._service, self.ref)
    return self.WaitOperation(
        op_res,
        operation_poller=operation_poller,
        message='Deleting the organization firewall policy.',
    )

  def _ExtractOrgId(
      self, rollout_status=None, firewall_policy=None, operation=None
  ):
    """Extracts the organization ID from rollout status, policy, or operation."""
    if (
        rollout_status
        and rollout_status.nextRollout
        and rollout_status.nextRollout.rolloutPlan
        and rollout_status.nextRollout.rolloutPlan.startswith('organizations/')
    ):
      return rollout_status.nextRollout.rolloutPlan.split('/')[1]
    if rollout_status and rollout_status.ongoingRollouts:
      for ongoing in rollout_status.ongoingRollouts:
        if ongoing.rollout and ongoing.rollout.startswith('organizations/'):
          return ongoing.rollout.split('/')[1]
        if ongoing.rolloutPlan and ongoing.rolloutPlan.startswith(
            'organizations/'
        ):
          return ongoing.rolloutPlan.split('/')[1]
    if (
        firewall_policy
        and firewall_policy.parent
        and firewall_policy.parent.startswith('organizations/')
    ):
      return firewall_policy.parent.split('/')[1]
    if operation and operation.name and operation.name.startswith('org-'):
      parts = operation.name.split('-')
      if len(parts) > 1 and parts[1]:
        return parts[1]
    return None

  def _FormatRolloutName(
      self,
      rollout_id,
      rollout_status=None,
      firewall_policy=None,
      operation=None,
  ):
    """Formats a rollout ID as a full organization rollout resource name."""
    if rollout_id.startswith('organizations/'):
      return rollout_id
    org_id = self._ExtractOrgId(
        rollout_status=rollout_status,
        firewall_policy=firewall_policy,
        operation=operation,
    )
    if org_id:
      return 'organizations/{}/locations/global/rollouts/{}'.format(
          org_id, rollout_id
      )
    return rollout_id

  def _PrintRolloutInfo(self, fp_id, operation=None):
    """Fetches the firewall policy and prints progressive rollout info if present."""
    firewall_policy = self._service.Get(
        self._MakeDescribeRequestTuple(fp_id=fp_id)[2]
    )
    if (
        not firewall_policy
        or not getattr(firewall_policy, 'rolloutOperation', None)
        or not firewall_policy.rolloutOperation.rolloutStatus
    ):
      return

    rollout_status = firewall_policy.rolloutOperation.rolloutStatus
    current_rollout = None
    if (
        rollout_status.ongoingRollouts
        and rollout_status.ongoingRollouts[0].rollout
    ):
      current_rollout = self._FormatRolloutName(
          rollout_status.ongoingRollouts[0].rollout,
          rollout_status=rollout_status,
          firewall_policy=firewall_policy,
          operation=operation,
      )

    next_rollout = None
    if rollout_status.nextRollout and rollout_status.nextRollout.rolloutId:
      next_rollout = self._FormatRolloutName(
          rollout_status.nextRollout.rolloutId,
          rollout_status=rollout_status,
          firewall_policy=firewall_policy,
          operation=operation,
      )

    if next_rollout:
      log.status.Print(
          'Progressive rollout: waiting for the previous rollout to complete'
      )
      if current_rollout:
        log.status.Print('Current rollout {}'.format(current_rollout))
      log.status.Print('Next rollout {}'.format(next_rollout))
    elif current_rollout:
      log.status.Print(
          'Progressive rollout: started {}'.format(current_rollout)
      )

  def WaitOperation(
      self, operation, operation_poller=None, message=None, fp_id=None
  ):
    """Waits for operation to finish."""

    if not operation_poller:
      operation_poller = poller.Poller(
          self._service, self.ref, has_project=self._api_has_project
      )
    if self._op_has_project and 'projects' not in operation.selfLink:
      operation.selfLink = operation.selfLink.replace(
          'locations', 'projects/locations'
      )
    operation_ref = self._resources.Parse(
        operation.selfLink, collection=OP_COLLECTION_NAME
    )
    result = waiter.WaitFor(operation_poller, operation_ref, message)
    if self._version == 'alpha' and fp_id:
      self._PrintRolloutInfo(fp_id, operation)
    return result

  def Update(
      self,
      fp_id=None,
      only_generate_request=False,
      firewall_policy=None,
      batch_mode=False,
  ):
    """Sends request to update an organization firewall policy."""

    if batch_mode:
      requests = [
          self._MakeUpdateRequestTuple(
              fp_id=fp_id, firewall_policy=firewall_policy
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.Patch(
        self._MakeUpdateRequestTuple(
            fp_id=fp_id, firewall_policy=firewall_policy
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message='Updating the organization firewall policy.',
        fp_id=fp_id or self.ref.Name(),
    )

  def Move(
      self,
      only_generate_request=False,
      fp_id=None,
      parent_id=None,
      batch_mode=False,
  ):
    """Sends request to move the firewall policy to anther parent."""
    if batch_mode:
      requests = [self._MakeMoveRequestTuple(fp_id=fp_id, parent_id=parent_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.Move(
        self._MakeMoveRequestTuple(fp_id=fp_id, parent_id=parent_id)[2]
    )
    return self.WaitOperation(
        op_res,
        message='Moving the organization firewall policy.',
        fp_id=fp_id,
    )

  def CloneRules(
      self,
      only_generate_request=False,
      dest_fp_id=None,
      source_firewall_policy=None,
      batch_mode=False,
  ):
    """Sends request to clone all the rules from another firewall policy."""

    if batch_mode:
      requests = [
          self._MakeCloneRulesRequestTuple(
              dest_fp_id=dest_fp_id,
              source_firewall_policy=source_firewall_policy,
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.CloneRules(
        self._MakeCloneRulesRequestTuple(
            dest_fp_id=dest_fp_id, source_firewall_policy=source_firewall_policy
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message='Cloning rules to the organization firewall policy.',
        fp_id=dest_fp_id,
    )

  def Describe(self, fp_id=None, batch_mode=False, only_generate_request=False):
    """Sends request to describe a firewall policy."""

    if batch_mode:
      requests = [self._MakeDescribeRequestTuple(fp_id=fp_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    return [self._service.Get(self._MakeDescribeRequestTuple(fp_id=fp_id)[2])]

  def List(self, parent_id=None, batch_mode=False, only_generate_request=False):
    """Sends request to list all the firewall policies."""

    if batch_mode:
      requests = [self._MakeListRequestTuple(parent_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    return [self._service.List(self._MakeListRequestTuple(parent_id)[2])]

  def Create(
      self,
      firewall_policy=None,
      parent_id=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to create a firewall policy."""

    if batch_mode:
      requests = [self._MakeCreateRequestTuple(firewall_policy, parent_id)]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.Insert(
        self._MakeCreateRequestTuple(firewall_policy, parent_id)[2]
    )
    return self.WaitOperation(
        op_res, message='Creating the organization firewall policy.'
    )

  def _MakeGetIamPolicyRequestTuple(self, fp_id=None):
    request = self._messages.ComputeFirewallPoliciesGetIamPolicyRequest(
        resource=fp_id or self.ref.Name(),
        # Explicitly request max supported IAM policy version (v3)
        # to prevent the backend from truncating IAM Conditions.
        optionsRequestedPolicyVersion=(
            iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
        ),
    )
    return (
        self._client.firewallPolicies,
        'GetIamPolicy',
        request,
    )

  def _MakeSetIamPolicyRequestTuple(self, policy, fp_id=None):
    set_policy_req = self._messages.GlobalOrganizationSetPolicyRequest(
        policy=policy
    )
    request = self._messages.ComputeFirewallPoliciesSetIamPolicyRequest(
        resource=fp_id or self.ref.Name(),
        globalOrganizationSetPolicyRequest=set_policy_req,
    )
    return (
        self._client.firewallPolicies,
        'SetIamPolicy',
        request,
    )

  def GetIamPolicy(self, fp_id=None, only_generate_request=False):
    """Sends request to get the IAM policy."""
    requests = [self._MakeGetIamPolicyRequestTuple(fp_id=fp_id)]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)[0]
    return requests

  def SetIamPolicy(self, policy, fp_id=None, only_generate_request=False):
    """Sends request to set the IAM policy."""
    requests = [self._MakeSetIamPolicyRequestTuple(policy, fp_id=fp_id)]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)[0]
    return requests

  def _MakeTestIamPermissionsRequestTuple(self, permissions, fp_id=None):
    test_req = self._messages.TestPermissionsRequest(
        permissions=permissions
    )
    request = self._messages.ComputeFirewallPoliciesTestIamPermissionsRequest(
        resource=fp_id or self.ref.Name(),
        testPermissionsRequest=test_req,
    )

    return (
        self._client.firewallPolicies,
        'TestIamPermissions',
        request,
    )

  def TestIamPermissions(
      self, permissions, fp_id=None, only_generate_request=False
  ):
    requests = [
        self._MakeTestIamPermissionsRequestTuple(permissions, fp_id=fp_id)
    ]

    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)[0]

    return requests

  def ForceStartProgressiveRollout(
      self,
      firewall_policy=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to start rollout of a firewall policy."""

    if batch_mode:
      requests = [
          self._MakeForceStartProgressiveRolloutRequestTuple(firewall_policy)
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.ForceStartProgressiveRollout(
        self._MakeForceStartProgressiveRolloutRequestTuple(firewall_policy)[2]
    )
    return self.WaitOperation(
        op_res,
        message='Starting rollout of the organization firewall policy.',
        fp_id=firewall_policy,
    )


class OrgFirewallPolicyRule(OrgFirewallPolicy):
  """Abstracts Organization FirewallPolicy Rule."""

  def __init__(
      self, ref=None, compute_client=None, resources=None, version='beta'
  ):
    super(OrgFirewallPolicyRule, self).__init__(
        ref=ref,
        compute_client=compute_client,
        resources=resources,
        version=version,
    )

  def _MakeCreateRuleRequestTuple(
      self, firewall_policy=None, firewall_policy_rule=None
  ):
    return (
        self._client.firewallPolicies,
        'AddRule',
        self._messages.ComputeFirewallPoliciesAddRuleRequest(
            firewallPolicy=firewall_policy,
            firewallPolicyRule=firewall_policy_rule,
        ),
    )

  def _MakeDeleteRuleRequestTuple(self, priority=None, firewall_policy=None):
    return (
        self._client.firewallPolicies,
        'RemoveRule',
        self._messages.ComputeFirewallPoliciesRemoveRuleRequest(
            firewallPolicy=firewall_policy, priority=priority
        ),
    )

  def _MakeDescribeRuleRequestTuple(self, priority=None, firewall_policy=None):
    return (
        self._client.firewallPolicies,
        'GetRule',
        self._messages.ComputeFirewallPoliciesGetRuleRequest(
            firewallPolicy=firewall_policy, priority=priority
        ),
    )

  def _MakeUpdateRuleRequestTuple(
      self, priority=None, firewall_policy=None, firewall_policy_rule=None
  ):
    return (
        self._client.firewallPolicies,
        'PatchRule',
        self._messages.ComputeFirewallPoliciesPatchRuleRequest(
            priority=priority,
            firewallPolicy=firewall_policy,
            firewallPolicyRule=firewall_policy_rule,
        ),
    )

  def CreateRule(
      self,
      firewall_policy=None,
      firewall_policy_rule=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to create an organization firewall policy rule."""

    if batch_mode:
      requests = [
          self._MakeCreateRuleRequestTuple(
              firewall_policy=firewall_policy,
              firewall_policy_rule=firewall_policy_rule,
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.AddRule(
        self._MakeCreateRuleRequestTuple(
            firewall_policy=firewall_policy,
            firewall_policy_rule=firewall_policy_rule,
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message='Adding a rule to the organization firewall policy.',
        fp_id=firewall_policy,
    )

  def DeleteRule(
      self,
      priority=None,
      firewall_policy_id=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to delete an organization firewall policy rule."""

    if batch_mode:
      requests = [
          self._MakeDeleteRuleRequestTuple(
              priority=priority, firewall_policy=firewall_policy_id
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.RemoveRule(
        self._MakeDeleteRuleRequestTuple(
            priority=priority, firewall_policy=firewall_policy_id
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message='Deleting a rule from the organization firewall policy.',
        fp_id=firewall_policy_id,
    )

  def DescribeRule(
      self,
      priority=None,
      firewall_policy_id=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to describe a firewall policy rule."""

    if batch_mode:
      requests = [
          self._MakeDescribeRuleRequestTuple(
              priority=priority, firewall_policy=firewall_policy_id
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    return self._service.GetRule(
        self._MakeDescribeRuleRequestTuple(
            priority=priority, firewall_policy=firewall_policy_id
        )[2]
    )

  def UpdateRule(
      self,
      priority=None,
      firewall_policy=None,
      firewall_policy_rule=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to update an organization firewall policy rule."""

    if batch_mode:
      requests = [
          self._MakeUpdateRuleRequestTuple(
              priority=priority,
              firewall_policy=firewall_policy,
              firewall_policy_rule=firewall_policy_rule,
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.PatchRule(
        self._MakeUpdateRuleRequestTuple(
            priority=priority,
            firewall_policy=firewall_policy,
            firewall_policy_rule=firewall_policy_rule,
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message='Updating a rule in the organization firewall policy.',
        fp_id=firewall_policy,
    )


class OrgFirewallPolicyPacketMirroringRule(OrgFirewallPolicy):
  """Abstracts Organization FirewallPolicy Packet Mirroring Rule."""

  def __init__(
      self, ref=None, compute_client=None, resources=None, version='alpha'
  ):
    super(OrgFirewallPolicyPacketMirroringRule, self).__init__(
        ref=ref,
        compute_client=compute_client,
        resources=resources,
        version=version,
    )

  def _MakeCreateRuleRequestTuple(
      self, firewall_policy=None, firewall_policy_rule=None
  ):
    return (
        self._client.firewallPolicies,
        'AddPacketMirroringRule',
        self._messages.ComputeFirewallPoliciesAddPacketMirroringRuleRequest(
            firewallPolicy=firewall_policy,
            firewallPolicyRule=firewall_policy_rule,
        ),
    )

  def _MakeDeleteRuleRequestTuple(self, priority=None, firewall_policy=None):
    return (
        self._client.firewallPolicies,
        'RemovePacketMirroringRule',
        self._messages.ComputeFirewallPoliciesRemovePacketMirroringRuleRequest(
            firewallPolicy=firewall_policy, priority=priority
        ),
    )

  def _MakeDescribeRuleRequestTuple(self, priority=None, firewall_policy=None):
    return (
        self._client.firewallPolicies,
        'GetPacketMirroringRule',
        self._messages.ComputeFirewallPoliciesGetPacketMirroringRuleRequest(
            firewallPolicy=firewall_policy, priority=priority
        ),
    )

  def _MakeUpdateRuleRequestTuple(
      self, priority=None, firewall_policy=None, firewall_policy_rule=None
  ):
    return (
        self._client.firewallPolicies,
        'PatchPacketMirroringRule',
        self._messages.ComputeFirewallPoliciesPatchPacketMirroringRuleRequest(
            priority=priority,
            firewallPolicy=firewall_policy,
            firewallPolicyRule=firewall_policy_rule,
        ),
    )

  def CreateRule(
      self,
      firewall_policy=None,
      firewall_policy_rule=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to create an organization firewall policy rule."""

    if batch_mode:
      requests = [
          self._MakeCreateRuleRequestTuple(
              firewall_policy=firewall_policy,
              firewall_policy_rule=firewall_policy_rule,
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.AddPacketMirroringRule(
        self._MakeCreateRuleRequestTuple(
            firewall_policy=firewall_policy,
            firewall_policy_rule=firewall_policy_rule,
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message='Adding a rule to the organization firewall policy.',
        fp_id=firewall_policy,
    )

  def DeleteRule(
      self,
      priority=None,
      firewall_policy_id=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to delete an organization firewall policy rule."""

    if batch_mode:
      requests = [
          self._MakeDeleteRuleRequestTuple(
              priority=priority, firewall_policy=firewall_policy_id
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.RemovePacketMirroringRule(
        self._MakeDeleteRuleRequestTuple(
            priority=priority, firewall_policy=firewall_policy_id
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message='Deleting a rule from the organization firewall policy.',
        fp_id=firewall_policy_id,
    )

  def DescribeRule(
      self,
      priority=None,
      firewall_policy_id=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to describe a firewall policy rule."""

    if batch_mode:
      requests = [
          self._MakeDescribeRuleRequestTuple(
              priority=priority, firewall_policy=firewall_policy_id
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    return self._service.GetPacketMirroringRule(
        self._MakeDescribeRuleRequestTuple(
            priority=priority, firewall_policy=firewall_policy_id
        )[2]
    )

  def UpdateRule(
      self,
      priority=None,
      firewall_policy=None,
      firewall_policy_rule=None,
      batch_mode=False,
      only_generate_request=False,
  ):
    """Sends request to update an organization firewall policy rule."""

    if batch_mode:
      requests = [
          self._MakeUpdateRuleRequestTuple(
              priority=priority,
              firewall_policy=firewall_policy,
              firewall_policy_rule=firewall_policy_rule,
          )
      ]
      if not only_generate_request:
        return self._compute_client.MakeRequests(requests)
      return requests

    op_res = self._service.PatchPacketMirroringRule(
        self._MakeUpdateRuleRequestTuple(
            priority=priority,
            firewall_policy=firewall_policy,
            firewall_policy_rule=firewall_policy_rule,
        )[2]
    )
    return self.WaitOperation(
        op_res,
        message='Updating a rule in the organization firewall policy.',
        fp_id=firewall_policy,
    )
