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
"""Command to create a tuning job in Vertex AI."""

from googlecloudsdk.api_lib.ai.tuning_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.ai.tuning_jobs import flags
from googlecloudsdk.command_lib.ai.tuning_jobs import tuning_jobs_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log

_TUNING_JOB_CREATION_DISPLAY_MESSAGE = """\
Tuning job [{id}] submitted successfully.

Your job is still active. You may view the status of your job with the command

 $ gcloud{command_version} ai tuning-jobs describe {id} --region={region}

Job State: {state}\
"""


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  r"""Create a supervised fine-tuning job.

    This command creates a new supervised fine-tuning (SFT) tuning job in
    Vertex AI. The job tunes a base foundation model using the provided
    training dataset to produce a customized tuned model.

    ## EXAMPLES

    To create a tuning job that fine-tunes ``gemini-1.0-pro-002'' in region
    ``us-central1'', run:

      $ {command} --region=us-central1 \
        --source-model=gemini-1.0-pro-002 \
        --training-dataset-uri=gs://my-bucket/training.jsonl \
        --tuned-model-display-name=my-tuned-model

    To create a tuning job with labels and hyperparameters:

      $ {command} --region=us-central1 \
        --source-model=gemini-1.0-pro-002 \
        --training-dataset-uri=gs://my-bucket/training.jsonl \
        --validation-dataset-uri=gs://my-bucket/validation.jsonl \
        --epoch-count=3 \
        --learning-rate-multiplier=1.0 \
        --labels=env=prod,team=ml
  """

  _api_version = constants.GA_VERSION
  # Open-model-only flags (`--learning-rate`, `--custom-base-model`,
  # `--output-uri`, `--tuning-mode`, `--batch-size`) are restricted to v1beta1
  # in the proto, so they are only exposed in BETA/ALPHA tracks.
  _include_open_model_flags = False

  @classmethod
  def Args(cls, parser):
    flags.AddCreateTuningJobFlags(
        parser, include_open_model_flags=cls._include_open_model_flags
    )

  def Run(self, args):
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()["locationsId"]
    validation.ValidateRegion(
        region, available_regions=constants.SUPPORTED_TRAINING_REGIONS
    )

    with endpoint_util.AiplatformEndpointOverrides(
        version=self._api_version, region=region
    ):
      api_client = client.TuningJobsClient(version=self._api_version)

      labels = labels_util.ParseCreateArgs(
          args, api_client.TuningJobMessage().LabelsValue
      )

      adapter_size = api_client.ParseAdapterSize(args.adapter_size)

      # Open-model-only flags may not be defined on the GA argparse namespace
      # because they are gated to v1beta1 tracks. Use getattr to read them
      # safely so the GA Run() can share the same body as BETA/ALPHA.
      learning_rate = getattr(args, "learning_rate", None)
      batch_size = getattr(args, "batch_size", None)
      custom_base_model = getattr(args, "custom_base_model", None)
      output_uri = getattr(args, "output_uri", None)
      tuning_mode = api_client.ParseTuningMode(
          getattr(args, "tuning_mode", None)
      )

      response = api_client.Create(
          parent=region_ref.RelativeName(),
          source_model=args.source_model,
          training_dataset_uri=args.training_dataset_uri,
          validation_dataset_uri=args.validation_dataset_uri,
          tuned_model_display_name=args.tuned_model_display_name,
          description=args.description,
          epoch_count=args.epoch_count,
          learning_rate_multiplier=args.learning_rate_multiplier,
          learning_rate=learning_rate,
          batch_size=batch_size,
          adapter_size=adapter_size,
          tuning_mode=tuning_mode,
          export_last_checkpoint_only=args.export_last_checkpoint_only,
          custom_base_model=custom_base_model,
          output_uri=output_uri,
          labels=labels,
          encryption_key_name=validation.GetAndValidateKmsKey(args),
          service_account=args.service_account,
      )

      log.status.Print(
          _TUNING_JOB_CREATION_DISPLAY_MESSAGE.format(
              id=tuning_jobs_util.ParseJobName(response.name),
              command_version=tuning_jobs_util.OutputCommandVersion(
                  self.ReleaseTrack()
              ),
              region=region,
              state=response.state,
          )
      )
      return response


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreatePreGA(CreateGA):
  """Create a supervised fine-tuning job."""

  _api_version = constants.BETA_VERSION
  _include_open_model_flags = True
