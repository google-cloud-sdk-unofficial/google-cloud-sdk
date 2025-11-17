# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Implements the command for starting a tunnel with Cloud IAP."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import iap_tunnel as run_iap_tunnel
from googlecloudsdk.core import log


_NUMPY_HELP_TEXT = """

To increase the performance of the tunnel, consider installing NumPy. For instructions,
please see https://cloud.google.com/iap/docs/using-tcp-forwarding#increasing_the_tcp_upload_bandwidth
"""


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StartIapTunnel(base.Command):
  """Starts an IAP tunnel to a Cloud Run instance."""

  detailed_help = {
      "DESCRIPTION": """\
          Starts a tunnel to Cloud Identity-Aware Proxy for TCP forwarding through which
          another process can SSH into a Cloud Run instance. This command is only to be used by
          other gcloud commands (gcloud run ssh), and should not be used directly.
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds arguments to the parser."""
    parser.add_argument(
        "--project_number",
        required=True,
        help="The project number of the project that the deployment is in.",
    )
    parser.add_argument(
        "--project_id",
        required=True,
        help="The project id of the project that the deployment is in.",
    )
    parser.add_argument(
        "--workload_type",
        required=True,
        help="The type of the workload. One of service, job, or worker-pool.",
    )
    parser.add_argument(
        "--deployment_name",
        required=True,
        help="The name of the deployment to connect to.",
    )
    flags.AddContainerArg(parser)
    flags.AddInstanceArg(parser)
    flags.AddRegionArg(parser)

  def Run(self, args):
    """Runs the command."""
    tunneler = run_iap_tunnel.CloudRunIAPWebsocketTunnelHelper(args)
    iap_tunnel_helper = iap_tunnel.IapTunnelStdinHelper(tunneler)
    self._CheckNumpyInstalled()
    iap_tunnel_helper.Run()

  def _CheckNumpyInstalled(self):
    # Check if user has numpy installed, show message asking them to install.
    # Numpy will be used later inside the websocket library to speed up the
    # transfer rate. Showing the message here before the process start looks
    # better than showing when the actual import happen inside the websocket.
    try:
      import numpy  # pylint: disable=g-import-not-at-top, unused-import
    except ImportError:
      log.warning(_NUMPY_HELP_TEXT)
