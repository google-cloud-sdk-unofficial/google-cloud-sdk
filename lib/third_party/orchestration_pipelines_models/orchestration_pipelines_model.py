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
"""Wrapper model for union of pipeline models."""

from typing import Union
from orchestration_pipelines_models.pipeline_v1_model.orchestration_pipeline_builder import (
    OrchestrationPipelineBuilder, )
from orchestration_pipelines_models.pipeline_v1_model.protos.orchestration_pipeline_pb2 import (
    OrchestrationPipeline, )


class OrchestrationPipelinesModel:
    """
    Wrapper class for orchestration pipelines models.
    This class provides a `build` method to parse a dictionary
    and return the correct model version.
    """

    @classmethod
    def build(cls, pipeline_def: dict) -> Union[OrchestrationPipeline]:
        """
        Builds 1.0 pipeline model from a dictionary based on `modelVersion`.

        Args:
            pipeline_def: A dictionary representing the pipeline model.

        Returns:
            An OrchestrationPipeline instance.

        Raises:
            TypeError: If the input is not a dictionary.
            ValueError: If 'modelVersion' is missing or not supported.
        """
        if not isinstance(pipeline_def, dict):
            raise TypeError("Input must be a dictionary")

        # Support both camelCase ('modelVersion') and snake_case ('model_version').
        model_version = pipeline_def.get("modelVersion") or pipeline_def.get(
            "model_version")

        # For backwards compatibility, map legacy "v2" to "1.0".
        builder_dict = pipeline_def.copy()
        if model_version == "v2":
            model_version = "1.0"
            builder_dict["model_version"] = model_version

        if model_version == "1.0":
            return OrchestrationPipelineBuilder.build(builder_dict)
        else:
            raise ValueError(
                f"Invalid or missing 'model_version'. Value: {model_version}. "
                "Expected '1.0'.")
