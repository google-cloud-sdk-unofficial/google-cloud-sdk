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
"""Command for calculating the cancellation fee of Compute Engine commitments."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.commitments import flags


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CalculateCancellationFee(base.Command):
  """Calculate the cancellation fee for a Compute Engine commitment."""

  detailed_help = {
      'EXAMPLES': '''
        To calculate the cancellation fee for the commitment called ``commitment-1'' in the ``us-central1''
        region, run:

          $ {command} commitment-1 --region=us-central1
      '''
  }

  @staticmethod
  def Args(parser):
    flags.MakeCommitmentArg(False).AddArgument(
        parser, operation_type='calculate cancellation fee')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources
    commitment_ref = flags.MakeCommitmentArg(False).ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    service = client.apitools_client.regionCommitments
    messages = client.messages
    request = messages.ComputeRegionCommitmentsCalculateCancellationFeeRequest(
        commitment=commitment_ref.Name(),
        project=commitment_ref.project,
        region=commitment_ref.region)
    return client.MakeRequests([(service, 'CalculateCancellationFee', request)])
