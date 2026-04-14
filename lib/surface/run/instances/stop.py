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
"""Command for stopping instances."""

import argparse

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import cancellation
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.console import console_io


@base.UniverseCompatible
class Stop(base.Command):
  """Stop a running instance."""

  detailed_help = {
      'DESCRIPTION': (
          """
          {description}
          """
      ),
      'EXAMPLES': (
          """
          To stop an instance:

              $ {command} my-instance
          """
      ),
  }

  @staticmethod
  def CommonArgs(parser: argparse.ArgumentParser) -> None:
    instance_presentation = presentation_specs.ResourcePresentationSpec(
        'INSTANCE',
        resource_args.GetInstanceResourceSpec(),
        'Instance to stop.',
        required=True,
        prefixes=False,
    )
    flags.AddAsyncFlag(parser)
    concept_parsers.ConceptParser([instance_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    Stop.CommonArgs(parser)

  def Run(self, args: argparse.Namespace) -> None:
    """Stop an instance."""
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    instance_ref = args.CONCEPTS.instance.Parse()

    console_io.PromptContinue(
        message=f'Instance [{instance_ref.instancesId}] will be stopped.',
        throw_if_unattended=True,
        cancel_on_no=True,
    )

    with serverless_operations.Connect(conn_context) as client:
      cancellation.Cancel(
          instance_ref,
          client.GetInstance,
          client.StopInstance,
          args.async_,
          expected_reason='Stopped',
      )
    if args.async_:
      pretty_print.Success(
          f'Instance [{instance_ref.instancesId}] is being stopped.'
      )
    else:
      pretty_print.Success(
          f'Stopped instance [{instance_ref.instancesId}].'
      )
