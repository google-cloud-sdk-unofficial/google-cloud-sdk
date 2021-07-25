# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.container.hub import util
from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.hub.config_management import utils
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io


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
    # Get Hub memberships (cluster registered with Hub) from GCP Project.
    memberships = base.ListMemberships()
    if not memberships:
      raise exceptions.Error('No Memberships available in Hub.')
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
            'Membership {} is not in Hub.'.format(membership))

    f = self.GetFeature()
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
    merge_config_sync(membership_spec, full_config)
    merge_non_cs_components(membership_spec, full_config)

    return template


def merge_config_sync(spec, config):
  """Merge configSync set in feature spec with the config template.

  ConfigSync has nested object structs need to be flatten.

  Args:
    spec: the ConfigManagementMembershipSpec message
    config: the dict loaded from full config template
  """
  if not spec or not spec.configSync:
    return
  git = spec.configSync.git
  if not spec.configSync.git or not git.syncRepo:
    return
  cs = config[utils.CONFIG_SYNC]
  cs['enabled'] = True
  if spec.configSync.sourceFormat:
    cs['sourceFormat'] = spec.configSync.sourceFormat
  if git.syncWaitSecs:
    cs['syncWait'] = git.syncWaitSecs
  for field in [
      'policyDir', 'httpsProxy', 'secretType', 'syncBranch', 'syncRepo',
      'syncRev', 'gcpServiceAccountEmail'
  ]:
    if hasattr(git, field) and getattr(git, field) is not None:
      cs[field] = getattr(git, field)


def merge_non_cs_components(spec, config):
  for components in [utils.POLICY_CONTROLLER, utils.HNC]:
    if not spec or not getattr(spec, components):
      continue
    c = config[components]
    for field in list(config[components]):
      if hasattr(getattr(spec, components), field) and getattr(
          getattr(spec, components), field) is not None:
        c[field] = getattr(getattr(spec, components), field)
