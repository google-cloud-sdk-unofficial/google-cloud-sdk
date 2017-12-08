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
"""ml models versions create command."""

from googlecloudsdk.api_lib.ml import operations
from googlecloudsdk.api_lib.ml import versions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.core import apis
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaCreate(base.CreateCommand):
  """Create a new Cloud ML version."""

  def Collection(self):
    return 'ml.models.versions'

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.GetModelName(positional=False, required=True).AddToParser(parser)
    flags.VERSION_NAME.AddToParser(parser)
    flags.VERSION_DATA.AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    op = versions.Create(args.model, args.version, args.origin)
    if args.async:
      return op
    client = apis.GetClientInstance('ml', 'v1beta1')

    with console_io.ProgressTracker(
        'Creating version (this might take a few minutes)...'):
      operations.WaitForOperation(
          client.projects_operations,
          op)
    return op.response
