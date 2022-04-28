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
"""Implements a command to forward TCP traffic to a workstation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import socket
import threading

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
import websocket


class StartTcpTunnel(base.Command):
  """Starts a tunnel through which a local process can forward TCP traffic to the workstation."""

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser.ForResource(
        'workstation',
        concepts.ResourceSpec(
            'workstations.projects.locations.workstationClusters.workstations',
            resource_name='workstation',
            projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
            locationsId=concepts.ResourceParameterAttributeConfig(
                name='region', help_text='The region for the workstation.'),
            workstationClustersId=concepts.ResourceParameterAttributeConfig(
                name='cluster', help_text='The cluster for the workstation.'),
            workstationsId=concepts.ResourceParameterAttributeConfig(
                name='workstation', help_text='The workstation.'),
        ),
        'The workstation to which traffic should be sent.',
        required=True).AddToParser(parser)
    parser.add_argument(
        'workstation_port',
        type=int,
        help='The port on the workstation to which traffic should be sent.')
    parser.add_argument(
        '--local-host-port',
        type=arg_parsers.HostPort.Parse,
        default='localhost:0',
        help="""\
`LOCAL_HOST:LOCAL_PORT` on which gcloud should bind and listen for connections
that should be tunneled.

`LOCAL_PORT` may be omitted, in which case it is treated as 0 and an arbitrary
unused local port is chosen. The colon also may be omitted in that case.

If `LOCAL_PORT` is 0, an arbitrary unused local port is chosen.""")

  def Run(self, args):
    messages = apis.GetMessagesModule('workstations', 'v1alpha1')
    client = apis.GetClientInstance('workstations', 'v1alpha1')
    workstation_ref = args.CONCEPTS.workstation.Parse()

    # Look up the workstation host and determine port
    self.host = client.projects_locations_workstationClusters_workstations.Get(
        messages
        .WorkstationsProjectsLocationsWorkstationClustersWorkstationsGetRequest(
            name=workstation_ref.RelativeName())).host
    self.port = args.workstation_port

    # Generate an access token
    self.access_token = client.projects_locations_workstationClusters_workstations.GenerateAccessToken(
        messages.
        WorkstationsProjectsLocationsWorkstationClustersWorkstationsGenerateAccessTokenRequest(
            workstation=workstation_ref.RelativeName())).accessToken

    # Bind on the local TCP port
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.bind(self._GetLocalHostPort(args))
    self.socket.listen(1)

    # Accept new client connections
    log.status.Print('Awaiting connections on port %d...' %
                     self.socket.getsockname()[1])
    try:
      with execution_utils.RaisesKeyboardInterrupt():
        while True:
          conn, addr = self.socket.accept()
          self._AcceptConnection(conn, addr)
    except KeyboardInterrupt:
      log.info('Keyboard interrupt received.')

  def _GetLocalHostPort(self, args):
    host = args.local_host_port.host or 'localhost'
    port = args.local_host_port.port or '0'
    return host, int(port)

  def _AcceptConnection(self, client, addr):
    server = websocket.WebSocketApp(
        'wss://%s/_workstation/tcp/%d' % (self.host, self.port),
        header={'Authorization': 'Bearer %s' % self.access_token},
        on_open=lambda ws: self._ForwardClientToServer(client, ws),
        on_data=lambda ws, data, op, finished: client.send(data),
    )
    t = threading.Thread(target=server.run_forever)
    t.daemon = True
    t.start()

  def _ForwardClientToServer(self, client, server):

    def forward():
      while True:
        data = client.recv(4096)
        if not data:
          break
        server.send(data)

    log.status.Print('Connected to server')
    t = threading.Thread(target=forward)
    t.daemon = True
    t.start()
