# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to list a application service in the Project/Location."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub.applications import services as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To list all services, run:

          $ {command}
        """,
}

_FORMAT = """
  table(
    name.basename():label=NAME,
    displayName,
    description,
    serviceReference
  )
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List application services."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddListApplicationServiceFlags(parser)
    parser.display_info.AddFormat(_FORMAT)

  def Run(self, args):
    """Run the list command."""
    client = apis.ServicesClient()
    application_ref = args.CONCEPTS.application.Parse()
    return client.List(
        limit=args.limit,
        page_size=args.page_size,
        parent=application_ref.RelativeName(),
    )
