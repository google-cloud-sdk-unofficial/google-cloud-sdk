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
"""Command to remove a list of BGP peers from a Distributed Cloud Edge Network router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.networking.routers import routers
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.networking import resource_args
from googlecloudsdk.core import log

DESCRIPTION = ('Delete a list of BGP peers from a Distributed Cloud Edge '
               'Network router')
EXAMPLES = """\
    To delete a list of BGP peers contains 'peer1' and 'peer2' from the
    Distributed Cloud Edge Network router 'my-router' in edge zone 'us-central1-edge-den1' , run:

        $ {command} my-router --peer-names=peer1,peer2 --location=us-central1 --zone=us-central1-edge-den1

   """


class RemoveBgpPeer(base.UpdateCommand):
  """Remove a list of BGP peers from a Distributed Cloud Edge Network router.

  *{command}* is used to delete a list of BGP peers from a Distributed Cloud
  Edge
  Network router.
  """

  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddRouterResourceArg(
        parser, 'from which we delete a list of bgp peers', True)
    parser.add_argument(
        '--peer-names',
        type=arg_parsers.ArgList(),
        required=True,
        metavar='BGP_PEER_NAME',
        help='''The list of names for peers being removed.
        Only single value allowed currently.
        '''
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    routers_client = routers.RoutersClient()
    router_ref = args.CONCEPTS.router.Parse()
    update_req_op = routers_client.RemoveBgpPeer(router_ref, args)

    async_ = args.async_
    if not async_:
      response = routers_client.WaitForOperation(update_req_op)
      log.UpdatedResource(router_ref, details='Operation was successful.')
      return response

    log.status.Print('Updating [{0}] with operation [{1}].'.format(
        router_ref, update_req_op.name))
