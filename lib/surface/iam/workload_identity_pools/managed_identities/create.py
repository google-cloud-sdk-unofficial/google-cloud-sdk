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
  """Create a workload identity pool managed identity."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command creates a workload identity pool managed
          identity in the default project with the ID my-managed-identity.

            $ {command} my-managed-identity --location="global" \
            --namespace="my-namespace" \
            --workload-identity-pool="my-workload-identity-pool"

          The following command creates a workload identity pool managed
          identity in the default project with the ID `my-managed-identity`. The
          command also authorizes any workload in Google Cloud project `123`
          with the given service accounts attached to assume the identity.

            $ {command} my-managed-identity --location="global" \
            --namespace="my-namespace" \
            --workload-identity-pool="my-workload-identity-pool" \
            --source="project-123" \
            --attached-service-accounts='foo@bar.iam.gserviceaccount.com', \
                                        'bar@foo.iam.gserviceaccount.com'
          """,
  }

  @staticmethod
  def Args(parser):
    managed_identity_data = yaml_data.ResourceYAMLData.FromPath(
        'iam.workload_identity_pool_managed_identity'
    )
    # b/295594640: The help text for this command should include what the ID
    # represents and format constraints enforced. Figure out if it's possible
    # to add that information to this parser.
    concept_parsers.ConceptParser.ForResource(
        'managed_identity',
        concepts.ResourceSpec.FromYaml(
            managed_identity_data.GetData(), is_positional=True
        ),
        'The workload identity pool managed identity to create.',
        required=True,
    ).AddToParser(parser)
    parser.add_argument(
        '--description',
        help=(
            'A description of the managed identity.'
        ),
    )
    parser.add_argument(
        '--disabled',
        action='store_true',
        help=(
            'Whether the managed identity is disabled. If disabled, '
            'credentials may longer be issued for this identity. Existing '
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
    managed_identity_ref = args.CONCEPTS.managed_identity.Parse()

    managed_identity_lro_ref = self.CreateWorkloadIdentityPoolManagedIdentity(
        args, client, messages, managed_identity_ref
    )

    if args.async_ and not args.source:
      return managed_identity_lro_ref

    managed_identity_result = (
        self.WaitForCreateWorkloadIdentityPoolManagedIdentityOperation(
            client, managed_identity_lro_ref, managed_identity_ref
        )
    )

    if not args.source:
      return managed_identity_result

    workload_source_lro_ref = self.CreateWorkloadSource(
        args, client, messages, managed_identity_ref
    )

    if args.async_:
      return managed_identity_lro_ref, workload_source_lro_ref

    workload_source_result = self.WaitForCreateWorkloadSourceOperation(
        args, client, workload_source_lro_ref
    )

    return managed_identity_result, workload_source_result

  def CheckWorkloadSourceArgs(self, args):
    if (
        args.source
        and not args.resources
        and not args.attached_service_accounts
    ):
      raise gcloud_exceptions.OneOfArgumentsRequiredException(
          ['--resources', '--attached-service-accounts'],
          'Must provide at least one attribute that matches workload(s) '
          'from the source.',
      )

    if (args.resources or args.attached_service_accounts) and not args.source:
      raise gcloud_exceptions.RequiredArgumentException(
          ['--source'],
          'source must be specified when attributes are set.',
      )

  def CreateWorkloadIdentityPoolManagedIdentity(
      self, args, client, messages, managed_identity_ref
  ):
    new_managed_identity = messages.WorkloadIdentityPoolManagedIdentity(
        description=args.description,
        disabled=args.disabled,
    )
    lro_ref = client.projects_locations_workloadIdentityPools_namespaces_managedIdentities.Create(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesManagedIdentitiesCreateRequest(
            parent=managed_identity_ref.Parent().RelativeName(),
            workloadIdentityPoolManagedIdentityId=managed_identity_ref.managedIdentitiesId,
            workloadIdentityPoolManagedIdentity=new_managed_identity,
        )
    )
    log.status.Print(
        'Create request issued for: [{}]'.format(
            managed_identity_ref.managedIdentitiesId
        )
    )

    return lro_ref

  def WaitForCreateWorkloadIdentityPoolManagedIdentityOperation(
      self, client, lro_ref, managed_identity_ref
  ):
    lro_resource = resources.REGISTRY.ParseRelativeName(
        lro_ref.name,
        collection=(
            'iam.projects.locations.workloadIdentityPools.namespaces.managedIdentities.operations'
        ),
    )
    namespace_result = waiter.WaitFor(
        identity_pool_waiter.IdentityPoolOperationPoller(
            client.projects_locations_workloadIdentityPools_namespaces_managedIdentities,
            client.projects_locations_workloadIdentityPools_namespaces_managedIdentities_operations,
        ),
        lro_resource,
        'Waiting for operation [{}] to complete'.format(lro_ref.name),
        # Wait for a maximum of 5 minutes, as the IAM replication has a lag of
        # up to 80 seconds.
        max_wait_ms=300000,
    )
    log.status.Print(
        'Created workload identity pool managed identity [{}].'.format(
            managed_identity_ref.managedIdentitiesId
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
        for_managed_identity=True,
    )
    log.status.Print('Create request issued for: [{}]'.format(args.source))

    return workload_source_lro_ref

  def WaitForCreateWorkloadSourceOperation(
      self, args, client, workload_source_lro_ref
  ):
    workload_source_result = workload_sources.WaitForWorkloadSourceOperation(
        client=client,
        lro_ref=workload_source_lro_ref,
        for_managed_identity=True,
    )
    log.status.Print('Created workload source [{}].'.format(args.source))

    return workload_source_result
