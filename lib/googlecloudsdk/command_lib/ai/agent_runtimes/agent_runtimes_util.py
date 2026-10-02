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
from googlecloudsdk.api_lib.cloudbuild import snapshot
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


_OPERATIONS_COLLECTION = 'aiplatform.projects.locations.operations'
_RUNTIME_OPERATIONS_COLLECTION = (
    'aiplatform.projects.locations.reasoningEngines.operations'
)
_SOURCE_ARCHIVE_NAME = 'source.tar.gz'
_DEFAULT_SECRET_VERSION = 'latest'


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


class AgentRuntimeBuilder:
  """Builds `ReasoningEngine` messages out of parsed command line arguments."""

  def __init__(self, client):
    """Initializes the builder.

    Args:
      client: The api_lib.ai.agent_runtimes.client.AgentRuntimesClient to read
        the version specific message classes from.
    """
    self._messages = client.messages

  def Build(self, args) -> Any:
    """Builds the `ReasoningEngine` message described by `args`."""
    runtime_cls = self._messages.GoogleCloudAiplatformV1beta1ReasoningEngine
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
        labels=labels_util.ParseCreateArgs(args, runtime_cls.LabelsValue),
        spec=self._Spec(args),
    )

  def _Spec(self, args) -> Any:
    """Builds `ReasoningEngine.spec`."""
    spec_cls = self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpec
    identity_type = (
        spec_cls.IdentityTypeValueValuesEnum.AGENT_IDENTITY
        if args.use_agent_identity
        else None
    )

    fields = {
        'agentCard': self._AgentCard(spec_cls, args),
        'agentFramework': args.agent_framework,
        'classMethods': self._ClassMethods(spec_cls, args),
        'containerSpec': self._ContainerSpec(args),
        'deploymentSpec': self._DeploymentSpec(args),
        'identityType': identity_type,
        'serviceAccount': args.service_account,
        'sourceCodeSpec': self._SourceCodeSpec(args),
    }
    non_null_fields = {k: v for k, v in fields.items() if v is not None}
    if not non_null_fields:
      return None

    return spec_cls(**non_null_fields)

  def _ContainerSpec(self, args) -> Any:
    """Builds `ReasoningEngine.spec.container_spec` from `--image`."""
    if not args.image:
      return None
    return self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecContainerSpec(
        imageUri=args.image
    )

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

    fields = {
        'imageSpec': image_spec,
        'inlineSource': inline_source,
        'pythonSpec': python_spec,
    }
    non_null_fields = {k: v for k, v in fields.items() if v is not None}
    return self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecSourceCodeSpec(
        **non_null_fields
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
        for key, value in (('cpu', args.cpu_limit), ('memory',
                                                     args.memory_limit))
        if value is not None
    }

    fields = {
        'agentGatewayConfig': self._AgentGatewayConfig(args),
        'agentServerMode': agent_server_mode,
        'containerConcurrency': args.container_concurrency,
        'env': self._EnvVars(args.env_vars),
        'keepAliveProbe': self._KeepAliveProbe(args),
        'maxInstances': args.max_instances,
        'minInstances': args.min_instances,
        'pscInterfaceConfig': self._PscInterfaceConfig(args),
        'resourceLimits': _StringMap(
            deployment_spec_cls.ResourceLimitsValue, resource_limits
        ),
        'secretEnv': self._SecretEnvVars(args.secret_env_vars),
    }
    non_null_fields = {k: v for k, v in fields.items() if v is not None}
    if not non_null_fields:
      return None

    return deployment_spec_cls(**non_null_fields)

  def _EnvVars(self, env_vars: dict[str, str] | None) -> Any:
    """Builds `deployment_spec.env` from `--env-vars`."""
    if not env_vars:
      return None
    env_var_cls = self._messages.GoogleCloudAiplatformV1beta1EnvVar
    return [
        env_var_cls(name=name, value=value)
        for name, value in sorted(env_vars.items())
    ]

  def _SecretEnvVars(self, secret_env_vars: dict[str, str] | None) -> Any:
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
            '--secret-env-vars',
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
    fields = {
        'dnsPeeringConfigs': dns_peering_configs or None,
        'networkAttachment': args.network_attachment,
    }
    non_null_fields = {k: v for k, v in fields.items() if v is not None}
    if not non_null_fields:
      return None
    return self._messages.GoogleCloudAiplatformV1beta1PscInterfaceConfig(
        **non_null_fields
    )

  def _AgentGatewayConfig(self, args) -> Any:
    """Builds `deployment_spec.agent_gateway_config`."""
    c2a = None
    if args.client_to_agent_gateway:
      c2a = (
          self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecDeploymentSpecAgentGatewayConfigClientToAgentConfig(
              agentGateway=args.client_to_agent_gateway
          )
      )
    a2a = None
    if args.agent_to_anywhere_gateway:
      a2a = (
          self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecDeploymentSpecAgentGatewayConfigAgentToAnywhereConfig(
              agentGateway=args.agent_to_anywhere_gateway
          )
      )
    if not (c2a or a2a):
      return None
    return self._messages.GoogleCloudAiplatformV1beta1ReasoningEngineSpecDeploymentSpecAgentGatewayConfig(
        agentToAnywhereConfig=a2a,
        clientToAgentConfig=c2a,
    )

  def _KeepAliveProbe(self, args) -> Any:
    """Builds `deployment_spec.keep_alive_probe`."""
    has_path = args.keep_alive_probe_path is not None
    has_port = args.keep_alive_probe_port is not None
    has_timeout = args.keep_alive_probe_timeout is not None
    if not (has_path or has_port or has_timeout):
      return None

    http_get = None
    if has_path or has_port:
      http_get = (
          self._messages.GoogleCloudAiplatformV1beta1KeepAliveProbeHttpGet(
              path=args.keep_alive_probe_path,
              port=args.keep_alive_probe_port,
          )
      )
    return self._messages.GoogleCloudAiplatformV1beta1KeepAliveProbe(
        httpGet=http_get,
        maxSeconds=args.keep_alive_probe_timeout,
    )
