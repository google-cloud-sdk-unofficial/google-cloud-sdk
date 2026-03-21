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

from enum import Enum
from typing import Optional, List, Union

from attrs import define, field, validators
import cattrs

from orchestration_pipelines_models.v1.action_models import PythonScriptActionModel, PythonVirtualenvActionModel, DataprocOperatorActionModel, PipelineActionModel
from orchestration_pipelines_models.v1.action_models import AnyEngineModel, EngineModel
from orchestration_pipelines_models.v1.trigger_models import ScheduleTriggerModel

AnyAction = Union[PythonScriptActionModel, PythonVirtualenvActionModel,
                  DataprocOperatorActionModel, PipelineActionModel]
AnyScheduleTrigger = Union[ScheduleTriggerModel]


class RunnerType(str, Enum):
    CORE = 'core'
    AIRFLOW = 'airflow'


@define(kw_only=True)
class ExecutionConfigModel:
    retries: int = field(converter=int, validator=validators.ge(0))


@define(kw_only=True)
class DefaultsModel:
    project: str
    region: str
    executionConfig: ExecutionConfigModel


@define(kw_only=True)
class OnPipelineFailureModel:
    email: List[str]


@define(kw_only=True)
class NotificationModel:
    onPipelineFailure: OnPipelineFailureModel


@define(kw_only=True)
class PipelineModel:
    pipelineId: str = field(
        validator=validators.matches_re(r'^[a-zA-Z0-9_.-]+$'))
    description: str
    runner: RunnerType
    owner: str
    defaults: DefaultsModel
    triggers: List[AnyScheduleTrigger]
    actions: List[AnyAction]
    tags: Optional[List[str]] = None
    notifications: Optional[NotificationModel] = None

    @classmethod
    def from_dict(cls, definition: dict):
        main_converter = cattrs.Converter(detailed_validation=True)

        def _boolean_structure_hook(obj, _):
            if isinstance(obj, bool):
                return obj
            if isinstance(obj, str):
                if obj.lower() == "true":
                    return True
                if obj.lower() == "false":
                    return False
            raise ValueError(f"Expected a boolean value, but got '{obj}'")

        def _dataproc_engine_structure_hook(value, _):
            if value == 'bq':
                return value

            return main_converter.structure(value, EngineModel)

        def _impersonation_chain_structure_hook(value, _):
            if isinstance(value, str):
                return [value]
            return value

        main_converter.register_structure_hook(bool, _boolean_structure_hook)
        main_converter.register_structure_hook(
            AnyEngineModel, _dataproc_engine_structure_hook)
        main_converter.register_structure_hook(
            Optional[Union[str, List[str]]],
            _impersonation_chain_structure_hook)

        try:
            return main_converter.structure(definition, cls)
        except Exception as e:
            raise e
