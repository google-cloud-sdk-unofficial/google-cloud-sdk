# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""The command to enable Config Management feature."""


import textwrap

import apitools
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.config_management import command
from googlecloudsdk.command_lib.container.fleet.config_management import flags
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base as features_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Enable(features_base.EnableCommand,
             features_base.UpdateCommand,
             command.Common):
  """Enable the Config Management feature.

  Enable the Config Management feature in a fleet.

  `{command}` without flags creates the Config Management feature or no-ops if
  the feature already exists.

  ## EXAMPLES

  To enable the Config Management feature, run:

    $ {command}
  """
  feature_name = utils.CONFIG_MANAGEMENT_FEATURE_NAME

  @classmethod
  def Args(cls, parser):
    v1_api_version = util.VERSION_MAP[cls.ReleaseTrack()]
    parser.add_argument(
        '--fleet-default-member-config',
        help=textwrap.dedent(
            f"""\
            Path to YAML file, or `-` to read from stdin, that specifies the
            [fleet-default membership configuration](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/manage-features)
            to create the feature with. Errors if the feature already exists.
            Accepts the same schema as the `MembershipSpec`
            [API field](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/reference/rpc/google.cloud.gkehub.configmanagement.{v1_api_version}#google.cloud.gkehub.configmanagement.{v1_api_version}.MembershipSpec).
            Provides the additional field-handling documented at
            https://docs.cloud.google.com/kubernetes-engine/config-sync/docs/reference/gcloud-configuration-field-behavior.
            Use the `update` command to update the fleet-default membership
            configuration or sync a membership to the fleet-default membership
            configuration.

            To create a Config Management feature with a fleet-default
            membership configuration and inform the process with logs, populate
            a `config.yaml` and run:

              $ {{command}} --fleet-default-member-config=config.yaml --verbosity=info

            To create a Config Management feature in the current project with
            the same fleet-default membership configuration as another project
            ``${{PROJECT_ID}}'', run:

              $ gcloud {cls.ReleaseTrack().prefix} container fleet config-management describe --view=fleet-default-member-config --project="${{PROJECT_ID}}" | {{command}} --fleet-default-member-config="-"

            Supports fleet-default membership configuration updates in
            the
            [apply spec schema](https://docs.cloud.google.com/kubernetes-engine/config-sync/docs/reference/gcloud-apply-fields)
            in YAML files for backward compatibility.
            """
        )
    )

  @api_lib_exceptions.CatchHTTPErrorRaiseHTTPException('{message}')
  def Run(self, args):
    feature = self.messages.Feature()
    # Empty string still counts as setting the flag.
    is_fleet_default = args.fleet_default_member_config is not None
    is_apply_spec = False
    if is_fleet_default:
      data = console_io.ReadFromFileOrStdin(args.fleet_default_member_config,
                                            binary=False)
      yaml_data = yaml.load(data)
      if not isinstance(yaml_data, dict):
        raise exceptions.Error(
            '--fleet-default-member-config'
            f' [{args.fleet_default_member_config}] is not a YAML mapping node.'
            ' See'
            ' https://docs.cloud.google.com/kubernetes-engine/config-sync/docs/reference/gcloud-configuration-field-behavior#example_configuration_files'
            ' for examples'
        )
      is_apply_spec = yaml_data.get('applySpecVersion')
      if is_apply_spec:
        log.info(
            "'applySpecVersion' field is present. Using old apply spec schema."
        )
        log.warning(
            'Consider using the new API schema instead of the apply spec schema'
            ' for the --fleet-default-member-config flag. See --help for how'
            ' the new API schema works with the describe command and the new'
            ' --fleet-default-member-config flag on the update command.'
        )
        cm_spec = self.parse_config_management(args.fleet_default_member_config)
      else:
        log.info(
            "'applySpecVersion' field is not present. Using new API schema."
        )
        cm_spec = flags.Parser(self).parse_config_data(
            data, is_fleet_default=True
        )
      feature.fleetDefaultMemberConfig = (
          self.messages.CommonFleetDefaultMemberConfigSpec(
              configmanagement=cm_spec
          )
      )
      if is_apply_spec:
        try:
          self.Update(['fleet_default_member_config'], feature)
          return
        except exceptions.Error as e:
          if str(e) != str(self.FeatureNotEnabledError()):
            raise
    try:
      self.Enable(feature, error_if_feature_exists=is_fleet_default)
    except apitools.base.py.exceptions.HttpConflictError as e:
      # --fleet-default-member-config must have been specified.
      parsed_e = api_lib_exceptions.HttpErrorPayload(e)
      if parsed_e.status_description == 'ALREADY_EXISTS':
        if is_apply_spec:
          e = exceptions.Error(
              f'another source has created the {self.feature.display_name} '
              'feature since the start of this command, re-run this command to'
              ' update the feature'
          )
        else:
          e = exceptions.Error(
              f'{self.feature.display_name} feature already exists, use the'
              ' --fleet-default-member-config flag on the update command'
              ' instead'
          )
      raise e
