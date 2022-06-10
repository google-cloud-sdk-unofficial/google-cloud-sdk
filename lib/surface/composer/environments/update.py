# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command that updates scalar properties of an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import environment_patch_util as patch_util
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import image_versions_util as image_versions_command_util
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util

DETAILED_HELP = {
    'EXAMPLES':
        """\
          To update the Cloud Composer environment named ``env-1'' to have 8
          Airflow workers, and not have the ``production'' label, run:

            $ {command} env-1 --node-count=8 --remove-labels=production
        """
}

_INVALID_OPTION_FOR_V2_ERROR_MSG = """\
Cannot specify --{opt} with Composer 2.X or greater.
"""

_INVALID_OPTION_FOR_V1_ERROR_MSG = """\
Cannot specify --{opt} with Composer 1.X.
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update properties of a Cloud Composer environment."""

  detailed_help = DETAILED_HELP
  _support_autoscaling = True
  _support_maintenance_window = False
  _support_environment_size = True
  _support_airflow_database_retention = False

  @staticmethod
  def Args(parser, release_track=base.ReleaseTrack.GA):
    resource_args.AddEnvironmentResourceArg(parser, 'to update')
    base.ASYNC_FLAG.AddToParser(parser)

    Update.update_type_group = parser.add_mutually_exclusive_group(
        required=True, help='The update type.')
    flags.AddNodeCountUpdateFlagToGroup(Update.update_type_group)
    flags.AddPypiUpdateFlagsToGroup(Update.update_type_group)
    flags.AddEnvVariableUpdateFlagsToGroup(Update.update_type_group)
    flags.AddAirflowConfigUpdateFlagsToGroup(Update.update_type_group)
    flags.AddLabelsUpdateFlagsToGroup(Update.update_type_group)
    web_server_group = Update.update_type_group.add_mutually_exclusive_group()
    flags.UPDATE_WEB_SERVER_ALLOW_IP.AddToParser(web_server_group)
    flags.WEB_SERVER_ALLOW_ALL.AddToParser(web_server_group)
    flags.WEB_SERVER_DENY_ALL.AddToParser(web_server_group)

    flags.CLOUD_SQL_MACHINE_TYPE.AddToParser(Update.update_type_group)
    flags.WEB_SERVER_MACHINE_TYPE.AddToParser(Update.update_type_group)

    flags.AddAutoscalingUpdateFlagsToGroup(Update.update_type_group,
                                           release_track)
    flags.AddMasterAuthorizedNetworksUpdateFlagsToGroup(
        Update.update_type_group)
    if release_track == base.ReleaseTrack.ALPHA:
      flags.AIRFLOW_DATABASE_RETENTION_DAYS.AddToParser(
          Update.update_type_group.add_argument_group(hidden=True))

  def _ConstructPatch(self, env_ref, args, support_environment_upgrades=False):
    env_obj = environments_api_util.Get(
        env_ref, release_track=self.ReleaseTrack())
    is_composer_v1 = image_versions_command_util.IsImageVersionStringComposerV1(
        env_obj.config.softwareConfig.imageVersion)

    params = dict(
        is_composer_v1=is_composer_v1,
        env_ref=env_ref,
        node_count=args.node_count,
        update_pypi_packages_from_file=args.update_pypi_packages_from_file,
        clear_pypi_packages=args.clear_pypi_packages,
        remove_pypi_packages=args.remove_pypi_packages,
        update_pypi_packages=dict(
            command_util.SplitRequirementSpecifier(r)
            for r in args.update_pypi_package),
        clear_labels=args.clear_labels,
        remove_labels=args.remove_labels,
        update_labels=args.update_labels,
        clear_airflow_configs=args.clear_airflow_configs,
        remove_airflow_configs=args.remove_airflow_configs,
        update_airflow_configs=args.update_airflow_configs,
        clear_env_variables=args.clear_env_variables,
        remove_env_variables=args.remove_env_variables,
        update_env_variables=args.update_env_variables,
        release_track=self.ReleaseTrack())

    if support_environment_upgrades:
      params['update_image_version'] = args.image_version
    params['update_web_server_access_control'] = (
        environments_api_util.BuildWebServerAllowedIps(
            args.update_web_server_allow_ip, args.web_server_allow_all,
            args.web_server_deny_all))

    if (args.cloud_sql_machine_type and not is_composer_v1):
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(opt='cloud-sql-machine-type'))
    if (args.web_server_machine_type and not is_composer_v1):
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(
              opt='web-server-machine-type'))
    params['cloud_sql_machine_type'] = args.cloud_sql_machine_type
    params['web_server_machine_type'] = args.web_server_machine_type
    params['scheduler_count'] = args.scheduler_count

    if self._support_environment_size:
      if (args.environment_size and is_composer_v1):
        raise command_util.InvalidUserInputError(
            _INVALID_OPTION_FOR_V1_ERROR_MSG.format(opt='environment-size'))
      if self.ReleaseTrack() == base.ReleaseTrack.GA:
        params['environment_size'] = flags.ENVIRONMENT_SIZE_GA.GetEnumForChoice(
            args.environment_size)
      elif self.ReleaseTrack() == base.ReleaseTrack.BETA:
        params[
            'environment_size'] = flags.ENVIRONMENT_SIZE_BETA.GetEnumForChoice(
                args.environment_size)
      elif self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
        params[
            'environment_size'] = flags.ENVIRONMENT_SIZE_ALPHA.GetEnumForChoice(
                args.environment_size)
    if self._support_autoscaling:
      if (is_composer_v1 and
          (args.scheduler_cpu or args.worker_cpu or args.web_server_cpu or
           args.scheduler_memory or args.worker_memory or args.web_server_memory
           or args.scheduler_storage or args.worker_storage or
           args.web_server_storage or args.min_workers or args.max_workers)):
        raise command_util.InvalidUserInputError(
            'Workloads Config flags introduced in Composer 2.X'
            ' cannot be used when creating Composer 1.X environments.')
      params['scheduler_cpu'] = args.scheduler_cpu
      params['worker_cpu'] = args.worker_cpu
      params['web_server_cpu'] = args.web_server_cpu
      params['scheduler_memory_gb'] = environments_api_util.MemorySizeBytesToGB(
          args.scheduler_memory)
      params['worker_memory_gb'] = environments_api_util.MemorySizeBytesToGB(
          args.worker_memory)
      params[
          'web_server_memory_gb'] = environments_api_util.MemorySizeBytesToGB(
              args.web_server_memory)
      params[
          'scheduler_storage_gb'] = environments_api_util.MemorySizeBytesToGB(
              args.scheduler_storage)
      params['worker_storage_gb'] = environments_api_util.MemorySizeBytesToGB(
          args.worker_storage)
      params[
          'web_server_storage_gb'] = environments_api_util.MemorySizeBytesToGB(
              args.web_server_storage)
      params['min_workers'] = args.min_workers
      params['max_workers'] = args.max_workers
    if self._support_maintenance_window:
      params['maintenance_window_start'] = args.maintenance_window_start
      params['maintenance_window_end'] = args.maintenance_window_end
      params[
          'maintenance_window_recurrence'] = args.maintenance_window_recurrence
    if self._support_airflow_database_retention:
      params[
          'airflow_database_retention_days'] = args.airflow_database_retention_days
    if args.enable_master_authorized_networks and args.disable_master_authorized_networks:
      raise command_util.InvalidUserInputError(
          'Cannot specify --enable-master-authorized-networks with --disable-master-authorized-networks'
      )
    if args.disable_master_authorized_networks and args.master_authorized_networks:
      raise command_util.InvalidUserInputError(
          'Cannot specify --disable-master-authorized-networks with --master-authorized-networks'
      )
    if args.enable_master_authorized_networks is None and args.master_authorized_networks:
      raise command_util.InvalidUserInputError(
          'Cannot specify --master-authorized-networks without --enable-master-authorized-networks'
      )
    if args.enable_master_authorized_networks or args.disable_master_authorized_networks:
      params[
          'master_authorized_networks_enabled'] = True if args.enable_master_authorized_networks else False
    command_util.ValidateMasterAuthorizedNetworks(
        args.master_authorized_networks)
    params['master_authorized_networks'] = args.master_authorized_networks
    return patch_util.ConstructPatch(**params)

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()
    field_mask, patch = self._ConstructPatch(env_ref, args)
    return patch_util.Patch(
        env_ref,
        field_mask,
        patch,
        args.async_,
        release_track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update properties of a Cloud Composer environment."""

  _support_autoscaling = True
  _support_maintenance_window = True
  _support_environment_size = True

  @staticmethod
  def AlphaAndBetaArgs(parser, release_track=base.ReleaseTrack.BETA):
    """Arguments available only in both alpha and beta."""
    Update.Args(parser, release_track=release_track)

    # Environment upgrade arguments
    UpdateBeta.support_environment_upgrades = True
    flags.AddEnvUpgradeFlagsToGroup(Update.update_type_group)
    flags.AddMaintenanceWindowFlagsGroup(Update.update_type_group)

  @staticmethod
  def Args(parser):
    """Arguments available only in beta, not in alpha."""
    UpdateBeta.AlphaAndBetaArgs(parser, base.ReleaseTrack.BETA)

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()

    if args.airflow_version:
      # Converts airflow_version arg to image_version arg
      args.image_version = (
          image_versions_command_util.ImageVersionFromAirflowVersion(
              args.airflow_version))

    # Checks validity of image_version upgrade request.
    if (args.image_version and
        not image_versions_command_util.IsValidImageVersionUpgrade(
            env_ref, args.image_version, self.ReleaseTrack())):
      raise command_util.InvalidUserInputError(
          'Invalid environment upgrade. [Requested: {}]'.format(
              args.image_version))

    # Checks validity of update_web_server_allow_ip
    if (self.ReleaseTrack() == base.ReleaseTrack.BETA and
        args.update_web_server_allow_ip):
      flags.ValidateIpRanges(
          [acl['ip_range'] for acl in args.update_web_server_allow_ip])

    field_mask, patch = self._ConstructPatch(
        env_ref, args, UpdateBeta.support_environment_upgrades)

    return patch_util.Patch(
        env_ref,
        field_mask,
        patch,
        args.async_,
        release_track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update properties of a Cloud Composer environment."""

  _support_autoscaling = True
  _support_airflow_database_retention = True

  @staticmethod
  def Args(parser):
    UpdateBeta.AlphaAndBetaArgs(parser, base.ReleaseTrack.ALPHA)
