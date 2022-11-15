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
import ssl
import sys
import threading
import time

from apitools.base.py.exceptions import Error

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from requests import certs
import websocket
import websocket._exceptions as websocket_exceptions


class StartTcpTunnel(base.Command):
  """Starts a tunnel through which a local process can forward TCP traffic to the workstation."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To start a tunnel to port 22 on a workstation, run:

            $ {command} --project=my-project --region=us-central1 --cluster=my-cluster --config=my-config my-workstation 22
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser.ForResource(
        'workstation',
        concepts.ResourceSpec(
            'workstations.projects.locations.workstationClusters.workstationConfigs.workstations',
            resource_name='workstation',
            projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
            locationsId=concepts.ResourceParameterAttributeConfig(
                name='region', help_text='The region for the workstation.'),
            workstationClustersId=concepts.ResourceParameterAttributeConfig(
                name='cluster', help_text='The cluster for the workstation.'),
            workstationConfigsId=concepts.ResourceParameterAttributeConfig(
                name='config', help_text='The config for the workstation.'),
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
    workstation_name = args.CONCEPTS.workstation.Parse().RelativeName()
    self.messages = apis.GetMessagesModule('workstations', 'v1beta')
    self.client = apis.GetClientInstance('workstations', 'v1beta')

    # Look up the workstation host and determine port
    workstation = self.client.projects_locations_workstationClusters_workstationConfigs_workstations.Get(
        self.messages.
        WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsWorkstationsGetRequest(
            name=workstation_name))
    self.host = workstation.host
    self.port = args.workstation_port
    if workstation.state != self.messages.Workstation.StateValueValuesEnum.STATE_RUNNING:
      log.error('Workstation is not running.')
      sys.exit(1)

    # Generate an access token and refresh it periodically
    self._FetchAccessToken(workstation_name)
    self._RefreshAccessToken(workstation_name)

    # Bind on the local TCP port
    (host, port) = self._GetLocalHostPort(args)
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.bind((host, port))
    self.socket.listen(1)
    if port == 0:
      log.status.Print('Picking local unused port [{0}].'.format(
          self.socket.getsockname()[1]))

    # Accept new client connections
    log.status.Print('Listening on port [{0}].'.format(
        self.socket.getsockname()[1]))
    try:
      with execution_utils.RaisesKeyboardInterrupt():
        while True:
          conn, addr = self.socket.accept()
          self._AcceptConnection(conn, addr)
    except KeyboardInterrupt:
      log.info('Keyboard interrupt received.')
    log.status.Print('Server shutdown complete.')

  def _FetchAccessToken(self, workstation):
    try:
      self.access_token = self.client.projects_locations_workstationClusters_workstationConfigs_workstations.GenerateAccessToken(
          self.messages.
          WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsWorkstationsGenerateAccessTokenRequest(
              workstation=workstation)).accessToken
    except Error as e:
      log.error('Error fetching access token: {0}'.format(e))
      sys.exit(1)

  def _RefreshAccessToken(self, workstation):

    def refresh():
      while True:
        time.sleep(2700)  # 45 minutes
        self._FetchAccessToken(workstation)

    t = threading.Thread(target=refresh)
    t.daemon = True
    t.start()

  def _GetLocalHostPort(self, args):
    host = args.local_host_port.host or 'localhost'
    port = args.local_host_port.port or '0'
    return host, int(port)

  def _AcceptConnection(self, client, addr):
    custom_ca_certs = properties.VALUES.core.custom_ca_certs_file.Get()
    if custom_ca_certs:
      ca_certs = custom_ca_certs
    else:
      ca_certs = certs.where()

    server = websocket.WebSocketApp(
        'wss://%s/_workstation/tcp/%d' % (self.host, self.port),
        header={'Authorization': 'Bearer %s' % self.access_token},
        on_open=lambda ws: self._ForwardClientToServer(client, ws),
        on_data=lambda ws, data, op, finished: client.send(data),
        on_error=lambda ws, e: self._OnWebsocketError(client, e),
    )

    def run():
      server.run_forever(sslopt={
          'cert_reqs': ssl.CERT_REQUIRED,
          'ca_certs': ca_certs,
      })

    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

  def _ForwardClientToServer(self, client, server):

    def forward():
      while True:
        data = client.recv(4096)
        if not data:
          break
        server.send(data)

    t = threading.Thread(target=forward)
    t.daemon = True
    t.start()

  def _OnWebsocketError(self, client, error):
    if isinstance(error, websocket_exceptions.WebSocketBadStatusException
                 ) and error.status_code == 503:
      log.error(
          'The workstation does not have a server running on port {0}.'.format(
              self.port))
      client.close()
    elif isinstance(error,
                    websocket_exceptions.WebSocketConnectionClosedException):
      pass
    else:
      log.error('Received error from workstation: {0}'.format(error))
