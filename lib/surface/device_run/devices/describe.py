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
"""Command for describing a Device Run device."""

import collections
from googlecloudsdk.api_lib import device_run
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.device_run import resource_args
from googlecloudsdk.command_lib.device_run.devices import devices


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a Device Run device."""

  @staticmethod
  def Args(parser):
    resource_args.AddDeviceResourceArg(parser, 'describe')

  def Run(self, args):
    device_ref = args.CONCEPTS.device.Parse()
    client = device_run.DevicesClient(api_version='v1alpha')
    device = client.Get(device_ref)

    summary = collections.OrderedDict()
    summary['id'] = device_ref.Name()
    summary['name'] = device.displayName or ''
    summary['manufacturer'] = device.manufacturer or ''
    summary['modelCode'] = device.modelCode or ''
    if device.platform is not None:
      platform_str = str(device.platform)
      if platform_str == 'IOS':
        summary['platform'] = 'iOS'
      else:
        summary['platform'] = platform_str.capitalize()
    if device.hardwareType is not None:
      summary['hardware_type'] = str(device.hardwareType)
    if device.formFactor is not None:
      summary['formFactor'] = str(device.formFactor)
    if device.primaryScreen:
      if device.primaryScreen.densityDpi is not None:
        summary['screenDensity'] = device.primaryScreen.densityDpi
      if device.primaryScreen.widthPx is not None:
        summary['screenX'] = device.primaryScreen.widthPx
      if device.primaryScreen.heightPx is not None:
        summary['screenY'] = device.primaryScreen.heightPx
    if device.androidDetails and device.androidDetails.supportedAbis:
      summary['supportedAbis'] = list(device.androidDetails.supportedAbis)

    if device.supportedProducts:
      supported_products = []
      for sp in device.supportedProducts:
        if sp.automation is not None:
          supported_products.append({'product': 'AUTOMATION'})
        if sp.deviceStreaming is not None:
          item = collections.OrderedDict()
          item['product'] = 'DEVICE_STREAMING'
          if sp.deviceStreaming.minimumAndroidStudioVersion:
            item['minimumAndroidStudioVersion'] = (
                sp.deviceStreaming.minimumAndroidStudioVersion
            )
          supported_products.append(item)
      if supported_products:
        summary['supportedProducts'] = supported_products

    if device.labels and device.labels.additionalProperties:
      tags = []
      for prop in device.labels.additionalProperties:
        if prop.key in ('tag', 'tags') and prop.value:
          tags.append(prop.value)
        elif not prop.value:
          tags.append(prop.key)
        else:
          tags.append(f'{prop.key}:{prop.value}')
      if tags:
        summary['tags'] = sorted(tags)

    if device.availability:
      capacity = devices.StripCapacityPrefix(device.availability.capacity)
      if capacity is not None:
        summary['capacity'] = capacity
      available = devices.StripAvailabilityPrefix(device.availability.available)
      if available is not None:
        summary['availability'] = available

    return summary


Describe.detailed_help = {
    'DESCRIPTION': 'Describe a Device Run device.',
    'EXAMPLES': """\
The following command describes the Device Run device `redfin_30`:

  $ {command} redfin_30
""",
}
