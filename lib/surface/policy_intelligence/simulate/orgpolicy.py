# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to simulate orgpolicy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding_helper
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.orgpolicy import utils as orgpolicy_utils
from googlecloudsdk.api_lib.policy_intelligence import orgpolicy_simulator
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.policy_intelligence.simulator.orgpolicy import utils
from googlecloudsdk.core import log


_DETAILED_HELP_ALPHA = {
    'brief':
        """\
      Preview of Violations Service for OrgPolicy Simulator.
        """,
    'DESCRIPTION':
        """\
      Preview of Violations Service for OrgPolicy Simulator.
        """,
    'EXAMPLES':
        """\
      Simulate changes to Organization Policies:, run:

        $ {command}
        --organization=ORGANIZATION_ID
        --policy policy.json
        --custom-constraint custom-constraint.json

      See https://cloud.google.com/iam for more information about Org Policy Simulator.
      The official Org Policy Simulator document will be released soon.

      """
}


def _ArgsAlpha(parser):
  """Parses arguments for the commands."""
  parser.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      required=True,
      help=('Organization ID.'))

  parser.add_argument(
      '--policies',
      type=arg_parsers.ArgList(),
      metavar='POLICIES',
      action=arg_parsers.UpdateAction,
      help="""Path to the JSON or YAML file that contains the Org Policy to simulate.
      Multiple Policies can be simulated by providing multiple, comma-separated paths.
      E.g. --policies=p1.json,p2.json.
      The format of policy can be found and created by `gcloud org-policies set-policy`.
      See https://cloud.google.com/sdk/gcloud/reference/org-policies/set-policy for more details.
      """)

  parser.add_argument(
      '--custom-constraints',
      type=arg_parsers.ArgList(),
      metavar='CUSTOM_CONSTRAINTS',
      action=arg_parsers.UpdateAction,
      help="""Path to the JSON or YAML file that contains the Custom Constraints to simulate.
      Multiple Custom Constraints can be simulated by providing multiple, comma-separated paths.
      e.g., --custom-constraints=constraint1.json,constraint2.json.
      """)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class SimulateAlpha(base.Command):
  """Simulate the Org Policies."""

  detailed_help = _DETAILED_HELP_ALPHA

  @staticmethod
  def Args(parser):
    """Parses arguments for the commands."""
    _ArgsAlpha(parser)

  def Run(self, args):
    if not args.policies and not args.custom_constraints:
      raise exceptions.ConflictingArgumentsException(
          'Must specify either --policies or --custom-constraints or both.')

    orgpolicy_simulator_api = orgpolicy_simulator.OrgPolicySimulatorApi(
        self.ReleaseTrack())
    # Parse files and get Policy Overlay
    policies = []
    if args.policies:
      for policy_file in args.policies:
        policy = utils.GetPolicyMessageFromFile(policy_file,
                                                self.ReleaseTrack())
        if not policy.name:
          raise exceptions.InvalidArgumentException(
              'Policy name',
              "'name' field not present in the organization policy.")
        policy_parent = orgpolicy_utils.GetResourceFromPolicyName(
            policy.name)
        policy_overlay = orgpolicy_simulator_api.GetOrgPolicyPolicyOverlay(
            policy=policy,
            policy_parent=policy_parent)
        policies.append(policy_overlay)

    # Parse files and get Custom Constraints Overlay
    custom_constraints = []
    if args.custom_constraints:
      for custom_constraint_file in args.custom_constraints:
        custom_constraint = utils.GetCustomConstraintMessageFromFile(
            custom_constraint_file,
            self.ReleaseTrack())
        if not custom_constraint.name:
          raise exceptions.InvalidArgumentException(
              'Custom constraint name',
              "'name' field not present in the custom constraint.")
        custom_constraint_parent = orgpolicy_utils.GetResourceFromPolicyName(
            custom_constraint.name)
        constraint_overlay = orgpolicy_simulator_api.GetOrgPolicyCustomConstraintOverlay(
            custom_constraint=custom_constraint,
            custom_constraint_parent=custom_constraint_parent)
        custom_constraints.append(constraint_overlay)

    overlay = orgpolicy_simulator_api.GetOrgPolicyOverlay(
        policies=policies, custom_constraints=custom_constraints)

    # Generate Violations Preview and get long operation id
    organization_resource = 'organizations/' + args.organization
    parent = utils.GetParentFromOrganization(organization_resource)
    violations = orgpolicy_simulator_api.GetPolicysimulatorOrgPolicyViolationsPreview(
        overlay=overlay)
    request = orgpolicy_simulator_api.GenerateOrgPolicyViolationsPreviewRequest(
        violations_preview=violations,
        parent=parent)
    op_simulator_service = orgpolicy_simulator_api.client.OrganizationsLocationsService(
        orgpolicy_simulator_api.client)
    violations_preview_operation = op_simulator_service.OrgPolicyViolationsPreviews(
        request=request)

    # Poll Long Running Operation and get Violations Preview
    operation_response_raw = orgpolicy_simulator_api.WaitForOperation(
        violations_preview_operation,
        'Waiting for operation [{}] to complete'.format(
            violations_preview_operation.name))

    violations_preview = encoding_helper.JsonToMessage(
        orgpolicy_simulator_api.messages
        .GoogleCloudPolicysimulatorV1alphaOrgPolicyViolationsPreview,
        encoding_helper.MessageToJson(operation_response_raw))

    if not violations_preview.violationsCount or not violations_preview.resourceCounts:
      log.err.Print('No violations found in the violations preview.\n')

    # List results of the Violations under Violations Preview.
    list_violations_request = orgpolicy_simulator_api.messages.PolicysimulatorOrganizationsLocationsOrgPolicyViolationsPreviewsOrgPolicyViolationsListRequest(
        parent=violations_preview.name)
    pov_service = orgpolicy_simulator_api.client.OrganizationsLocationsOrgPolicyViolationsPreviewsOrgPolicyViolationsService(
        orgpolicy_simulator_api.client)

    return list_pager.YieldFromList(
        pov_service,
        list_violations_request,
        batch_size=1000,
        field='orgPolicyViolations',
        batch_size_attribute='pageSize')

