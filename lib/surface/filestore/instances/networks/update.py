# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Update a network of a Filestore instance."""

import textwrap

from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.filestore.instances import flags as instances_flags
from googlecloudsdk.core import log

_NETWORKS_UPDATE_MASK = 'networks'


@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
class UpdateBeta(base.UpdateCommand):
  """Update a network of a Filestore instance."""

  _API_VERSION = filestore_client.BETA_API_VERSION

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Update a network of a Filestore instance.

          This command is used to replace the user-created Private Service
          Connect (PSC) endpoint which is registered for an existing network of
          the instance, for example after the user deleted the forwarding rule
          of the previous endpoint and created a new one in the same VPC
          network. All the other settings of the network are kept as is.
          """),
      'EXAMPLES': textwrap.dedent("""\
          To register the user-created Private Service Connect endpoint with IP
          address `10.0.0.6` and PSC connection ID `987654321` for the network
          `my-network` of the instance `my-instance` in region `us-central1`,
          run:

            $ {command} my-instance --region=us-central1 --name=my-network \\
                --ip-address=10.0.0.6 --psc-connection-id=987654321
          """),
  }

  @staticmethod
  def Args(parser):
    instances_flags.AddInstanceNetworksUpdateArgs(parser)

  def Run(self, args):
    """Updates a network of a Filestore instance.

    Args:
      args: argparse.Namespace, the command line arguments.

    Returns:
      The update operation if --async is specified, otherwise the updated
      instance.

    Raises:
      InvalidArgumentException: If the network is not attached to the
        instance or if missing ip-address or psc-connection-id.
    """
    instance_ref = args.CONCEPTS.instance.Parse()
    client = filestore_client.FilestoreClient(self._API_VERSION)
    instance = client.GetInstance(instance_ref)

    try:
      instance = client.ParseUpdatedNetworkPscEndpointIntoInstance(
          instance,
          network_name=args.name,
          ip_address=args.ip_address,
          psc_connection_id=args.psc_connection_id,
      )
    except filestore_client.InvalidArgumentError as e:
      raise exceptions.InvalidArgumentException('--name', str(e))
    except filestore_client.InvalidIpAddressError as e:
      raise exceptions.InvalidArgumentException('--ip-address', str(e))
    except filestore_client.InvalidPscConnectionIdError as e:
      raise exceptions.InvalidArgumentException('--psc-connection-id', str(e))

    result = client.UpdateInstance(
        instance_ref, instance, _NETWORKS_UPDATE_MASK, args.async_
    )
    if args.async_:
      log.status.Print(
          'To check the status of the operation, run `gcloud beta filestore '
          'operations describe {}`'.format(result.name)
      )
    return result
