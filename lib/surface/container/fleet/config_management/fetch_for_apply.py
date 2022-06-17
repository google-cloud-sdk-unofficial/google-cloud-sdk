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
"""The command to describe the status of the Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import semver


@gbase.ReleaseTracks(gbase.ReleaseTrack.ALPHA)
class Fetch(base.DescribeCommand):
  """Prints the Config Management configuration applied to the given membership.

  The output is in the format that is used by the apply subcommand. The fields
  that have not been configured will be shown with default values.

  ## EXAMPLES

  To fetch the applied Config Management configuration, run:

    $ {command}

  """

  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help='The Membership name provided during registration.',
    )

  def Run(self, args):
    # Get Hub memberships (cluster registered with fleet) from GCP Project.
    memberships = base.ListMemberships()
    if not memberships:
      raise exceptions.Error('No Memberships available in the fleet.')
    # User should choose an existing membership if not provide one
    membership = None
    if args.membership is None:
      index = console_io.PromptChoice(
          options=memberships,
          message='Please specify a membership to fetch the config:\n')
      membership = memberships[index]
    else:
      membership = args.membership
      if membership not in memberships:
        raise exceptions.Error(
            'Membership {} is not in the fleet.'.format(membership))

    f = self.GetFeature()
    version = utils.get_backfill_version_from_feature(f, membership)
    membership_spec = None
    for full_name, spec in self.hubclient.ToPyDict(f.membershipSpecs).items():
      if util.MembershipShortname(full_name) == membership and spec is not None:
        membership_spec = spec.configmanagement

    if membership_spec is None:
      log.status.Print('Membership {} not initialized'.format(membership))

    # load the config template and merge with config has been applied to the
    # feature spec
    template = yaml.load(utils.APPLY_SPEC_VERSION_1)
    full_config = template['spec']
    merge_config_sync(membership_spec, full_config, version)
    merge_policy_controller(membership_spec, full_config, version)
    merge_hierarchy_controller(membership_spec, full_config)

    return template


def merge_config_sync(spec, config, version):
  """Merge configSync set in feature spec with the config template.

  ConfigSync has nested object structs need to be flatten.

  Args:
    spec: the ConfigManagementMembershipSpec message
    config: the dict loaded from full config template
    version: the version string of the membership
  """
  if not spec or not spec.configSync:
    return
  git = spec.configSync.git
  cs = config[utils.CONFIG_SYNC]
  if spec.configSync.enabled is not None:
    cs['enabled'] = spec.configSync.enabled
  else:
    # when enabled is no set in feature spec, it's determined by syncRepo
    if spec.configSync.git and git.syncRepo:
      cs['enabled'] = True
  if (not version or
      semver.SemVer(version) >= semver.SemVer(utils.PREVENT_DRIFT_VERSION)):
    if spec.configSync.preventDrift:
      cs['preventDrift'] = spec.configSync.preventDrift
  else:
    del cs['preventDrift']
  if spec.configSync.sourceFormat:
    cs['sourceFormat'] = spec.configSync.sourceFormat
  if not git:
    return
  if git.syncWaitSecs:
    cs['syncWait'] = git.syncWaitSecs
  for field in [
      'policyDir', 'httpsProxy', 'secretType', 'syncBranch', 'syncRepo',
      'syncRev', 'gcpServiceAccountEmail'
  ]:
    if hasattr(git, field) and getattr(git, field) is not None:
      cs[field] = getattr(git, field)


def merge_policy_controller(spec, config, version):
  """Merge configSync set in feature spec with the config template.

  ConfigSync has nested object structs need to be flatten.

  Args:
    spec: the ConfigManagementMembershipSpec message
    config: the dict loaded from full config template
    version: the version string of the membership
  """
  if not spec or not spec.policyController:
    return
  c = config[utils.POLICY_CONTROLLER]
  for field in list(config[utils.POLICY_CONTROLLER]):
    if hasattr(spec.policyController, field) and getattr(
        spec.policyController, field) is not None:
      c[field] = getattr(spec.policyController, field)

  valid_version = not version or semver.SemVer(version) >= semver.SemVer(
      utils.MONITORING_VERSION)
  spec_monitoring = spec.policyController.monitoring
  if not valid_version:
    c.pop('monitoring', None)
  elif spec_monitoring:
    c['monitoring'] = spec_monitoring


def merge_hierarchy_controller(spec, config):
  if not spec or not spec.hierarchyController:
    return
  c = config[utils.HNC]
  for field in list(config[utils.HNC]):
    if hasattr(spec.hierarchyController, field) and getattr(
        spec.hierarchyController, field) is not None:
      c[field] = getattr(spec.hierarchyController, field)
