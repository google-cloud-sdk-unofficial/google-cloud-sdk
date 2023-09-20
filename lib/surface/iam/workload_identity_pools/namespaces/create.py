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
"""Command to create a new namespace under a workload identity pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.api_lib.iam.workload_identity_pools import workload_sources
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.iam import identity_pool_waiter
from googlecloudsdk.command_lib.iam.workload_identity_pools import flags
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class Create(base.CreateCommand):
  """Create a workload identity pool namespace."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command creates a workload identity pool namespace in
          the default project with the ID my-namespace.

            $ {command} my-namespace --location="global" \
            --workload-identity-pool="my-workload-identity-pool"

          The following command creates a workload identity pool namespace in
          the default project with the ID my-namespace, and then authorizes any
          workload in Google Cloud project `123` with the given service
          accounts attached to assume any identity within the namespace.

            $ {command} my-namespace --location="global" \
            --workload-identity-pool="my-workload-identity-pool" \
            --source="project-123" \
            --attached-service-accounts='foo@bar.iam.gserviceaccount.com', \
                                        'bar@foo.iam.gserviceaccount.com'
          """,
  }

  @staticmethod
  def Args(parser):
    namespace_data = yaml_data.ResourceYAMLData.FromPath(
        'iam.workload_identity_pool_namespace'
    )
    concept_parsers.ConceptParser.ForResource(
        'namespace',
        concepts.ResourceSpec.FromYaml(
            namespace_data.GetData(), is_positional=True
        ),
        'The workload identity pool namespace to create.',
        required=True,
    ).AddToParser(parser)
    parser.add_argument(
        '--description',
        help='A description of the namespace.',
    )
    parser.add_argument(
        '--disabled',
        action='store_true',
        help=(
            'Whether the namespace is disabled. If disabled, credentials may '
            'longer be issued for identities in this namespace. Existing '
            'credentials may continue to be accepted until they expire.'
        ),
    )
    base.ASYNC_FLAG.AddToParser(parser)
    # Flags for creating workload source
    parser.add_argument(
        '--source',
        help='The workload source to be created.',
    )
    flags.AddGcpWorkloadSourceFlags(parser)

  def Run(self, args):
    self.CheckWorkloadSourceArgs(args)

    client, messages = util.GetClientAndMessages()
    namespace_ref = args.CONCEPTS.namespace.Parse()

    namespace_lro_ref = self.CreateWorkloadIdentityPoolNamespace(
        args, client, messages, namespace_ref
    )

    if args.async_ and not args.source:
      return namespace_lro_ref

    namespace_result = self.WaitForCreateWorkloadIdentityPoolNamespaceOperation(
        client, namespace_lro_ref, namespace_ref
    )

    if not args.source:
      return namespace_result

    workload_source_lro_ref = self.CreateWorkloadSource(
        args, client, messages, namespace_ref
    )

    if args.async_:
      return namespace_lro_ref, workload_source_lro_ref

    workload_source_result = self.WaitForCreateWorkloadSourceOperation(
        args, client, workload_source_lro_ref
    )

    return namespace_result, workload_source_result

  def CheckWorkloadSourceArgs(self, args):
    if (
        args.source
        and not args.resources
        and not args.attached_service_accounts
    ):
      raise gcloud_exceptions.OneOfArgumentsRequiredException(
          ['--resources', '--attached-service-accounts'],
          'Must provide at least one attribute that will match workload(s) '
          'from the source.',
      )

    if (args.resources or args.attached_service_accounts) and not args.source:
      raise gcloud_exceptions.RequiredArgumentException(
          ['--source'],
          'Must provide a source of workloads to match the attributes on.',
      )

  def CreateWorkloadIdentityPoolNamespace(
      self, args, client, messages, namespace_ref
  ):
    new_namespace = messages.WorkloadIdentityPoolNamespace(
        description=args.description,
        disabled=args.disabled,
    )
    lro_ref = client.projects_locations_workloadIdentityPools_namespaces.Create(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesCreateRequest(
            parent=namespace_ref.Parent().RelativeName(),
            workloadIdentityPoolNamespaceId=namespace_ref.namespacesId,
            workloadIdentityPoolNamespace=new_namespace,
        )
    )
    log.status.Print(
        'Create request issued for: [{}]'.format(namespace_ref.namespacesId)
    )

    return lro_ref

  def WaitForCreateWorkloadIdentityPoolNamespaceOperation(
      self, client, lro_ref, namespace_ref
  ):
    lro_resource = resources.REGISTRY.ParseRelativeName(
        lro_ref.name,
        collection=(
            'iam.projects.locations.workloadIdentityPools.namespaces.operations'
        ),
    )
    namespace_result = waiter.WaitFor(
        identity_pool_waiter.IdentityPoolOperationPoller(
            client.projects_locations_workloadIdentityPools_namespaces,
            client.projects_locations_workloadIdentityPools_namespaces_operations,
        ),
        lro_resource,
        'Waiting for operation [{}] to complete'.format(lro_ref.name),
        # Wait for a maximum of 5 minutes, as the IAM replication has a lag of
        # up to 80 seconds.
        max_wait_ms=300000,
    )
    log.status.Print(
        'Created workload identity pool namespace [{}].'.format(
            namespace_ref.namespacesId
        )
    )

    return namespace_result

  def CreateWorkloadSource(self, args, client, messages, namespace_ref):
    workload_source_lro_ref = workload_sources.CreateGcpWorkloadSource(
        client=client,
        messages=messages,
        workload_source_id=args.source,
        resources=args.resources,
        attached_service_accounts=args.attached_service_accounts,
        parent=namespace_ref.RelativeName(),
        for_managed_identity=False,
    )
    log.status.Print('Create request issued for: [{}]'.format(args.source))

    return workload_source_lro_ref

  def WaitForCreateWorkloadSourceOperation(
      self, args, client, workload_source_lro_ref
  ):
    workload_source_result = workload_sources.WaitForWorkloadSourceOperation(
        client=client,
        lro_ref=workload_source_lro_ref,
        for_managed_identity=False,
    )
    log.status.Print('Created workload source [{}].'.format(args.source))

    return workload_source_result
