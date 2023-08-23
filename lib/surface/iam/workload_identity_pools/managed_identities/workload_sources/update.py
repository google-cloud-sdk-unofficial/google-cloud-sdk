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
"""Command to update a workload source under a workload identity pool managed identity."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.api_lib.iam.workload_identity_pools import workload_sources
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.iam.workload_identity_pools import flags
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Update a workload identity pool managed identity workload source."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command adds resources and service accounts to a
          workload identity pool managed identity workload source in the default
          project with the ID project-123.

            $ {command} project-123 --location="global" \
            --workload-identity-pool="my-workload-identity-pool" \
            --namespace="my-namespace" \
            --managed-identity="my-managed-identity" \
            --add-resources="resource-1","resource-2" \
            --add-attached-service-accounts="service-account1","service-account2"

          The following command removes all the resources and service accounts
          from a workload identity pool managed identity workload source in the
          default project with the ID project-123.

            $ {command} project-123 --location="global" \
            --workload-identity-pool="my-workload-identity-pool" \
            --namespace="my-namespace" \
            --managed-identity="my-managed-identity" \
            --clear-resources \
            --clear-attached-service-accounts
          """,
  }

  upsert = False

  @staticmethod
  def Args(parser):
    workload_source_data = yaml_data.ResourceYAMLData.FromPath(
        'iam.workload_identity_pool_managed_identity_workload_source'
    )
    concept_parsers.ConceptParser.ForResource(
        'workload_source',
        concepts.ResourceSpec.FromYaml(
            workload_source_data.GetData(), is_positional=True
        ),
        'The workload identity pool managed identity workload source to'
        ' update.',
        required=True,
    ).AddToParser(parser)
    # Flags for creating workload source
    flags.AddUpdateWorkloadSourceFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    workload_source_ref = args.CONCEPTS.workload_source.Parse()

    try:
      workload_source = client.projects_locations_workloadIdentityPools_namespaces_workloadSources.Get(
          messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesWorkloadSourcesGetRequest(
              name=workload_source_ref.RelativeName()
          )
      )
      conditions_dict = {
          'resources': {
              condition.value: None
              for condition in workload_source.conditionSet.conditions
              if condition.attribute == 'resource'
          },
          'attached_service_accounts': {
              condition.value: None
              for condition in workload_source.conditionSet.conditions
              if condition.attribute == 'attached_service_account'
          },
      }
    # This is an upsert request if not found
    except exceptions.HttpNotFoundError:
      workload_source = messages.WorkloadSource()
      conditions_dict = {'resources': {}, 'attached_service_accounts': {}}
      self.upsert = True

    self.BuildConditionsDictFromArgs(args, conditions_dict)

    if self.upsert:
      if not self.EmptyCondition(conditions_dict):
        verb = 'Create'
        lro_ref = self.CreateWorkloadSource(
            client, messages, workload_source_ref, conditions_dict
        )
      else:
        # Do nothing if it's an upsert but nothing to create
        return
    elif self.EmptyCondition(conditions_dict):
      verb = 'Delete'
      lro_ref = self.DeleteWorkloadSource(
          client, messages, workload_source, workload_source_ref
      )
    else:
      verb = 'Update'
      workload_source.conditionSet = self.ToWorkloadSourceConditionSet(
          messages, conditions_dict
      )
      lro_ref = self.UpdateWorkloadSource(
          client, messages, workload_source, workload_source_ref
      )

    if args.async_:
      return lro_ref

    result = self.WaitForWorkloadSourceOperation(
        client, lro_ref, workload_source_ref, verb
    )

    return result

  def BuildConditionsDictFromArgs(self, args, conditions_dict):
    if args.clear_resources:
      conditions_dict['resources'] = {}
    if args.clear_attached_service_accounts:
      conditions_dict['attached_service_accounts'] = {}
    if args.remove_resources:
      for value in args.remove_resources:
        conditions_dict['resources'].pop(value, None)
    if args.remove_attached_service_accounts:
      for value in args.remove_attached_service_accounts:
        conditions_dict['attached_service_accounts'].pop(value, None)
    if args.add_resources:
      for value in args.add_resources:
        conditions_dict['resources'][value] = None
    if args.add_attached_service_accounts:
      for value in args.add_attached_service_accounts:
        conditions_dict['attached_service_accounts'][value] = None

  def CreateWorkloadSource(
      self, client, messages, workload_source_ref, conditions_dict
  ):
    lro_ref = workload_sources.CreateGcpWorkloadSource(
        client=client,
        messages=messages,
        workload_source_id=workload_source_ref.workloadSourcesId,
        resources=conditions_dict['resources'],
        attached_service_accounts=conditions_dict['attached_service_accounts'],
        parent=workload_source_ref.Parent().RelativeName(),
        for_managed_identity=True,
    )
    log.status.Print(
        'Create request issued for: [{}]'.format(
            workload_source_ref.workloadSourcesId
        )
    )

    return lro_ref

  def WaitForWorkloadSourceOperation(
      self, client, lro_ref, workload_source_ref, verb: str
  ):
    workload_source_result = workload_sources.WaitForWorkloadSourceOperation(
        client=client,
        lro_ref=lro_ref,
        for_managed_identity=True,
        delete=True if verb == 'Delete' else False,
    )
    log.status.Print(
        '{}d workload source [{}].'.format(
            verb, workload_source_ref.workloadSourcesId
        )
    )

    return workload_source_result

  def DeleteWorkloadSource(
      self, client, messages, workload_source, workload_source_ref
  ):
    lro_ref = client.projects_locations_workloadIdentityPools_namespaces_managedIdentities_workloadSources.Delete(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesManagedIdentitiesWorkloadSourcesDeleteRequest(
            name=workload_source.name, etag=workload_source.etag
        )
    )
    log.status.Print(
        'Delete request issued for: [{}]'.format(
            workload_source_ref.workloadSourcesId
        )
    )
    return lro_ref

  def UpdateWorkloadSource(
      self, client, messages, workload_source, workload_source_ref
  ):
    lro_ref = client.projects_locations_workloadIdentityPools_namespaces_managedIdentities_workloadSources.Patch(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesManagedIdentitiesWorkloadSourcesPatchRequest(
            name=workload_source.name,
            workloadSource=workload_source,
            updateMask='condition_set',
        )
    )
    log.status.Print(
        'Update request issued for: [{}]'.format(
            workload_source_ref.workloadSourcesId
        )
    )
    return lro_ref

  def EmptyCondition(self, conditions_dict):
    return not bool(conditions_dict['resources']) and not bool(
        conditions_dict['attached_service_accounts']
    )

  def ToWorkloadSourceConditionSet(self, messages, conditions_dict):
    conditions = []
    for value in conditions_dict['resources']:
      conditions.append(
          messages.WorkloadSourceCondition(attribute='resource', value=value)
      )
    for value in conditions_dict['attached_service_accounts']:
      conditions.append(
          messages.WorkloadSourceCondition(
              attribute='attached_service_account', value=value
          )
      )
    return messages.WorkloadSourceConditionSet(conditions=conditions)
