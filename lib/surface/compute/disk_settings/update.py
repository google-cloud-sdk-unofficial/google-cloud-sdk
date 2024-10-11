# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Command to update disk settings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disk_settings import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
@base.Hidden
class Update(base.UpdateCommand):
  """Update disk settings."""

  detailed_help = {'EXAMPLES': """
        To update the disk settings in zone us-west1-a, add the access location ``us-central1 `` and remove the access location ``us-central2``
        in the project ``my-gcp-project'', run:

          $ {command} --add-access-locations=us-central1 --remove-access-locations=us-central2 --project=my-gcp-project --zone=us-west1-a
      """}

  @staticmethod
  def Args(parser):
    flags.AddDiskSettingArg(parser)
    flags.AddUpdateDiskSettingsFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    # 1. Get the updated disk settings, we only support updating access
    # locations for now.
    new_locations_values = []

    if args.add_access_locations:
      for location in args.add_access_locations:
        new_locations_values.append(
            client.messages.DiskSettingsAccessLocation.LocationsValue.AdditionalProperty(
                key=location,
                value=client.messages.DiskSettingsAccessLocationAccessLocationPreference(
                    region=location
                ),
            )
        )

    if args.remove_access_locations:
      for location in args.remove_access_locations:
        new_locations_values.append(
            client.messages.DiskSettingsAccessLocation.LocationsValue.AdditionalProperty(
                key=location,
                value=client.messages.DiskSettingsAccessLocationAccessLocationPreference(),
            )
        )

    # 2. Patch the disk settings
    if args.zone:
      service = client.apitools_client.diskSettings
      patch_request = client.messages.ComputeDiskSettingsPatchRequest(
          diskSettings=client.messages.DiskSettings(
              accessLocation=client.messages.DiskSettingsAccessLocation(
                  locations=client.messages.DiskSettingsAccessLocation.LocationsValue(
                      additionalProperties=new_locations_values
                  )
              )
          ),
          project=properties.VALUES.core.project.GetOrFail(),
          updateMask='accessLocation',
          zone=args.zone,
      )
    else:
      service = client.apitools_client.regionDiskSettings
      patch_request = client.messages.ComputeRegionDiskSettingsPatchRequest(
          diskSettings=client.messages.DiskSettings(
              accessLocation=client.messages.DiskSettingsAccessLocation(
                  locations=client.messages.DiskSettingsAccessLocation.LocationsValue(
                      additionalProperties=new_locations_values
                  )
              )
          ),
          project=properties.VALUES.core.project.GetOrFail(),
          region=args.region,
          updateMask='accessLocation',
      )

    return client.MakeRequests(
        [(service, 'Patch', patch_request)], no_followup=True
    )[0]
