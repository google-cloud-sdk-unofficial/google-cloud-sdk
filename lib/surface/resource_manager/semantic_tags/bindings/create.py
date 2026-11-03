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
"""Create command for Resource Manager Semantic Tag Bindings."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.resource_manager import semantic_tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager.semantic_tags import flags
from googlecloudsdk.command_lib.resource_manager.semantic_tags import utils
from googlecloudsdk.core import log


# gcloud-disable-gdu-domain
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  r"""Create a Semantic Tag Binding.

  `{command}` creates a Semantic Tag Binding attaching a Semantic Tag Value to
  a target Google Cloud resource under the specified organization or project
  container.

  ## EXAMPLES

  To bind a Compute Engine VM instance to a customer-managed Semantic Tag Value
  under `projects/acme-sec-prod` in `us-central1`, run:

    $ {command} \
        --target-resource=//compute.googleapis.com/projects/acme-sec-prod/zones/us-central1-a/instances/order-matcher-01 \
        --semantic-tag-value=projects/acme-sec-prod/locations/us-central1/semanticTagValues/pci-dss \
        --location=us-central1 --parent=projects/acme-sec-prod

  To bind a Cloud Spanner database to a predefined Semantic Tag Value in the
  Google Cloud Semantic Tags Catalog, run:

    $ {command} \
        --target-resource=//spanner.googleapis.com/projects/acme-sec-prod/instances/prod-db/databases/orders \
        --semantic-tag-value=projects/gcp-semantic-tags-catalog/locations/us-central1/semanticTagValues/prod \
        --location=us-central1 --parent=projects/acme-sec-prod
  """

  @staticmethod
  def Args(parser):
    flags.AddTargetResourceArgToParser(parser, required=True)
    flags.AddSemanticTagValueArgToParser(parser, required=True)
    flags.AddLocationArgToParser(parser, required=False, default='global')
    flags.AddBindingParentArgToParser(parser)
    flags.AddValidateOnlyArgToParser(parser, action_description='create')
    flags.AddAsyncArgToParser(parser)

  def Run(self, args):
    target_resource = args.target_resource
    parent = utils.GetParent(args, default_to_catalog=False)
    location = args.location or 'global'
    parent_location = f'{parent}/locations/{location}'
    semantic_tag_value = utils.NormalizeSemanticTagValue(
        args.semantic_tag_value, parent=parent, location=location
    )

    with endpoints.CrmEndpointOverrides(location):
      op = semantic_tags.CreateSemanticTagBinding(
          parent=parent_location,
          target_resource=target_resource,
          semantic_tag_value=semantic_tag_value,
          validate_only=args.validate_only,
      )
      if args.validate_only:
        log.status.Print('Request is valid. No resources were created.')
        return op
      if args.async_:
        log.CreatedResource(
            op.name or target_resource,
            kind='Semantic Tag Binding',
            is_async=True,
        )
        return op
      if not op.done:
        op = operations.WaitForReturnOperation(
            op,
            'Waiting for SemanticTagBinding for target resource'
            f' [{target_resource}] and semantic tag value'
            f' [{semantic_tag_value}] to be created with [{op.name}]',
        )
      binding_name = target_resource
      if op.response is not None:
        response_dict = encoding.MessageToPyValue(op.response)
        if isinstance(response_dict, dict) and response_dict.get('name'):
          binding_name = response_dict['name']
      log.CreatedResource(binding_name, kind='Semantic Tag Binding')
      return op
