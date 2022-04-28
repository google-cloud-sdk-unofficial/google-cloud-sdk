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
"""Command to add a BGP peer to a Distributed Cloud Edge Network router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.networking.routers import routers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.networking import resource_args
from googlecloudsdk.command_lib.edge_cloud.networking.routers import flags as routers_flags
from googlecloudsdk.core import log

DESCRIPTION = ('Create a BGP peer to a Distributed Cloud Edge Network router')
EXAMPLES = """\
    To create and add a BGP peer for the Distributed Cloud Edge Network router
    'my-router' in edge zone 'us-central1-edge-den1' , run:

        $ {command} my-router --interface=my-int-r1 --peer-asn=33333 --peer-name=peer1 --peer-ipv4-range=208.117.254.232/31 --location=us-central1 --zone=us-central1-edge-den1

   """


class AddBgpPeer(base.UpdateCommand):
  """Add a BGP peer to a Distributed Cloud Edge Network router.

  *{command}* is used to add a BGP peer to a Distributed Cloud Edge Network
  router.
  """

  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddRouterResourceArg(parser, 'to which we add a bgp peer',
                                       True)
    routers_flags.AddBgpPeerArgs(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    routers_client = routers.RoutersClient()
    router_ref = args.CONCEPTS.router.Parse()
    update_req_op = routers_client.AddBgpPeer(router_ref, args)

    async_ = args.async_
    if not async_:
      response = routers_client.WaitForOperation(update_req_op)
      log.UpdatedResource(router_ref, details='Operation was successful.')
      return response

    log.status.Print('Updating [{0}] with operation [{1}].'.format(
        router_ref, update_req_op.name))
