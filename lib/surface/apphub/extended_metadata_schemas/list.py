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
"""gcloud apphub extended-metadata-schemas list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import extended_metadata_schemas as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """List App Hub extended metadata schemas."""

  detailed_help = {
      'EXAMPLES': """\
          To list extended metadata schemas in location `us-east1`, run:

            $ {command} --location=us-east1
      """,
  }

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    flags.AddListExtendedMetadataSchemaFlags(parser)
    # Manually add back the flags we want to keep from the standard list flags.
    base.PAGE_SIZE_FLAG.AddToParser(parser)
    base.LIMIT_FLAG.AddToParser(parser)
    base.URI_FLAG.AddToParser(parser)
    parser.display_info.AddFormat('table(name, schema_version)')

  def Run(self, args):
    """Runs the list command."""
    client = apis.ExtendedMetadataSchemasClient(self.ReleaseTrack())
    location_ref = args.CONCEPTS.location.Parse()
    return client.List(location_ref.RelativeName(), limit=args.limit)
