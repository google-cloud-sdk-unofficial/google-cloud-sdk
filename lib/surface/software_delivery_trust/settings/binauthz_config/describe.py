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
"""'software-delivery-trust settings binauthz-config describe' command."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.software_delivery_trust import util

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': (
        """\
        To describe the Binary Authorization config in location `us-central1`, run:

          $ {command} --location=us-central1
        """
    ),
}


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Retrieve details of a trusted Binary Authorization config."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    util.AddLocationResourceArg(
        parser,
        'Location of the Software Delivery Trust settings.',
        required=True,
    )

  def Run(self, args):
    client = util.GetClient()
    messages = util.GetMessages()
    location_ref = args.CONCEPTS.location.Parse()
    settings_name = '{}/settings'.format(location_ref.RelativeName())
    req = messages.SoftwaredeliverytrustProjectsLocationsGetSettingsRequest(
        name=settings_name
    )
    settings = client.projects_locations.GetSettings(req)
    return (
        settings.binaryAuthorizationConfig
        or messages.BinaryAuthorizationConfig()
    )
