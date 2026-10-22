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
"""Add a network to a Filestore instance."""

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
class AddBeta(base.UpdateCommand):
  """Add a network to a Filestore instance."""

  _API_VERSION = filestore_client.BETA_API_VERSION

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Add a network to a Filestore instance.

          This command is used to connect a Filestore instance which was
          created without a network to a VPC network using Private Service
          Connect (PSC) with a user-created endpoint, and to register the
          user-created endpoint in one command.
          """),
      'EXAMPLES': textwrap.dedent("""\
          To add the network `my-network` to the instance `my-instance` in
          region `us-central1`, and register the user-created Private Service
          Connect endpoint with IP address `10.0.0.5` and PSC connection ID
          `123456789`, run:

            $ {command} my-instance --region=us-central1 --name=my-network \\
                --connect-mode=private-service-connect \\
                --psc-endpoint-creation-mode=user-created \\
                --ip-address=10.0.0.5 --psc-connection-id=123456789
          """),
  }

  @staticmethod
  def Args(parser):
    instances_flags.AddInstanceNetworksAddArgs(parser)

  def Run(self, args):
    """Adds a network to a Filestore instance.

    Args:
      args: argparse.Namespace, the command line arguments.

    Returns:
      The update operation if --async is specified, otherwise the updated
      instance.

    Raises:
      InvalidArgumentException: If the network is already attached to the
        instance or if either psc-endpoint-creation-mode or
        connect-mode are not set or if connect-mode is not
        private-service-connect or if psc-endpoint-creation-mode
        is not user-created or if either ip-address or psc-connection-id
        are not set.
    """
    instance_ref = args.CONCEPTS.instance.Parse()
    client = filestore_client.FilestoreClient(self._API_VERSION)
    instance = client.GetInstance(instance_ref)

    try:
      instance = client.ParseAddNetworkIntoInstance(
          instance,
          network_name=args.name,
          connect_mode=instances_flags.ChoiceToEnumName(args.connect_mode),
          address_mode=instances_flags.ChoiceToEnumName(args.address_mode),
          psc_endpoint_creation_mode=instances_flags.ChoiceToEnumName(
              args.psc_endpoint_creation_mode
          ),
          ip_address=args.ip_address,
          psc_connection_id=args.psc_connection_id,
      )
    except filestore_client.InvalidArgumentError as e:
      raise exceptions.InvalidArgumentException('--name', str(e))
    except filestore_client.InvalidConnectModeError as e:
      raise exceptions.InvalidArgumentException('--connect-mode', str(e))
    except filestore_client.InvalidPscEndpointCreationModeError as e:
      raise exceptions.InvalidArgumentException(
          '--psc-endpoint-creation-mode', str(e))
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
