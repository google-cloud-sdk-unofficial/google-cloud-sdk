# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for creating a broker."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import flags
from googlecloudsdk.command_lib.events import resource_args
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as serverless_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log


_DEFAULT_BROKER_NAME = 'default'

_INJECTION_LABELS = {'knative-eventing-injection': 'enabled'}


class Create(base.Command):
  """Create a broker to initialize a namespace for eventing."""

  detailed_help = {
      'DESCRIPTION': """
          {description}
          Creates a new broker for the given namespace.
          Currently, you can only create a broker named "default".
          This command is only available with Cloud Run for Anthos.
          """,
      'EXAMPLES': """
          To create a broker, run:

              $ {command} create default
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    """Defines arguments common to all release tracks."""
    flags.AddBrokerArg(parser)
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetCoreNamespaceResourceSpec(),
        'Namespace to create the Broker in.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser(
        [namespace_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)

  def Run(self, args):
    """Executes when the user runs the create command."""
    if serverless_flags.GetPlatform() == serverless_flags.PLATFORM_MANAGED:
      raise exceptions.UnsupportedArgumentError(
          'This command is only available with Cloud Run for Anthos.')

    if args.BROKER != _DEFAULT_BROKER_NAME:
      raise exceptions.UnsupportedArgumentError(
          'Only brokers named "default" may be created.')

    conn_context = connection_context.GetConnectionContext(
        args, serverless_flags.Product.EVENTS, self.ReleaseTrack())

    namespace_ref = args.CONCEPTS.namespace.Parse()

    with eventflow_operations.Connect(conn_context) as client:
      client.UpdateNamespaceWithLabels(namespace_ref, _INJECTION_LABELS)

    log.status.Print('Created broker [{}] in namespace [{}].'.format(
        args.BROKER, namespace_ref.Name()))
