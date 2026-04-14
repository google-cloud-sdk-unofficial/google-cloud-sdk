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
"""Command for starting instances."""

import argparse

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.UniverseCompatible
class Start(base.Command):
  """Start a stopped instance."""

  detailed_help = {
      'DESCRIPTION': (
          """
          {description}
          """
      ),
      'EXAMPLES': (
          """
          To start an instance:

              $ {command} my-instance
          """
      ),
  }

  @staticmethod
  def CommonArgs(parser: argparse.ArgumentParser) -> None:
    instance_presentation = presentation_specs.ResourcePresentationSpec(
        'INSTANCE',
        resource_args.GetInstanceResourceSpec(),
        'Instance to start.',
        required=True,
        prefixes=False,
    )
    flags.AddAsyncFlag(parser)
    concept_parsers.ConceptParser([instance_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    Start.CommonArgs(parser)

  def Run(self, args: argparse.Namespace) -> None:
    """Start an instance."""
    instance_ref = args.CONCEPTS.instance.Parse()
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    with serverless_operations.Connect(conn_context) as client:
      instance = client.StartInstance(
          instance_ref, asyn=args.async_
      )

    if args.async_:
      pretty_print.Success(
          f'Instance [{instance.name}] is being started.'
      )
    else:
      pretty_print.Success(
          f'Started instance [{instance.name}].'
      )
