# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'vmware hcx activationkeys describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.hcxactivationkeys import HcxActivationKeysClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe a Google Cloud VMware HCX activation key."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddHcxActivationKeyArgToParser(parser)

  def Run(self, args):
    key = args.CONCEPTS.hcx_activation_key.Parse()
    client = HcxActivationKeysClient()
    return client.Get(key)


Describe.detailed_help = {
    'DESCRIPTION':
        """
          Describe a HCX activation key in a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To describe a HCX activation key called ``key1'' in private cloud ``my-privatecloud'' in zone ``us-west2-a'', run:

            $ {command} key1 --location=us-west2-a --project=my-project --privatecloud=my-privatecloud

            Or:

            $ {command} key1 --privatecloud=my-privatecloud

           In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}
