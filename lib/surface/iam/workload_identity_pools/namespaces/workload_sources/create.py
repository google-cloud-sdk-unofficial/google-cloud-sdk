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
"""Command to create a workload source under a workload identity pool namespace."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.api_lib.iam.workload_identity_pools import workload_sources
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.iam.workload_identity_pools import flags
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log


class CreateGcp(base.CreateCommand):
  """Create a workload identity pool namespace workload source for a hosted source."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command creates a workload identity pool namespace
          workload source in the default project with the ID projects/123.

            $ {command} projects/123 --location="global" \\
            --workload-identity-pool="my-workload-identity-pool" \\
            --namespace="my-namespace" \\
            --resoures="resource-1","resource-2"
          """,
  }

  @staticmethod
  def Args(parser):
    workload_source_data = yaml_data.ResourceYAMLData.FromPath(
        'iam.workload_identity_pool_namespace_workload_source'
    )
    concept_parsers.ConceptParser.ForResource(
        'workload_source',
        concepts.ResourceSpec.FromYaml(
            workload_source_data.GetData(), is_positional=True
        ),
        'The workload identity pool namespace workload source to create.',
        required=True,
    ).AddToParser(parser)
    # Flags for creating workload source
    flags.AddGcpWorkloadSourceFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    self.CheckArgs(args)

    client, messages = util.GetClientAndMessages()
    workload_source_ref = args.CONCEPTS.workload_source.Parse()

    lro_ref = self.CreateWorkloadSource(
        args, client, messages, workload_source_ref
    )

    if args.async_:
      return lro_ref

    result = self.WaitForCreateWorkloadSourceOperation(
        client, lro_ref, workload_source_ref
    )

    return result

  def CheckArgs(self, args):
    if not args.resources and not args.attached_service_accounts:
      raise gcloud_exceptions.OneOfArgumentsRequiredException(
          ['--resources', '--attached_service_accounts'],
          'Must provide at least one attribute when gcp-source is specified.',
      )

  def CreateWorkloadSource(self, args, client, messages, workload_source_ref):
    lro_ref = workload_sources.CreateGcpWorkloadSource(
        client=client,
        messages=messages,
        workload_source_id=workload_source_ref.workloadSourcesId,
        resources=args.resources,
        attached_service_accounts=args.attached_service_accounts,
        parent=workload_source_ref.Parent().RelativeName(),
        for_managed_identity=False,
    )
    log.status.Print(
        'Create request issued for: [{}]'.format(
            workload_source_ref.workloadSourcesId
        )
    )

    return lro_ref

  def WaitForCreateWorkloadSourceOperation(
      self, client, lro_ref, workload_source_ref
  ):
    workload_source_result = workload_sources.WaitForWorkloadSourceOperation(
        client=client,
        lro_ref=lro_ref,
        for_managed_identity=False,
    )
    log.status.Print(
        'Created workload source [{}].'.format(
            workload_source_ref.workloadSourcesId
        )
    )

    return workload_source_result
