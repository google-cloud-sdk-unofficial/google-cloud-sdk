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
"""ml versions create command."""

from googlecloudsdk.api_lib.ml import versions_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.command_lib.ml import models_util
from googlecloudsdk.command_lib.ml import uploads
from googlecloudsdk.command_lib.ml import versions_util
from googlecloudsdk.core import exceptions


class InvalidArgumentCombinationError(exceptions.Error):
  """Indicates that a given combination of arguments was invalid."""
  pass


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
    flags.RUNTIME_VERSION.AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    flags.STAGING_BUCKET.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    try:
      origin = uploads.UploadDirectoryIfNecessary(args.origin,
                                                  args.staging_bucket)
    except uploads.MissingStagingBucketException:
      raise InvalidArgumentCombinationError(
          'If --origin is provided as a local path, --staging-bucket must be '
          'given as well.')

    versions_client = versions_api.VersionsClient()
    model_ref = models_util.ParseModel(args.model)
    op = versions_client.Create(
        model_ref, args.version, origin, args.runtime_version)
    return versions_util.WaitForOpMaybe(
        op, async_=args.async,
        message='Creating version (this might take a few minutes)...')
