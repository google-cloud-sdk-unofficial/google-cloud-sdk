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
"""'Marketplace Solutions Converge instances describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.mps.mps_client import MpsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.mps import flags
from googlecloudsdk.core import properties


DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe a Marketplace Solutions Converge instance.
        """,
    'EXAMPLES':
        """
          To get a description of an instance called ``my-instance'' in
          project ``my-project'' and region ``us-central1'', run:

          $ {command} my-instance --project=my-project --region=us-central1
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Describe(base.DescribeCommand):
  """Describe a Marketplace Solutions Converge instance."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddInstanceArgToParser(parser, positional=True)

  def Run(self, args):
    instance = args.CONCEPTS.instance.Parse()
    vendor = properties.VALUES.mps.vendor.Get(required=True)
    client = MpsClient()
    return client.GetInstance(vendor, instance)


Describe.detailed_help = DETAILED_HELP

