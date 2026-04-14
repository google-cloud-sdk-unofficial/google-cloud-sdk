# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Flags definition specifically for gcloud ai ray job."""


import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import flags as shared_flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai.serverless_ray_jobs import serverless_ray_jobs_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers


_ENTRYPOINT_FILE_URI = base.Argument(
    '--entrypoint',
    metavar='ENTRYPOINT_FILE_URI',
    required=True,
    help='The Ray job entrypoint Python file Google Cloud Storage URI.',
)

_CONTAINER_IMAGE_URI = base.Argument(
    '--container-image-uri',
    metavar='CONTAINER_IMAGE_URI',
    help='The container image URI to use for the Ray worker node.',
)

_WORKER_POOL_SPEC = base.Argument(
    '--worker-pool-spec',
    type=arg_parsers.ArgDict(
        spec={
            'disk-size': int,
            'max-node-count': int,
        }
    ),
    metavar='WORKER_POOL_SPEC',
    help=textwrap.dedent("""\
      Define the worker pool resource spec for the serverless ray job.

      The spec can contain the following fields:

      *disk-size*::: Optional, default to 100. Disk size in GB on one worker node.
      *max-node-count*::: Optional, default to 2000. The max number of worker nodes this job can occupy while running.

      ::::
      Example:
      --worker-pool-spec=disk-size=100,max-node-count=10
      """),
)

_SERVERLESS_RAY_JOB_SERVICE_ACCOUNT = base.Argument(
    '--service-account',
    metavar='SERVICE_ACCOUNT',
    hidden=True,
    help=(
        'The service account to use for the Ray job. If not specified, the'
        ' default service account is used.'
    ),
)


def AddCreateServerlessRayJobFlags(parser):
  """Adds flags related to create a serverless ray job."""
  shared_flags.AddRegionResourceArg(
      parser,
      'to create a serverless ray job',
      prompt_func=region_util.GetPromptForRegionFunc(
          constants.SUPPORTED_TRAINING_REGIONS
      ),
  )
  shared_flags.GetDisplayNameArg('serverless ray job').AddToParser(parser)

  labels_util.AddCreateLabelsFlags(parser)

  _SERVERLESS_RAY_JOB_SERVICE_ACCOUNT.AddToParser(parser)
  _ENTRYPOINT_FILE_URI.AddToParser(parser)
  _WORKER_POOL_SPEC.AddToParser(parser)
  _CONTAINER_IMAGE_URI.AddToParser(parser)


def AddServerlessRayJobResourceArg(
    parser, verb, regions=constants.SUPPORTED_TRAINING_REGIONS
):
  """Add a resource argument for a Vertex AI serverless ray job.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the job resource, such as 'to update'.
    regions: list[str], the list of supported regions.
  """
  resource_spec = concepts.ResourceSpec(
      resource_collection=serverless_ray_jobs_util.SERVERLESS_RAY_JOB_COLLECTION,
      resource_name='serverless ray job',
      locationsId=shared_flags.RegionAttributeConfig(
          prompt_func=region_util.GetPromptForRegionFunc(regions)
      ),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )

  concept_parsers.ConceptParser.ForResource(
      'serverless_ray_job',
      resource_spec,
      'The serverless ray job {}.'.format(verb),
      required=True,
  ).AddToParser(parser)
