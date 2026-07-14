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
"""Command for restarting instances."""

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
@base.RegionalEndpointsSupported
class Restart(base.Command):
  """Restart an instance."""

  detailed_help = {
      'DESCRIPTION': (
          """
          {description}

          If the instance is already stopped, this command will start it.

          Note that because this command orchestrates separate stop and start
          operations, if `--async` is specified, only the start portion of
          the restart is asynchronous. The stop portion will still block until
          the instance has stopped.
          """
      ),
      'EXAMPLES': (
          """
          To restart an instance:

              $ {command} my-instance
          """
      ),
  }

  @staticmethod
  def CommonArgs(parser: argparse.ArgumentParser) -> None:
    instance_presentation = presentation_specs.ResourcePresentationSpec(
        'INSTANCE',
        resource_args.GetInstanceResourceSpec(),
        'Instance to restart.',
        required=True,
        prefixes=False,
    )
    flags.AddAsyncFlag(parser)
    concept_parsers.ConceptParser([instance_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    Restart.CommonArgs(parser)

  def Run(self, args: argparse.Namespace) -> None:
    """Restart an instance."""
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    instance_ref = args.CONCEPTS.instance.Parse()

    console_io.PromptContinue(
        message=f'Instance [{instance_ref.instancesId}] will be restarted.',
        throw_if_unattended=True,
        cancel_on_no=True,
    )

    with serverless_operations.Connect(conn_context) as client:
      instance = client.GetInstance(instance_ref)
      if instance.is_running or not instance.conditions.IsTerminal():
        # Stop the instance. We must wait for it to stop before starting.
        cancellation.Cancel(
            instance_ref,
            client.GetInstance,
            client.StopInstance,
            async_=False,
            expected_reason='Stopped',
        )
      # Start the instance.
      instance = client.StartInstance(instance_ref, asyn=args.async_)

    if args.async_:
      pretty_print.Success(f'Instance [{instance.name}] is being restarted.')
    else:
      pretty_print.Success(f'Restarted instance [{instance.name}].')
