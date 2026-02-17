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
"""List command to list security profile groups."""

from googlecloudsdk.api_lib.network_security.security_profile_groups import spg_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import spg_flags

_DETAILED_HELP = {
    'DESCRIPTION': """

          List all Security Profile Groups in the specified location.

        """,
    'EXAMPLES': """
          To list Security Profile Groups in specifed location, run:

              $ {command} --location=global

        """,
}

_FORMAT = """\
table(
    name.basename():label=NAME
)
"""

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class ListProfileGroup(base.ListCommand):
  """List Security Profile Groups."""

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(spg_flags.MakeGetUriFunc(cls.ReleaseTrack()))
    spg_flags.AddLocationResourceArg(
        parser=parser,
        help_text='Parent resource for the list operation.',
        required=True,
        project_scope_supported=project_scope_supported,
    )

  def Run(self, args):
    result = args.CONCEPTS.location.Parse()
    parent_ref = result.result

    project_scoped = (
        result.concept_type.name
        == spg_flags.PROJECT_LOCATION_RESOURCE_COLLECTION
    )
    client = spg_api.Client(self.ReleaseTrack(), project_scoped)

    return client.ListSecurityProfileGroups(
        parent_ref.RelativeName(), page_size=args.page_size
    )


ListProfileGroup.detailed_help = _DETAILED_HELP
