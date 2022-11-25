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
"""Policy Controller feature status command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import utils
from googlecloudsdk.core import properties
import six


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class Status(base.DescribeCommand):
  """Display the runtime status of the Policy Controller feature.

  ## EXAMPLES

  To display the runtime status of the Policy Controller feature:

      $ {command}
  """
  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'The membership names for which to display the Policy Controller '
            'runtime status.'))

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()
    project_id = properties.VALUES.core.project.Get(required=True)
    feature = self.GetFeature()

    status_client = status_api_utils.GetClientInstance(
        self.ReleaseTrack())
    status_messages = status_api_utils.GetMessagesModule(
        self.ReleaseTrack())

    status = {}

    if args.memberships is not None:
      memberships_filter = args.memberships
    else:
      memberships_filter = None

    memberships = status_api_utils.ListMemberships(status_client,
                                                   status_messages, project_id)
    for membership in memberships:
      if memberships_filter and membership.ref.name not in memberships_filter:
        continue

      status[membership.ref.name] = {
          'status': {}
      }
      if membership.runtimeStatus.numConstraintTemplates:
        status[membership.ref.name]['status'][
            'templates'] = membership.runtimeStatus.numConstraintTemplates
      else:
        status[membership.ref.name]['status']['templates'] = 0
      if membership.runtimeStatus.numConstraints:
        status[membership.ref.name]['status'][
            'constraints'] = membership.runtimeStatus.numConstraints
      else:
        status[membership.ref.name]['status']['constraints'] = 0
      if membership.runtimeStatus.numConstraintViolations:
        status[membership.ref.name]['status'][
            'violations'] = membership.runtimeStatus.numConstraintViolations
      else:
        status[membership.ref.name]['status']['violations'] = 0

    specs = client.HubClient.ToPyDict(feature.membershipSpecs)
    for membership, spec in specs.items():
      if memberships_filter and membership not in memberships_filter:
        continue

      if membership not in status:
        status[membership] = {
            'status': {
                'constraints': 0,
                'templates': 0,
                'violations': 0
            }
        }

      if spec.policycontroller.policyControllerHubConfig.installSpec == self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum(
          self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum
          .INSTALL_SPEC_ENABLED):
        version = spec.policycontroller.version
      else:
        version = utils.get_install_spec_label(six.text_type(
            spec.policycontroller.policyControllerHubConfig.installSpec))
      status[membership]['version'] = version

    return status
