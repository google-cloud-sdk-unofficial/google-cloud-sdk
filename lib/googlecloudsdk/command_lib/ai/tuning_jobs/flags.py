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
"""Flag definitions specifically for gcloud ai tuning-jobs."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai.tuning_jobs import tuning_jobs_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers

_SOURCE_MODEL = base.Argument(
    "--source-model",
    required=True,
    help=(
        "The base model to tune, e.g. ``gemini-1.0-pro-002`` or "
        "``meta/llama3_1@llama-3.1-8b``. To start tuning from a custom "
        "checkpoint or a previously tuned open model, also pass "
        "``--custom-base-model``."
    ),
)

_CUSTOM_BASE_MODEL = base.Argument(
    "--custom-base-model",
    help=(
        "Cloud Storage path to custom model weights. Set this to tune from a "
        "custom checkpoint or to continue tuning a previously tuned model. "
        "Must be a Cloud Storage directory containing model weights in "
        ".safetensors format. ``--source-model`` must still be set to "
        "indicate the base model architecture. Only available for open "
        "source models."
    ),
)

_TRAINING_DATASET_URI = base.Argument(
    "--training-dataset-uri",
    required=True,
    help=(
        "Cloud Storage URI of the training dataset. The dataset must be "
        "formatted as a JSONL file."
    ),
)

_VALIDATION_DATASET_URI = base.Argument(
    "--validation-dataset-uri",
    help=(
        "Cloud Storage URI of the optional validation dataset. The dataset "
        "must be formatted as a JSONL file."
    ),
)

_TUNED_MODEL_DISPLAY_NAME = base.Argument(
    "--tuned-model-display-name", help="Display name of the tuned model."
)

_DESCRIPTION = base.Argument(
    "--description",
    help="Description of the tuning job.",
)

_EPOCH_COUNT = base.Argument(
    "--epoch-count",
    type=int,
    help=(
        "Number of training epochs. If not set, a default value will be "
        "calculated based on the training dataset size."
    ),
)

_LEARNING_RATE_MULTIPLIER = base.Argument(
    "--learning-rate-multiplier",
    type=float,
    help=(
        "Multiplier for adjusting the default learning rate. Only applicable "
        "to Gemini models. Mutually exclusive with `--learning-rate`. If "
        "neither flag is set, a default value will be calculated based on "
        "the training dataset size."
    ),
)

_LEARNING_RATE = base.Argument(
    "--learning-rate",
    type=float,
    help=(
        "Learning rate for tuning. Only applicable to open source models. "
        "Mutually exclusive with `--learning-rate-multiplier`."
    ),
)

_BATCH_SIZE = base.Argument(
    "--batch-size",
    type=int,
    help="Batch size for tuning. Only applicable to open source models.",
)

_OUTPUT_URI = base.Argument(
    "--output-uri",
    help=(
        "Cloud Storage path to the directory where tuning job outputs are "
        "written. Required for open source models."
    ),
)

_EXPORT_LAST_CHECKPOINT_ONLY = base.Argument(
    "--export-last-checkpoint-only",
    action="store_true",
    default=None,
    help=(
        "If set, disable intermediate checkpoints for the tuning job and "
        "only export the last checkpoint. Default is to enable intermediate "
        "checkpoints."
    ),
)

_TUNING_MODE_CHOICES = ["FULL", "PEFT_ADAPTER"]

_TUNING_MODE = base.Argument(
    "--tuning-mode",
    choices=_TUNING_MODE_CHOICES,
    help=(
        "Tuning mode. ``FULL`` performs full fine-tuning. ``PEFT_ADAPTER`` "
        "performs parameter-efficient fine-tuning (PEFT). Only applicable "
        "to open source models."
    ),
)

_SERVICE_ACCOUNT = base.Argument(
    "--service-account",
    help=(
        "The service account that the tuning job runs as. If not specified, "
        "the Vertex AI Custom Code Service Agent is used."
    ),
)

_ADAPTER_SIZE_CHOICES = ["1", "2", "4", "8", "16", "32"]


def AddCreateTuningJobFlags(parser, include_open_model_flags=False):
  """Adds arguments for creating a tuning job.

  Args:
   parser: the parser for the command.
   include_open_model_flags: bool, whether to include flags whose underlying
     proto fields are restricted to v1beta1 (e.g. ``--learning-rate``,
     ``--custom-base-model``, ``--output-uri``, ``--tuning-mode``,
     ``--batch-size``). These flags should only be exposed on BETA/ALPHA tracks.
  """
  _SOURCE_MODEL.AddToParser(parser)
  _TRAINING_DATASET_URI.AddToParser(parser)
  _VALIDATION_DATASET_URI.AddToParser(parser)
  _TUNED_MODEL_DISPLAY_NAME.AddToParser(parser)
  _DESCRIPTION.AddToParser(parser)
  _EPOCH_COUNT.AddToParser(parser)
  _EXPORT_LAST_CHECKPOINT_ONLY.AddToParser(parser)
  if include_open_model_flags:
    # `--learning-rate-multiplier` (for Gemini) and `--learning-rate` (for open
    # models) are mutually exclusive.
    learning_rate_group = base.ArgumentGroup(
        mutex=True,
        help=(
            "Learning rate configuration for tuning. At most one of "
            "`--learning-rate-multiplier` or `--learning-rate` can be set."
        ),
    )
    learning_rate_group.AddArgument(_LEARNING_RATE_MULTIPLIER)
    learning_rate_group.AddArgument(_LEARNING_RATE)
    learning_rate_group.AddToParser(parser)

    # The following flags are restricted to v1beta1 in the proto and only
    # apply to open source model tuning.
    _CUSTOM_BASE_MODEL.AddToParser(parser)
    _OUTPUT_URI.AddToParser(parser)
    _TUNING_MODE.AddToParser(parser)
    _BATCH_SIZE.AddToParser(parser)
  else:
    _LEARNING_RATE_MULTIPLIER.AddToParser(parser)
  _SERVICE_ACCOUNT.AddToParser(parser)

  labels_util.AddCreateLabelsFlags(parser)

  flags.AddRegionResourceArg(
      parser,
      "to create a tuning job",
      prompt_func=region_util.GetPromptForRegionFunc(
          constants.SUPPORTED_TRAINING_REGIONS
      ),
  )
  flags.AddKmsKeyResourceArg(parser, "tuning job")

  base.Argument(
      "--adapter-size",
      choices=_ADAPTER_SIZE_CHOICES,
      help=(
          "Adapter size for parameter-efficient fine-tuning. "
          "This is only applicable when using a PEFT-compatible model."
      ),
  ).AddToParser(parser)


def AddTuningJobResourceArg(
    parser, verb, regions=constants.SUPPORTED_TRAINING_REGIONS
):
  """Adds a resource argument for a Vertex AI tuning job.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
   parser: the parser for the command.
   verb: str, the verb to describe the resource, such as 'to describe'.
   regions: list[str], the list of supported regions.
  """
  job_resource_spec = concepts.ResourceSpec(
      resource_collection=tuning_jobs_util.TUNING_JOB_COLLECTION,
      resource_name="tuning job",
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=flags.RegionAttributeConfig(
          prompt_func=region_util.GetPromptForRegionFunc(regions)
      ),
      disable_auto_completers=False,
  )

  concept_parsers.ConceptParser.ForResource(
      "tuning_job",
      job_resource_spec,
      "The tuning job {}.".format(verb),
      required=True,
  ).AddToParser(parser)
