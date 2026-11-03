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
"""List command for Resource Manager Semantic Tag Bindings."""

from googlecloudsdk.api_lib.resource_manager import semantic_tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager.semantic_tags import flags
from googlecloudsdk.command_lib.resource_manager.semantic_tags import utils
from googlecloudsdk.core.resource import resource_projection_spec


# gcloud-disable-gdu-domain
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  r"""List Semantic Tag Bindings.

  `{command}` lists Semantic Tag Bindings attached to the specified target
  Google Cloud resource.

  ## EXAMPLES

  To list all Semantic Tag Bindings attached to a Compute Engine VM instance
  under `projects/acme-sec-prod` in `us-central1`, run:

    $ {command} --location=us-central1 --parent=projects/acme-sec-prod \
        --target-resource=//compute.googleapis.com/projects/acme-sec-prod/zones/us-central1-a/instances/order-matcher-01
  """

  @staticmethod
  def Args(parser):
    flags.AddTargetResourceArgToParser(parser, required=True)
    flags.AddLocationArgToParser(parser, required=False, default='global')
    flags.AddBindingParentArgToParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(
        'table('
        'name:label=NAME, '
        'targetResource:label=TARGET_RESOURCE, '
        'semanticTagKey.basename():label=SEMANTIC_TAG_KEY_ID, '
        'semanticTagValue.basename():label=VALUE_ID'
        ')'
    )

  def Run(self, args):
    parent = utils.GetParent(args, default_to_catalog=False)
    location = args.location or 'global'
    parent_location = f'{parent}/locations/{location}'

    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases
    )
    # Expand short semanticTagKey IDs in --filter so client-side evaluation
    # matches the full key names returned by the API.
    rewriter = utils.SemanticTagBindingsFilterRewriter(location=location)
    args.filter, _ = rewriter.Rewrite(args.filter, defaults=defaults)

    with endpoints.CrmEndpointOverrides(location):
      return semantic_tags.ListSemanticTagBindings(
          parent=parent_location,
          target_resource=args.target_resource,
          page_size=args.page_size,
      )
