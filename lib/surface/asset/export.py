# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Command to export assets to Google Cloud Storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags
from googlecloudsdk.command_lib.asset import utils as asset_utils
from googlecloudsdk.core import log


OPERATION_DESCRIBE_COMMAND = 'gcloud asset operations describe'


# pylint: disable=line-too-long
_DETAILED_HELP = {
    'DESCRIPTION':
        """\
      Export the cloud assets to Google Cloud Storage. Use gcloud asset operations
      describe to get the latest status of the operation. Note that to export a
      project different from the project you want to bill, you can either
      explicitly set the billing/quota_project property or authenticate with a service account.
      See https://cloud.google.com/resource-manager/docs/cloud-asset-inventory/gcloud-asset
      for examples of using a service account.
      """,
    'EXAMPLES':
        """\
      To export a snapshot of assets of type 'compute.googleapis.com/Disk' in
      project 'test-project' at '2019-03-05T00:00:00Z' to
      'gs://bucket-name/object-name' and only export the asset metadata, run:

        $ {command} --project='test-project' --asset-types='compute.googleapis.com/Disk' --snapshot-time='2019-03-05T00:00:00Z' --output-path='gs://bucket-name/object-name' --content-type='resource'
      """
}
# pylint: enable=line-too-long


def AddCommonExportFlags(parser):
  flags.AddParentArgs(parser)
  flags.AddSnapshotTimeArgs(parser)
  flags.AddAssetTypesArgs(parser)
  flags.AddContentTypeArgs(parser, required=False)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Export(base.Command):
  """Export the cloud assets to Google Cloud Storage.

  Doesn't support --output_path_prefix flag for export destination.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    AddCommonExportFlags(parser)
    # The GA release continues to only support --output_path while we roll out
    # --output_path_prefix through the Alpha and Beta releases.
    flags.AddOutputPathArgs(parser, required=True)

  def Run(self, args):
    parent = asset_utils.GetParentNameForExport(args.organization, args.project,
                                                args.folder)
    client = client_util.AssetExportClient(parent)
    operation = client.Export(args)

    log.ExportResource(parent, is_async=True, kind='root asset')
    log.status.Print('Use [{} {}] to check the status of the operation.'.format(
        OPERATION_DESCRIBE_COMMAND, operation.name))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ExportBeta(Export):
  """Export the cloud assets to Google Cloud Storage.

  Supports both --output_path and --output_path_prefix for export destination.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    AddCommonExportFlags(parser)
    # Supports both --output_path and --output_path_prefix flags for export
    # destination.
    flags.AddDestinationArgs(parser)
