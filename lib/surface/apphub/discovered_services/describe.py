# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to describe the discovered services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import discovered_services as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.apphub import flags

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To describe the DiscoveredService `my-discovered-service` in
        location `us-east1`, run:

          $ {command} my-discovered-service --location=us-east1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe an Apphub discovered service."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribeDiscoveredServiceFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    client = apis.DiscoveredServicesClient()
    dis_service_ref = args.CONCEPTS.discovered_service.Parse()
    if not dis_service_ref.Name():
      raise exceptions.InvalidArgumentException(
          'discovered service', 'discovered service id must be non-empty.'
      )
    return client.Describe(discovered_service=dis_service_ref.RelativeName())
