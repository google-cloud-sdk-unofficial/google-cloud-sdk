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
"""Command for listing Instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.run import commands
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run.printers import instance_printer
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.resource import resource_printer


class List(commands.List):
  """List instances."""

  detailed_help = {
      'DESCRIPTION': """
          {description}
          """,
      'EXAMPLES': """
          To list all instances in all regions:

              $ {command}
         """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetNamespaceResourceSpec(),
        'Namespace to list instances in.',
        required=True,
        prefixes=False,
        hidden=True,
    )
    concept_parsers.ConceptParser([namespace_presentation]).AddToParser(parser)
    parser.display_info.AddFormat(
        'table('
        f'{instance_printer.status_color_format()},'
        'name:label=INSTANCE,'
        'region:label=REGION,'
        'creation_timestamp.date("%Y-%m-%d %H:%M:%S %Z"):label="CREATED AT",'
        f'author:label="CREATED BY"):({commands.SATISFIES_PZS_ALIAS})'
    )
    parser.display_info.AddUriFunc(cls._GetResourceUri)
    resource_printer.RegisterFormatter(
        instance_printer.INSTANCE_PRINTER_FORMAT,
        instance_printer.InstancePrinter,
    )

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    """List instances."""
    # Use the mixer for global request if there's no --region flag.
    namespace_ref = args.CONCEPTS.namespace.Parse()
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    with serverless_operations.Connect(conn_context) as client:
      self.SetCompleteApiEndpoint(conn_context.endpoint)
      return commands.SortByName(client.ListInstances(namespace_ref))
