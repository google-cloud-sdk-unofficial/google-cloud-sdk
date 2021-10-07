# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex asset create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.dataplex import asset
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataplex import flags
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Creating an Asset."""

  detailed_help = {
      'EXAMPLES':
          """\
          To create a Dataplex Asset, run:

            $ {command} projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id}/assets/{asset_id}
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddAssetResourceArg(parser, 'to create an Asset to.')
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the create action, but don\'t actually perform it.')
    parser.add_argument('--description', help='Description of the Asset')
    parser.add_argument('--display-name', help='Display Name of the Asset')
    resource_spec = parser.add_group(
        required=True,
        help='Specification of the resource that is referenced by this asset.')
    resource_creation_spec = resource_spec.add_group(
        required=True,
        help='Configurations for Creating/Attaching a resource to the asset. One field must be specified.'
    )
    resource_creation_spec.add_argument(
        '--resource-name',
        help=""""Relative name of the cloud resource that contains the data that
                 is being managed within a lake. For example:
                 projects/{project_number}/buckets/{bucket_id} projects/{project_number}/datasets/{dataset_id}"""
    )
    resource_creation_spec.add_argument(
        '--creation-policy',
        choices={
            'ATTACH_RESOURCE': 'attach resource',
            'CREATE_RESOURCE': 'create resource',
        },
        type=arg_utils.ChoiceToEnumName,
        default='ATTACH_RESOURCE',
        help="""If the creation policy indicates ATTACH behavior, then an
                existing resource must be provided. If the policy indicates
                CREATE behavior, new resource will be created with the given
                name.However if it is empty, nthen the resource will be created
                using {asset_id}-{UUID} template for name. The location of the
                referenced resource must always match that of the asset.""")
    resource_spec.add_argument(
        '--resource-type',
        required=True,
        choices={
            'STORAGE_BUCKET': 'Cloud Storage Bucket',
            'BIGQUERY_DATASET': 'BigQuery Dataset',
        },
        type=arg_utils.ChoiceToEnumName,
        help='Type')

    resource_spec.add_argument(
        '--deletion-policy',
        required=False,
        choices={
            'DETACH_RESOURCE': 'detach resource',
            'DELETE_RESOURCE': 'delete resource',
        },
        type=arg_utils.ChoiceToEnumName,
        help='Deletion policy of the attached resource.')
    flags.AddDiscoveryArgs(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    asset_ref = args.CONCEPTS.asset.Parse()
    dataplex_client = dataplex_util.GetClientInstance()

    # Checks to see if the resource_name exist.
    try:
      operation_detail = None
      if args.IsSpecified('resource_name'):
        resource_path = args.resource_name.split('/')
        if args.resource_type == 'BIGQUERY_DATASET':
          apis.GetClientInstance('bigquery', 'v2').datasets.Get(
              operation_detail=apis.GetMessagesModule('bigquery', 'v2')
              .BigqueryDatasetsGetRequest(
                  datasetId=resource_path[-1], projectId=asset_ref.projectsId))
        elif args.resource_type == 'STORAGE_BUCKET':
          operation_detail = storage_api.StorageClient().GetBucket(
              resource_path[-1])
      if args.creation_policy == 'CREATE_RESOURCE' and operation_detail is not None:
        raise exceptions.BadArgumentException(
            '--resource-name', 'Resource argument already exist.')
    except (apitools_exceptions.HttpError,
            storage_api.BucketNotFoundError) as error:
      if args.creation_policy == 'ATTACH_RESOURCE':
        if error.__class__ == storage_api.BucketNotFoundError or error.status_code == 404:
          raise exceptions.BadArgumentException(
              '--resource-name',
              'Resource: [' + resource_path[-1] + '] does not exist.')
        raise error

    create_req_op = dataplex_client.projects_locations_lakes_zones_assets.Create(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesZonesAssetsCreateRequest(
            assetId=asset_ref.Name(),
            parent=asset_ref.Parent().RelativeName(),
            validateOnly=args.validate_only,
            googleCloudDataplexV1Asset=asset.GenerateAssetForCreateRequest(
                args)))
    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete with errors:')
      return create_req_op

    async_ = getattr(args, 'async_', False)
    if not async_:
      return asset.WaitForOperation(create_req_op)
    return create_req_op
