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
"""Export Security Profile."""


import sys

from googlecloudsdk.api_lib.network_security.security_profiles import sp_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.export import util
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

DETAILED_HELP = {
    'DESCRIPTION': """

          Export a Security Profile.

        """,
    'EXAMPLES': """
          To export a Security Profile, run:

              $ {command} my-security-profile --organization=1234 --location=global --destination=my-security-profile.yaml

        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Export(base.ExportCommand):
  """Export Security Profile."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    sp_flags.AddSecurityProfileResource(
        parser, cls.ReleaseTrack(), project_scope_supported
    )
    util.AddExportFlags(
        parser, sp_api.GetSchemaPath(cls.ReleaseTrack(), for_help=True))

  def Run(self, args):
    result = args.CONCEPTS.security_profile.Parse()
    security_profile = result.result

    project_scoped = (
        result.concept_type.name
        == sp_flags.PROJECT_SECURITY_PROFILE_RESOURCE_COLLECTION
    )
    client = sp_api.Client(self.ReleaseTrack(), project_scoped)

    sp = client.GetSecurityProfile(security_profile.RelativeName())
    yaml_data = yaml.load(util.Export(
        message=sp, schema_path=sp_api.GetSchemaPath(self.ReleaseTrack())
    ))

    if args.destination:
      with files.FileWriter(args.destination) as stream:
        yaml.dump(yaml_data, stream=stream)
      return log.status.Print(
          'Exported [{}] to \'{}\'.'.format(
              sp.name, args.destination
          )
      )
    else:
      yaml.dump(yaml_data, stream=sys.stdout)
