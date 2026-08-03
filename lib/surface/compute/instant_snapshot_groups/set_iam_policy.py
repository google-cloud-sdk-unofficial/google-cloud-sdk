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
"""Set IAM policy for an instant snapshot group command."""

from typing import Any

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute.instant_snapshot_groups import flags as isg_flags
from googlecloudsdk.command_lib.iam import iam_util

_DETAILED_HELP = {  # Dict[str, str]
    'brief': (
        'Set the IAM policy binding for a Compute Engine instant snapshot '
        'group.'
    ),
    'DESCRIPTION': (
        """\
        *{command}* sets the IAM policy for a Compute Engine instant snapshot group as defined in a JSON or YAML file.
        """
    ),
    'EXAMPLES': (
        """\
        To set the IAM policy for the instant snapshot group 'instant-snapshot-group-1' in zone 'us-east1-a' from 'policy.json', run:

            $ {command} instant-snapshot-group-1 policy.json --zone=us-east1-a
        """
    ),
}


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.UniverseCompatible
class SetIamPolicy(base.Command):
  """Set the IAM policy binding for a Compute Engine instant snapshot group."""

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor) -> None:
    cls.ISG_ARG = isg_flags.MakeInstantSnapshotGroupArg()
    cls.ISG_ARG.AddArgument(parser, operation_type='set IAM policy')
    iam_util.AddArgForPolicyFile(parser)

  def _Run(self, args: parser_extensions.Namespace) -> Any:
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    isg_ref = self.ISG_ARG.ResolveAsResource(args, holder.resources)

    policy = iam_util.ParsePolicyFile(args.policy_file, messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    if isg_ref.Collection() == 'compute.instantSnapshotGroups':
      service = client.apitools_client.instantSnapshotGroups
      request_type = messages.ComputeInstantSnapshotGroupsSetIamPolicyRequest
      request = request_type(
          project=isg_ref.project,
          zone=isg_ref.zone,
          resource=isg_ref.Name(),
          zoneSetPolicyRequest=messages.ZoneSetPolicyRequest(policy=policy),
      )
    else:
      service = client.apitools_client.regionInstantSnapshotGroups
      request_type = (
          messages.ComputeRegionInstantSnapshotGroupsSetIamPolicyRequest
      )
      request = request_type(
          project=isg_ref.project,
          region=isg_ref.region,
          resource=isg_ref.Name(),
          regionSetPolicyRequest=messages.RegionSetPolicyRequest(policy=policy),
      )

    result = client.MakeRequests([(service, 'SetIamPolicy', request)])[0]
    iam_util.LogSetIamPolicy(isg_ref.Name(), 'instant snapshot group')
    return result

  def Run(self, args: parser_extensions.Namespace) -> Any:
    return self._Run(args)


SetIamPolicy.detailed_help = _DETAILED_HELP
