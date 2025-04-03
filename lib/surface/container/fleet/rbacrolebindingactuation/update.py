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
"""The command to update the RbacRoleBinding Actuation Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.features import base as feature_base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Update(feature_base.UpdateCommand):
  r"""Update RbacRoleBinding Actuation Feature.

  This command updates RbacRoleBinding Actuation Feature in a fleet.

  ## EXAMPLES

  To update the RbacRoleBinding Actuation Feature, run:

    $ gcloud container fleet rbacrolebinding-actuation update \
        --allowed-custom-roles=role1,role2
  """

  feature_name = 'rbacrolebindingactuation'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--allowed-custom-roles',
        required=True,
        type=arg_parsers.ArgList(min_length=1),
        metavar='ROLES',
        help=textwrap.dedent("""\
          The list of allowed custom roles that can be used in scope
          RBACRoleBindings.
          """),
    )

  def Run(self, args):
    feature = self.messages.Feature(
        spec=self.messages.CommonFeatureSpec(
            rbacrolebindingactuation=self.messages.RBACRoleBindingActuationFeatureSpec(
                allowedCustomRoles=args.allowed_custom_roles,
            ),
        )
    )

    self.Update(
        ['spec.rbacrolebindingactuation.allowed_custom_roles'],
        feature,
    )
