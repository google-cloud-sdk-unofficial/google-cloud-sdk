# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""'vmware privateclouds delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Marks a VMware Engine private cloud for deletion. The resource is deleted 3 hours after being marked for deletion. This process can be reversed by using `gcloud vmware privateclouds undelete`.
        """,
    'EXAMPLES':
        """
          To mark a private cloud called ``my-privatecloud'' for deletion, run:

            $ {command} my-privatecloud --location=us-west2-a --project=my-project

          Or:

            $ {command} my-privatecloud

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete a VMware Engine private cloud."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)

  def Run(self, args):
    privatecloud = args.CONCEPTS.privatecloud.Parse()
    client = PrivateCloudsClient()
    operation = client.Delete(privatecloud)
    log.DeletedResource(operation.name, kind='private cloud', is_async=True)


Delete.detailed_help = DETAILED_HELP
