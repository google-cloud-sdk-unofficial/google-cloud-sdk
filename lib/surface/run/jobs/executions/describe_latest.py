# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command for obtaining details about the latest execution of a job."""

import copy

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run.printers import export_printer
from googlecloudsdk.command_lib.run.printers import job_printer
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_printer


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeLatest(base.DescribeCommand):
  """Obtain details about the latest execution of a job."""

  detailed_help = {
      'DESCRIPTION': (
          """
          {description}
          """
      ),
      'EXAMPLES': (
          """
          To describe the latest execution of a job:

              $ {command} --job=my-job
          """
      ),
  }

  @staticmethod
  def CommonArgs(parser):
    job_presentation = presentation_specs.ResourcePresentationSpec(
        '--job',
        resource_args.GetJobResourceSpec(),
        'Job to describe the latest execution of.',
        required=True,
        prefixes=False,
    )
    concept_parsers.ConceptParser([job_presentation]).AddToParser(parser)

    resource_printer.RegisterFormatter(
        job_printer.EXECUTION_PRINTER_FORMAT,
        job_printer.ExecutionPrinter,
    )
    parser.display_info.AddFormat(job_printer.EXECUTION_PRINTER_FORMAT)
    resource_printer.RegisterFormatter(
        export_printer.EXPORT_PRINTER_FORMAT,
        export_printer.ExportPrinter,
    )

  @staticmethod
  def Args(parser):
    DescribeLatest.CommonArgs(parser)

  def Run(self, args):
    """Show details about the latest execution of a job."""
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack(), version_override='v1'
    )
    job_ref = args.CONCEPTS.job.Parse()

    with serverless_operations.Connect(conn_context) as client:
      job = client.GetJob(job_ref)
      if not job:
        raise exceptions.ArgumentError(
            'Cannot find job [{}].'.format(job_ref.Name())
        )

      if not job.status or not job.status.latestCreatedExecution:
        raise exceptions.ArgumentError(
            'Job [{}] has no executions.'.format(job_ref.Name())
        )

      execution_name = job.status.latestCreatedExecution.name

      # Parse the execution name in the same namespace (project) as the job.
      execution_ref = resources.REGISTRY.Parse(
          execution_name,
          params={'namespacesId': job_ref.namespacesId},
          collection='run.namespaces.executions',
      )

      execution = client.GetExecution(execution_ref)

    if not execution:
      raise exceptions.ArgumentError(
          'Cannot find execution [{}].'.format(execution_name)
      )
    return execution


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
class BetaDescribeLatest(DescribeLatest):
  """Obtain details about the latest execution of a job."""

  detailed_help = copy.deepcopy(DescribeLatest.detailed_help)
