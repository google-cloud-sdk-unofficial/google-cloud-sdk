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
"""Command for describing Cloud Run Integration types."""

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
class Describe(base.DescribeCommand):
  """Describes a Cloud Run Integration."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To describe an integration type

              $ {command} [TYPE]

         """,
  }

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    flags.AddPositionalTypeArg(parser)
    parser.display_info.AddFormat(
        'table('
        'name:label="PARAMETER",'
        'required.yesno(yes="yes", no=""),'
        'description:label=DESCRIPTION)')

  def Run(self, args):
    """Describe an integration type."""
    type_name = args.type
    conn_context = connection_context.GetConnectionContext(
        args, run_flags.Product.RUN_APPS, self.ReleaseTrack())
    with run_apps_operations.Connect(conn_context) as client:
      type_def = client.GetIntegrationTypeDefinition(type_name)
      if not type_def:
        raise exceptions.ArgumentError(
            'Cannot find integration type [{}]'.format(type_name))
      return list(type_def['parameters'])
