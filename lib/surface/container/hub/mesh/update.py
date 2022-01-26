# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io


@gbase.ReleaseTracks(gbase.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update the configuration of the Service Mesh Feature.

  Update the Service Mesh Feature Spec of a Membership.

  ## EXAMPLES

  To update the control plane management of a Membership named MEMBERSHIP, run:

    $ {command} --membership=MEMBERSHIP
      --control-plane=CONTROL_PLANE
  """

  feature_name = 'servicemesh'

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--membership',
        type=str,
        help='The Membership name to update.',
    )
    parser.add_argument(
        '--control-plane',
        choices=['automatic', 'manual'],
        help='The control plane management to update to.',
        required=True
    )

  def Run(self, args):
    memberships = base.ListMemberships()
    if not memberships:
      raise exceptions.Error('No Memberships available in the Fleet.')
    membership = args.membership
    if not membership:
      if console_io.CanPrompt():
        index = console_io.PromptChoice(
            options=memberships,
            message='Please specify a Membership:\n',
            cancel_option=True)
        membership = memberships[index]
      else:
        raise calliope_exceptions.RequiredArgumentException(
            '--membership',
            ('Cannot prompt a console for membership. Membership is required. '
             'Please specify `--membership` to select a membership.'))
    else:
      if membership not in memberships:
        raise exceptions.Error(
            'Membership {} does not exist in the Fleet.'.format(membership))
    membership = self.MembershipResourceName(membership)

    f = self.GetFeature()
    patch = self.messages.MembershipFeatureSpec()

    for name, spec in self.hubclient.ToPyDict(f.membershipSpecs).items():
      if name == membership and spec:
        patch = spec
    if not patch.mesh:
      patch.mesh = self.messages.ServiceMeshMembershipSpec()

    control_plane = (
        self.messages.ServiceMeshMembershipSpec.ControlPlaneValueValuesEnum(
            'MANUAL'))
    if args.control_plane == 'automatic':
      control_plane = (
          self.messages.ServiceMeshMembershipSpec.ControlPlaneValueValuesEnum(
              'AUTOMATIC'))
    patch.mesh.controlPlane = control_plane

    f = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs({membership: patch}))
    self.Update(['membershipSpecs'], f)
