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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

import apitools
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
import six


# TODO(b/468375060) : Add beta track to alpha class and delete this beta class.
@base.ReleaseTracks(base.ReleaseTrack.BETA)
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
  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--fleet-default-member-config',
        help=('Path to YAML file that contains the [fleet-default membership'
              ' configuration]('
              'https://cloud.google.com/kubernetes-engine/fleet-management/docs'
              '/manage-features) to enable with a new feature.'
              ' This file shares the syntax of the `--config` flag on the'
              ' `apply` command: see recognized fields [here]('
              'https://docs.cloud.google.com/kubernetes-engine/config-sync/docs/reference/gcloud-apply-fields).'
              ' Errors if the Policy Controller or Hierarchy Controller field'
              ' is set.'
              ' This flag will also enable or update the fleet-default'
              ' membership configuration on an existing feature.'
              ' See the `apply` command for how to sync a membership to the'
              ' fleet-default membership configuration.')
    )

  def Run(self, args):
    try:
      _ = self.enable_feature_with_fdc(args)
    except apitools.base.py.exceptions.HttpError as e:
      # Do not show stack trace to user.
      raise api_lib_exceptions.HttpException(e, error_format='{message}')

  def enable_feature_with_fdc(self, args):
    """Enable feature and fleet-default membership configuration, if specified.

    Args:
      args: Command arguments.
    Returns:
      Enabled or updated GKE Hub Feature.
    """
    feature = self.messages.Feature()
    # Empty string still counts as setting the flag.
    if args.fleet_default_member_config is not None:
      spec = self.parse_config_management(args.fleet_default_member_config)
      feature.fleetDefaultMemberConfig = (
          self.messages.CommonFleetDefaultMemberConfigSpec(
              configmanagement=spec
          )
      )
      try:
        return self.Update(['fleet_default_member_config'], feature)
      except exceptions.Error as e:
        if six.text_type(e) != six.text_type(self.FeatureNotEnabledError()):
          raise
    return self.Enable(feature)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EnableAlpha(features_base.EnableCommand,
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
    parser.add_argument(
        '--fleet-default-member-config',
        help=textwrap.dedent(
            f"""\
            Path to YAML file, or `-` to read from stdin, that specifies the
            [fleet-default membership configuration](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/manage-features)
            to create the feature with. Errors if the feature already exists.
            Accepts the same schema as the `MembershipSpec`
            [API field](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/reference/rpc/google.cloud.gkehub.configmanagement.v1alpha#google.cloud.gkehub.configmanagement.v1alpha.MembershipSpec).
            Provides the additional field-handling documented at
            https://docs.cloud.google.com/kubernetes-engine/config-sync/docs/reference/gcloud-configuration-field-behavior.
            Use the `update` command to update the fleet-default membership
            configuration or sync a membership to the fleet-default membership
            configuration.

            To create a Config Management feature with a fleet-default
            membership configuration from a file and debug logs, populate a
            `config.yaml` and run:

              $ {{command}} --fleet-default-member-config=config.yaml --verbosity=debug

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
    if args.fleet_default_member_config is not None:
      data = console_io.ReadFromFileOrStdin(args.fleet_default_member_config,
                                            binary=False)
      yaml_data = yaml.load(data)
      if not isinstance(yaml_data, dict):
        raise exceptions.Error(
            '--fleet-default-member-config'
            f' [{args.fleet_default_member_config}] is not a YAML mapping node.'
            ' See --help for examples'
        )
      is_apply_spec = yaml_data.get('applySpecVersion')
      if is_apply_spec:
        log.debug(
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
        log.debug(
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
          if six.text_type(e) != six.text_type(self.FeatureNotEnabledError()):
            raise
    self.Enable(
        feature,
        error_if_feature_exists=args.fleet_default_member_config is not None,
    )
