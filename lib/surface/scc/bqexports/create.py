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

"""Command for creating a Cloud Security Command Center BigQuery export."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client as sc_client
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import util
from googlecloudsdk.command_lib.scc.bqexports import bqexport_util
from googlecloudsdk.command_lib.scc.bqexports import flags as bqexports_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Cloud Security Command Center BigQuery export."""

  detailed_help = {
      'DESCRIPTION': """\
      Create a Cloud Security Command Center BigQuery export.
      """,
      'EXAMPLES': """\
      To create a BigQuery export my-bq-export given organization 123 with a
      dataset abc in project 234 and filter on category that equals to
      XSS_SCRIPTING, run:

        $ gcloud scc bqexports create my-bq-export \
          --organization=organizations/123 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""
        $ gcloud scc bqexports create my-bq-export --organization=123 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""
        $ gcloud scc bqexports create \
          organizations/123/bigQueryExports/my-bq-export \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""

      To create a BigQuery export my-bq-export given folder 456 with a dataset
      abc in project 234 and filter on category that equals to XSS_SCRIPTING,
      run:

        $ gcloud scc bqexports create my-bq-export --folder=folders/456 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""
        $ gcloud scc bqexports create my-bq-export --folder=456 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""
        $ gcloud scc bqexports create \
          folders/456/bigQueryExports/my-bq-export \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""

      To create a BigQuery export my-bq-export given project 789 with a dataset
      abc in project 234 and filter on category that equals to XSS_SCRIPTING,
      run:

        $ gcloud scc bqexports create my-bq-export --project=projects/789 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""
        $ gcloud scc bqexports create my-bq-export --project=789 \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""
        $ gcloud scc bqexports create \
          projects/789/bigQueryExports/my-bq-export \
          --dataset=projects/234/datasets/abc \
          --description="This is a test BigQuery export" \
          --filter="category=\\"XSS_SCRIPTING\\""

      """,
      'API REFERENCE': """\
      This command uses the securitycenter/v1 API. The full documentation for
      this API can be found at: https://cloud.google.com/security-command-center
      """,
  }

  @staticmethod
  def Args(parser):
    bqexports_flags.DATASET_FLAG_REQUIRED.AddToParser(parser)
    bqexports_flags.DESCRIPTION_FLAG.AddToParser(parser)
    bqexports_flags.FILTER_FLAG.AddToParser(parser)

    bqexports_flags.AddBigQueryPositionalArgument(parser)
    bqexports_flags.AddParentGroup(parser)

    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    req = (
        securitycenter_v1_messages.SecuritycenterOrganizationsBigQueryExportsCreateRequest()
    )

    # Validate and compose the BigQuery Export Name.
    parent = util.GetParentFromNamedArguments(args)
    if parent is not None:
      req.bigQueryExportId = bqexport_util.ValidateAndGetBigQueryExportId(args)
      req.parent = parent
    else:
      bq_export_name = (
          bqexport_util.ValidateAndGetBigQueryExportFullResourceName(args)
      )
      req.bigQueryExportId = _GetBigQueryExportIdFromFullResourceName(
          bq_export_name
      )
      bqparent = _GetParentFromFullResourceName(bq_export_name)
      req.parent = bqparent

    messages = sc_client.GetMessages('v1')
    req.googleCloudSecuritycenterV1BigQueryExport = (
        messages.GoogleCloudSecuritycenterV1BigQueryExport()
    )
    req.googleCloudSecuritycenterV1BigQueryExport.dataset = args.dataset
    req.googleCloudSecuritycenterV1BigQueryExport.description = args.description
    req.googleCloudSecuritycenterV1BigQueryExport.filter = args.filter

    # Set the args' filter to None to avoid downstream naming conflicts.
    args.filter = None

    client = apis.GetClientInstance('securitycenter', 'v1')
    bq_export_response = client.organizations_bigQueryExports.Create(req)
    log.status.Print('Created.')
    return bq_export_response


def _GetBigQueryExportIdFromFullResourceName(bq_export_name):
  """Gets BigQuery export id from the full resource name."""
  bq_export_components = bq_export_name.split('/')
  return bq_export_components[len(bq_export_components) - 1]


def _GetParentFromFullResourceName(bq_export_name):
  """Gets parent from the full resource name."""
  bq_export_components = bq_export_name.split('/')
  return bq_export_components[0] + '/' + bq_export_components[1]
