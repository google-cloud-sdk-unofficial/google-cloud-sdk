# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""List endpoint group associations command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.intercept_endpoint_group_associations import api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security.intercept import endpoint_group_association_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          List intercept endpoint group associations.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To list intercept endpoint group associations in project `my-project` and location `global`, run:

            $ {command} --project=my-project --location=global

            OR

            $ {command} --location=global

            OR

            $ {command} --location=projects/my-project/locations/global
        """,
}

_FORMAT = """\
table(
    name.scope("interceptEndpointGroupAssociations"):label=ID,
    name.scope("locations").segment(0):label=LOCATION,
    state
)
"""


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Intercept Endpoint Group Associations."""

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(
        endpoint_group_association_flags.MakeGetUriFunc(cls.ReleaseTrack())
    )
    endpoint_group_association_flags.AddLocationResourceArg(
        parser, help_text='The location for a list operation'
    )

  def Run(self, args):
    client = api.Client(self.ReleaseTrack())

    parent_ref = args.CONCEPTS.location.Parse()

    return client.ListEndpointGroupAssociations(
        parent_ref.RelativeName(), page_size=args.page_size
    )


List.detailed_help = DETAILED_HELP
