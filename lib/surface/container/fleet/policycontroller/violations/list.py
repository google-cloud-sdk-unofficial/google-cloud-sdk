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
"""List violations command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from surface.container.fleet.policycontroller.violations import list_membership_violations


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class List(calliope_base.ListCommand):
  """List Policy Controller audit violations.

  ## EXAMPLES

  To list all Policy Controller audit violations across the Fleet:

      $ {command}
  """

  @staticmethod
  def Args(parser):
    calliope_base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Include error message with violations.',
        default=False)
    parser.add_argument(
        '--group-by',
        type=str,
        help='If set, returns violations grouped by a common attribute. Options: constraint, membership',
        default=''
    )

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()

    if args.group_by not in ['constraint', 'membership', '']:
      raise exceptions.Error(
          'Invalid group-by parameter "{}"'.format(args.group_by))
    project_id = properties.VALUES.core.project.Get(required=True)

    client = status_api_utils.GetClientInstance(
        self.ReleaseTrack())
    messages = status_api_utils.GetMessagesModule(
        self.ReleaseTrack())

    return list_membership_violations(
        messages=messages,
        client=client,
        project_id=project_id,
        verbose=args.verbose,
        group_by=args.group_by,
        constraint_filter=None)
