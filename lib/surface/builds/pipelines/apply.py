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
"""Command to create or update a Cloud Build Pipeline declaratively."""

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import pipeline_config
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import pipeline_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """\
        To apply a pipeline defined in `pipeline.yaml` in region `us-central1`:

          $ {command} --file=pipeline.yaml --region=us-central1

        To apply a pipeline with an explicit ID and service account:

          $ {command} main-pipeline --file=pipeline.yaml --region=us-central1 \\
              --service-account=cb-sa@my-project.iam.gserviceaccount.com

        To validate a pipeline definition without persisting changes:

          $ {command} --file=pipeline.yaml --region=us-central1 --dry-run
        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Apply(base.CreateCommand):
  """Create or update a Cloud Build Pipeline declaratively."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    pipeline_flags.AddPipelineApplyFlags(parser)

  def Run(self, args):
    """Executes the `apply` command."""
    client = cloudbuild_util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE

    # Load the definition before resolving the resource, so that a missing or
    # malformed file is reported as such. The pipeline ID falls through to
    # this same file, which would otherwise turn a typo in --file into a
    # complaint about an unspecified pipeline.
    pipeline = pipeline_config.LoadPipelineConfigFromPath(args.file, messages)

    pipeline_ref = args.CONCEPTS.pipeline.Parse()
    pipeline_name = pipeline_ref.RelativeName()

    if args.IsSpecified('display_name'):
      pipeline.displayName = args.display_name
    if args.IsSpecified('service_account'):
      pipeline.serviceAccount = args.service_account

    mask = pipeline_config.ComputeUpdateMask(pipeline)
    req = messages.CloudbuildProjectsLocationsPipelinesPatchRequest(
        name=pipeline_name,
        pipeline=pipeline,
        updateMask=mask,
        allowMissing=True,
        validateOnly=args.dry_run,
    )
    op = client.projects_locations_pipelines.Patch(req)

    if args.dry_run:
      log.status.Print(
          'Dry run validated pipeline [{}].'.format(pipeline_name)
      )
      return None

    op_resource = resources.REGISTRY.ParseRelativeName(
        op.name, collection='cloudbuild.projects.locations.operations'
    )
    poller = waiter.CloudOperationPoller(
        client.projects_locations_pipelines,
        client.projects_locations_operations,
    )
    result = waiter.WaitFor(
        poller, op_resource, 'Applying pipeline', max_wait_ms=3600000
    )
    log.status.Print('Applied pipeline [{}].'.format(pipeline_name))
    return result
