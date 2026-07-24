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


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List available Device Run devices."""

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'list devices')

    parser.display_info.AddFormat(
        'table(name.segment(-1):label=ID, '
        'manufacturer:label=MAKE, '
        'displayName:label=NAME, '
        'hardwareType:label=FORM, '
        'osVersion:label=OS_VERSION, '
        'products():label=PRODUCTS)'
    )
    parser.display_info.AddTransforms({'products': _TransformProducts})

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
