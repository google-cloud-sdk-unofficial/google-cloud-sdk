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
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run.integrations import api_utils
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags as run_flags
from googlecloudsdk.command_lib.run.integrations import flags
from googlecloudsdk.command_lib.run.integrations import run_apps_operations


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Apply(base.Command):
  """Creates or replaces an application from a YAML specification."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To create an application from specification

              $ {command} appconfig.yaml

         """,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddFileArg(parser)

  def _ValidateAppConfigFile(self, file_content):
    if 'name' not in file_content:
      raise exceptions.FieldMismatchError("'name' is missing.")

  def Run(self, args):
    """Create or Update application from YAML."""

    messages = api_utils.GetMessages()
    self._ValidateAppConfigFile(args.FILE)
    app_dict = dict(args.FILE)
    name = app_dict.pop('name')
    try:
      appconfig = messages_util.DictToMessageWithErrorCheck(
          app_dict, messages.Config)
    except messages_util.ScalarTypeMismatchError as e:
      raise exceptions.FieldMismatchError(
          e,
          help_text='Please make sure that the YAML file matches the Cloud Run '
          'Integrations definition spec.')

    conn_context = connection_context.GetConnectionContext(
        args, run_flags.Product.RUN_APPS, self.ReleaseTrack())
    with run_apps_operations.Connect(conn_context) as client:
      return client.ApplyAppConfig(name, appconfig)
