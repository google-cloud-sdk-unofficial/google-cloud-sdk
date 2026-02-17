# -*- coding: utf-8 -*- #
# Copyright 2026 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex entry-links update-aspects` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import entry_link as entry_link_api
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.dataplex import flags
from googlecloudsdk.command_lib.dataplex import resource_args


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA
)
class UpdateAspects(base.UpdateCommand):
  """Add or update one aspect for a Dataplex Entry Link."""

  detailed_help = {
      'EXAMPLES': """\

          To add or update an aspect for the Dataplex entry link `entrylink1` within the entry group `entry-group1` in location `us-central1` from a YAML/JSON file, run:

            $ {command} entrylink1 --project=test-project --location=us-central1 --entry-group entry-group1 --aspects=path-to-a-file-with-aspect.json

          """,
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    resource_args.AddDataplexEntryLinkResourceArg(parser, 'to update aspects')

    flags.AddEntryLinkAspectFlags(
        parser,
        update_aspects_name='aspects',
        required=True,
    )

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args: parser_extensions.Namespace):
    # Under the hood we perform an UpdateEntryLink call affecting only aspects.
    return entry_link_api.Update(args, update_aspects_arg_name='aspects')
