# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Create a release."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import client_util
from googlecloudsdk.api_lib.clouddeploy import release
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import delivery_pipeline_util
from googlecloudsdk.command_lib.deploy import deploy_util
from googlecloudsdk.command_lib.deploy import flags
from googlecloudsdk.command_lib.deploy import promote_util
from googlecloudsdk.command_lib.deploy import release_util
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
    To create a release with source located at storage URL `gs://bucket/object.zip`
    and the first rollout in the first target of the promotion sequence:

       $ {command} my-release --source=`gs://bucket/object.zip` --delivery-pipeline=my-pipeline --region=us-central1

    To create a release with source located at current directory
    and deploy a rollout to target prod :

      $ {command} my-release --delivery-pipeline=my-pipeline --region=us-central1 --to-target=prod

    The current UTC date and time on the machine running the gcloud command can
    also be included in the release name by adding $DATE and $TIME parameters:

      $ {command} 'my-release-$DATE-$TIME' --delivery-pipeline=my-pipeline --region=us-central1

    If the current UTC date and time is set to 2021-12-21 12:02, then the created release
    will have its name set as my-release-20211221-1202.

    When using these parameters, please be sure to wrap the release name in single quotes
    or else the template parameters will be overridden by environment variables.
    """,
}
_RELEASE = 'release'


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  resource_args.AddReleaseResourceArg(parser, positional=True, required=True)
  flags.AddSourceFlag(parser)
  flags.AddGcsSourceStagingDirFlag(parser)
  flags.AddImagesGroup(parser)
  flags.AddIgnoreFileFlag(parser)
  flags.AddToTargetFlag(parser)
  flags.AddDescription(parser, 'Description of the release.')
  flags.AddAnnotationsFlag(parser, _RELEASE)
  flags.AddLabelsFlag(parser, _RELEASE)
  flags.AddSkaffoldVersion(parser)
  flags.AddSkaffoldFileFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Creates a new release, delivery pipeline qualified."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    args.CONCEPTS.parsed_args.release = release_util.RenderPattern(
        args.CONCEPTS.parsed_args.release)
    release_ref = args.CONCEPTS.release.Parse()
    failed_activity_msg = 'Cannot create release {}.'.format(
        release_ref.RelativeName())
    delivery_pipeline_util.ThrowIfPipelineSuspended(release_ref.Parent(),
                                                    failed_activity_msg)
    client = release.ReleaseClient()
    # Create the release create request.
    release_config = release_util.CreateReleaseConfig(
        args.source, args.gcs_source_staging_dir, args.ignore_file, args.images,
        args.build_artifacts, args.description, args.skaffold_version,
        args.skaffold_file,
        release_ref.AsDict()['locationsId'])
    deploy_util.SetMetadata(client.messages, release_config,
                            deploy_util.ResourceType.RELEASE, args.annotations,
                            args.labels)
    operation = client.Create(release_ref, release_config)
    operation_ref = resources.REGISTRY.ParseRelativeName(
        operation.name, collection='clouddeploy.projects.locations.operations')
    client_util.OperationsClient().WaitForOperation(operation, operation_ref)

    log.status.Print('Created Cloud Deploy release {}.'.format(
        release_ref.Name()))

    release_obj = release.ReleaseClient().Get(release_ref.RelativeName())
    rollout_resource = promote_util.Promote(release_ref, release_obj,
                                            args.to_target, True)
    return release_obj, rollout_resource
