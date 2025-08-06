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

"""Command to show a specified investigation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.gemini_cloud_assist import args as gca_args
from googlecloudsdk.api_lib.gemini_cloud_assist import util as gca_util
from googlecloudsdk.calliope import base


@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Show metadata for an investigation.

  Shows metadata for an investigation given a valid investigation ID.

  This command can fail for the following reasons:
  * The investigation specified does not exist.
  * The active account does not have permission to access the given
  investigation.

  ## EXAMPLES

  The following command prints metadata for an investigation with the ID
  `example-foo-bar-1`:

    $ {command} example-foo-bar-1
  """

  @staticmethod
  def Args(parser):
    gca_args.AddInvestigationResourceArg(parser, verb="to describe")
    parser.display_info.AddFormat("value(investigation_short())")
    parser.add_argument(
        "--detail",
        required=False,
        action="store_true",
        help="Include extra information in the default output.",
    )

  def Run(self, args):
    if args.detail and not args.IsSpecified("format"):
      args.format = "value(investigation_detailed())"

    investigation_ref = args.CONCEPTS.investigation.Parse()
    return gca_util.GetInvestigation(investigation_ref.RelativeName())
