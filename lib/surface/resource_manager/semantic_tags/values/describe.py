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
"""Describe command for Resource Manager Semantic Tag Values."""

from googlecloudsdk.api_lib.resource_manager import semantic_tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager.semantic_tags import flags
from googlecloudsdk.command_lib.resource_manager.semantic_tags import utils


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  r"""Describe a Semantic Tag Value.

  `{command}` describes a Semantic Tag Value given its ID, location, and parent,
  or its full resource name. When `--parent` is omitted with a short ID, it
  defaults to the Google Cloud Semantic Tags Catalog container
  (`projects/gcp-semantic-tags-catalog`).

  ## EXAMPLES

  To describe a Google Cloud predefined Semantic Tag Value `prod` in
  `us-central1`, run:

    $ {command} prod --location=us-central1

  To describe a customer Semantic Tag Value `Trading` under `organizations/1001`
  in `us-central1`, run:

    $ {command} Trading --location=us-central1 --parent=organizations/1001

  To describe a Semantic Tag Value by its full resource name, run:

    $ {command} projects/my-project/locations/us-central1/semanticTagValues/eng
  """

  @staticmethod
  def Args(parser):
    # TODO: b/561830899 - Evaluate migrating to multitype resource arguments
    # after Private Preview launch.
    flags.AddValueIdArgToParser(
        parser,
        help_text=(
            'ID of the Semantic Tag Value to describe, or its full resource'
            ' name.'
        ),
    )
    flags.AddLocationArgToParser(parser, required=False, default='global')
    flags.AddParentArgToParser(
        parser,
        help_text=(
            'Parent container of the Semantic Tag Value in the form'
            ' `organizations/{organization_id}` or'
            ' `projects/{project_id_or_number}`. Defaults to'
            ' `projects/gcp-semantic-tags-catalog` when omitted.'
        ),
    )

  def Run(self, args):
    full_name, _, location, _ = utils.ParseSemanticTagValueName(
        args, default_to_catalog=True
    )
    with endpoints.CrmEndpointOverrides(location):
      return semantic_tags.GetSemanticTagValue(full_name)
