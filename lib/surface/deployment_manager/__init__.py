# Copyright 2014 Google Inc. All Rights Reserved.
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

"""The command group for the DeploymentManager CLI."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store


@base.ReleaseTracks(base.ReleaseTrack.GA,
                    base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class DmV2(base.Group):
  """Manage deployments of cloud resources."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    pass

  @exceptions.RaiseToolExceptionInsteadOf(store.Error)
  def Filter(self, context, args):
    """Context() is a filter function that can update the context.

    Args:
      context: The current context.
      args: The argparse namespace that was specified on the CLI or API.

    Returns:
      The updated context.
    Raises:
      ToolException: When no project is specified.
    """

    # v2
    context['deploymentmanager-client'] = apis.GetClientInstance(
        'deploymentmanager', 'v2')
    context['deploymentmanager-messages'] = apis.GetMessagesModule(
        'deploymentmanager', 'v2')
    return context
