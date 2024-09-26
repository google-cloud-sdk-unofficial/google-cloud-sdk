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
"""Command for remediating a Cloud Security Command Center Finding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from typing import Any

from googlecloudsdk.api_lib.scc.iac_remediation import findings
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.iac_remediation import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
@base.UniverseCompatible
class Create(base.CreateCommand):
  """Remediates a Security Command Center finding."""

  detailed_help = {
      "DESCRIPTION": "Remediates a Security Command Center finding.",
      "EXAMPLES": """
          Sample usage:

          $ {{command}} iac-remediation create --finding-org-id=123456789
          --finding-name=projects/123456789/sources/123456789/locations/global/findings/123456789
          --tfstate-file-paths-list=/path/to/file1.tfstate,/path/to/file2.tfstate --llm-proj-id=my-proj""",
  }

  @staticmethod
  def Args(parser):
    flags.FINDING_ORG_ID_FLAG.AddToParser(parser)
    flags.FINDING_NAME_FLAG.AddToParser(parser)
    flags.LLM_PROJ_ID_FLAG.AddToParser(parser)
    flags.TFSTATE_FILE_PATHS_LIST_FLAG.AddToParser(parser)

  def Run(self, args: Any) -> None:
    """Remediates a Security Command Center finding.

    Args:
      args: Arguments for the command.
    """
    resp = findings.MakeApiCall(args.finding_org_id, args.finding_name)
    print(resp)
