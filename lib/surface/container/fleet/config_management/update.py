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
"""The official command to update the Config Management Feature."""

import copy
import textwrap

from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.config_management import flags
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base as features_base
from googlecloudsdk.command_lib.container.fleet.features import flags as feature_flags
from googlecloudsdk.command_lib.container.fleet.membershipfeatures import base as mf_base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(mf_base.UpdateCommand, features_base.UpdateCommand):
  """Update the Config Management feature."""
  detailed_help = {
      # TODO(b/433355766): Update introduction of
      # update compared to apply command with new flags.
      'DESCRIPTION': textwrap.dedent(
          """\
          {description}

          `{command}` replaces the `apply` command. It accepts the `describe`
          command output as input to ease configuration updates and supports
          updates to multiple memberships. This command will gradually introduce
          all the `apply` command flags and graduate to `GA`."""
      ),
      # TODO(b/435530306): Use GA describe command in example instead.
      'EXAMPLES': textwrap.dedent(
          """\
          To update only the Config Sync sync directory on an existing
          membership configuration, run:

            $ gcloud alpha container fleet config-management describe
                --view=config --memberships=example-membership-1 > config.yaml

            $ sed -i "s/policyDir: foo/policyDir: bar/g" config.yaml

            $ {command} --config=config.yaml --memberships=example-membership-1"""
      ),
  }
  mf_name = utils.CONFIG_MANAGEMENT_FEATURE_NAME
  feature_name = utils.CONFIG_MANAGEMENT_FEATURE_NAME

  @classmethod
  def Args(cls, parser):
    all_flags_group = parser.add_group(
        required=True,
        mutex=True,
        # TODO(b/440401143): Add help text.
    )
    membership_specific_group = all_flags_group.add_group(
        # TODO(b/440401143): Add help text.
    )
    configuration_group = membership_specific_group.add_group(
        required=True,
        mutex=True,
        # TODO(b/440401143): Add help text. Can reference --source help text.
        # Explain .yaml files in error msg.
    )
    api_reference_by_release_track = {
        base.ReleaseTrack.ALPHA: (
            'https://cloud.google.com/kubernetes-engine/fleet-management/docs/reference/rpc/google.cloud.gkehub.configmanagement.v2alpha#google.cloud.gkehub.configmanagement.v2alpha.Spec'
        )
    }
    # TODO(b/435530306): Use GA describe command in example instead.
    configuration_group.add_argument(
        '--config',
        help=textwrap.dedent(
            f"""\
            Path to YAML file, or `-` to read from stdin, that specifies the
            configuration to update the target membership(s) to. Accepts the
            same schema as the `Spec`
            [API field]({api_reference_by_release_track[cls.ReleaseTrack()]}).
            Provides the additional field-handling documented in
            ["gcloud configuration field behavior"](https://cloud.google.com/kubernetes-engine/config-sync/docs/reference/gcloud-configuration-field-behavior).

            To update the entire configuration for select memberships to that
            specified in a `config.yaml`, run:

              $ {{command}} --config=path/to/config.yaml
                  --memberships=example-membership-1,example-membership-2

            To update only the Config Sync sync directory on an existing
            membership configuration in a single invocation, making sure to
            first inspect the existing membership configuration, run:

              $ gcloud alpha container fleet config-management describe --view=config --memberships=example-membership-1

              $ gcloud alpha container fleet config-management describe --view=config --memberships=example-membership-1 | sed "s/policyDir: foo/policyDir: bar/g" | {{command}} --config="-" --memberships=example-membership-1"""
        ),
    )
    memberships_group = membership_specific_group.add_mutually_exclusive_group()
    resources.AddMembershipResourceArg(memberships_group, plural=True)
    feature_flags.ALL_MEMBERSHIPS_FLAG.AddToParser(memberships_group)

  @exceptions.CatchHTTPErrorRaiseHTTPException('{message}')
  def Run(self, args):
    # Do not search or auto-select.
    memberships = features_base.ParseMembershipsPlural(args, prompt=True)
    # Feature must exist to reconcile configuration changes.
    feature = self.GetFeature()
    cm_spec = flags.Parser(self).parse_config(args.config)
    cm_specs_to_update = [copy.deepcopy(cm_spec) for _ in memberships]
    # Backfill even if user mapped version to empty string to avoid edge case
    # behavior and because version preservation is much safer. Backfill will
    # return the empty string anyway if user is starting clean. Users with
    # existing installations should always explicitly specify a version change,
    # including to the latest version.
    if not cm_spec.version:
      versions = utils.get_backfill_versions_from_feature(
          feature,
          memberships,
      )
      for per_membership_cm_spec, v in zip(cm_specs_to_update, versions):
        per_membership_cm_spec.version = v
    for m, per_membership_cm_spec in zip(memberships, cm_specs_to_update):
      self.UpdateV2(
          membership_path=m,
          mask=['spec'],
          patch=self.messages_v2.MembershipFeature(
              spec=self.messages_v2.FeatureSpec(
                  configmanagement=per_membership_cm_spec,
              ),
          )
      )
