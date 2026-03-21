# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Wrapper model for union of v1 and v2 pipeline models."""

from typing import Union
from orchestration_pipelines_models.v1.pipeline_model import PipelineModel as PipelineModelV1
from orchestration_pipelines_models.v2.orchestration_pipeline_builder import (
    OrchestrationPipelineBuilder, )
from orchestration_pipelines_models.v2.protos.orchestration_pipeline_pb2 import (
    OrchestrationPipeline, )


class OrchestrationPipelinesModel:
    """
    Wrapper class for orchestration pipelines models.
    This class provides a `build` method to parse a dictionary
    and return the correct model version.
    """

    @classmethod
    def build(cls, obj: dict) -> Union[PipelineModelV1, OrchestrationPipeline]:
        """
        Builds a v1 or v2 model from a dictionary based on `model_version`.

        Args:
            obj: A dictionary representing the pipeline model.

        Returns:
            A PipelineModelV1 or OrchestrationPipeline instance.

        Raises:
            TypeError: If the input is not a dictionary.
            ValueError: If 'model_version' is missing or invalid.
            """
        if not isinstance(obj, dict):
            raise TypeError("Input must be a dictionary")

        # Temporary fallback as we are migrating towards CamelCase
        model_version = obj.get("modelVersion")
        if not model_version:
            model_version = obj.get("model_version")

        if model_version == "v1":
            return PipelineModelV1.from_dict(obj)
        elif model_version == "v2":
            return OrchestrationPipelineBuilder.build(obj)
        else:
            raise ValueError(
                f"Invalid or missing 'model_version'. Value: {model_version}. "
                "Expected 'v1' or 'v2'.")
