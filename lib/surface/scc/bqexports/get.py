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

"""Command for getting a Cloud Security Command Center BigQuery export."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.command_lib.scc.bqexports import bqexport_util
from googlecloudsdk.command_lib.scc.bqexports import flags as bqexports_flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Get(base.DescribeCommand):
  """Get a Cloud Security Command Center BigQuery export."""

  detailed_help = {
      'DESCRIPTION': """\
      Get a Cloud Security Command Center BigQuery export.
      """,
      'EXAMPLES': """\
      To get a BigQuery export under given organization 123 with id my-bq-export,
      run:

        $ gcloud scc bqexports get my-bq-export \
            --organization=organizations/123
        $ gcloud scc bqexports get my-bq-export --organization=123
        $ gcloud scc bqexports get \
            organizations/123/bigQueryExports/bq-export

      To get a BigQuery export under given folder 456 with id my-bq-export, run:

        $ gcloud scc bqexports get my-bq-export --folder=folders/456
        $ gcloud scc bqexports get my-bq-export --folder=456
        $ gcloud scc bqexports get folders/456/bigQueryExports/my-bq-export

      To get a BigQuery export under given project 789 with id my-bq-export, run:

        $ gcloud scc bqexports get my-bq-export --project=projects/789
        $ gcloud scc bqexports get my-bq-export --project=789
        $ gcloud scc bqexports get projects/789/bigQueryExports/my-bq-export
      """,
      'API REFERENCE': """\
      This command uses the securitycenter/v1 API. The full documentation for
      this API can be found at: https://cloud.google.com/security-command-center
      """,
  }

  @staticmethod
  def Args(parser):
    bqexports_flags.AddBigQueryPositionalArgument(parser)
    bqexports_flags.AddParentGroup(parser)

    # TODO: b/311713896 - Remove api-version flag when v2 is fully GA.
    scc_flags.API_VERSION_FLAG.AddToParser(parser)
    scc_flags.LOCATION_FLAG.AddToParser(parser)

  def Run(self, args):

    # Determine what version to call from --location and --api-version. The
    # BigQueryExport is a version_specific_existing_resource that may not be
    # accessed through v2 if it currently exists in v1, and vice versa.
    version = scc_util.GetVersionFromArguments(
        args, args.BIG_QUERY_EXPORT, version_specific_existing_resource=True
    )
    messages = securitycenter_client.GetMessages(version)
    client = securitycenter_client.GetClient(version)

    if version == 'v1':
      req = messages.SecuritycenterOrganizationsBigQueryExportsGetRequest()
      req.name = bqexport_util.ValidateAndGetBigQueryExportV1Name(args)
      bq_export_response = client.organizations_bigQueryExports.Get(req)
    else:
      req = (
          messages.SecuritycenterOrganizationsLocationsBigQueryExportsGetRequest()
      )
      req.name = bqexport_util.ValidateAndGetBigQueryExportV2Name(args)
      bq_export_response = client.organizations_locations_bigQueryExports.Get(
          req
      )
    return bq_export_response
