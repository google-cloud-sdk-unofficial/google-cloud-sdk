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
"""Builds an OrchestrationPipeline protobuf message from a dictionary."""

from typing import Any, Dict

from cloudsdk.google.protobuf import json_format
from orchestration_pipelines_models.pipeline_v1_model.protos.orchestration_pipeline_pb2 import (
    OrchestrationPipeline, )
from orchestration_pipelines_models.pipeline_v1_model.pipeline_validation import (
    PipelineValidator, )


class OrchestrationPipelineBuilder:
    """Builds an OrchestrationPipeline from a dictionary."""

    @classmethod
    def build(cls, pipeline_def: Dict[str, Any]) -> OrchestrationPipeline:
        """Maps a dictionary to an OrchestrationPipeline object."""
        pipeline = OrchestrationPipeline()
        json_format.ParseDict(js_dict=pipeline_def,
                              message=pipeline,
                              ignore_unknown_fields=False)
        PipelineValidator.validate(pipeline)
        return pipeline
