# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for expanding IP range of a subnetwork."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as exceptions
from googlecloudsdk.command_lib.compute.networks.subnets import flags
from googlecloudsdk.core.console import console_io
import ipaddr


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class ExpandIpRange(base_classes.NoOutputAsyncMutator):
  """Expand IP range of a subnetwork."""

  SUBNETWORK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SUBNETWORK_ARG = flags.SubnetworkArgument()
    cls.SUBNETWORK_ARG.AddArgument(parser)

    parser.add_argument(
        '--prefix-length',
        type=int,
        help=(
            'The new prefix length of the subnet. It must be smaller than the '
            'original and in the private address space 10.0.0.0/8, '
            '172.16.0.0/12 or 192.168.0.0/16 defined in RFC 1918.'),
        required=True)

  @property
  def service(self):
    return self.compute.subnetworks

  @property
  def method(self):
    return 'ExpandIpCidrRange'

  @property
  def resource_type(self):
    return 'subnetworks'

  def CreateRequests(self, args):
    """Returns requests for expanding IP CIDR range."""
    new_prefix_length = self._ValidatePrefixLength(args.prefix_length)
    subnetwork_ref = self.SUBNETWORK_ARG.ResolveAsResource(args, self.resources)
    original_ip_cidr_range = self._GetOriginalIpCidrRange(subnetwork_ref)
    new_ip_cidr_range = self._InferNewIpCidrRange(
        subnetwork_ref.Name(), original_ip_cidr_range, new_prefix_length)
    self._PromptToConfirm(
        subnetwork_ref.Name(), original_ip_cidr_range, new_ip_cidr_range)
    request = self._CreateExpandIpCidrRangeRequest(
        subnetwork_ref, new_ip_cidr_range)
    return [request]

  def _ValidatePrefixLength(self, new_prefix_length):
    if not 0 <= new_prefix_length <= 29:
      raise exceptions.InvalidArgumentException(
          '--prefix-length',
          'Prefix length must be in the range [0, 29].')
    return new_prefix_length

  def _GetOriginalIpCidrRange(self, subnetwork_ref):
    subnetwork = self._GetSubnetwork(subnetwork_ref)
    if not subnetwork:
      raise exceptions.ToolException(
          'Subnet [{subnet}] was not found in region {region}.'.format(
              subnet=subnetwork_ref.Name(), region=subnetwork_ref.region))

    return subnetwork['ipCidrRange']

  def _InferNewIpCidrRange(
      self, subnet_name, original_ip_cidr_range, new_prefix_length):
    unmasked_new_ip_range = '{0}/{1}'.format(
        original_ip_cidr_range.split('/')[0],
        new_prefix_length)
    network = ipaddr.IPv4Network(unmasked_new_ip_range)
    return str(network.masked())

  def _PromptToConfirm(
      self, subnetwork_name, original_ip_cidr_range, new_ip_cidr_range):
    prompt_message_template = (
        'The IP range of subnetwork [{0}] will be expanded from {1} to {2}. '
        'This operation may take several minutes to complete '
        'and cannot be undone.')
    prompt_message = prompt_message_template.format(
        subnetwork_name, original_ip_cidr_range, new_ip_cidr_range)
    if not console_io.PromptContinue(message=prompt_message, default=True):
      raise exceptions.ToolException('Operation aborted by user.')

  def _CreateExpandIpCidrRangeRequest(self, subnetwork_ref, new_ip_cidr_range):
    request_body = self.messages.SubnetworksExpandIpCidrRangeRequest(
        ipCidrRange=new_ip_cidr_range)
    return self.messages.ComputeSubnetworksExpandIpCidrRangeRequest(
        subnetwork=subnetwork_ref.Name(),
        subnetworksExpandIpCidrRangeRequest=request_body,
        project=self.project,
        region=subnetwork_ref.region)

  def _GetSubnetwork(self, subnetwork_ref):
    get_request = (
        self.compute.subnetworks,
        'Get',
        self.messages.ComputeSubnetworksGetRequest(
            project=self.project,
            region=subnetwork_ref.region,
            subnetwork=subnetwork_ref.Name()))

    errors = []
    objects = request_helper.MakeRequests(
        requests=[get_request],
        http=self.http,
        batch_url=self.batch_url,
        errors=errors)

    resources = list(lister.ProcessResults(objects, field_selector=None))
    return resources[0] if resources else None


ExpandIpRange.detailed_help = {
    'brief': 'Expand the IP range of a Google Compute Engine subnetwork',
    'DESCRIPTION': """\
        *{command}* is used to expand the IP range of a subnetwork in a custom
        mode network.
        """,
    'EXAMPLES': """\
        To expand the IP range of ``SUBNET'' to /16, run:

          $ {command} SUBNET --region us-central1 --prefix-length 16
        """,
}
