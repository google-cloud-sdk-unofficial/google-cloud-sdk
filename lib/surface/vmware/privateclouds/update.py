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
"""'vmware privateclouds update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To update a private cloud named ``example-pc'' by changing its description to ``Example description'' and adding the labels ``key1'' and ``key2'' with respective values ``value1'' and ``value2'', run:

            $ {command} example-pc --location=us-west2-a --project=my-project --description='Example description' --labels=key1=value1,key2=value2

          Or:

            $ {command} example-pc --description='Example description' --labels=key1=value1,key2=value2

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.

    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update VMware Engine private cloud."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)
    parser.add_argument(
        '--description',
        help="""\
        Text describing the private cloud
        """)
    parser.add_argument(
        '--external-ip-access',
        action='store_true',
        default=None,
        hidden=True,
        help="""\
        Enable public IP address service for management appliances.
        Use --no-external-ip-access to disable
        """)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    privatecloud = args.CONCEPTS.privatecloud.Parse()
    client = PrivateCloudsClient()
    operation = client.Update(
        privatecloud,
        labels=args.labels,
        description=args.description,
        external_ip_access=args.external_ip_access)
    log.UpdatedResource(operation.name, kind='private cloud', is_async=True)

Update.detailed_help = DETAILED_HELP
