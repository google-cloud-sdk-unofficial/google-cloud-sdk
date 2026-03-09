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
from typing import Any

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import gae_to_cr_migration_util
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util import export_image
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util import list_incompatible_features
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util import translate
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from surface.run import deploy
from typing_extensions import override


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
          gcloud app migrate-to-run --appyaml=path/to/app.yaml --entrypoint=main\n
          OR\n
          through service and version\n
          gcloud app migrate-to-run --service=default --version=v1 --entrypoint=main\n
          """,
  }

  @classmethod
  def Args(cls, parser):
    deploy.Deploy.CommonArgs(parser)
    cls.CommonArgs(parser)
    cls.AddCloudRunFlags(parser)

  @classmethod
  def CommonArgs(cls, parser) -> None:
    """Common arguments for the App Engine to Cloud Run migration command."""
    parser.add_argument(
        '--appyaml',
        help=(
            'YAML file for the second generation App Engine version to be'
            ' migrated.'
        ),
    )
    parser.add_argument(
        '--service',
        help='service name that is deployed in App Engine',
    )
    parser.add_argument(
        '--version',
        help='version name that is deployed in App Engine',
    )
    parser.add_argument(
        '--entrypoint',
        help='entrypoint required for some runtimes',
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
      flags.FlagIsExplicitlySet = self._FlagIsExplicitlySetWrapper
      self.StartMigration(args)
      # Execute the gcloud run deploy command using the arguments prepared in
      # StartMigration.
      super().Run(args)
      self.PrintMigrationSummary(args)
    finally:
      flags.FlagIsExplicitlySet = original_flag_is_explicitly_set

  def _FlagIsExplicitlySetWrapper(self, unused_args, flag) -> bool:
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

  def _GetBaseChanges(self, args):
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

  def StartMigration(self, args) -> None:
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
    list_incompatible_features.list_incompatible_features(
        args.appyaml, args.service, args.version
    )

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

      cloud_run_deploy_command = translate.translate_from_image(
          args.service,
          args.version,
          args.entrypoint,
          export_image_response,
      )
    else:
      cloud_run_deploy_command = translate.translate_from_source(
          args.appyaml, args.service, args.version, args.entrypoint
      )
    print_deploy_command = ' '.join(cloud_run_deploy_command) + ' '
    if args.entrypoint:
      setattr(
          args,
          'set-build-env-vars',
          {'GOOGLE_ENTRYPOINT': args.entrypoint},
      )
      print_deploy_command += (
          ' --set-build-env-vars GOOGLE_ENTRYPOINT=' + args.entrypoint
      )

    log.status.Print('Command to run:', print_deploy_command, '\n')
    setattr(args, 'SERVICE', cloud_run_deploy_command[3])
    self._migration_flags = []
    for command_str in cloud_run_deploy_command:
      if command_str.startswith('--'):
        command_str = command_str.replace('--', '')
        # TODO: b/445905035 - Use ArgDict type for args to simplify the parsing
        # logic
        command_args = command_str.split('=')
        command_args[0] = command_args[0].replace('-', '_')
        self._migration_flags.append(command_args[0])
        if command_args[0] == 'labels':
          args.__setattr__(
              command_args[0],
              {
                  'migrated-from': 'app-engine',
                  'migration-tool': 'gcloud-app-migrate-standard-v1',
              },
          )
          continue
        if command_args[0] == 'image':
          setattr(args, command_args[0], command_args[1])
          continue
        if command_args[0] == 'set_env_vars':
          args.__setattr__(command_args[0], self.ParseSetEnvVars(command_str))
          continue
        if command_args[0] == 'timeout':
          if command_args[1] == '600':
            args.__setattr__(command_args[0], 600)
          elif command_args[1] == '3600':
            args.__setattr__(command_args[0], 3600)
          continue
        if command_args[0] == 'min_instances':
          args.__setattr__(command_args[0], flags.ScaleValue(command_args[1]))
          continue
        if command_args[0] == 'max_instances':
          args.__setattr__(command_args[0], flags.ScaleValue(command_args[1]))
          continue
        if command_args[0] == 'scaling':
          args.__setattr__(command_args[0], flags.ScalingValue(command_args[1]))
          continue
        if len(command_args) > 1:
          args.__setattr__(command_args[0], command_args[1])
        else:
          args.__setattr__(command_args[0], True)
    return

  def PrintMigrationSummary(self, args):
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

  def ParseSetEnvVars(
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

  @override
  def _ValidateAndGeDeployFromSource(self, containers: Any) -> dict[Any, Any]:
    if hasattr(self, '_migration_flags') and 'image' in self._migration_flags:
      # If an image is provided, we are not deploying from source, so we return
      # an empty dict to skip source deployment validation.
      return {}
    return super()._ValidateAndGeDeployFromSource(containers)
