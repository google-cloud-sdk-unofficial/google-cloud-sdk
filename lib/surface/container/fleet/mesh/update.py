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

from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.mesh import utils


def _RunUpdate(cmd, args):
  """Runs the update command implementation that is common across release tracks.

  Args:
    cmd: the release track specific command
    args: the args passed to the command
  """
  # Deprecated non-resource arg
  if args.IsKnownAndSpecified('membership'):
    resource = False
    memberships = utils.ParseMemberships(args)
  else:
    resource = True
    memberships = base.ParseMembershipsPlural(args, prompt=True, search=True)
  f = cmd.GetFeature()
  membership_specs = {}
  for membership in memberships:
    if not resource:
      membership = cmd.MembershipResourceName(membership)
    patch = cmd.messages.MembershipFeatureSpec()

    for name, spec in cmd.hubclient.ToPyDict(f.membershipSpecs).items():
      if util.MembershipShortname(name) == util.MembershipShortname(
          membership) and spec:
        patch = spec
    if not patch.mesh:
      patch.mesh = cmd.messages.ServiceMeshMembershipSpec()

    if hasattr(args, 'management') and args.management is not None:
      management = (
          cmd.messages.ServiceMeshMembershipSpec.ManagementValueValuesEnum(
              'MANAGEMENT_MANUAL'))
      if args.management == 'automatic':
        management = (
            cmd.messages.ServiceMeshMembershipSpec.ManagementValueValuesEnum(
                'MANAGEMENT_AUTOMATIC'))
      patch.mesh.management = management

    if args.control_plane is not None:
      control_plane = (
          cmd.messages.ServiceMeshMembershipSpec.ControlPlaneValueValuesEnum(
              'MANUAL'))
      if args.control_plane == 'automatic':
        control_plane = (
            cmd.messages.ServiceMeshMembershipSpec.ControlPlaneValueValuesEnum(
                'AUTOMATIC'))
      patch.mesh.controlPlane = control_plane

    membership_specs[membership] = patch

  f = cmd.messages.Feature(
      membershipSpecs=cmd.hubclient.ToMembershipSpecs(membership_specs))
  cmd.Update(['membershipSpecs'], f)


@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update the configuration of the Service Mesh Feature.

  Update the Service Mesh Feature Spec of a membership.

  ## EXAMPLES

  To update the control plane management of comma separated memberships like
  `MEMBERSHIP1,MEMBERSHIP2`, run:

    $ {command} --memberships=MEMBERSHIP1,MEMBERSHIP2
      --control-plane=CONTROL_PLANE
  """

  feature_name = 'servicemesh'

  @staticmethod
  def Args(parser):
    group = parser.add_mutually_exclusive_group()
    resources.AddMembershipResourceArg(
        group,
        plural=True,
        membership_help='Membership names to update, separated by commas if '
        'multiple are supplied.')
    group.add_argument(
        '--membership',
        type=str,
        help='Membership name to update.',
        action=actions.DeprecationAction(
            '--membership',
            warn='The {flag_name} flag is now '
            'deprecated. Please use `--memberships` '
            'instead.'))
    group = parser.add_argument_group(required=True)
    group.add_argument(
        '--management',
        choices=['automatic', 'manual'],
        help='The management mode to update to.')
    group.add_argument(
        '--control-plane',
        choices=['automatic', 'manual'],
        help='The control plane management to update to.',
        action=actions.DeprecationAction(
            '--control-plane',
            warn='The {flag_name} flag is now '
            'deprecated. Please use `--management` '
            'instead. '
            'See https://cloud.google.com/service-mesh/docs/managed/provision-managed-anthos-service-mesh'))

  def Run(self, args):
    _RunUpdate(self, args)


@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.GA)
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
    resources.AddMembershipResourceArg(
        group,
        plural=True,
        membership_help=('Membership names to update, separated by commas if '
                         'multiple are supplied.'),
    )
    group = parser.add_argument_group(required=True)
    group.add_argument(
        '--management',
        choices=['automatic', 'manual'],
        help='The management mode to update to.')
    group.add_argument(
        '--control-plane',
        choices=['automatic', 'manual'],
        help='Control plane management to update to.',
        action=actions.DeprecationAction(
            '--control-plane',
            warn='The {flag_name} flag is now '
            'deprecated. Please use `--management` '
            'instead. '
            'See https://cloud.google.com/service-mesh/docs/managed/provision-managed-anthos-service-mesh'))

  def Run(self, args):
    _RunUpdate(self, args)
