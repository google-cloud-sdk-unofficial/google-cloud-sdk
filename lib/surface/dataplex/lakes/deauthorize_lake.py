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
"""`gcloud dataplex lake deauthorize` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.dataplex import lake
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.projects import util as project_util


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeauthorizeLake(base.Command):
  """Deauthorize a lake from managing given resource."""

  detailed_help = {
      'EXAMPLES':
          """\
          To deauthorize a lake from managing a given resource, run:

            $ {command} de-authorize --namespace=my-namespace --location=us-east1 --project=testproject --{secondary-resource}={resource}

            Secondary-resource is defined as project-resource, bigquery-dataset-resource, or storage-bucket-resource.
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddLakeResourceArg(
        parser, 'to remove service agent IAM policy binding from.')
    data_group = parser.add_group(
        mutex=True, required=True, help='Container or Object to unbind p4sa')
    data_group.add_argument(
        '--storage-bucket-resource',
        help='The name of the Cloud Storage bucket to authorize the lake on.')
    data_group.add_argument(
        '--project-resource',
        help='The name of the project to authorize the lake on.')
    dataset_group = data_group.add_group(help='Dataset fields')
    dataset_group.add_argument(
        '--bigquery-dataset-resource',
        help='The name of the BigQuery dataset to authorize the lake on.')
    dataset_group.add_argument(
        '--secondary-project', help='Project Name of BigQuery dataset.')

  def Run(self, args):
    lake_ref = args.CONCEPTS.lake.Parse()
    service_account = 'service-' + str(
        project_util.GetProjectNumber(
            lake_ref.projectsId)) + '@gcp-sa-dataplex.iam.gserviceaccount.com'
    if args.IsSpecified('storage_bucket_resource'):
      return lake.RemoveServiceAccountFromBucketPolicy(
          storage_util.BucketReference(args.storage_bucket_resource),
          'serviceAccount:' + service_account, 'roles/dataplex.serviceAgent')
    if args.IsSpecified('bigquery_dataset_resource'):
      get_dataset_request = apis.GetMessagesModule(
          'bigquery', 'v2').BigqueryDatasetsGetRequest(
              datasetId=args.bigquery_dataset_resource,
              projectId=args.secondary_project)
      dataset = apis.GetClientInstance(
          'bigquery', 'v2').datasets.Get(request=get_dataset_request)
      lake.RemoveServiceAccountFromDatasetPolicy(dataset, service_account,
                                                 'roles/dataplex.serviceAgent')
      return apis.GetClientInstance('bigquery', 'v2').datasets.Patch(
          apis.GetMessagesModule('bigquery', 'v2').BigqueryDatasetsPatchRequest(
              datasetId=args.bigquery_dataset_resource,
              projectId=args.secondary_project,
              dataset=dataset))
    if args.IsSpecified('project_resource'):
      return projects_api.RemoveIamPolicyBinding(
          project_util.ParseProject(args.project_resource),
          'serviceAccount:' + service_account, 'roles/dataplex.serviceAgent')
