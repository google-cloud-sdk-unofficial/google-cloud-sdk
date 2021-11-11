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
"""'vmware hcx activationkeys create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.hcxactivationkeys import HcxActivationKeysClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Google Cloud VMware HCX activation key."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddHcxActivationKeyArgToParser(parser)

  def Run(self, args):
    hcx_activation_key = args.CONCEPTS.hcx_activation_key.Parse()
    client = HcxActivationKeysClient()
    operation = client.Create(hcx_activation_key)
    log.CreatedResource(
        operation.name, kind='hcx activation key', is_async=True)


Create.detailed_help = {
    'DESCRIPTION':
        """
          Create a HCX activation key in a VMware Engine private cloud. Successful creation of a HCX activation key results in a HCX activation key in AVAILABLE state. Check the progress of a HCX activation key using `gcloud alpha vmware hcx activationkeys list`.
        """,
    'EXAMPLES':
        """
          To create a HCX activation key called ``key1'' in private cloud ``my-privatecloud'' in zone ``us-west2-a'', run:

            $ {command} key1 --location=us-west2-a --project=my-project --privatecloud=my-privatecloud

            Or:

            $ {command} my-cluster --privatecloud=my-privatecloud

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}
