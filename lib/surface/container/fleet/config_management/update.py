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

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.config_management import flags
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base as features_base
from googlecloudsdk.command_lib.container.fleet.features import flags as feature_flags
from googlecloudsdk.command_lib.container.fleet.membershipfeatures import base as mf_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(mf_base.UpdateCommand, features_base.UpdateCommand):
  """Update the Config Management feature."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          {description}

          `{command}` replaces the `apply` and `upgrade` commands for feature
          updates. The `update` command streamlines partial configuration
          changes by accepting the `describe` command output as input. In
          addition to the plural `--memberships` and `--all-memberships` flags,
          the command also supports a `--version` flag dedicated to upgrades
          that operates independently of the `--config` flag. This command
          errors if the feature does not exist."""),
      # TODO: b/435530306 - Use GA describe command in example instead.
      'EXAMPLES': textwrap.dedent(
          """\
          To update only the Config Sync sync directory on an existing
          membership configuration, run:

            $ gcloud alpha container fleet config-management describe --view=config --memberships=example-membership-1 > config.yaml

            $ sed -i "s/policyDir: foo/policyDir: bar/g" config.yaml

            $ {command} --config=config.yaml --memberships=example-membership-1

          To update the Config Sync version for all memberships to
          ``${VERSION}'', run:

            $ {command} --version="${VERSION}" --all-memberships

          To update the [fleet-default membership configuration](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/manage-features)
          and sync select membership configurations to it, run:

            $ {command} --fleet-default-member-config=config.yaml

            $ {command} --origin=fleet --memberships=example-membership-1,example-membership-2"""
      ),
  }
  mf_name = utils.CONFIG_MANAGEMENT_FEATURE_NAME
  feature_name = utils.CONFIG_MANAGEMENT_FEATURE_NAME

  @classmethod
  def Args(cls, parser):
    all_flags_group = parser.add_group(
        required=True,
        mutex=True,
    )
    v1_api_version = util.VERSION_MAP[cls.ReleaseTrack()]
    all_flags_group.add_argument(
        '--fleet-default-member-config',
        # TODO: b/435530306 - Use GA describe command in example instead.
        help=textwrap.dedent(
            f"""\
            Path to YAML file, or `-` to read from stdin, that specifies the
            [fleet-default membership configuration](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/manage-features)
            to update the feature to. Accepts the same schema as the
            `MembershipSpec`
            [API field](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/reference/rpc/google.cloud.gkehub.configmanagement.{v1_api_version}#google.cloud.gkehub.configmanagement.{v1_api_version}.MembershipSpec).
            Provides the additional field-handling documented at
            https://docs.cloud.google.com/kubernetes-engine/config-sync/docs/reference/gcloud-configuration-field-behavior.

            To update only the Config Sync sync directory on the existing
            fleet-default membership configuration, run:

              $ gcloud alpha container fleet config-management describe --view=fleet-default-member-config > config.yaml

              $ sed -i "s/policyDir: foo/policyDir: bar/g" config.yaml

              $ {{command}} --fleet-default-member-config=config.yaml

            To achieve the same result in a single invocation, run:

              $ gcloud alpha container fleet config-management describe --view=fleet-default-member-config | sed "s/policyDir: foo/policyDir: bar/g" | {{command}} --fleet-default-member-config="-\""""
        ),
    )
    membership_specific_group = all_flags_group.add_group()
    configuration_group = membership_specific_group.add_group(
        required=True,
        mutex=True,
        help=(
            '`MEMBERSHIP CONFIGURATION FLAGS`. Updates membership'
            ' configuration(s), but does not wait for the resulting on-cluster'
            ' changes to complete.'
        ),
    )
    cls.ORIGIN_FLAG.AddToParser(configuration_group)
    v2_api_version = util.V2_VERSION_MAP[cls.ReleaseTrack()]
    # TODO: b/435530306 - Use GA describe command in example instead.
    configuration_group.add_argument(
        '--config',
        help=textwrap.dedent(
            f"""\
            Path to YAML file, or `-` to read from stdin, that specifies the
            configuration to update the target membership(s) to. Accepts the
            same schema as the `Spec`
            [API field](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/reference/rpc/google.cloud.gkehub.configmanagement.{v2_api_version}#google.cloud.gkehub.configmanagement.{v2_api_version}.Spec).
            Provides the additional field-handling documented at
            https://docs.cloud.google.com/kubernetes-engine/config-sync/docs/reference/gcloud-configuration-field-behavior.

            To update the entire configuration for select memberships to that
            specified in a `config.yaml`, run:

              $ {{command}} --config=path/to/config.yaml --memberships=example-membership-1,example-membership-2

            To update only the Config Sync sync directory on an existing
            membership configuration in a single invocation, making sure to
            first inspect the existing membership configuration, run:

              $ gcloud alpha container fleet config-management describe --view=config --memberships=example-membership-1

              $ gcloud alpha container fleet config-management describe --view=config --memberships=example-membership-1 | sed "s/policyDir: foo/policyDir: bar/g" | {{command}} --config="-" --memberships=example-membership-1"""
        ),
    )
    # This group is to distinguish the functional difference between the
    # --version flag and the --config, --origin flags. It also moves the
    # per-field explanation out of the --version help text and makes room for
    # future per-field flags.
    per_field_group = configuration_group.add_group(help=textwrap.dedent(f"""\
            `PER-FIELD FLAGS`. Updates a single field and preserves all other
            existing configuration fields for target membership(s). Use the
            `--config` flag to update other configuration fields.

            Warns if the `configSync` field is not enabled. Only if the
            `configSync` field is enabled according to the `configSync.enabled`
            [field description](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/reference/rpc/google.cloud.gkehub.configmanagement.{v2_api_version}#google.cloud.gkehub.configmanagement.{v2_api_version}.ConfigSync)
            does the feature install and manage Config Sync based on the
            membership configuration field values. Use `--verbosity=error` to
            suppress the warning.
            """))
    per_field_group.add_argument(
        '--version',
        help=textwrap.dedent(f"""\
            Version of Config Sync to update the target membership
            configuration(s) to. Upgrades Config Sync if the `configSync` field
            is enabled, and logs a warning otherwise. See the `PER-FIELD FLAGS`
            section above for details.
            To bypass the upgrade confirmation prompt, use `--quiet`.
            Find supported versions and the default version behavior in the
            `version`
            [field description](https://docs.cloud.google.com/kubernetes-engine/fleet-management/docs/reference/rpc/google.cloud.gkehub.configmanagement.{v2_api_version}#spec).

            To upgrade all memberships to the latest version, unless the
            `configSync` field is not enabled for any membership, for which the
            flag will log a warning, run:

              $ {{command}} --version="" --all-memberships
            """),
    )
    memberships_group = membership_specific_group.add_mutually_exclusive_group()
    resources.AddMembershipResourceArg(memberships_group, plural=True)
    feature_flags.ALL_MEMBERSHIPS_FLAG.AddToParser(memberships_group)

  @api_lib_exceptions.CatchHTTPErrorRaiseHTTPException('{message}')
  def Run(self, args):
    flag_parser = flags.Parser(self)
    # Empty string counts as specifying the --fleet-default-member-config flag.
    if args.fleet_default_member_config is not None:
      self.Update(
          ['fleet_default_member_config'],
          self.messages.Feature(
              fleetDefaultMemberConfig=(
                  self.messages.CommonFleetDefaultMemberConfigSpec(
                      configmanagement=flag_parser.parse_config(
                          args.fleet_default_member_config,
                          is_fleet_default=True,
                      )
                  )
              )
          ),
      )
      return
    # Do not auto-select. --version needs to search because it prompts users
    # about Config Sync versions on Memberships.
    memberships = features_base.ParseMembershipsPlural(
        args,
        prompt=True,
        search=args.version is not None,
    )
    if args.origin:
      self.sync_memberships_to_fleet_default(memberships)
      return
    # Feature must exist to reconcile v2 configuration changes.
    feature = self.GetFeature()
    if args.config is not None:
      cm_spec = flag_parser.parse_config(args.config, is_fleet_default=False)
      cm_specs_to_update = [copy.deepcopy(cm_spec) for _ in memberships]
      # Backfill even if user mapped version to empty string to avoid edge case
      # behavior and because version preservation is much safer. Backfill will
      # return the empty string anyway if user is starting clean. Users with
      # existing installations should always explicitly specify a version
      # change, including to the latest version.
      if not cm_spec.version:
        versions = utils.get_backfill_versions_from_feature(
            feature,
            memberships,
        )
        for per_membership_cm_spec, v in zip(cm_specs_to_update, versions):
          per_membership_cm_spec.version = v
      for m, per_membership_cm_spec in zip(memberships, cm_specs_to_update):
        self._update_membership_feature(m, per_membership_cm_spec)
      return
    # --version must be set.
    _, installed_versions = utils.extract_membership_versions_from_feature(
        feature, memberships
    )
    for m, installed_v in zip(memberships, installed_versions):
      existing_cm_spec = self._cm_spec_for_membership(m)
      new_cm_spec = copy.deepcopy(existing_cm_spec)
      new_cm_spec.version = args.version
      if not self._is_config_sync_enabled(new_cm_spec):
        log.warning(
            "'configSync' field is not enabled. Configuration fields are not"
            ' managing Config Sync on membership [%s]. See --help for details.',
            m,
        )
      # Move under "if args.version" when other per-field flags are introduced.
      self._prompt_for_version_confirmation(
          m, existing_cm_spec, new_cm_spec, installed_v
      )
      self._update_membership_feature(m, new_cm_spec)

  def _update_membership_feature(self, membership: str, cm_spec):
    try:
      return self.UpdateV2(
          membership_path=membership,
          mask=['spec'],
          patch=self.messages_v2.MembershipFeature(
              spec=self.messages_v2.FeatureSpec(
                  configmanagement=cm_spec,
              ),
          ),
      )
    except apitools_exceptions.HttpNotFoundError as e:
      # TODO: b/431859521 - Remove this extra handling once Membership does
      # not exist error message is more readable. UpdateV2 creates
      # MembershipFeature if it does not exist, so NOT FOUND must mean
      # Membership does not exist.
      readable_e = api_lib_exceptions.HttpException(e, '{message}')
      # Do not use 'from readable_e' because readable_e won't display.
      raise exceptions.Error(
          f'membership [{membership}] not found: {readable_e}'
      )

  def _cm_spec_for_membership(self, membership: str):
    # CLH will error if cm_spec remains this default value because configSync
    # is not configured. Do not error here to not duplicate the CLH behavior,
    # which is also subject to change. The existing behavior is also preferred
    # if future per-field flags are introduced that populate the configSync
    # field.
    cm_spec = self.messages_v2.ConfigManagementSpec()
    try:
      mf = self.GetMembershipFeature(membership)
      if mf.spec and mf.spec.configmanagement:
        cm_spec = mf.spec.configmanagement
    except apitools_exceptions.HttpNotFoundError:
      pass
    return cm_spec

  def _prompt_for_version_confirmation(
      self, membership: str, existing_spec, new_spec, installed_version: str
  ):
    """Prompts for --version change confirmation.

    Should only be called when the --version flag is set and after all other
    flags update new_spec. Skips prompt if --version does not change the
    existing version or the configSync field is not enabled.

    Args:
      membership: Membership whose spec is being updated with --version.
      existing_spec: Existing spec for Membership. Version field may be None if
        unset.
      new_spec: Spec to update to with change from --version and all other
        flags.
      installed_version: Installed version in Membership state. May be empty
        string.
    """
    skip_prompt_msg = None
    # If --version="". defer to configSync enabled check, since empty string may
    # default to latest version if configSync enabled in same command call.
    if existing_spec.version == new_spec.version and new_spec.version:
      # Do not skip API call just because version flag specifies the existing
      # value. In the event of future per-field flags, we'd have to check the
      # entire spec for equality and handle edge cases. CLH may also introduce
      # side effects. We want minimize logic here.
      skip_prompt_msg = (
          f"--version='{new_spec.version}' is equivalent to the existing"
          f' configured version for membership [{membership}].'
      )
    elif not self._is_config_sync_enabled(new_spec):
      skip_prompt_msg = (
          "The 'version' field is not managing Config Sync because the"
          f" 'configSync' field is not enabled for membership [{membership}]."
          ' See --help for details.'
      )
    if skip_prompt_msg:
      if not properties.VALUES.core.disable_prompts.GetBool():
        log.status.Print(
            f'Skipping --version confirmation prompt. {skip_prompt_msg}'
        )
      return
    if installed_version:
      # Note that installed version could be same as intended version.
      installed_version_msg = (
          f"The feature state detects version '{installed_version}' on this"
          ' cluster.'
      )
    else:
      # Cannot rely on lack of installed version to indicate lack of
      # Config Sync installation and skip prompt as a result because the spec
      # may have been empty or state updates may lag. This matters even more if
      # we introduce per-field flags --git or --oci that can enable the
      # configSync field.
      installed_version_msg = (
          'The feature state has yet to detect Config Sync on this cluster.'
      )
    version_msg = (
        'the latest version'
        if not new_spec.version
        else f"'{new_spec.version}'"
    )
    console_io.PromptContinue(
        message=(
            f'About to upgrade Config Sync to {version_msg} for membership'
            f' [{membership}]. {installed_version_msg}'
            ' This command will not block on upgrade completion.'
        ),
        # Declarative. Entire operation either succeeds or fails.
        cancel_on_no=True,
    )

  def _is_config_sync_enabled(self, cm_spec) -> bool:
    # Hopefully, we can avoid replicating the CLH logic in the future if, say,
    # the CLH backfills the enabled field based on git or oci presence.
    if not cm_spec.configSync:
      return False
    if cm_spec.configSync.enabled is not None:
      return cm_spec.configSync.enabled
    is_git_configured = (
        cm_spec.configSync.git is not None
        and cm_spec.configSync.git
        != self.messages_v2.ConfigManagementGitConfig()
    )
    is_oci_configured = (
        cm_spec.configSync.oci is not None
        and cm_spec.configSync.oci
        != self.messages_v2.ConfigManagementOciConfig()
    )
    return is_git_configured or is_oci_configured
