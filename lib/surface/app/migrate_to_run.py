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
import re
from typing import Any, Mapping, Sequence

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import gae_to_cr_migration_util
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util import export_image
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util import list_incompatible_features
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util import translate
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.common import util
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.config import feature_helper
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from surface.run import deploy


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
class AppEngineToCloudRun(deploy.Deploy):
  """Migrate a second-generation App Engine app to Cloud Run."""
  detailed_help = {
      'DESCRIPTION': """\
          Migrates the second-generation App Engine app to Cloud Run.
          """,
      'EXAMPLES': """\
          To migrate an App Engine app to Cloud Run:\n
          through app.yaml\n
          gcloud app migrate-to-run --appyaml=path/to/app.yaml\n
          OR\n
          through service and version\n
          gcloud app migrate-to-run --service=default --version=v1\n
          """,
  }

  @classmethod
  def Args(cls, parser):
    hidden_parser = _HiddenParserProxy(parser)
    deploy.Deploy.CommonArgs(hidden_parser)
    cls.CommonArgs(parser)
    cls.AddCloudRunFlags(hidden_parser)

  @classmethod
  def CommonArgs(cls, parser) -> None:
    """Common arguments for the App Engine to Cloud Run migration command."""
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

  @classmethod
  def AddCloudRunFlags(cls, parser) -> None:
    """Adds Cloud Run flags common to Alpha and Beta migration commands."""
    container_args = deploy.ContainerArgGroup(cls.ReleaseTrack())
    container_args.AddArgument(flags.ReadinessProbeFlag())
    deploy.container_parser.AddContainerFlags(
        parser, container_args, cls.ReleaseTrack()
    )

    flags.AddRuntimeFlag(parser)
    flags.SERVICE_MESH_FLAG.AddToParser(parser)
    flags.IDENTITY_FLAG.AddToParser(parser)
    flags.IDENTITY_CERTIFICATE_FLAG.AddToParser(parser)
    flags.IDENTITY_TYPE_FLAG.AddToParser(parser)
    flags.FUNCTIONAL_TYPE_FLAG.AddToParser(parser)
    flags.MESH_DATAPLANE_FLAG.AddToParser(parser)
    flags.AddDelegateBuildsFlag(parser)
    flags.AddOverflowScalingFlag(parser)
    flags.AddCpuUtilizationFlag(parser)
    flags.AddConcurrencyUtilizationFlag(parser)
    flags.AddPresetFlags(parser)

  def Run(self, args):
    """Overrides the Deploy.Run method.

    This method applies wrapper logic for FlagIsExplicitlySet.

    Args:
      args: The argparse namespace.
    """
    self.api_client = appengine_api_client.GetApiClientForTrack(
        self.ReleaseTrack()
    )
    gae_to_cr_migration_util.GAEToCRMigrationUtil(self.api_client, args)
    self.release_track = self.ReleaseTrack()
    original_flag_is_explicitly_set = flags.FlagIsExplicitlySet
    try:
      flags.FlagIsExplicitlySet = self._flag_is_explicitly_set_wrapper
      self._start_migration(args)
      # Execute the gcloud run deploy command using the arguments prepared in
      # StartMigration.

      # Calling super().Run() from a parent class is considered an
      # anti-pattern and should not be replicated(see yaqs/3868851564655411200).
      # Our long-term plan is to refactor the cloud run deploy logic into a
      # shared command_lib so that both the App Engine migration tool and Cloud
      # Run can utilize it.
      super().Run(args)
      self._print_migration_summary(args)
    finally:
      flags.FlagIsExplicitlySet = original_flag_is_explicitly_set

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

  def _start_migration(self, args) -> None:
    """Starts the migration process.

    This method translates App Engine configuration to Cloud Run deployment
    flags and updates the `args` object with these flags, preparing it
    for the `gcloud run deploy` command.

    Args:
      args: The argparse namespace containing command line arguments. This
        object is mutated to include flags necessary for the Cloud Run
        deployment.
    """

    # List incompatible features.
    input_data, input_type = util.get_version_data(
        appyaml=args.appyaml, service=args.service, version=args.version
    )
    list_incompatible_features.list_incompatible_features(
        input_data, input_type, args.appyaml, args.service, args.version
    )

    if util.is_flex_env(input_data):
      cloud_run_deploy_command = self._run_deploy_command_for_flex(
          args, input_data, input_type
      )
    else:
      cloud_run_deploy_command = self._run_deploy_command_for_standard(
          args, input_data, input_type
      )

    print_deploy_command = ' '.join(cloud_run_deploy_command) + ' '
    log.status.Print('Command to run:', print_deploy_command, '\n')
    setattr(args, 'SERVICE', cloud_run_deploy_command[3])
    self._migration_flags = []
    for command_str in cloud_run_deploy_command:
      if command_str.startswith('--'):
        command_str = command_str.replace('--', '')
        # TODO: b/445905035 - Use ArgDict type for args to simplify the parsing
        # logic
        parts = command_str.split('=', 1)
        flag_name = parts[0].replace('-', '_')
        self._migration_flags.append(flag_name)
        flag_value = parts[1] if len(parts) > 1 else None
        if flag_name == 'labels':
          label_value = parts[1] if len(parts) > 1 else ''
          setattr(args, flag_name, _parse_labels(label_value))
          continue
        if flag_name == 'image':
          setattr(args, flag_name, flag_value)
          continue
        if flag_name == 'set_env_vars':
          env_vars_value = parts[1] if len(parts) > 1 else ''
          setattr(
              args, flag_name, _parse_set_env_vars(env_vars_value.strip('"'))
          )
          continue
        if flag_name == 'timeout':
          if flag_value == '600':
            setattr(args, flag_name, 600)
          elif flag_value == '3600':
            setattr(args, flag_name, 3600)
          continue
        if flag_name == 'min_instances':
          setattr(args, flag_name, flags.ScaleValue(flag_value))
          continue
        if flag_name == 'max_instances':
          setattr(args, flag_name, flags.ScaleValue(flag_value))
          continue
        if flag_name in ['liveness_probe', 'readiness_probe']:
          setattr(args, flag_name, self._parse_dict_string(flag_value))
          continue
        if flag_name == 'scaling':
          setattr(args, flag_name, flags.ScalingValue(flag_value))
          continue
        if flag_name in ['add_volume', 'add_volume_mount']:
          current_value = getattr(args, flag_name, None)
          if current_value is None:
            setattr(args, flag_name, [])
          getattr(args, flag_name).append(
              self._parse_dict_string(flag_value)
          )
          continue
        if flag_name == 'network_tags':
          setattr(args, flag_name, flag_value.split(',') if flag_value else [])
          continue
        if flag_name == 'ingress':
          setattr(args, flag_name, flag_value)
          continue
        if flag_name == 'network':
          setattr(args, flag_name, flag_value)
          continue
        if flag_name == 'subnet':
          setattr(args, flag_name, flag_value)
          continue
        if flag_name == 'session_affinity':
          setattr(args, flag_name, True)
          continue
        if flag_name == 'port':
          setattr(args, flag_name, flag_value)
          continue
        if flag_value is not None:
          setattr(args, flag_name, flag_value)
        else:
          setattr(args, flag_name, True)
    return

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
          f' https://console.cloud.google.com/run/detail/{region}/{service}/metrics?project={project}\n'
          f'Deploy new versions of your code with the same configuration using "gcloud'
          f' run deploy {service} --image=<new-image>'
          f' --region={region} --project={project}"\n'
      )
    else:
      log.status.Print(
          'View and edit in Cloud Run console:'
          f' https://console.cloud.google.com/run/detail/{region}/{service}/metrics?project={project}\nDeploy'
          ' new versions of your code with the same configuration using "gcloud'
          f' run deploy {service} --source=.'
          f' --region={region} --project={project}"\n'
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

  def _run_deploy_command_for_flex(
      self,
      args,
      input_data: Mapping[str, any],
      input_type: feature_helper.InputType,
  ) -> Sequence[str]:
    """Handles the flex environment."""
    if getattr(args, 'from_image', False):
      return translate.translate_from_image(
          input_data,
          args.service,
      )
    else:
      return translate.translate_from_source(
          input_data, input_type, args.appyaml, args.service
      )

  def _run_deploy_command_for_standard(
      self,
      args,
      input_data: Mapping[str, any],
      input_type: feature_helper.InputType,
  ) -> Sequence[str]:
    """Handles the standard environment."""

    if self.release_track is base.ReleaseTrack.ALPHA and args.from_image:
      project = properties.VALUES.core.project.Get()

      export_image_response = export_image.export_image(
          project,
          args.service,
          args.version,
          args.destination_repository,
          api_client=self.api_client,
          export_service_account=None,
      )

      return translate.translate_from_exported_image(
          input_data,
          args.service,
          export_image_response,
      )
    else:
      return translate.translate_from_source(
          input_data, input_type, args.appyaml, args.service
      )


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

  def _ValidateAndGeDeployFromSource(self, containers: Any) -> dict[Any, Any]:
    if hasattr(self, '_migration_flags') and 'image' in self._migration_flags:
      # If an image is provided, we are not deploying from source, so we return
      # an empty dict to skip source deployment validation.
      return {}
    return super()._ValidateAndGeDeployFromSource(containers)
