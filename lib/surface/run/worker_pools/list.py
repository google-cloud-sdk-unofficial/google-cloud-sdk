# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command for listing available worker-pools."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import commands
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run.printers.v2 import printer_util
from googlecloudsdk.command_lib.run.v2 import worker_pools_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """List available worker-pools."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To list available worker-pools:

              $ {command}
          """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    region_presentation = presentation_specs.ResourcePresentationSpec(
        '--region',
        resource_args.GetRegionResourceSpec(),
        'Region to list worker-pools in.',
        required=True,
        prefixes=False,
    )
    concept_parsers.ConceptParser([region_presentation]).AddToParser(parser)
    parser.display_info.AddFormat(
        f'table(ready_symbol().{pretty_print.READY_COLUMN_COLOR},'
        'name():label="WORKER POOL",region():label=REGION,'
        'last_modifier:label="LAST DEPLOYED BY",'
        'last_transition_time().date("%Y-%m-%d %H:%M:%S %Z"):'
        'label="LAST DEPLOYED AT")'
    )
    parser.display_info.AddTransforms(
        {'ready_symbol': printer_util.GetReadySymbolFromDict}
    )
    parser.display_info.AddTransforms({'name': printer_util.GetNameFromDict})
    parser.display_info.AddTransforms(
        {'region': printer_util.GetRegionFromDict}
    )
    parser.display_info.AddTransforms(
        {'last_transition_time': printer_util.GetLastTransitionTimeFromDict}
    )

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    """List available worker-pools."""
    # TODO(b/382273085): Support YAML format once WorkerPools V1 API is ready.
    if 'format' in args and args.format == 'yaml':
      raise exceptions.ArgumentError(
          'YAML format is not supported for worker pools yet.'
      )

    def DeriveRegionalEndpoint(endpoint):
      region = args.CONCEPTS.region.Parse().locationsId
      return region + '-' + endpoint

    region_ref = args.CONCEPTS.region.Parse()
    run_client = apis.GetGapicClientInstance(
        'run', 'v2', address_override_func=DeriveRegionalEndpoint
    )
    worker_pools_client = worker_pools_operations.WorkerPoolsOperations(
        run_client
    )
    response = worker_pools_client.ListWorkerPools(region_ref)
    return commands.SortByName(response.worker_pools)
