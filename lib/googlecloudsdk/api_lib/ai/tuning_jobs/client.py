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
"""Utilities for querying tuning jobs in Vertex AI."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants


class TuningJobsClient(object):
  """Client used for interacting with the Vertex AI TuningJob endpoint."""

  # Mapping from the user-facing adapter size string to the enum suffix.
  _ADAPTER_SIZE_TO_ENUM_SUFFIX = {
      "1": "ONE",
      "2": "TWO",
      "4": "FOUR",
      "8": "EIGHT",
      "16": "SIXTEEN",
      "32": "THIRTY_TWO",
  }

  def __init__(self, version=constants.GA_VERSION):
    client = apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version],
    )
    self._messages = client.MESSAGES_MODULE
    self._service = client.projects_locations_tuningJobs
    self._version = version
    self._message_prefix = constants.AI_PLATFORM_MESSAGE_PREFIX[version]

  def _GetMessage(self, message_name):
    """Returns the API messages class by name."""
    return getattr(
        self._messages,
        "{prefix}{name}".format(prefix=self._message_prefix, name=message_name),
        None,
    )

  def TuningJobMessage(self):
    """Returns the TuningJob resource message class."""
    return self._GetMessage("TuningJob")

  def SupervisedTuningSpecMessage(self):
    """Returns the SupervisedTuningSpec message class."""
    return self._GetMessage("SupervisedTuningSpec")

  def SupervisedHyperParametersMessage(self):
    """Returns the SupervisedHyperParameters message class."""
    return self._GetMessage("SupervisedHyperParameters")

  def AdapterSizeEnum(self):
    """Returns enum message representing AdapterSize."""
    return self.SupervisedHyperParametersMessage().AdapterSizeValueValuesEnum

  def TuningModeEnum(self):
    """Returns enum message representing SupervisedTuningSpec.TuningMode.

    Returns None on the GA (v1) version because the field is gated to v1beta1
    in the proto and so the enum is not generated on the v1 message.
    """
    spec_msg = self.SupervisedTuningSpecMessage()
    return getattr(spec_msg, "TuningModeValueValuesEnum", None)

  def ParseAdapterSize(self, adapter_size):
    """Converts an adapter size string choice to the API enum value.

    Args:
     adapter_size: str, the adapter size choice (e.g. "1", "2", "4", "8", "16",
       "32"), or None.

    Returns:
     The corresponding AdapterSizeValueValuesEnum value, or None.
    """
    if adapter_size is None:
      return None
    enum_cls = self.AdapterSizeEnum()
    suffix = self._ADAPTER_SIZE_TO_ENUM_SUFFIX[adapter_size]
    return enum_cls("ADAPTER_SIZE_{}".format(suffix))

  def ParseTuningMode(self, tuning_mode):
    """Converts a tuning mode string choice to the API enum value.

    Args:
     tuning_mode: str, the tuning mode choice (e.g. "FULL", "PEFT_ADAPTER"), or
       None.

    Returns:
     The corresponding TuningModeValueValuesEnum value, or None if the field is
     unsupported on this API version.
    """
    if tuning_mode is None:
      return None
    enum_cls = self.TuningModeEnum()
    if enum_cls is None:
      return None
    name = "TUNING_MODE_{}".format(tuning_mode)
    return enum_cls(name)

  def Create(
      self,
      parent,
      source_model,
      training_dataset_uri,
      validation_dataset_uri=None,
      tuned_model_display_name=None,
      description=None,
      epoch_count=None,
      learning_rate_multiplier=None,
      learning_rate=None,
      batch_size=None,
      adapter_size=None,
      tuning_mode=None,
      export_last_checkpoint_only=None,
      custom_base_model=None,
      output_uri=None,
      labels=None,
      encryption_key_name=None,
      service_account=None,
  ):
    """Creates a supervised fine-tuning job with given parameters.

    Args:
     parent: str, parent resource name for the tuning job. e.g.
       projects/xxx/locations/xxx/
     source_model: str, the base model to tune, e.g. "gemini-1.0-pro-002" or
       "meta/llama3_1@llama-3.1-8b". Maps to TuningJob.base_model.
     training_dataset_uri: str, Cloud Storage URI of the training dataset.
     validation_dataset_uri: str, optional Cloud Storage URI of the validation
       dataset.
     tuned_model_display_name: str, optional display name for the tuned model.
     description: str, optional description for the tuning job.
     epoch_count: int, optional number of training epochs.
     learning_rate_multiplier: float, optional learning rate multiplier (Gemini
       models only). Mutually exclusive with `learning_rate`.
     learning_rate: float, optional learning rate (open source models only).
       Mutually exclusive with `learning_rate_multiplier`. Only available on
       v1beta1; silently ignored on v1.
     batch_size: int, optional batch size for tuning (open source models only,
       v1beta1).
     adapter_size: AdapterSizeValueValuesEnum, optional adapter size for
       parameter-efficient fine-tuning.
     tuning_mode: TuningModeValueValuesEnum, optional tuning mode (FULL or
       PEFT_ADAPTER). Only available on v1beta1; silently ignored on v1.
     export_last_checkpoint_only: bool, if True disable intermediate checkpoints
       and only export the last one. Available on both v1 and v1beta1.
     custom_base_model: str, optional Cloud Storage path to custom model weights
       to start tuning from (open source models only, v1beta1).
     output_uri: str, optional Cloud Storage path to write tuning job outputs
       (required for open source models, v1beta1).
     labels: LabelsValue, optional map-like user-defined metadata to organize
       the tuning jobs.
     encryption_key_name: str, optional customer-managed encryption key.
     service_account: str, optional service account email.

    Returns:
     Created TuningJob resource.
    """
    # Build the hyperparameters.
    hyper_parameters = self.SupervisedHyperParametersMessage()()
    has_hyper_params = False
    if epoch_count is not None:
      hyper_parameters.epochCount = epoch_count
      has_hyper_params = True
    if learning_rate_multiplier is not None:
      hyper_parameters.learningRateMultiplier = learning_rate_multiplier
      has_hyper_params = True
    if learning_rate is not None and hasattr(hyper_parameters, "learningRate"):
      hyper_parameters.learningRate = learning_rate
      has_hyper_params = True
    if batch_size is not None and hasattr(hyper_parameters, "batchSize"):
      hyper_parameters.batchSize = batch_size
      has_hyper_params = True
    if adapter_size is not None:
      hyper_parameters.adapterSize = adapter_size
      has_hyper_params = True

    # Build the supervised tuning spec.
    supervised_tuning_spec = self.SupervisedTuningSpecMessage()(
        trainingDatasetUri=training_dataset_uri
    )
    if validation_dataset_uri:
      supervised_tuning_spec.validationDatasetUri = validation_dataset_uri
    if has_hyper_params:
      supervised_tuning_spec.hyperParameters = hyper_parameters
    if export_last_checkpoint_only is not None:
      supervised_tuning_spec.exportLastCheckpointOnly = (
          export_last_checkpoint_only
      )
    if tuning_mode is not None and hasattr(
        supervised_tuning_spec, "tuningMode"
    ):
      supervised_tuning_spec.tuningMode = tuning_mode

    # Build the tuning job.
    tuning_job = self.TuningJobMessage()(
        baseModel=source_model, supervisedTuningSpec=supervised_tuning_spec
    )

    if tuned_model_display_name:
      tuning_job.tunedModelDisplayName = tuned_model_display_name

    if description:
      tuning_job.description = description

    if custom_base_model and hasattr(tuning_job, "customBaseModel"):
      tuning_job.customBaseModel = custom_base_model

    if output_uri and hasattr(tuning_job, "outputUri"):
      tuning_job.outputUri = output_uri

    if encryption_key_name is not None:
      tuning_job.encryptionSpec = self._GetMessage("EncryptionSpec")(
          kmsKeyName=encryption_key_name
      )

    if service_account:
      tuning_job.serviceAccount = service_account

    if labels:
      tuning_job.labels = labels

    if self._version == constants.GA_VERSION:
      request = (
          self._messages.AiplatformProjectsLocationsTuningJobsCreateRequest(
              parent=parent, googleCloudAiplatformV1TuningJob=tuning_job
          )
      )
    else:
      request = (
          self._messages.AiplatformProjectsLocationsTuningJobsCreateRequest(
              parent=parent, googleCloudAiplatformV1beta1TuningJob=tuning_job
          )
      )
    return self._service.Create(request)

  def Get(self, name):
    """Gets a tuning job by its full resource name.

    Args:
     name: str, the full resource name of the tuning job.

    Returns:
     The TuningJob resource.
    """
    request = self._messages.AiplatformProjectsLocationsTuningJobsGetRequest(
        name=name
    )
    return self._service.Get(request)

  def Cancel(self, name):
    """Cancels a tuning job.

    Args:
     name: str, the full resource name of the tuning job.

    Returns:
     Empty response.
    """
    request = self._messages.AiplatformProjectsLocationsTuningJobsCancelRequest(
        name=name
    )
    return self._service.Cancel(request)

  def List(self, limit=None, region=None):
    """Lists tuning jobs in the given region.

    Args:
     limit: int, optional maximum number of results to return.
     region: str, the parent resource name (projects/x/locations/y).

    Returns:
     An iterator of TuningJob resources.
    """
    return list_pager.YieldFromList(
        self._service,
        self._messages.AiplatformProjectsLocationsTuningJobsListRequest(
            parent=region
        ),
        field="tuningJobs",
        batch_size_attribute="pageSize",
        limit=limit,
    )
