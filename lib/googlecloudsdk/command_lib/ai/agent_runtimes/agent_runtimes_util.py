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
"""Utilities shared by the `gcloud ai agent runtimes` commands.

Agent Runtimes are backed by the `ReasoningEngine` API resource. This module
translates the flags declared in
`googlecloudsdk.command_lib.ai.agent_runtimes.flags` into the corresponding
`ReasoningEngine` message, so that the surface commands only have to deal with
the CLI experience.
"""

from __future__ import annotations

import os
from typing import Any

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.agent_runtimes import client
from googlecloudsdk.api_lib.cloudbuild import snapshot
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


# --- Constants ---

_OPERATIONS_COLLECTION = 'aiplatform.projects.locations.operations'
_RUNTIME_OPERATIONS_COLLECTION = (
    'aiplatform.projects.locations.reasoningEngines.operations'
)
_SOURCE_ARCHIVE_NAME = 'source.tar.gz'
_DEFAULT_SECRET_VERSION = 'latest'
_AGENT_RUNTIME_CREATE_DISPLAY_MESSAGE = """\
Request to create the agent runtime [{id}] has been sent.

You may view the status of your agent runtime with the command

  $ {command_prefix} ai agent runtimes describe {id} --region={region}
"""

_FLAG_TO_MASKS = {
    'display_name': ('display_name',),
    'description': ('description',),
    'image': ('spec.container_spec',),
    'source': ('spec.source_code_spec',),
    'agent_framework': ('spec.agent_framework',),
    'agent_card_file': ('spec.agent_card',),
    'class_methods_file': ('spec.class_methods',),
    'service_account': ('spec.service_account', 'spec.identity_type'),
    'default_service_account': ('spec.service_account', 'spec.identity_type'),
    'use_agent_identity': ('spec.service_account', 'spec.identity_type'),
    'min_instances': ('spec.deployment_spec.min_instances',),
    'max_instances': ('spec.deployment_spec.max_instances',),
    'container_concurrency': ('spec.deployment_spec.container_concurrency',),
    'agent_server_mode': ('spec.deployment_spec.agent_server_mode',),
    'cpu_limit': ('spec.deployment_spec.resource_limits',),
    'memory_limit': ('spec.deployment_spec.resource_limits',),
    'env_vars': ('spec.deployment_spec.env',),
    'update_env_vars': ('spec.deployment_spec.env',),
    'remove_env_vars': ('spec.deployment_spec.env',),
    'clear_env_vars': ('spec.deployment_spec.env',),
    'secret_env_vars': ('spec.deployment_spec.secret_env',),
    'update_secret_env_vars': ('spec.deployment_spec.secret_env',),
    'remove_secret_env_vars': ('spec.deployment_spec.secret_env',),
    'clear_secret_env_vars': ('spec.deployment_spec.secret_env',),
    'network_attachment': (
        'spec.deployment_spec.psc_interface_config.network_attachment',
    ),
    'dns_peering_configs': (
        'spec.deployment_spec.psc_interface_config.dns_peering_configs',
    ),
    'client_to_agent_gateway': ('spec.deployment_spec.agent_gateway_config',),
    'agent_to_anywhere_gateway': ('spec.deployment_spec.agent_gateway_config',),
    'keep_alive_probe_path': ('spec.deployment_spec.keep_alive_probe',),
    'keep_alive_probe_port': ('spec.deployment_spec.keep_alive_probe',),
    'keep_alive_probe_timeout': ('spec.deployment_spec.keep_alive_probe',),
    'traffic_split_always_latest': ('traffic_config',),
    'traffic_split_to_revisions': ('traffic_config',),
}


# --- Operation & Execution Helpers ---


def ParseOperation(operation_name: str) -> resources.Resource:
  """Parses an operation resource name into an operation reference.

  Mutations on an agent runtime may return either a location scoped operation
  or one scoped to the agent runtime itself, so both collections are tried.

  Args:
    operation_name: The relative name of the operation resource.

  Returns:
    The parsed operation reference.
  """
  if '/reasoningEngines/' in operation_name:
    try:
      return resources.REGISTRY.ParseRelativeName(
          operation_name, collection=_RUNTIME_OPERATIONS_COLLECTION
      )
    except resources.WrongResourceCollectionException:
      pass
  return resources.REGISTRY.ParseRelativeName(
      operation_name, collection=_OPERATIONS_COLLECTION
  )


def CommandPrefix(release_track) -> str:
  """Returns the `gcloud` invocation prefix for a release track.

  Args:
    release_track: The calliope base.ReleaseTrack of the running command.

  Returns:
    `gcloud` for GA, and `gcloud <track>` otherwise.
  """
  return ' '.join(filter(None, ('gcloud', release_track.prefix)))


def ValidateRegion(region: str) -> None:
  """Validates that the region is supported in the default universe."""
  if properties.IsDefaultUniverse():
    validation.ValidateRegion(
        region, available_regions=constants.SUPPORTED_AP_REGIONS
    )


def CreateRuntime(
    region_ref: resources.Resource,
    args: Any,
    release_track: Any,
    asynchronous: bool = False,
) -> Any:
  """Creates an agent runtime and waits for the operation."""
  region = region_ref.AsDict()['locationsId']
  ValidateRegion(region)
  validation.ValidateDisplayName(args.display_name)
  with endpoint_util.AiplatformEndpointOverrides(
      constants.BETA_VERSION, region=region
  ):
    runtimes_client = client.AgentRuntimesClient(version=constants.BETA_VERSION)
    agent_runtime = AgentRuntimeBuilder(runtimes_client).Build(args)
    try:
      operation = runtimes_client.Create(
          region_ref.RelativeName(), agent_runtime
      )
    except apitools_exceptions.HttpError as error:
      raise api_exceptions.HttpException(
          error,
          'ResponseError: code={status_code}, message={status_message}',
      )
    op_ref = ParseOperation(operation.name)
    runtime_id = op_ref.AsDict().get('reasoningEnginesId')
    response = operations_util.WaitForOpMaybe(
        operations_client=operations.OperationsClient(),
        op=operation,
        op_ref=op_ref,
        asynchronous=asynchronous,
        message='Waiting for the agent runtime to be created...',
    )
    if asynchronous:
      log.status.Print(
          _AGENT_RUNTIME_CREATE_DISPLAY_MESSAGE.format(
              id=runtime_id,
              region=region,
              command_prefix=CommandPrefix(release_track),
          )
      )
    else:
      log.CreatedResource(runtime_id, kind='agent runtime')
    return response


# --- Generic Utility Helpers ---


def _BuildIfAny(cls, **kwargs):
  """Instantiates `cls` only if at least one argument is present (not None)."""
  filtered = {k: v for k, v in kwargs.items() if v is not None}
  return cls(**filtered) if filtered else None


def _Coalesce(val, fallback):
  """Returns `val` if it is not None, otherwise returns `fallback`."""
  return val if val is not None else fallback


def _MutateMap(existing_map, update=None, remove=None):
  """Applies update and remove mutations to a key-value mapping."""
  res = dict(existing_map or {})
  for key in remove or []:
    res.pop(key, None)
  if update:
    res.update(update)
  return res


def _StringMap(map_cls: Any, entries: dict[str, str] | None) -> Any:
  """Converts a dict of strings into an apitools additional properties map."""
  if not entries:
    return None
  return encoding.DictToAdditionalPropertyMessage(
      entries, map_cls, sort_items=True
  )


def _LoadStructuredFile(flag_name: str, path: str | None) -> Any:
  """Loads a JSON or YAML file, returning None when no path is given."""
  if path is None:
    return None
  try:
    # YAML is a superset of JSON, so both formats are parsed the same way.
    return yaml.load_path(path)
  except yaml.Error as e:
    raise gcloud_exceptions.InvalidArgumentException(flag_name, str(e))


def _SourceArchive(source: str) -> bytes:
  """Compresses a local source directory into a `.tar.gz` archive.

  Args:
    source: Path to the local directory holding the agent source code.

  Returns:
    The bytes of the compressed archive.

  Raises:
    InvalidArgumentException: If `source` is not a directory.
  """
  if not os.path.isdir(source):
    raise gcloud_exceptions.InvalidArgumentException(
        '--source', 'Expected a directory but got [{}].'.format(source)
    )
  with files.TemporaryDirectory() as temp_dir:
    archive_path = os.path.join(temp_dir, _SOURCE_ARCHIVE_NAME)
    snapshot.Snapshot(source).MakeTarball(archive_path)
    return files.ReadBinaryFileContents(archive_path)


# --- Update Mask Helpers ---


def _IsFlagSpecified(args, flag_name: str) -> bool:
  if hasattr(args, 'IsSpecified'):
    return args.IsSpecified(flag_name)
  val = getattr(args, flag_name, None)
  return val is not None


def GetUpdateMaskPaths(args, has_labels_update: bool = False) -> list[str]:
  """Returns the update mask paths implied by the flags on the command line."""
  paths = set()
  for flag, masks in _FLAG_TO_MASKS.items():
    if _IsFlagSpecified(args, flag):
      paths.update(masks)
  if has_labels_update:
    paths.add('labels')
  return sorted(paths)


# --- Agent Runtime Builder ---


class AgentRuntimeBuilder:
  """Builds `ReasoningEngine` messages out of parsed command line arguments."""

  def __init__(self, runtimes_client):
    """Initializes the builder.

    Args:
      runtimes_client: The api_lib.ai.agent_runtimes.client.AgentRuntimesClient
        to read the version specific message classes from.
    """
    self._messages = runtimes_client.messages

  def Build(self, args) -> Any:
    """Builds the `ReasoningEngine` message described by `args`."""
    runtime_cls = self._messages.GoogleCloudAiplatformV1beta1ReasoningEngine
    labels = (
        labels_util.ParseCreateArgs(args, runtime_cls.LabelsValue)
        if hasattr(args, 'labels')
        else None
    )
    encryption_spec = None
    if args.kms_key_name:
      encryption_spec = (
          self._messages.GoogleCloudAiplatformV1beta1EncryptionSpec(
              kmsKeyName=args.kms_key_name
          )
      )

    return runtime_cls(
        description=args.description,
        displayName=args.display_name,
        encryptionSpec=encryption_spec,
        labels=labels,
        spec=self._Spec(args),
    )

  def BuildForUpdate(self, args, existing_runtime: Any = None) -> Any:
    """Builds the `ReasoningEngine` message for updating an existing runtime."""
    runtime_cls = self._messages.GoogleCloudAiplatformV1beta1ReasoningEngine
    etag = args.etag or (existing_runtime.etag if existing_runtime else None)
    return runtime_cls(
        description=args.description,
        displayName=args.display_name,
        etag=etag,
        labels=self._UpdateLabels(args, runtime_cls, existing_runtime),
        spec=self._SpecForUpdate(args, existing_runtime),
        trafficConfig=self._TrafficConfig(args),
    )

  def _UpdateLabels(self, args, runtime_cls: Any, existing_runtime: Any) -> Any:
    """Applies label modifications to the existing runtime labels."""
    diff = labels_util.Diff.FromUpdateArgs(args)
    if not diff.MayHaveUpdates():
      return None
    existing_labels = existing_runtime.labels if existing_runtime else None
    return diff.Apply(runtime_cls.LabelsValue, existing_labels).GetOrNone()

  def _TrafficConfig(self, args) -> Any:
    """Builds `ReasoningEngine.traffic_config` from traffic flags."""
    traffic_config_cls = (
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineTrafficConfig
    )
    if args.traffic_split_always_latest:
      always_latest_cls = (
          self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineTrafficConfigTrafficSplitAlwaysLatest
      )
      return traffic_config_cls(trafficSplitAlwaysLatest=always_latest_cls())
    targets = args.traffic_split_to_revisions
    if not targets:
      return None
    target_cls = (
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineTrafficConfigTrafficSplitManualTarget
    )
    manual_cls = (
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineTrafficConfigTrafficSplitManual
    )
    return traffic_config_cls(
        trafficSplitManual=manual_cls(
            targets=[
                target_cls(runtimeRevisionName=rev, percent=pct)
                for rev, pct in sorted(targets.items())
            ]
        )
    )

  def _SpecForUpdate(self, args, existing_runtime: Any = None) -> Any:
    """Builds `ReasoningEngine.spec` for updating an existing runtime."""
    existing_dep = (
        existing_runtime.spec.deploymentSpec
        if existing_runtime and existing_runtime.spec
        else None
    )
    env = self._MutateEnvVars(
        existing_env=existing_dep.env if existing_dep else None,
        update=args.update_env_vars,
        remove=args.remove_env_vars,
        clear=args.clear_env_vars,
        override=args.env_vars,
    )
    secret_env = self._MutateSecretEnvVars(
        existing_secret_env=existing_dep.secretEnv if existing_dep else None,
        update=args.update_secret_env_vars,
        remove=args.remove_secret_env_vars,
        clear=args.clear_secret_env_vars,
        override=args.secret_env_vars,
    )
    deployment_spec = self._DeploymentSpecForUpdate(
        args, env=env, secret_env=secret_env, existing_dep=existing_dep
    )
    spec_cls = self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpec
    identity_type = None
    if args.use_agent_identity:
      identity_type = spec_cls.IdentityTypeValueValuesEnum.AGENT_IDENTITY
    elif args.default_service_account:
      identity_type = spec_cls.IdentityTypeValueValuesEnum.SERVICE_ACCOUNT
    service_account = args.service_account

    return _BuildIfAny(
        spec_cls,
        agentCard=self._AgentCard(spec_cls, args),
        agentFramework=args.agent_framework,
        classMethods=self._ClassMethods(spec_cls, args),
        containerSpec=self._ContainerSpec(args),
        deploymentSpec=deployment_spec,
        identityType=identity_type,
        serviceAccount=service_account,
        sourceCodeSpec=self._SourceCodeSpec(args),
    )

  def _MutateEnvVars(
      self, existing_env, update=None, remove=None, clear=False, override=None
  ) -> Any:
    """Mutates environment variables based on flags and existing state."""
    if clear:
      return []
    if override is not None:
      return self._EnvVars(override)
    if update is None and remove is None:
      return None

    existing_map = {var.name: var.value for var in existing_env or []}
    mutated = _MutateMap(existing_map, update=update, remove=remove)
    return self._EnvVars(mutated) if mutated else []

  def _MutateSecretEnvVars(
      self,
      existing_secret_env,
      update=None,
      remove=None,
      clear=False,
      override=None,
  ) -> Any:
    """Mutates secret env vars based on flags and existing state."""
    if clear:
      return []
    if override is not None:
      return self._SecretEnvVars(override)
    if update is None and remove is None:
      return None

    existing_map = {
        var.name: (
            f'{var.secretRef.secret}:{var.secretRef.version or _DEFAULT_SECRET_VERSION}'
        )
        for var in existing_secret_env or []
        if var.secretRef and var.secretRef.secret
    }
    mutated = _MutateMap(existing_map, update=update, remove=remove)
    return (
        self._SecretEnvVars(mutated, flag_name='--update-secret-env-vars')
        if mutated
        else []
    )

  def _Spec(self, args) -> Any:
    """Builds `ReasoningEngine.spec`."""
    spec_cls = self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpec
    identity_type = (
        spec_cls.IdentityTypeValueValuesEnum.AGENT_IDENTITY
        if args.use_agent_identity
        else None
    )
    service_account = args.service_account

    return _BuildIfAny(
        spec_cls,
        agentCard=self._AgentCard(spec_cls, args),
        agentFramework=args.agent_framework,
        classMethods=self._ClassMethods(spec_cls, args),
        containerSpec=self._ContainerSpec(args),
        deploymentSpec=self._DeploymentSpec(args),
        identityType=identity_type,
        serviceAccount=service_account,
        sourceCodeSpec=self._SourceCodeSpec(args),
    )

  def _ContainerSpec(self, args) -> Any:
    """Builds `ReasoningEngine.spec.container_spec` from `--image`."""
    if not args.image:
      return None
    container_spec_cls = (
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecContainerSpec
    )
    return container_spec_cls(imageUri=args.image)

  def _AgentCard(self, spec_cls: Any, args) -> Any:
    """Builds `ReasoningEngine.spec.agent_card` from `--agent-card-file`."""
    agent_card = _LoadStructuredFile('--agent-card-file', args.agent_card_file)
    if not agent_card:
      return None
    return messages_util.DictToMessageWithErrorCheck(
        agent_card, spec_cls.AgentCardValue
    )

  def _ClassMethods(self, spec_cls: Any, args) -> Any:
    """Builds `ReasoningEngine.spec.class_methods`."""
    class_methods = _LoadStructuredFile(
        '--class-methods-file', args.class_methods_file
    )
    if not class_methods:
      return None
    if not isinstance(class_methods, list):
      raise gcloud_exceptions.InvalidArgumentException(
          '--class-methods-file',
          'Expected a list of class method declarations.',
      )
    return [
        messages_util.DictToMessageWithErrorCheck(
            class_method, spec_cls.ClassMethodsValueListEntry
        )
        for class_method in class_methods
    ]

  def _SourceCodeSpec(self, args) -> Any:
    """Builds `ReasoningEngine.spec.source_code_spec` from `--source`."""
    if args.source is None:
      return None

    image_spec = None
    if args.build_args:
      image_spec_cls = (
          self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecSourceCodeSpecImageSpec
      )
      image_spec = image_spec_cls(
          buildArgs=_StringMap(image_spec_cls.BuildArgsValue, args.build_args)
      )

    python_spec = None
    if any((
        args.entrypoint_module,
        args.entrypoint_object,
        args.requirements_file,
        args.python_version,
    )):
      python_spec = (
          self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecSourceCodeSpecPythonSpec(
              entrypointModule=args.entrypoint_module,
              entrypointObject=args.entrypoint_object,
              requirementsFile=args.requirements_file,
              version=args.python_version,
          )
      )

    inline_source = (
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecSourceCodeSpecInlineSource(
            sourceArchive=_SourceArchive(args.source)
        )
    )

    return _BuildIfAny(
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecSourceCodeSpec,
        imageSpec=image_spec,
        inlineSource=inline_source,
        pythonSpec=python_spec,
    )

  def _DeploymentSpec(self, args) -> Any:
    """Builds `ReasoningEngine.spec.deployment_spec`."""
    deployment_spec_cls = (
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecDeploymentSpec
    )
    agent_server_mode = None
    if args.agent_server_mode is not None:
      agent_server_mode = (
          deployment_spec_cls.AgentServerModeValueValuesEnum(
              args.agent_server_mode.upper()
          )
      )
    resource_limits = {
        key: value
        for key, value in (
            ('cpu', args.cpu_limit),
            ('memory', args.memory_limit),
        )
        if value is not None
    }
    return _BuildIfAny(
        deployment_spec_cls,
        agentGatewayConfig=self._AgentGatewayConfig(args),
        agentServerMode=agent_server_mode,
        containerConcurrency=args.container_concurrency,
        env=self._EnvVars(args.env_vars),
        keepAliveProbe=self._KeepAliveProbe(args),
        maxInstances=args.max_instances,
        minInstances=args.min_instances,
        pscInterfaceConfig=self._PscInterfaceConfig(args),
        resourceLimits=_StringMap(
            deployment_spec_cls.ResourceLimitsValue, resource_limits
        ),
        secretEnv=self._SecretEnvVars(args.secret_env_vars),
    )

  def _DeploymentSpecForUpdate(
      self,
      args,
      env: Any = None,
      secret_env: Any = None,
      existing_dep: Any = None,
  ) -> Any:
    """Builds `ReasoningEngine.spec.deployment_spec` for an update operation."""
    deployment_spec_cls = (
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecDeploymentSpec
    )
    agent_server_mode = None
    if args.agent_server_mode is not None:
      agent_server_mode = deployment_spec_cls.AgentServerModeValueValuesEnum(
          args.agent_server_mode.upper()
      )

    resource_limits = None
    if args.cpu_limit is not None or args.memory_limit is not None:
      limits = {}
      if (
          existing_dep
          and existing_dep.resourceLimits
          and existing_dep.resourceLimits.additionalProperties
      ):
        for prop in existing_dep.resourceLimits.additionalProperties:
          limits[prop.key] = prop.value
      if args.cpu_limit is not None:
        limits['cpu'] = args.cpu_limit
      if args.memory_limit is not None:
        limits['memory'] = args.memory_limit
      resource_limits = _StringMap(
          deployment_spec_cls.ResourceLimitsValue, limits
      )

    agent_gw = self._AgentGatewayConfig(
        args, existing_dep=existing_dep, is_update=True
    )
    keep_alive_probe = self._KeepAliveProbe(
        args, existing_dep=existing_dep, is_update=True
    )

    return _BuildIfAny(
        deployment_spec_cls,
        agentGatewayConfig=agent_gw,
        agentServerMode=agent_server_mode,
        containerConcurrency=args.container_concurrency,
        env=env,
        keepAliveProbe=keep_alive_probe,
        maxInstances=args.max_instances,
        minInstances=args.min_instances,
        pscInterfaceConfig=self._PscInterfaceConfig(args),
        resourceLimits=resource_limits,
        secretEnv=secret_env,
    )

  def _EnvVars(self, env_vars: dict[str, str] | None) -> Any:
    """Builds `deployment_spec.env` from `--env-vars`."""
    if not env_vars:
      return None
    env_var_cls = self._messages.GoogleCloudAiplatformV1beta1EnvVar
    return [
        env_var_cls(name=name, value=value)
        for name, value in sorted(env_vars.items())
    ]

  def _SecretEnvVars(
      self,
      secret_env_vars: dict[str, str] | None,
      flag_name: str = '--secret-env-vars',
  ) -> Any:
    """Builds `deployment_spec.secret_env` from `--secret-env-vars`."""
    if not secret_env_vars:
      return None
    secret_env_var_cls = self._messages.GoogleCloudAiplatformV1beta1SecretEnvVar
    secret_ref_cls = self._messages.GoogleCloudAiplatformV1beta1SecretRef
    secret_envs = []
    for name, value in sorted(secret_env_vars.items()):
      secret, _, version = value.partition(':')
      if not secret:
        raise gcloud_exceptions.InvalidArgumentException(
            flag_name,
            'Expected [{}] to be of the form SECRET[:VERSION].'.format(value),
        )
      secret_envs.append(
          secret_env_var_cls(
              name=name,
              secretRef=secret_ref_cls(
                  secret=secret, version=version or _DEFAULT_SECRET_VERSION
              ),
          )
      )
    return secret_envs

  def _PscInterfaceConfig(self, args) -> Any:
    """Builds `deployment_spec.psc_interface_config`."""
    dns_peering_config_cls = (
        self._messages.GoogleCloudAiplatformV1beta1DnsPeeringConfig
    )
    dns_peering_configs = [
        dns_peering_config_cls(
            domain=config['domain'],
            targetNetwork=config['target-network'],
            targetProject=config['target-project'],
        )
        for config in args.dns_peering_configs or []
    ]
    return _BuildIfAny(
        self._messages.GoogleCloudAiplatformV1beta1PscInterfaceConfig,
        dnsPeeringConfigs=dns_peering_configs or None,
        networkAttachment=args.network_attachment,
    )

  def _AgentGatewayConfig(
      self, args, existing_dep: Any = None, is_update: bool = False
  ) -> Any:
    """Builds `deployment_spec.agent_gateway_config`."""
    has_c2a = args.client_to_agent_gateway is not None
    has_a2a = args.agent_to_anywhere_gateway is not None
    if is_update and not (has_c2a or has_a2a):
      return None

    existing_gw = existing_dep.agentGatewayConfig if existing_dep else None
    c2a = existing_gw.clientToAgentConfig if existing_gw else None
    a2a = existing_gw.agentToAnywhereConfig if existing_gw else None

    c2a_val = _Coalesce(
        args.client_to_agent_gateway, c2a.agentGateway if c2a else None
    )
    a2a_val = _Coalesce(
        args.agent_to_anywhere_gateway, a2a.agentGateway if a2a else None
    )

    c2a_msg = _BuildIfAny(
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecDeploymentSpecAgentGatewayConfigClientToAgentConfig,
        agentGateway=c2a_val,
    )
    a2a_msg = _BuildIfAny(
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecDeploymentSpecAgentGatewayConfigAgentToAnywhereConfig,
        agentGateway=a2a_val,
    )
    return _BuildIfAny(
        self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecDeploymentSpecAgentGatewayConfig,
        agentToAnywhereConfig=a2a_msg,
        clientToAgentConfig=c2a_msg,
    )

  def _KeepAliveProbe(
      self, args, existing_dep: Any = None, is_update: bool = False
  ) -> Any:
    """Builds `deployment_spec.keep_alive_probe`."""
    has_path = args.keep_alive_probe_path is not None
    has_port = args.keep_alive_probe_port is not None
    has_timeout = args.keep_alive_probe_timeout is not None
    if is_update and not (has_path or has_port or has_timeout):
      return None

    probe = existing_dep.keepAliveProbe if existing_dep else None
    http = probe.httpGet if probe else None

    path = _Coalesce(args.keep_alive_probe_path, http.path if http else None)
    port = _Coalesce(args.keep_alive_probe_port, http.port if http else None)
    timeout = _Coalesce(
        args.keep_alive_probe_timeout, probe.maxSeconds if probe else None
    )

    http_get = _BuildIfAny(
        self._messages.GoogleCloudAiplatformV1beta1KeepAliveProbeHttpGet,
        path=path,
        port=port,
    )
    return _BuildIfAny(
        self._messages.GoogleCloudAiplatformV1beta1KeepAliveProbe,
        httpGet=http_get,
        maxSeconds=timeout,
    )
