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
"""Implements command to extract metadata from a source data warehouse."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq.migration import cloud_extractor
from googlecloudsdk.command_lib.bq.migration import extractor_flags
from googlecloudsdk.command_lib.bq.migration import local_extractor


@base.RegionalEndpointsSupported
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Extract(base.Command):
  """Extract metadata from a source data warehouse."""

  detailed_help = extractor_flags.GetDetailedHelp(
      extractor_flags.ExtractType.METADATA
  )

  @staticmethod
  def Args(parser):
    extractor_flags.AddExtractorFlags(
        parser, extract_type=extractor_flags.ExtractType.METADATA
    )

  def Run(self, args):
    if args.run_mode == 'local':
      return local_extractor.Run(
          args, extract_type=extractor_flags.ExtractType.METADATA
      )
    return cloud_extractor.Run(
        args, extract_type=extractor_flags.ExtractType.METADATA
    )
