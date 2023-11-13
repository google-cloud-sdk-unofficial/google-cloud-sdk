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

"""Command for deleting a Cloud Security Command Center BigQuery export."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.bqexports import bqexport_util
from googlecloudsdk.command_lib.scc.bqexports import flags as bqexport_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Cloud Security Command Center BigQuery export."""

  detailed_help = {
      'DESCRIPTION': """\
      Delete a Cloud Security Command Center BigQuery export.
      """,
      'EXAMPLES': """\
      To delete a BigQuery export given organization 123 with id my-bq-export,
      run:

        $ gcloud scc bqexports delete my-bq-export \
          --organization=organizations/123
        $ gcloud scc bqexports delete my-bq-export --organization=123
        $ gcloud scc bqexports delete \
          organizations/123/bigQueryExports/my-bq-export

      To delete a BigQuery export given folder 456 with id my-bq-export, run:

        $ gcloud scc bqexports delete my-bq-export --folder=folders/456
        $ gcloud scc bqexports delete my-bq-export --folder=456
        $ gcloud scc bqexports delete \
          folders/456/bigQueryExports/my-bq-export

      To delete a BigQuery export given project 789 with id my-bq-export, run:

        $ gcloud scc bqexports delete my-bq-export --project=projects/789
        $ gcloud scc bqexports delete my-bq-export --project=789
        $ gcloud scc bqexports delete \
          projects/789/bigQueryExports/my-bq-export

      """,
      'API REFERENCE': """\
      This command uses the securitycenter/v1 API. The full documentation for
      this API can be found at: https://cloud.google.com/security-command-center
      """,
  }

  @staticmethod
  def Args(parser):
    bqexport_flags.AddBigQueryPositionalArgument(parser)
    bqexport_flags.AddParentGroup(parser)

  def Run(self, args):
    req = (
        securitycenter_v1_messages.SecuritycenterOrganizationsBigQueryExportsDeleteRequest()
    )

    # Prompt user to confirm deletion.
    console_io.PromptContinue(
        message='Are you sure you want to delete a BigQuery export?\n',
        cancel_on_no=True,
    )

    # Compose and validate after prompt.
    parent = scc_util.GetParentFromNamedArguments(args)
    if parent is not None:
      bq_export_id = bqexport_util.ValidateAndGetBigQueryExportId(args)
      req.name = parent + '/bigQueryExports/' + bq_export_id
    else:
      bq_export_name = (
          bqexport_util.ValidateAndGetBigQueryExportFullResourceName(args)
      )
      req.name = bq_export_name

    client = apis.GetClientInstance('securitycenter', 'v1')
    empty_bq_response = client.organizations_bigQueryExports.Delete(req)
    log.status.Print('Deleted.')
    return empty_bq_response
