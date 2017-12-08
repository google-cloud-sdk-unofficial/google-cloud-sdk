# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Command for creating Google Compute Engine commitments."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import waiters
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.commitments import flags
from googlecloudsdk.core import properties


class Create(base.Command):
  """Create Google Compute Engine commitments."""

  @classmethod
  def Args(cls, parser):
    flags.MakeCommitmentArg(False).AddArgument(parser)
    parser.add_argument('--plan',
                        required=True,
                        help=('Duration of the commitment. Can be `12-months` '
                              'or `36-months`.'))
    resources_help = """\
    Resources to be included in the commitment commitment:
    * MEMORY should include unit (eg. 3072MiB or 9GiB). If no units are
      specified, GiB is assumed.
    * VCPU is number of commited cores.
    Ratio between number of VCPU cores and memory must conform to limits
    described on:
    https://cloud.google.com/compute/docs/instances/creating-instance-with-custom-machine-type"""

    parser.add_argument('--resources',
                        required=True,
                        help=resources_help,
                        metavar='RESOURCE=COMMITMENT',
                        type=arg_parsers.ArgDict(spec={
                            'VCPU': int,
                            'MEMORY': arg_parsers.BinarySize(),
                        }))

  def _ValidateArgs(self, args):
    flags.ValidatePlanArg(args.plan)
    flags.ValidateResourcesArg(args.resources)

  def _MakeCreateRequest(self, args, messages, project, region, commitment_ref):
    commitment = messages.Commitment(
        name=commitment_ref.Name(),
        plan=flags.TranslatePlanArg(messages, args.plan),
        resources=flags.TranslateResourcesArg(messages, args.resources),
    )
    return messages.ComputeRegionCommitmentsInsertRequest(
        commitment=commitment,
        project=project,
        region=commitment_ref.region,
    )

  def Run(self, args):
    self._ValidateArgs(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resources = holder.resources
    commitment_ref = flags.MakeCommitmentArg(False).ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    region = properties.VALUES.compute.region.Get()
    project = properties.VALUES.core.project.Get()
    create_request = self._MakeCreateRequest(
        args, messages, project, region, commitment_ref)

    service = holder.client.apitools_client.regionCommitments
    batch_url = holder.client.batch_url
    http = holder.client.apitools_client.http
    errors = []
    operations = list(
        request_helper.MakeRequests(
            requests=[(service, 'Insert', create_request)],
            http=http,
            batch_url=batch_url,
            errors=errors))

    operation_service = holder.client.apitools_client.regionOperations
    return waiters.WaitForOperations(
        operations=operations,
        project=project,
        operation_service=operation_service,
        resource_service=service,
        http=http,
        batch_url=batch_url,
        warnings=[],
        errors=errors)
