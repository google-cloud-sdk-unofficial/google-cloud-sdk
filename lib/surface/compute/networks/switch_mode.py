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
"""Command for switching network mode."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as exceptions
from googlecloudsdk.core import apis
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SwitchMode(base_classes.NoOutputAsyncMutator):
  """Switch network mode."""

  messages = apis.GetMessagesModule('compute', 'alpha')

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--mode',
        help=('The target mode of the network. Only support "custom" now.'),
        required=True)
    parser.add_argument(
        'name',
        completion_resource='compute.networks',
        help='The name of the network for which to switch mode.')

  @property
  def service(self):
    return self.compute.networks

  @property
  def method(self):
    return 'SwitchToCustomMode'

  @property
  def resource_type(self):
    return 'networks'

  def CreateRequests(self, args):
    """Returns requests necessary for switching to custom mode."""

    if args.mode != 'custom':
      raise exceptions.InvalidArgumentException(
          '--mode', 'Only switching to custom mode is supported now.')

    if not console_io.PromptContinue(
        message='Network [{0}] will be switched to {1} mode.'.format(
            args.name, args.mode) + ' This operation cannot be undone.',
        default=True):
      raise exceptions.ToolException('Operation aborted by user.')
    request = self.messages.ComputeNetworksSwitchToCustomModeRequest(
        network=args.name,
        project=self.project)

    return [request]

SwitchMode.detailed_help = {
    'brief': 'Switch the mode of a Google Compute Engine network',
    'DESCRIPTION': """\
        *{command}* is used to change the mode of a network. Currently, only
        changing from auto to custom mode is supported.
        """,
    'EXAMPLES': """\
        To switch ``NETWORK'' to custom subnet mode, run:

          $ {command} NETWORK --mode custom
        """,
}
