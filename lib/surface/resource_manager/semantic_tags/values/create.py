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
"""Create command for Resource Manager Semantic Tag Values."""

from googlecloudsdk.api_lib.resource_manager import semantic_tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager.semantic_tags import flags
from googlecloudsdk.command_lib.resource_manager.semantic_tags import utils
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  r"""Create a Semantic Tag Value.

  `{command}` creates a Semantic Tag Value under the specified organization or
  project container.

  ## EXAMPLES

  To create a composite Semantic Tag Value `cc-01` under `organizations/1001`
  using inline `--value-field` flags, run:

    $ {command} cc-01 \
        --key=projects/gcp-semantic-tags-catalog/locations/global/semanticTagKeys/costcenter.allocation \
        --parent=organizations/1001 \
        --value-field=sre=40,infra=60 \
        --display-name="Core Payments Allocation" \
        --description="Cost allocation for core payments services"

  To create a composite Semantic Tag Value `Trading` under
  `organizations/123456789012` from a YAML file `trading_value.yaml`, run:

    $ {command} Trading \
        --key=placement.latency \
        --parent=organizations/123456789012 \
        --value-file=trading_value.yaml

  To create a Semantic Tag Value `eng` under `projects/my-project` for key
  `costcenter.department`, run:

    $ {command} eng \
        --key=projects/gcp-semantic-tags-catalog/locations/global/semanticTagKeys/costcenter.department \
        --parent=projects/my-project \
        --value=engineering \
        --display-name="Engineering" \
        --description="Engineering department tag value"
  """

  @staticmethod
  def Args(parser):
    flags.AddValueIdArgToParser(
        parser,
        help_text=(
            'ID of the Semantic Tag Value to create, or its full resource name.'
        ),
    )
    flags.AddKeyArgToParser(parser, required=True)
    flags.AddLocationArgToParser(parser, required=False, default='global')
    flags.AddParentArgToParser(parser)
    flags.AddValueGroupToParser(parser)
    flags.AddDisplayNameArgToParser(parser)
    flags.AddDescriptionArgToParser(parser)
    flags.AddValidateOnlyArgToParser(parser, action_description='create')
    flags.AddAsyncArgToParser(parser)

  def Run(self, args):
    _, parent_location, location, value_id = utils.ParseSemanticTagValueName(
        args, default_to_catalog=False
    )
    semantic_tag_key = utils.NormalizeSemanticTagKey(args.key, location)

    string_value = None
    composite_fields = None
    file_display_name = None
    file_description = None

    if args.IsSpecified('value'):
      string_value = args.value
    elif args.IsSpecified('value_field'):
      composite_fields = args.value_field
    elif args.IsSpecified('value_file'):
      (
          string_value,
          composite_fields,
          file_display_name,
          file_description,
      ) = utils.ParseValueFile(args.value_file)

    display_name = (
        args.display_name
        if args.IsSpecified('display_name')
        else file_display_name
    )
    description = (
        args.description
        if args.IsSpecified('description')
        else file_description
    )

    with endpoints.CrmEndpointOverrides(location):
      op = semantic_tags.CreateSemanticTagValue(
          parent=parent_location,
          value_id=value_id,
          semantic_tag_key=semantic_tag_key,
          string_value=string_value,
          composite_fields=composite_fields,
          display_name=display_name,
          description=description,
          validate_only=args.validate_only,
      )
      if args.validate_only:
        log.status.Print('Request is valid. No resources were created.')
        return op
      if args.async_:
        log.CreatedResource(value_id, kind='semanticTagValue', is_async=True)
        return op

      result = operations.WaitForOperation(
          op,
          f'Waiting for SemanticTagValue [{value_id}] to be created',
          semantic_tags.GetSemanticTagValuesService(parent_location),
      )
      log.CreatedResource(value_id, kind='semanticTagValue')
      return result
