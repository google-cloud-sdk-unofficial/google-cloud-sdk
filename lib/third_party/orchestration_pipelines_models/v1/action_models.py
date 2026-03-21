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

from typing import Literal, Optional, List, Any, Dict, Union
from attrs import define, field, validators
import cattrs
from orchestration_pipelines_models.utils.time_utils import validate_duration


@define(kw_only=True)
class ActionBaseModel:
    name: str
    dependsOn: Optional[List[str]] = None


@define(kw_only=True)
class PythonScriptConfigurationModel:
    pythonCallable: str
    opKwargs: Optional[Dict[str, Any]] = None


@define(kw_only=True)
class PythonScriptActionModel(ActionBaseModel):
    type: Literal['script']
    filename: str
    config: PythonScriptConfigurationModel


@define(kw_only=True)
class PythonVirtualenvConfigurationModel(PythonScriptConfigurationModel):
    requirementsPath: Optional[str] = None
    requirements: Optional[List[str]] = None
    systemSitePackages: Optional[bool] = None

    def __attrs_post_init__(self):
        if bool(self.requirements) == bool(
                self.requirementsPath) and self.requirements:
            raise ValueError(
                'Either "requirements" list or "requirementsPath" must be provided, but not both.'
            )


@define(kw_only=True)
class PythonVirtualenvActionModel(ActionBaseModel):
    type: Literal['python-virtual-env']
    filename: str
    config: PythonVirtualenvConfigurationModel


@define(kw_only=True)
class ResourceProfile:
    runtimeConfig: Optional[Dict[str, Any]] = None
    environmentConfig: Optional[Dict[str, Any]] = None
    gcsReference: Optional[str] = None

    def __attrs_post_init__(self):
        if self.gcsReference is not None and (self.runtimeConfig is not None
                                              or self.environmentConfig
                                              is not None):
            raise ValueError(
                'If "gcsReference" is specified, "runtimeConfig" and "environmentConfig" must be empty.'
            )


@define(kw_only=True)
class DataprocCreateBatchOperatorConfigurationModel:
    resourceProfile: ResourceProfile


@define(kw_only=True)
class BqOperationConfigurationModel:
    location: str
    destinationTable: Optional[str] = None


@define(kw_only=True)
class DataprocServerlessSQLJobConfigurationModel():
    job: Dict[str, Any]


@define(kw_only=True)
class DataprocEphemeralConfigurationModel:
    region: str
    project_id: str
    cluster_name: str
    cluster_config: Dict[str, Any]
    job: Dict[str, Any]


@define(kw_only=True)
class DataprocGceExistingClusterConfigurationModel:
    cluster: str


@define(kw_only=True)
class EngineModel:
    engineType: Literal['dataproc-gce', 'dataproc-serverless']
    clusterMode: Optional[Literal['existing', 'ephemeral']] = None


AnyEngineModel = Union[Literal['bq'], EngineModel]


@define(kw_only=True)
class DataprocOperatorActionModel(ActionBaseModel):
    type: Literal['notebook', 'pyspark', 'operation']
    filename: Optional[str] = None
    query: Optional[str] = None
    executionTimeout: Optional[str] = field(
        default=None, validator=validators.optional(validate_duration))
    region: Optional[str] = None
    engine: AnyEngineModel
    archives: Optional[List[str]] = None
    depsBucket: Optional[str] = None
    impersonationChain: Optional[Union[str, List[str]]] = None
    config: Union[DataprocGceExistingClusterConfigurationModel,
                  DataprocEphemeralConfigurationModel,
                  DataprocCreateBatchOperatorConfigurationModel,
                  BqOperationConfigurationModel,
                  DataprocServerlessSQLJobConfigurationModel]

    def __attrs_post_init__(self):
        engine = self.engine
        config = self.config
        if self.type != 'operation' and isinstance(engine, EngineModel):
            if engine.engineType == 'dataproc-gce':
                if not engine.clusterMode:
                    raise ValueError(
                        "clusterMode is required for 'dataproc-gce' engine")
                if not config:
                    raise ValueError(
                        "config is required for 'dataproc-gce' engine")
                if engine.clusterMode == 'existing':
                    if not isinstance(
                            config,
                            DataprocGceExistingClusterConfigurationModel):
                        raise ValueError(
                            "Incorrect config type for existing cluster")
                elif engine.clusterMode == 'ephemeral':
                    if not isinstance(config,
                                      DataprocEphemeralConfigurationModel):
                        raise ValueError(
                            "Incorrect config type for ephemeral cluster")

            elif engine.engineType == 'dataproc-serverless':
                if engine.clusterMode:
                    raise ValueError(
                        "clusterMode is not allowed for 'dataproc-serverless' engine"
                    )
                if not config:
                    raise ValueError(
                        "config is required for 'dataproc-serverless' engine")
                if not isinstance(
                        config, DataprocCreateBatchOperatorConfigurationModel):
                    raise ValueError(
                        "Incorrect config type for dataproc-serverless")


@define(kw_only=True)
class DbtLocalExecutionModel:
    path: str


@define(kw_only=True)
class DataformServiceConfigModel:
    project_id: Optional[str] = None
    region: Optional[str] = None
    repository_id: str
    workflow_invocation: Dict[str, Any]


@define(kw_only=True)
class DataformConfigModel:
    executionMode: Literal['local', 'service']
    dataformProjectPath: Optional[str] = None
    dataformServiceConfig: Optional[DataformServiceConfigModel] = None


@define(kw_only=True)
class DbtConfigModel:
    executionMode: Literal['local']
    source: DbtLocalExecutionModel
    select_models: Optional[List[str]] = None


@define(kw_only=True)
class PipelineActionModel(ActionBaseModel):
    type: Literal['pipeline']
    engine: Literal['dbt', 'dataform']
    config: dict

    def __attrs_post_init__(self):
        c = cattrs.Converter()
        if self.engine == 'dataform':
            if not isinstance(self.config, (DataformConfigModel, dict)):
                raise ValueError("Incorrect config type for dataform engine")
            if isinstance(self.config, dict):
                self.config = c.structure(self.config, DataformConfigModel)
        elif self.engine == 'dbt':
            if not isinstance(self.config, (DbtConfigModel, dict)):
                raise ValueError("Incorrect config type for dbt engine")
            if isinstance(self.config, dict):
                self.config = c.structure(self.config, DbtConfigModel)
        return self
