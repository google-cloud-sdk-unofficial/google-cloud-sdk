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
"""Describe endpoint group association command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.intercept_endpoint_group_associations import api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security.intercept import endpoint_group_association_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          Describe an intercept endpoint group association.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To get a description of an intercept endpoint group association called `my-association` in
            project `my-project` and location `global`, run:

            $ {command} my-association --project=my-project --location=global

            OR

            $ {command} projects/my-project/locations/global/interceptEndpointGroupAssociations/my-association
        """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe an Intercept Endpoint Group Association."""

  @classmethod
  def Args(cls, parser):
    endpoint_group_association_flags.AddEndpointGroupAssociationResource(
        cls.ReleaseTrack(), parser
    )

  def Run(self, args):
    client = api.Client(self.ReleaseTrack())

    association = args.CONCEPTS.intercept_endpoint_group_association.Parse()

    return client.DescribeEndpointGroupAssociation(association.RelativeName())


Describe.detailed_help = DETAILED_HELP
