# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for creating or replacing an application from YAML specification."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags as run_flags
from googlecloudsdk.command_lib.run.integrations import flags
from googlecloudsdk.command_lib.run.integrations import run_apps_operations


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Creates a Cloud Run Integration."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To create an application from specification

              $ {command} --type [TYPE] --service [SERVICE]

         """,
  }

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    flags.AddTypeArg(parser)
    flags.AddNameArg(parser)
    flags.AddServiceArg(parser)
    flags.AddParametersArg(parser)

  def Run(self, args):
    """Create or Update application from YAML."""

    integration_type = args.type
    service = args.service
    integration_name = args.name
    parameters = flags.GetAndValidateParameters(args, integration_type)

    conn_context = connection_context.GetConnectionContext(
        args, run_flags.Product.RUN_APPS, self.ReleaseTrack())
    with run_apps_operations.Connect(conn_context) as client:
      return client.CreateIntegration(
          integration_type, parameters, name=integration_name, service=service)
