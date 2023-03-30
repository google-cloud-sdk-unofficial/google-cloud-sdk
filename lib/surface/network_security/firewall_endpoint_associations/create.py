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
"""Create endpoint association command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from googlecloudsdk.api_lib.network_security.firewall_endpoint_associations import association_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import association_flags
from googlecloudsdk.command_lib.util.args import labels_util

DETAILED_HELP = {
    'DESCRIPTION': """
          Associate the specified network with the firewall endpoint. Successful
          creation of a firewall endpoint association results in an association
          in READY state. Check the progress of association creation by using
          `gcloud network-security firewall-endpoint-associations list`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To associate a network with a firewall endpoint, run:

            $ {command} my-association --network=my-network --endpoint=organizations/1234/locations/us-central1-a/firewallEndpoints/my-endpoint --zone=us-central1-a --project=my-project

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Firewall Plus endpoint association."""

  @staticmethod
  def Args(parser):
    association_flags.AddAssociationResource(parser)
    association_flags.AddEndpointResource(parser)
    association_flags.AddNetworkResource(parser)
    association_flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    client = association_api.Client(self.ReleaseTrack())

    association = args.CONCEPTS.firewall_endpoint_association.Parse()
    labels = labels_util.ParseCreateArgs(
        args, client.messages.FirewallEndpointAssociation.LabelsValue
    )

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    network = args.CONCEPTS.network.Parse()
    endpoint = args.CONCEPTS.endpoint.Parse()

    operation = client.CreateAssociation(
        name=association.Name(),
        parent=association.Parent().RelativeName(),
        network=network.RelativeName(),
        firewall_endpoint=endpoint.RelativeName(),
        labels=labels,
    )
    # Return the in-progress operation if async is requested.
    if is_async:
      # Delete operations have no format by default,
      # but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'waiting for firewall endpoint association [{}] to be created'
            .format(association.RelativeName())
        ),
        max_wait=max_wait,
    )


Create.detailed_help = DETAILED_HELP
