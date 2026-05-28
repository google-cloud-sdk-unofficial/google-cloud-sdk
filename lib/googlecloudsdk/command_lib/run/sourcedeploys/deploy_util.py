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


"""Utility for deploying Cloud Run resources from source."""

import argparse
import os.path
import re
from typing import Any, Tuple
import uuid

from googlecloudsdk.api_lib.run import api_enabler
from googlecloudsdk.api_lib.run import instance
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.run import artifact_registry
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as run_flags
from googlecloudsdk.command_lib.run import iap_util
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.run.sourcedeploys import deployer
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker


_CLOUDRUN_SOURCE_DEPLOY_REPO = 'cloud-run-source-deploy'
_PORT_ATTRIBUTE = 'port'
_INVOKER_IAM_CHECK_ATTRIBUTE = 'invoker_iam_check'
_INGRESS_SETTINGS_ATTRIBUTE = 'ingress_settings'
_Namespace = argparse.Namespace


class ImageCreationError(exceptions.Error):
  """Image creation failed."""
  pass


def _CreateBuildPack(
    image: str, source: str, args: _Namespace
) -> list[dict[str, Any]]:
  """A helper method to configure buildpack."""
  pack = [{'image': image}]
  project_toml_file = os.path.join(source, 'project.toml')
  command_arg = getattr(args, 'command', None)
  function_arg = getattr(args, 'function', None)
  if command_arg is not None:
    command = ' '.join(command_arg)
    pack[0].update(
        {'envs': ['GOOGLE_ENTRYPOINT="{command}"'.format(command=command)]}
    )
  elif function_arg is not None:
    pack[0].update({
        'envs': [
            'GOOGLE_FUNCTION_SIGNATURE_TYPE=http',
            'GOOGLE_FUNCTION_TARGET={target}'.format(target=function_arg),
        ]
    })
  if os.path.exists(project_toml_file):
    pack[0].update({'project_descriptor': 'project.toml'})
  return pack


def _BuildImageFromArgs(
    project: str, image_suffix: str, args: _Namespace
) -> Tuple[str, docker_util.DockerRepo | None]:
  """Prepares the build image name and repository to create.

  Args:
    project: The current GCP project ID.
    image_suffix: The suffix to use for the image name.
    args: The argparse namespace containing command-line arguments.

  Returns:
    A tuple (build_image_name, repo_to_create), where build_image_name is
    the full image name to be used for the build, and repo_to_create is
    the Docker repository to create if it doesn't exist, or None.
  """

  ar_repo = docker_util.DockerRepo(
      project_id=project,
      location_id=artifact_registry.RepoRegion(args),
      repo_id=_CLOUDRUN_SOURCE_DEPLOY_REPO,
  )
  repo_to_create = (
      ar_repo if artifact_registry.ShouldCreateRepository(ar_repo) else None
  )
  return f'{ar_repo.GetDockerString()}/{image_suffix}', repo_to_create


def _GetRequiredApis():
  apis = [api_enabler.get_run_api()]
  apis.append('artifactregistry.googleapis.com')
  apis.append('cloudbuild.googleapis.com')
  return apis


def _GetSourceBucketFromBuildSourceLocation(
    source_location: str | None,
) -> str | None:
  log.debug('source_location: %s', source_location)
  if not source_location:
    return None
  x = re.search(r'gs://([^/]+)/.*', source_location)
  if x:
    return x.group(1)
  log.debug('source_location does not match pattern gs://([^/]+)/.*')
  return None


def DeployInstanceFromSource(
    instance_ref: resources.Resource | None,
    source: str,
    region: str,
    args: _Namespace,
    release_track: base.ReleaseTrack,
    changes: list[config_changes.ConfigChanger] | None = None,
) -> instance.Instance:
  """Deploys a Cloud Run instance from source.

  Args:
    instance_ref: The fully parsed resource reference to the instance to deploy,
      or None to create an instance with a generated name.
    source: The path to the source to deploy.
    region: The region to deploy to.
    args: The arguments passed to the command.
    release_track: The release track of the command.
    changes: The list of config changes to apply.

  Returns:
    The created instance object.

  Raises:
    ImageCreationError: If the container image fails to build.
  """
  if not source:
    raise ValueError('Source is required for source deployment.')

  if changes is None:
    changes = []

  is_async = getattr(args, 'async_', False)
  already_activated_services = api_enabler.check_and_enable_apis(
      properties.VALUES.core.project.Get(), _GetRequiredApis()
  )

  instance_name = None
  project = properties.VALUES.core.project.Get(required=True)

  if instance_ref:
    parent_ref = instance_ref.Parent()
    instance_name = instance_ref.Name()
  else:
    # instance_ref is None, name not provided. Build parent_ref manually.
    # Construct the parent reference (namespace)
    parent_ref = resources.REGISTRY.Create(
        'run.namespaces', namespacesId=project
    )

  conn_context = connection_context.GetConnectionContext(
      args,
      run_flags.Product.RUN,
      release_track,
  )
  changes.extend(
      run_flags.GetInstanceConfigurationChanges(
          args, release_track=release_track
      )
  )
  changes.append(config_changes.SetLaunchStageAnnotationChange(release_track))

  messages_util.MaybeLogDefaultGpuTypeMessage(args, resource=None)
  with serverless_operations.Connect(
      conn_context, already_activated_services
  ) as operations:
    pretty_print.Info(
        messages_util.GetStartCreateInstanceMessage(
            conn_context, parent_ref, instance_name
        )
    )
    image_suffix = instance_name or f'instance-{uuid.uuid4().hex[:8]}'
    build_image, repo_to_create = _BuildImageFromArgs(
        project, image_suffix, args
    )

    header = 'Creating instance...'

    with progress_tracker.StagedProgressTracker(
        header,
        stages.InstanceStages(
            include_build=source is not None,
            include_create_repo=repo_to_create is not None,
        ),
        failure_message='Instance failed to deploy',
        suppress_output=is_async,
    ) as tracker:
      image_digest = None
      if source is not None:
        docker_file = os.path.join(source, 'Dockerfile')
        build_pack = None
        if not os.path.exists(docker_file):
          build_pack = _CreateBuildPack(build_image, source, args)
        try:
          image_digest, *_ = deployer.CreateImage(
              tracker=tracker,
              build_image=build_image,
              build_source=source,
              build_pack=build_pack,
              repo_to_create=repo_to_create,
              release_track=release_track,
              already_activated_services=already_activated_services,
              region=region,
              resource_ref=instance_ref,
              build_env_vars=getattr(args, 'build_env_vars', None),
          )
        except Exception as e:
          raise ImageCreationError(
              f'Failed to create image for instance {instance_name!r}: {e}'
          ) from e
        if image_digest is None:
          raise ImageCreationError(
              f'Failed to create image for instance {instance_name!r}.'
              ' Please check the build logs for more details.'
          )

      # If we have a digest, use it. Otherwise use the build_image name (which
      # might be just the image provided in args).
      final_image = (
          f'{build_image}@{image_digest}' if image_digest else build_image
      )
      changes.append(config_changes.ImageChange(final_image))

      result_instance = operations.CreateInstance(
          parent_ref,
          instance_name,
          changes,
          tracker=tracker,
          asyn=is_async,
      )

    if is_async:
      pretty_print.Success(
          'Instance [{{bold}}{instance}{{reset}}] is being created '
          'asynchronously.'.format(instance=result_instance.name)
      )
    else:
      pretty_print.Success(
          'Instance [{{bold}}{instance}{{reset}}] has successfully been'
          ' created.'.format(instance=result_instance.name)
      )
      if result_instance.urls:
        pretty_print.Success(
            'Instance URL: {{bold}}{url}{{reset}}'.format(
                url=result_instance.urls[0]
            )
        )

    return result_instance


def _GetIap(args: _Namespace, service_obj: Any) -> bool | None:
  """Gives the IAP state based on flags and service state.

  Args:
    args: The argparse namespace containing command-line arguments.
    service_obj: The existing service object, or None if the service does not
      exist yet.

  Returns:
    True or False: based on IAP flags for existing services.
    True: If flag is set to true for new service.
    None: If flag is set to false for new service, or if the flags are not
      explicitly set, or if the service does not exist and the flag was set
      to False.
  """
  if run_flags.FlagIsExplicitlySet(args, 'iap'):
    iap = args.iap
  elif run_flags.FlagIsExplicitlySet(args, 'public') and args.public:
    iap = False
  else:
    # Neither flag is specified, so we don't want to change the IAP state.
    return None

  if not iap and not service_obj:
    return None

  return iap


def DeployServiceFromSource(
    service_ref: resources.Resource | None,
    source: str,
    region: str,
    args: _Namespace,
    release_track: base.ReleaseTrack,
    changes: list[config_changes.ConfigChanger] | None = None,
) -> service.Service:
  """Deploys a Cloud Run service from source.

  Args:
    service_ref: The fully parsed resource reference to the service to deploy,
      or None to create a service with a generated name.
    source: The path to the source to deploy.
    region: The region to deploy to.
    args: The arguments passed to the command.
    release_track: The release track of the command.
    changes: The list of config changes to apply.

  Returns:
    The created service object.
  """
  if not source:
    raise ValueError('Source is required for source deployment.')

  if changes is None:
    changes = []

  is_async = getattr(args, 'async_', False)
  already_activated_services = api_enabler.check_and_enable_apis(
      properties.VALUES.core.project.Get(), _GetRequiredApis()
  )

  service_name = service_ref.Name()
  project = properties.VALUES.core.project.Get(required=True)

  conn_context = connection_context.GetConnectionContext(
      args,
      product=run_flags.Product.RUN,
      release_track=release_track,
      region_label=region,
  )
  changes.extend(run_flags.GetServiceConfigurationChanges(args, release_track))
  changes.append(config_changes.SetLaunchStageAnnotationChange(release_track))

  messages_util.MaybeLogDefaultGpuTypeMessage(args, resource=None)
  with serverless_operations.Connect(
      conn_context, already_activated_services
  ) as client:
    pretty_print.Info(
        messages_util.GetStartDeployMessage(
            conn_context, service_ref, service_name
        )
    )
    build_image, repo_to_create = _BuildImageFromArgs(
        project, service_name, args
    )
    changes.append(config_changes.ImageChange(build_image))

    service_obj = client.GetService(service_ref)
    iap = _GetIap(args, service_obj)

    if iap:
      if iap_util.IsOrglessProject(
          project
      ) and not iap_util.IsIapAlreadyEnabled(release_track):
        pretty_print.Info(
            '\n {bold}**[Warning]**{reset} Deploying services with IAP'
            ' enabled in a project outside of an Organization and may require'
            ' initial setup via the Cloud Console. Please use the Cloud Run'
            ' UI to enable IAP for the first time in the project. '
            'https://cloud.google.com/run/docs/securing/identity-aware-proxy-cloud-run#custom-oauth-client\n'
        )

    source_bucket = (
        _GetSourceBucketFromBuildSourceLocation(service_obj.source_location)
        if service_obj
        else None
    )
    allow_unauth = run_flags.GetAllowUnauthenticated(
        args,
        client=client,
        service_ref=service_ref,
        prompt=service_obj is None,
    )

    header = 'Deploying service...'

    with progress_tracker.StagedProgressTracker(
        header,
        stages.ServiceStages(
            include_iam_policy_set=allow_unauth is not None,
            include_validate_service=True,
            include_upload_source=True,
            include_build=True,
            # Include IAP stage if enabling IAP, or if disabling IAP on an
            # existing service (to clean up IAM bindings).
            include_iap=(iap or (iap is not None and service_obj is not None)),
            include_create_repo=repo_to_create is not None,
        ),
        failure_message='Service failed to deploy',
        suppress_output=is_async,
    ) as tracker:
      docker_file = os.path.join(source, 'Dockerfile')
      build_pack = None
      if not os.path.exists(docker_file):
        build_pack = _CreateBuildPack(build_image, source, args)

      deployed_service = client.ReleaseService(
          service_ref,
          changes,
          release_track,
          tracker,
          asyn=is_async,
          allow_unauthenticated=allow_unauth,
          prefetch=service_obj,
          build_image=build_image,
          build_source=source,
          build_pack=build_pack,
          repo_to_create=repo_to_create,
          build_region=region,
          already_activated_services=already_activated_services,
          source_bucket=source_bucket,
          iap_enabled=iap,
          build_env_vars=getattr(args, 'build_env_vars', None),
      )

    if is_async:
      pretty_print.Success(
          f'Service [{{bold}}{deployed_service.name}{{reset}}] is being'
          ' deployed asynchronously.'
      )
    else:
      pretty_print.Success(
          f'Service [{{bold}}{deployed_service.name}{{reset}}] has successfully'
          ' been deployed.'
      )
      url = deployed_service.latest_url or (
          deployed_service.status.url if deployed_service.status else ''
      )

      if url:
        pretty_print.Success(f'Service URL: {{bold}}{url}{{reset}}')

    return deployed_service
