# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""The 'gcloud firebase test android list-device-capacities' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.api_lib.firebase.test.device_capacities import DEVICE_CAPACITY_TABLE_FORMAT
from googlecloudsdk.api_lib.firebase.test.device_capacities import DeviceCapacities
from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'EXAMPLES':
        """
    To list capacity information for all devices which are available for
    testing, run:

      $ {command}

    To list capacity only for model named redfin, run:

      $ {command} --filter=redfin

    To list capacity only for API version 30, run:

      $ {command} --filter=30
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListDeviceCapacities(base.ListCommand, DeviceCapacities):
  """List capacity information for all supported Android models & versions.

    List device capacity (high/medium/low/none) for all Android models &
    versions.

    Device capacity is static information solely based on the number of devices
    in Firebase Test Lab. It's important to note that device capacity does not
    directly reflect any real-time data, like the length of the test queue,
    traffic, or the available/busy/broken state of the devices.
  """

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags for this command.

    Args:
      parser: An argparse parser used to add arguments that follow this
          command in the CLI. Positional arguments are allowed.
    """
    parser.display_info.AddFormat(DEVICE_CAPACITY_TABLE_FORMAT)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Run the 'gcloud firebase test android list-device-capacities' command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      The list of device models, versions, and capacity info we want to have
      printed later. Obsolete (unsupported) devices, versions, and entries
      missing capacity info are filtered out.
    """

    return self.get_capacity_data(util.GetAndroidCatalog(self.context))


ListDeviceCapacities.detailed_help = DETAILED_HELP
