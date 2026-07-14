# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command to import an Apigee API proxy."""

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.core.util import files


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Import(base.DescribeCommand):
  """Import an Apigee API proxy from local files."""

  detailed_help = {
      "DESCRIPTION": (
          """\
  {description}

  `{command}` uploads local files describing an API proxy to Apigee, creating a
  new API proxy or updating an existing one."""
      ),
  }

  @classmethod
  def Args(cls, parser):
    source_group = parser.add_mutually_exclusive_group(
        required=True,
        help="Source of the API proxy to import.",
    )
    source_group.add_argument(
        "--from-template",
        dest="template_path",
        type=files.ExpandHomeDir,
        help="Template file to import from.",
    )
    source_group.add_argument(
        "--from-bundle",
        dest="bundle_path",
        type=files.ExpandHomeDir,
        help="Bundle ZIP file to import from.",
    )
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.api",
        "API proxy to be imported.",
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()],
    )

  def Run(self, args):
    """Run the import command."""
    identifiers = args.CONCEPTS.api.Parse().AsDict()

    bundle_path = args.bundle_path
    if args.template_path:
      raise NotImplementedError(
          "Import from template is not implemented yet."
      )
    with files.BinaryFileReader(bundle_path) as f:
      return apigee.APIsClient.Create(identifiers, {}, f)

