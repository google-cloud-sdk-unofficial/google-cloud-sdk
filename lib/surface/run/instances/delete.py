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
"""Command for deleting instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import deletion
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Delete an instance."""

  detailed_help = {
      'DESCRIPTION': """
          {description}
          """,
      'EXAMPLES': """
          To delete an instance:

              $ {command} instance-name
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    instance_presentation = presentation_specs.ResourcePresentationSpec(
        'INSTANCE',
        resource_args.GetInstanceResourceSpec(),
        'Instance to delete.',
        required=True,
        prefixes=False,
    )
    flags.AddAsyncFlag(parser, default_async_for_cluster=True)
    concept_parsers.ConceptParser([instance_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser):
    Delete.CommonArgs(parser)

  def Run(self, args):
    """Delete an instance."""
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    instance_ref = args.CONCEPTS.instance.Parse()
    with serverless_operations.Connect(conn_context) as client:
      message = 'Instance [{}] will be deleted.'.format(
          instance_ref.instancesId
      )
      if console_io.CanPrompt() and self.IsRunningInstance(
          instance_ref, client
      ):
        message += (
            ' This instance is currently running and will be stopped and'
            ' deleted.'
        )
      console_io.PromptContinue(
          message=message,
          throw_if_unattended=True,
          cancel_on_no=True,
      )
      deletion.Delete(
          instance_ref, client.GetInstance, client.DeleteInstance, args.async_
      )
    if args.async_:
      pretty_print.Success(
          'Instance [{}] is being deleted.'.format(instance_ref.instancesId)
      )
    else:
      log.DeletedResource(instance_ref.instancesId, 'instance')

  def IsRunningInstance(self, instance_ref, client):
    instance = client.GetInstance(instance_ref)
    if instance:
      return instance.is_running
    return False
