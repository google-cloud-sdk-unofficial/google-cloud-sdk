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
"""Command for listing Device Run devices."""

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.device_run import resource_args
from googlecloudsdk.command_lib.device_run.devices import devices
from googlecloudsdk.core import resources


def _TransformProducts(resource):
  """Transforms supportedProducts into a comma-separated list of product names."""
  products = []
  if hasattr(resource, 'supportedProducts') and resource.supportedProducts:
    supported_products = resource.supportedProducts
  elif isinstance(resource, dict):
    supported_products = (
        resource.get('supportedProducts')
        or resource.get('supported_products')
        or []
    )
  else:
    supported_products = []

  for sp in supported_products:
    if hasattr(sp, 'automation') and sp.automation is not None:
      products.append('Automation')
    elif (
        isinstance(sp, dict)
        and 'automation' in sp
        and sp['automation'] is not None
    ):
      products.append('Automation')
    if (
        hasattr(sp, 'deviceStreaming')
        and getattr(sp, 'deviceStreaming', None) is not None
    ) or (
        hasattr(sp, 'device_streaming')
        and getattr(sp, 'device_streaming', None) is not None
    ):
      products.append('Streaming')
    elif isinstance(sp, dict) and (
        sp.get('deviceStreaming') is not None
        or sp.get('device_streaming') is not None
    ):
      products.append('Streaming')
  return ', '.join(products)


def _GetAvailabilityField(resource, field_name):
  """Safely retrieves a field from device's availability."""
  if isinstance(resource, dict):
    availability = resource.get('availability')
  else:
    availability = getattr(resource, 'availability', None)

  if not availability:
    return None

  if isinstance(availability, dict):
    return availability.get(field_name)
  else:
    return getattr(availability, field_name, None)


def _TransformCapacity(resource):
  """Transforms device availability capacity for table display.

  Args:
    resource: The device resource (dict or object).

  Returns:
    The capacity string with prefix removed, or empty string.
  """
  value = _GetAvailabilityField(resource, 'capacity')
  capacity = devices.StripCapacityPrefix(value)
  return capacity if capacity is not None else ''


def _TransformAvailability(resource):
  """Transforms device availability available status for table display."""
  value = _GetAvailabilityField(resource, 'available')
  available = devices.StripAvailabilityPrefix(value)
  return available if available is not None else ''


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List available Device Run devices."""

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'list devices')

    parser.display_info.AddFormat(
        'table(name.segment(-1):label=ID, '
        'manufacturer:label=MAKE, '
        'displayName:label=NAME, '
        'modelCode:label=MODEL, '
        'hardwareType:label=HARDWARE_TYPE, '
        'osVersion:label=OS_VERSION, '
        'capacity_status():label=CAPACITY, '
        'availability_status():label=AVAILABILITY, '
        'products():label=PRODUCTS)'
    )
    parser.display_info.AddTransforms({
        'products': _TransformProducts,
        'capacity_status': _TransformCapacity,
        'availability_status': _TransformAvailability,
    })

    def UriFunc(resource):
      ref = resources.REGISTRY.Parse(
          resource.name, collection='devicerun.projects.locations.devices'
      )
      return ref.SelfLink()

    parser.display_info.AddUriFunc(UriFunc)

  def Run(self, args):
    location_ref = args.CONCEPTS.location.Parse()
    client = device_run.DevicesClient(api_version='v1alpha')
    return client.List(location_ref, limit=args.limit)


List.detailed_help = {
    'DESCRIPTION': 'List available Device Run devices.',
    'EXAMPLES': """\
The following command lists all Device Run devices:

  $ {command}
""",
}
