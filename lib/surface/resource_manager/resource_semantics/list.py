# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""List Command for the Resource Manager - Resource Semantics CLI."""

import textwrap

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.Hidden
class List(base.Command):
  """Command for listing semantic meanings applicable to a resource."""

  detailed_help = {'EXAMPLES': textwrap.dedent("""\
        To list resource semantics for Project with name
        //cloudresourcemanager.googleapis.com/projects/1234 run: # gcloud-disable-gdu-domain

          $ {{command}} --parent=//cloudresourcemanager.googleapis.com/projects/1234 # gcloud-disable-gdu-domain

        To list resource semantics for Redis instance with name
        //redis.googleapis.com/projects/123/locations/asia-east1/instances/redis-instance # gcloud-disable-gdu-domain
        run:

          $ {{command}} --parent=//redis.googleapis.com/projects/123/locations/asia-east1/instances/redis-instance \\ # gcloud-disable-gdu-domain
              --location=asia-east1
      """)}

  @classmethod
  def Args(cls, parser):
    arguments.AddParentArgToParser(
        parser,
        message='Full resource name of the resource to get semantics for.',
    )
    arguments.AddLocationArgToParser(
        parser,
        'Region or zone of the resource. This '
        'field is not required if the resource is a global resource like '
        'projects, folders and organizations.',
    )

  def Run(self, args):
    del self  # Unused in Run.
    location = args.location if args.IsSpecified('location') else 'global'
    with endpoints.CrmEndpointOverrides(location):
      client = apis.GetClientInstance('cloudresourcemanager', 'v3')
      messages = client.MESSAGES_MODULE

      request = messages.CloudresourcemanagerFetchResourceSemanticsRequest(
          fullResourceName=args.parent
      )

      return client.v3.FetchResourceSemantics(request)
