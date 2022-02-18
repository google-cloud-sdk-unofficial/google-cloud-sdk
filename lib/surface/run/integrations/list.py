# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command for listing Cloud Run Integrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags as run_flags
from googlecloudsdk.command_lib.run.integrations import flags
from googlecloudsdk.command_lib.run.integrations import run_apps_operations


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Cloud Run Integrations."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          List Cloud Run Integrations within project

              $ {command} --type [TYPE] --service [SERVICE]

         """,
  }

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    flags.ListIntegrationsOfService(parser)
    flags.ListIntegrationsOfType(parser)

    # TODO(b/217741829): Create printer to limit outputed services to 3.
    parser.display_info.AddFormat("""
        table(
          name:label="Integration",
          type:label="Type",
          services:label="Service"
        )
      """)

  def Run(self, args):
    """Create a Cloud Run Integration."""

    integration_type = args.type.lower() if args.type else None
    service_name = args.service.lower() if args.service else None

    conn_context = connection_context.GetConnectionContext(
        args, run_flags.Product.RUN_APPS, self.ReleaseTrack())
    with run_apps_operations.Connect(conn_context) as client:
      if (integration_type and
          not client.IsValidIntegrationType(integration_type)):
        raise exceptions.IntegrationNotFoundError(
            'Invalid Integrations Type "{}"'.format(integration_type))

      return client.ListIntegrations(integration_type, service_name)
