# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to create a custom job in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.custom_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.ai.custom_jobs import custom_jobs_util
from googlecloudsdk.command_lib.ai.custom_jobs import flags
from googlecloudsdk.core import log

_CUSTOM_JOB_CREATION_DISPLAY_MESSAGE = """\
Custom Job [{id}] submitted successfully.

Your job is still active. You may view the status of your job with the command

  $ gcloud alpha ai custom-jobs describe {id}

Job State: {state}\
"""


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new custom job.

  This command will attempt to run the custom job immediately upon creation.
  """

  @staticmethod
  def Args(parser):
    flags.AddCreateCustomJobFlags(parser)

  def Run(self, args):
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.BETA_VERSION, region=region):
      api_client = client.CustomJobsClient(version=constants.BETA_VERSION)

      job_spec = custom_jobs_util.ConstructCustomJobSpec(
          api_client,
          config_path=args.config,
          specs=args.worker_pool_spec,
          network=args.network,
          service_account=args.service_account,
          python_package_uri=args.python_package_uris,
          args=args.args,
          command=args.command)
      validation.ValidateWorkerPoolSpec(job_spec.workerPoolSpecs)

      response = api_client.Create(
          parent=region_ref.RelativeName(),
          display_name=args.display_name,
          job_spec=job_spec,
          kms_key_name=validation.GetAndValidateKmsKey(args))
      log.status.Print(
          _CUSTOM_JOB_CREATION_DISPLAY_MESSAGE.format(
              id=custom_jobs_util.ParseJobName(response.name),
              state=response.state))
      return response
