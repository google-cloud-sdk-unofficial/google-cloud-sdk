# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Command for listing available revisions in a worker pool."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import commands
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run.printers.v2 import printer_util
from googlecloudsdk.command_lib.run.v2 import worker_pools_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """List available revisions in a worker pool in a region."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To list available revisions in a worker pool `worker1` in a us-central1:

              $ {command} worker1 --region=us-central1
          """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    worker_pool_presentation = presentation_specs.ResourcePresentationSpec(
        '--worker-pool',
        resource_args.GetWorkerPoolResourceSpec(),
        'WorkerPool to list revisions in.',
        required=True,
        prefixes=False,
    )
    concept_parsers.ConceptParser([worker_pool_presentation]).AddToParser(
        parser
    )

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)
    parser.display_info.AddFormat(
        f'table(ready_symbol().{pretty_print.READY_COLUMN_COLOR},'
        'name():label="REVISION",'
        'active().yesno(yes="yes", no=""):label="ACTIVE",'
        'parent():label="WORKER POOL",'
        'create_time.date("%Y-%m-%d %H:%M:%S %Z"):'
        'label=DEPLOYED:sort=2:reverse,'
        'creator:label="DEPLOYED BY")'
    )
    parser.display_info.AddTransforms(
        {'ready_symbol': printer_util.GetReadySymbolFromDict}
    )
    parser.display_info.AddTransforms(
        {'name': printer_util.GetChildNameFromDict}
    )
    parser.display_info.AddTransforms(
        {'active': printer_util.GetActiveStateFromDict}
    )
    parser.display_info.AddTransforms(
        {'parent': printer_util.GetParentFromDict}
    )

  def Run(self, args):
    """List available revisions in a worker pool in a region."""

    def DeriveRegionalEndpoint(endpoint):
      region = args.CONCEPTS.worker_pool.Parse().locationsId
      return region + '-' + endpoint

    worker_pool_ref = args.CONCEPTS.worker_pool.Parse()
    run_client = apis.GetGapicClientInstance(
        'run', 'v2', address_override_func=DeriveRegionalEndpoint
    )
    worker_pools_client = worker_pools_operations.WorkerPoolsOperations(
        run_client
    )
    response = worker_pools_client.ListRevisions(worker_pool_ref)
    return commands.SortByName(response.revisions)
