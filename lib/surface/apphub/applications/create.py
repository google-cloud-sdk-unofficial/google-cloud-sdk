# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Create Command for Application."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import utils as api_lib_utils
from googlecloudsdk.api_lib.apphub.applications import client as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.apphub import flags


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To create the Application `my-app` with scope type `REGIONAL`
        in location `us-east1`, run:

          $ {command} my-app --location=us-east1 --scope-type=REGIONAL
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create an Apphub application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.CreateApplicationFlags(parser)

  def Run(self, args):
    """Run the create command."""
    client = apis.ApplicationsClient()
    app_ref = args.CONCEPTS.application.Parse()
    parent_ref = app_ref.Parent()
    if not parent_ref.Name():
      raise exceptions.InvalidArgumentException(
          'project', ' project id must be non-empty.'
      )

    attributes = api_lib_utils.GetMessagesModule().Attributes()

    if args.environment:
      attributes.environment = api_lib_utils.GetMessagesModule().Environment(
          environment=args.environment
      )

    if args.criticality:
      criticality = api_lib_utils.GetMessagesModule().Criticality()
      criticality.level = args.criticality.get('level')
      criticality.missionCritical = args.criticality.get('mission-critical')
      attributes.criticality = criticality

    for b_owner in args.business_owners or []:
      business_owner = api_lib_utils.GetMessagesModule().ContactInfo()
      business_owner.email = b_owner.get('email', None)
      if b_owner.get('display-name', None):
        business_owner.displayName = b_owner.get('display-name', None)
      if b_owner.get('channel-uri', None):
        business_owner.channel = api_lib_utils.GetMessagesModule().Channel(
            uri=b_owner.get('channel-uri')
        )
      attributes.businessOwners.append(business_owner)

    for d_owner in args.developer_owners or []:
      developer_owner = api_lib_utils.GetMessagesModule().ContactInfo()
      developer_owner.email = d_owner.get('email', None)
      if d_owner.get('display-name', None):
        developer_owner.displayName = d_owner.get('display-name', None)
      if d_owner.get('channel-uri', None):
        developer_owner.channel = api_lib_utils.GetMessagesModule().Channel(
            uri=d_owner.get('channel-uri')
        )
      attributes.developerOwners.append(developer_owner)

    for o_owner in args.operator_owners or []:
      operator_owner = api_lib_utils.GetMessagesModule().ContactInfo()
      operator_owner.email = o_owner.get('email', None)
      if o_owner.get('display-name'):
        operator_owner.displayName = o_owner.get('display-name')
      if o_owner.get('channel-uri'):
        operator_owner.channel = api_lib_utils.GetMessagesModule().Channel(
            uri=o_owner.get('channel-uri')
        )
      attributes.operatorOwners.append(operator_owner)

    return client.Create(
        app_id=app_ref.Name(),
        scope_type=args.scope_type,
        display_name=args.display_name,
        description=args.description,
        attributes=attributes,
        async_flag=args.async_,
        parent=parent_ref.RelativeName(),
    )
