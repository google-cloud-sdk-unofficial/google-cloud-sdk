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
"""Hooks for Beyondcorp Security Gateway commands."""


def UpdateRequestWithMask(ref, args, request):
  """Update mask with logging and serviceDiscovery if they are specified."""
  del ref  # Unused

  fields_to_add = []

  # Check if logging is specified in args.
  if args.IsKnownAndSpecified('logging') or args.IsKnownAndSpecified(
      'clear_logging'
  ):
    fields_to_add.append('logging')

  # Check if service-discovery is specified in args.
  if (
      args.IsKnownAndSpecified('service_discovery')
      or args.IsKnownAndSpecified('clear_service_discovery')
      or args.IsKnownAndSpecified('resource_override_path')
  ):
    fields_to_add.append('service_discovery')

  mask = request.updateMask
  mask_fields = set(mask.split(',')) if mask else set()
  mask_fields.update(fields_to_add)

  # Collapse granular service_discovery fields to top-level service_discovery
  # as the server only expects top-level fields in the update mask.
  new_mask_fields = set()
  for f in mask_fields:
    if f.startswith('service_discovery.') or f.startswith('serviceDiscovery.'):
      new_mask_fields.add('service_discovery')
    else:
      new_mask_fields.add(f)

  request.updateMask = ','.join(sorted(new_mask_fields))

  if not fields_to_add:
    return request

  # Identify the name of the resource field in the request message.
  # For Beyondcorp SecurityGateways Update, it's
  # 'googleCloudBeyondcorpSecuritygatewaysV1SecurityGateway'.
  resource_field_name = None
  for field in request.all_fields():
    if 'SecurityGateway' in field.type.__name__:
      resource_field_name = field.name
      break

  if not resource_field_name:
    return request

  resource = getattr(request, resource_field_name)

  # Ensure the fields are initialized in the resource if they are None.
  # This is necessary because gcloud's GetMaskString/CreateRequest logic
  # might skip empty groups.
  resource_type = request.field_by_name(resource_field_name).type

  if (
      'logging' in fields_to_add
      and resource.logging is None
      and args.GetValue('logging') is not None
  ):
    resource.logging = resource_type.field_by_name('logging').type()

  if (
      'service_discovery' in fields_to_add
      and resource.serviceDiscovery is None
      and not args.IsKnownAndSpecified('clear_service_discovery')
  ):
    resource.serviceDiscovery = resource_type.field_by_name(
        'serviceDiscovery'
    ).type()

  return request
