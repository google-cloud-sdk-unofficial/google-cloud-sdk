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
"""Command for obtaining details about a given worker pool revision."""


from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run.printers.v2 import revision_printer
from googlecloudsdk.command_lib.run.v2 import worker_pools_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.resource import resource_printer


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.Command):
  """Obtain details about a given worker pool revision."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To describe a revision `rev.1` of a worker pool `worker1` in us-central1:

              $ {command} rev.1 --region=us-central1 --workerpool=worker1
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    revision_presentation = presentation_specs.ResourcePresentationSpec(
        'WORKER_POOL_REVISION',
        resource_args.GetWorkerPoolRevisionResourceSpec(),
        'Worker pool revision to describe.',
        required=True,
        prefixes=False,
    )
    concept_parsers.ConceptParser([revision_presentation]).AddToParser(parser)

    resource_printer.RegisterFormatter(
        revision_printer.REVISION_PRINTER_FORMAT,
        revision_printer.RevisionPrinter,
        hidden=True,
    )
    parser.display_info.AddFormat(revision_printer.REVISION_PRINTER_FORMAT)

  @staticmethod
  def Args(parser):
    Describe.CommonArgs(parser)

  def Run(self, args):
    """Show details about a revision."""

    # TODO(b/366115714): Make sure to cover all edge cases and possibly find
    # better location to be shared by all worker pools operations.
    def DeriveRegionalEndpoint(endpoint):
      region = args.CONCEPTS.worker_pool_revision.Parse().locationsId
      return region + '-' + endpoint

    worker_pool_revision_ref = args.CONCEPTS.worker_pool_revision.Parse()
    flags.ValidateResource(worker_pool_revision_ref)
    run_client = apis.GetGapicClientInstance(
        'run', 'v2', address_override_func=DeriveRegionalEndpoint
    )
    worker_pools_client = worker_pools_operations.WorkerPoolsOperations(
        run_client
    )
    worker_pool_revision = worker_pools_client.GetRevision(
        worker_pool_revision_ref
    )
    if not worker_pool_revision:
      raise exceptions.ArgumentError(
          'Cannot find worker pool revision [{revision}] in [{region}] region.'
          .format(
              revision=worker_pool_revision_ref.revisionsId,
              region=worker_pool_revision_ref.locationsId,
          )
      )
    return worker_pool_revision
