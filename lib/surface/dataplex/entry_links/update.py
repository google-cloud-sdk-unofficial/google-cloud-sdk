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
"""`gcloud dataplex entry-links update` command."""

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
class Update(base.UpdateCommand):
  """Update a Dataplex Entry Link."""

  detailed_help = {
      'DESCRIPTION': 'Update specified fields in a given Dataplex Entry Link.',
      'EXAMPLES': """
          To add or update aspects from the YAML/JSON file, run:

            $ {command} entrylink1 --project=test-project --location=us-central1 --entry-group=entry-group1 --update-aspects=path-to-a-file-with-aspects.json
          """,
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    resource_args.AddDataplexEntryLinkResourceArg(parser, 'to update.')
    flags.AddEntryLinkAspectFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args: parser_extensions.Namespace):
    return entry_link_api.Update(args)
