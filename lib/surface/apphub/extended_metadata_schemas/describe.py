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
"""gcloud apphub extended-metadata-schemas describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import extended_metadata_schemas as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe an App Hub extended metadata schema."""

  detailed_help = {
      'EXAMPLES': """\
          To describe the extended metadata schema `my-schema` in location
          `us-east1`, run:

            $ {command} my-schema --location=us-east1
      """,
  }

  @staticmethod
  def Args(parser):
    flags.AddDescribeExtendedMetadataSchemaFlags(parser)

  def Run(self, args):
    """Runs the describe command."""
    client = apis.ExtendedMetadataSchemasClient(self.ReleaseTrack())
    return client.Describe(args.CONCEPTS.extended_metadata_schema.Parse())
