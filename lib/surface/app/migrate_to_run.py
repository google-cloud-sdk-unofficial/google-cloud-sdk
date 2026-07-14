# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""The gcloud app migrate-to-run command."""

import collections
import os
import re
import textwrap
from typing import Any, Mapping

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import gae_to_cr_migration_util
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util import export_image
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util import list_incompatible_features
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util import translate
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.common import util
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import required_flags
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.run import artifact_registry
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.run.sourcedeploys import deployer
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files
from surface.run.services import replace


def _parse_labels(labels_str: str) -> Mapping[str, str]:
  """Parses a 'labels' string and converts it into an OrderedDict.

  Args:
      labels_str: A string in the format of 'key1=value1,key2=value2'.

  Returns:
      An OrderedDict containing the labels.
  """
  if not labels_str:
    return collections.OrderedDict()

  return collections.OrderedDict(
      pair.split('=', 1) for pair in labels_str.split(',') if '=' in pair
  )


def _parse_set_env_vars(
    env_vars_str: str,
) -> Mapping[str, str]:
  """Parses a 'set-env-vars' string and converts it into an OrderedDict.

  Args:
      env_vars_str: A string in the format of "KEY1=VALUE1,KEY2=VALUE2".

  Returns:
      An OrderedDict containing the environment variables.
  """
  if not env_vars_str:
    return collections.OrderedDict()

  return collections.OrderedDict(
      pair.split('=', 1) for pair in env_vars_str.split(',') if '=' in pair
  )


class _HiddenParserProxy:
  """Proxy for calliope parser that sets hidden=True for all added arguments."""

  def __init__(self, real_parser: Any) -> None:
    """Initializes the proxy."""
    self._real_parser = real_parser

  def add_argument(self, *args: Any, **kwargs: Any) -> Any:
    """Adds an argument to the parser, setting hidden=True."""
    kwargs['hidden'] = True
    return self._real_parser.add_argument(*args, **kwargs)

  def add_group(self, *args: Any, **kwargs: Any) -> '_HiddenParserProxy':
    """Adds a group to the parser, setting hidden=True."""
    kwargs['hidden'] = True
    return _HiddenParserProxy(self._real_parser.add_group(*args, **kwargs))

  def add_argument_group(
      self, *args: Any, **kwargs: Any
  ) -> '_HiddenParserProxy':
    """Adds an argument group to the parser, setting hidden=True."""
    kwargs['hidden'] = True
    return _HiddenParserProxy(
        self._real_parser.add_argument_group(*args, **kwargs)
    )

  def add_mutually_exclusive_group(
      self, *args: Any, **kwargs: Any
  ) -> '_HiddenParserProxy':
    """Adds a mutually exclusive group to the parser, setting hidden=True."""
    kwargs['hidden'] = True
    return _HiddenParserProxy(
        self._real_parser.add_mutually_exclusive_group(*args, **kwargs)
    )

  def set_defaults(self, **kwargs: Any) -> None:
    """Sets default values for arguments."""
    return self._real_parser.set_defaults(**kwargs)

  def get_default(self, dest: str) -> Any:
    """Gets the default value for an argument."""
    return self._real_parser.get_default(dest)

  def register(self, registry_name: str, value: Any, obj: Any) -> None:
    """Registers a value with the parser."""
    return self._real_parser.register(registry_name, value, obj)

  def parse_known_args(
      self, args: Any = None, namespace: Any = None
  ) -> tuple[Any, list[str]]:
    """Parses known arguments from a list of arguments."""
    return self._real_parser.parse_known_args(args=args, namespace=namespace)

  def __getattr__(self, name: str) -> Any:
    """Gets an attribute from the real parser."""
    return getattr(self._real_parser, name)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AppEngineToCloudRun(replace.Replace):
  """Migrate a second-generation App Engine app to Cloud Run."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Migrates the second-generation App Engine app to Cloud Run.
          """),
      'EXAMPLES': textwrap.dedent("""\
          To migrate an App Engine app to Cloud Run:\n
          through app.yaml\n
          gcloud app migrate-to-run --appyaml=path/to/app.yaml\n
          OR\n
          through service and version\n
          gcloud app migrate-to-run --service=default --version=v1\n
          """),
  }

  @classmethod
  def Args(cls, parser):
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetNamespaceResourceSpec(),
        'Namespace to replace service.',
        required=False,
        prefixes=False,
        hidden=True,
    )
    concept_parsers.ConceptParser([namespace_presentation]).AddToParser(parser)

    flags.AddAsyncFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddDryRunFlag(parser)

    parser.display_info.AddFormat('none')

    cls.CommonArgs(parser)

  @classmethod
  def CommonArgs(cls, parser) -> None:
    """Common arguments for the App Engine to Cloud Run migration command."""
    flags.AddRegionArg(parser)
    parser.add_argument(
        '--appyaml',
        help=(
            'Path to the app.yaml file for the second generation App Engine'
            ' version to be migrated. If not provided, the app.yaml present in'
            ' the current directory is used.'
        ),
    )
    parser.add_argument(
        '--service',
        help=(
            'Name of the service that is deployed in App Engine. If specified,'
            ' the configuration of the existing service will be used and'
            ' app.yaml in the current directory will be ignored.'
        ),
    )
    parser.add_argument(
        '--version',
        help=(
            'Name of the version that is deployed in App Engine. If specified,'
            ' the configuration of the existing version will be used and'
            ' app.yaml in the current directory will be ignored.'
        ),
    )
    parser.add_argument(
        '--export-only',
        metavar='EXPORT_PATH',
        help=(
            'Export the generated Cloud Run service.yaml to the provided path.'
            ' Migration stops without deploying the service.'
        ),
    )

  def Run(self, args):
    """Overrides the Replace.Run method.

    Args:
      args: The argparse namespace.
    """
    self.api_client = appengine_api_client.GetApiClientForTrack(
        self.ReleaseTrack()
    )
    gae_to_cr_migration_util.GAEToCRMigrationUtil(self.api_client, args)
    self.release_track = self.ReleaseTrack()

    # If region is not specified, default to us-central1.
    region = flags.GetRegion(args) or 'us-central1'
    properties.VALUES.run.region.Set(region)
    if not getattr(args, 'region', None):
      setattr(args, 'region', region)

    if not self._start_migration(args):
      return

    super().Run(args)
    self._print_migration_summary(args)

  def _flag_is_explicitly_set_wrapper(self, unused_args, flag) -> bool:
    """Wrapper function to check if a flag is explicitly set.

    This wrapper checks for flags added during the migration process,
    in addition to the original flags.FlagIsExplicitlySet check.

    Args:
      unused_args: The arguments to check (unused).
      flag: The flag to check.

    Returns:
      bool: True if the flag is explicitly set, False otherwise.
    """
    return hasattr(self, '_migration_flags') and flag in self._migration_flags

  def _get_base_changes(self, args):
    """Returns the service config changes with some default settings."""
    changes = flags.GetServiceConfigurationChanges(args, self.ReleaseTrack())
    changes.insert(
        0,
        config_changes.DeleteAnnotationChange(
            k8s_object.BINAUTHZ_BREAKGLASS_ANNOTATION
        ),
    )
    changes.append(
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack())
    )
    return changes

  def _get_image(self, args, input_data, project, preview_only=False):
    """Gets the image from arguments or infers it based on environment and flags.

    Args:
      args: The argparse namespace containing command line arguments.
      input_data: The parsed App Engine configuration data.
      project: The Google Cloud project ID.
      preview_only: If True, only attempts to find an existing image without
        triggering an export for Standard environments.

    Returns:
      tuple: (str, str): The URI of the container image and the base image,
      or (None, None) if they cannot be determined.
    """

    # Image-based deployment is only supported in ALPHA track with --from-image.
    if self.ReleaseTrack() is not base.ReleaseTrack.ALPHA:
      return None, None
    if not getattr(args, 'from_image', False):
      return None, None

    # For Flex environments, extract the existing container image.
    if util.is_flex_env(input_data):
      if 'deployment' in input_data and hasattr(
          input_data['deployment'], 'container'
      ):
        return input_data['deployment'].container.image, None
      return None, None

    if preview_only:
      return None, None

    # For Standard environments, perform an image export.
    export_image_response = export_image.export_image(
        project,
        args.service,
        args.version,
        getattr(args, 'destination_repository', None),
        api_client=self.api_client,
    )
    if export_image_response:
      return (
          export_image_response.image_uri,
          export_image_response.runtime_base_image,
      )

    return None, None

  def _build_image_from_source(
      self, args, input_data, input_type, project, target_service
  ):
    """Builds a container image from the application source.

    This function determines the source path, sets up an Artifact Registry
    repository, and uses the Cloud Build service to build a container image
    from the provided source code, potentially using a Dockerfile or buildpacks.

    Args:
      args: The argparse namespace containing command line arguments.
      input_data: The configuration data parsed from input.
      input_type: The type of input provided (e.g., 'appyaml',
        'service_version').
      project: The Google Cloud project ID.
      target_service: The name of the Cloud Run service.

    Returns:
      tuple: (str, str): The URI of the built container image with digest and
      the rectified base image URI, or (None, None) if the build fails.

    Raises:
      core_exceptions.Error: If the image build process fails.
    """
    # For --export-only runs, region might not be provided/prompted, so we
    # default to 'us-central1' to construct valid Artifact Registry repository
    # paths.
    region = flags.GetRegion(args) or 'us-central1'
    source_path = translate.get_source_path(input_type, args.appyaml)

    service_ref = resources.REGISTRY.Parse(
        target_service,
        params={'namespacesId': project},
        collection='run.namespaces.services',
    )

    ar_repo = docker_util.DockerRepo(
        project_id=project,
        location_id=region,
        repo_id='cloud-run-source-deploy',
    )
    if artifact_registry.ShouldCreateRepository(
        ar_repo, skip_activation_prompt=True
    ):
      repo_to_create = ar_repo
    else:
      repo_to_create = None

    build_image = f'{ar_repo.GetDockerString()}/{target_service}'

    build_env_vars = input_data.get('build_env_variables')
    base_image = util.determine_base_image(input_data, region)

    with progress_tracker.StagedProgressTracker(
        'Building Container...',
        stages.ServiceStages(
            include_upload_source=True,
            include_build=True,
            include_create_repo=repo_to_create is not None,
        ),
        failure_message='Container build failed',
        suppress_output=False,
    ) as tracker:
      docker_file = os.path.join(source_path, 'Dockerfile')
      build_pack = (
          [{'image': build_image}] if not os.path.exists(docker_file) else None
      )
      enable_automatic_updates = (
          base_image is not None and build_pack is not None
      )
      image_digest, base_image_from_build, *_ = deployer.CreateImage(
          tracker=tracker,
          build_image=build_image,
          build_source=source_path,
          build_pack=build_pack,
          repo_to_create=repo_to_create,
          release_track=self.ReleaseTrack(),
          skip_activation_prompt=True,
          region=region,
          resource_ref=service_ref,
          base_image=base_image,
          build_env_vars=build_env_vars,
          enable_automatic_updates=enable_automatic_updates,
      )
      if image_digest is None:
        raise core_exceptions.Error('Failed to create image.')
      if not enable_automatic_updates:
        base_image_from_build = None
      return f'{build_image}@{image_digest}', base_image_from_build

  def _start_migration(self, args) -> bool:
    """Starts the migration process.

    This method translates App Engine configuration to a Cloud Run service.yaml
    dictionary, performs source upload/build if necessary, and populates
    args.FILE.

    Args:
      args: The argparse namespace containing command line arguments.

    Returns:
      True if deployment should proceed, False if cancelled.
    """

    # List incompatible features.
    input_data, input_type = util.get_version_data(
        appyaml=args.appyaml, service=args.service, version=args.version
    )
    list_incompatible_features.list_incompatible_features(
        input_data, input_type, args.appyaml, args.service, args.version
    )

    if getattr(args, 'dry_run', False):
      log.status.Print('To deploy, use the command without the --dry-run flag.')
      return False

    project = properties.VALUES.core.project.Get()
    service_name = args.service
    service_yaml = translate.translate_to_service_yaml(
        input_data, input_type, project, service_name
    )
    target_service = service_yaml['metadata']['name']

    image, runtime_base_image = self._get_image(
        args, input_data, project, preview_only=True
    )

    if not image:
      service_yaml['spec']['template']['spec']['containers'][0][
          'image'
      ] = '<built-from-source>'
      if not getattr(args, 'from_image', False):
        runtime_base_image = util.determine_base_image(
            input_data, flags.GetRegion(args)
        )
    else:
      service_yaml['spec']['template']['spec']['containers'][0]['image'] = image

    if runtime_base_image:
      required_flags.update_service_yaml_with_base_image(
          service_yaml, runtime_base_image
      )

    yaml_str = yaml.dump(service_yaml)
    log.status.Print('\n--- Generated service.yaml ---\n')
    log.status.Print(yaml_str)

    from_image = getattr(args, 'from_image', False)
    export_val = getattr(args, 'export_only', None)
    yaml_path = None

    if export_val:
      if (
          os.path.isdir(export_val)
          or export_val.endswith('/')
          or export_val.endswith(os.sep)
      ):
        yaml_path = os.path.join(export_val, 'service.yaml')
      else:
        yaml_path = export_val
    elif not from_image:
      base_dir = '.'
      if getattr(args, 'appyaml', None):
        base_dir = os.path.dirname(args.appyaml) or '.'
      yaml_path = os.path.join(base_dir, 'service.yaml')

    if export_val is not None:
      try:
        files.WriteFileContents(yaml_path, yaml_str)
        log.status.Print(f'\nSaved service configuration to {yaml_path}')
      except (files.Error, OSError) as e:
        log.warning(
            'Could not save service configuration to %r. Error: %s',
            yaml_path,
            e,
        )
      return False

    if not console_io.PromptContinue(message='Proceed with the deployment?'):
      log.status.Print('Deployment cancelled by user.')
      return False

    if not image:
      if from_image:
        final_image, runtime_base_image = self._get_image(
            args, input_data, project, preview_only=False
        )
      else:
        final_image, runtime_base_image = self._build_image_from_source(
            args, input_data, input_type, project, target_service
        )

      if final_image:
        service_yaml['spec']['template']['spec']['containers'][0][
            'image'
        ] = final_image
        if runtime_base_image:
          required_flags.update_service_yaml_with_base_image(
              service_yaml, runtime_base_image
          )
        yaml_str = yaml.dump(service_yaml)

    if not from_image:
      try:
        files.WriteFileContents(yaml_path, yaml_str)
        log.status.Print(f'\nSaved service configuration to {yaml_path}')
      except (files.Error, OSError) as e:
        log.warning(
            'Could not save service configuration to %r. Error:'
            ' %s\nContinuing with deployment...',
            yaml_path,
            e,
        )

    setattr(args, 'FILE', service_yaml)
    setattr(args, 'SERVICE', target_service)

    # We must provide the correct namespace in the args.
    if not hasattr(args, 'namespace'):
      # Just stub this so the concept parser in replace.py doesn't complain
      # if the user hasn't supplied --namespace. We parsed it above anyway.
      pass

    return True

  def _print_migration_summary(self, args):
    """Prints the migration summary."""
    log.status.Print(
        '\n'
        'The code and configuration of your App Engine service has been copied'
        ' to Cloud Run.'
        '\n'
    )
    region = properties.VALUES.run.region.Get()
    service = args.SERVICE or 'default'
    project = properties.VALUES.core.project.Get()

    if self.release_track is base.ReleaseTrack.ALPHA and args.from_image:
      log.status.Print(
          'View and edit in Cloud Run console:'
          f' https://console.cloud.google.com/run/detail/{region}/{service}/metrics?project={project}\nDeploy'
          ' new versions of your code with the same configuration using'
          f' "gcloud run deploy {service} --image=<new-image> --region={region}'
          f' --project={project}"\n'
      )
    else:
      log.status.Print(
          'View and edit in Cloud Run console:'
          f' https://console.cloud.google.com/run/detail/{region}/{service}/metrics?project={project}\nDeploy'
          ' new versions of your code with the same configuration using'
          f' "gcloud run deploy {service} --source=. --region={region}'
          f' --project={project}"\n'
      )

    log.status.Print(
        'Note: By default, the migrated Cloud Run service does not allow'
        ' public access.\nTo allow public access, go to the Security tab of'
        ' this service in the Cloud Run Console:\n '
        f' https://console.cloud.google.com/run/detail/{region}/{service}/security?project={project}\nFor'
        ' more details, see:'
        ' https://cloud.google.com/run/docs/authenticating/public\n'
    )

  def _parse_dict_string(self, value_str: str) -> dict[str, str]:
    """Parses a comma-separated key=value string into a dictionary.

    Args:
        value_str: A string in the format of 'key1=val1,key2=val2'.

    Returns:
        A dictionary containing the parsed key-value pairs.
    """
    return dict(
        pair.split('=', 1) for pair in value_str.split(',') if '=' in pair
    )

  def _parse_set_env_vars(
      self, input_str: str
  ) -> collections.OrderedDict[str, str]:
    """Parses a 'set-env-vars' string and converts it into an OrderedDict.

    Args:
        input_str: A string in the format of
          'set-env-vars="KEY1=VALUE1,KEY2=VALUE2"'.

    Returns:
        An OrderedDict containing the environment variables.
    """
    match = re.search(r'="([^"]*)"', input_str)

    if not match:
      return collections.OrderedDict()
    vars_string = match.group(1)

    if not vars_string:
      return collections.OrderedDict()

    env_vars = collections.OrderedDict(
        pair.split('=', 1) for pair in vars_string.split(',')
    )
    return env_vars


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AppEngineToCloudRunAlpha(AppEngineToCloudRun):
  """Migrate a second-generation App Engine app to Cloud Run."""

  @classmethod
  def CommonArgs(cls, parser) -> None:
    super().CommonArgs(parser)
    parser.add_argument(
        '--from-source',
        action='store_true',
        help='Use source based migration.',
    )
    parser.add_argument(
        '--from-image',
        action='store_true',
        help='Use image based migration.',
    )
    parser.add_argument(
        '--destination-repository',
        help=(
            'The full resource name of the AR repository to export to in the'
            ' format of projects/*/locations/*/repositories/*.'
        ),
    )
