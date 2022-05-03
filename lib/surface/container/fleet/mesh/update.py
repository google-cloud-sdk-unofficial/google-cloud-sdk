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
"""The command to update Service Mesh Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.mesh import utils


def _RunUpdate(cmd, args):
  """Runs the update command implementation that is common across release tracks.

  Args:
    cmd: the release track specific command
    args: the args passed to the command
  """
  memberships = utils.ParseMemberships(args)
  f = cmd.GetFeature()
  membership_specs = {}
  for membership in memberships:
    membership = cmd.MembershipResourceName(membership)
    patch = cmd.messages.MembershipFeatureSpec()

    for name, spec in cmd.hubclient.ToPyDict(f.membershipSpecs).items():
      if name == membership and spec:
        patch = spec
    if not patch.mesh:
      patch.mesh = cmd.messages.ServiceMeshMembershipSpec()

    control_plane = (
        cmd.messages.ServiceMeshMembershipSpec.ControlPlaneValueValuesEnum(
            'MANUAL'))
    if args.control_plane == 'automatic':
      control_plane = (
          cmd.messages.ServiceMeshMembershipSpec
          .ControlPlaneValueValuesEnum('AUTOMATIC'))
    patch.mesh.controlPlane = control_plane
    membership_specs[membership] = patch

  f = cmd.messages.Feature(
      membershipSpecs=cmd.hubclient.ToMembershipSpecs(membership_specs))
  cmd.Update(['membershipSpecs'], f)


@gbase.ReleaseTracks(gbase.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update the configuration of the Service Mesh Feature.

  Update the Service Mesh Feature Spec of a Membership.

  ## EXAMPLES

  To update the control plane management of comma separated Memberships like
  `membership1,membership2`, run:

    $ {command} --memberships=membership1,membership2
      --control-plane=CONTROL_PLANE
  """

  feature_name = 'servicemesh'

  @staticmethod
  def Args(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--memberships',
        type=str,
        help='Membership names to update, separated by commas if multiple are supplied.',
    )
    group.add_argument(
        '--membership',
        type=str,
        help='Membership name to update.',
        action=actions.DeprecationAction(
            '--membership',
            warn='The {flag_name} flag is now '
            'deprecated. Please use `--memberships` '
            'instead.'))
    parser.add_argument(
        '--control-plane',
        choices=['automatic', 'manual'],
        help='The control plane management to update to.',
        required=True
    )

  def Run(self, args):
    _RunUpdate(self, args)


@gbase.ReleaseTracks(gbase.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  """Update the configuration of the Service Mesh Feature.

  Update the Service Mesh Feature Spec of a Membership.

  ## EXAMPLES

  To update the control plane management of comma separated Memberships like
  `membership1,membership2`, run:

    $ {command} --memberships=membership1,membership2
      --control-plane=CONTROL_PLANE
  """

  feature_name = 'servicemesh'

  @staticmethod
  def Args(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--memberships',
        type=str,
        help='Membership names to update, separated by commas if multiple are supplied.',
    )
    parser.add_argument(
        '--control-plane',
        choices=['automatic', 'manual'],
        help='Control plane management to update to.',
        required=True
    )

  def Run(self, args):
    _RunUpdate(self, args)
