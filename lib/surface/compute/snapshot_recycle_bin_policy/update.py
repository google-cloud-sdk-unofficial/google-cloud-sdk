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

"""Command to update snapshot recycle bin policy."""

import json

from apitools.base.py import encoding as apitools_encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _RulesValueEncoder(message, unused_encoder=None):
  """Encoder for SnapshotRecycleBinPolicy.RulesValue to support rule removal."""
  py_object = {}
  for item in message.additionalProperties:
    if item.value is None:
      py_object[item.key] = None
    else:
      py_object[item.key] = apitools_encoding.MessageToDict(item.value)
  return json.dumps(py_object)


def _RulesValueDecoder(unused_data, unused_decoder=None):
  """Decoder for SnapshotRecycleBinPolicy.RulesValue to support rule removal."""
  return None


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update the project's or organization's snapshot recycle bin policy."""

  detailed_help = {
      'EXAMPLES': """
      To set retention days for the default rule to 10 days for a project:

        $ {command} --set-rule=default --standard-snapshots-retention-duration-days=10

      To set retention days for the default rule to 6 days for organization 123456789:

        $ {command} --organization=123456789 --set-rule=default --standard-snapshots-retention-duration-days=6

      To set retention days for a tag-based rule '12345/env/prod' to 5 days for a project:

        $ {command} --set-rule='12345/env/prod' --standard-snapshots-retention-duration-days=5

      To remove rule '12345/env/prod' for a project:

        $ {command} --remove-rule='12345/env/prod'
      """,
  }

  @classmethod
  def Args(cls, parser):
    project_or_organization = parser.add_mutually_exclusive_group()
    project_or_organization.add_argument(
        '--organization',
        help='Organization ID to apply this policy to.',
    )
    project_or_organization.add_argument(
        '--project',
        help='Project ID to apply this policy to.',
    )
    action_group = parser.add_mutually_exclusive_group(required=True)

    set_rule_group = action_group.add_group()
    set_rule_group.add_argument(
        '--set-rule',
        metavar='RULE_KEY',
        help="""Key of the rule to set. Rule keys are 'default' or tag-based keys
        like '12345/env/prod'.""",
    )
    set_rule_group.add_argument(
        '--standard-snapshots-retention-duration-days',
        type=arg_parsers.BoundedInt(lower_bound=0),
        required=True,
        help="""Retention duration in days for standard snapshots.
        Must be provided with --set-rule.""",
    )

    action_group.add_argument(
        '--remove-rule',
        metavar='RULE_KEY',
        help="""Key of the rule to remove. Rule keys are 'default' or tag-based keys
        like '12345/env/prod'.""",
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    rules_dict = {}

    if args.remove_rule:
      rules_dict[args.remove_rule] = None
      apitools_encoding.RegisterCustomMessageCodec(
          encoder=_RulesValueEncoder, decoder=_RulesValueDecoder
      )(messages.SnapshotRecycleBinPolicy.RulesValue)
    else:
      rule_key = args.set_rule
      retention_days = args.standard_snapshots_retention_duration_days
      rules_dict[rule_key] = messages.SnapshotRecycleBinPolicyRule(
          standardSnapshots=messages.SnapshotRecycleBinPolicyRuleRuleConfig(
              retentionDurationDays=retention_days
          )
      )

    updated_policy = messages.SnapshotRecycleBinPolicy(
        rules=messages.SnapshotRecycleBinPolicy.RulesValue(
            additionalProperties=[
                messages.SnapshotRecycleBinPolicy.RulesValue.AdditionalProperty(
                    key=k, value=v
                )
                for k, v in rules_dict.items()
            ]
        )
    )

    if args.organization:
      patch_request = (
          messages.ComputeOrganizationSnapshotRecycleBinPolicyPatchRequest(
              organization='organizations/' + args.organization,
              snapshotRecycleBinPolicy=updated_policy,
          )
      )
      service = client.apitools_client.organizationSnapshotRecycleBinPolicy
      log_message = 'Updated policy for organization [{0}].'.format(
          args.organization
      )
      result = service.Patch(patch_request)
      if result and result.name:
        log.status.Print(log_message)
      return None

    else:
      project = args.project or properties.VALUES.core.project.Get(
          required=True
      )
      patch_request = messages.ComputeSnapshotRecycleBinPolicyPatchRequest(
          project=project,
          snapshotRecycleBinPolicy=updated_policy,
      )
      service = client.apitools_client.snapshotRecycleBinPolicy
      params = {'project': project}
      policy_collection = 'compute.snapshotRecycleBinPolicy'
      log_message = 'Updated policy for project [{0}].'.format(project)

      results = client.MakeRequests(
          [(service, 'Patch', patch_request)], no_followup=True
      )
      if not results:
        log.status.Print(log_message)
        return None

      operation_ref = resources.REGISTRY.Parse(
          results[0].name,
          params=params,
          collection='compute.globalOperations',
      )
      policy_ref = holder.resources.Parse(
          None,
          params=params,
          collection=policy_collection,
      )
      operation_poller = poller.Poller(
          service,
          policy_ref,
      )
      waiter.WaitFor(
          operation_poller,
          operation_ref,
          'Waiting for snapshot recycle bin policy update to complete...',
      )
      log.status.Print(log_message)
