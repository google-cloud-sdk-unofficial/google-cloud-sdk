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
"""Reconciles network infrastructure for a Cloud SQL instance."""

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

DESCRIPTION = """\
    Reconciles network infrastructure (e.g. Service Connection Maps, Automated
    DNS Records) for a Cloud SQL instance.
    """

EXAMPLES_GA = """\
    To reconcile PSC DNS networking for a Cloud SQL instance:

        $ {command} instance-foo --psc-dns

    To reconcile PSC DNS networking for specific consumer VPC networks:

        $ {command} instance-foo --psc-dns --networks=projects/p1/global/networks/n1,projects/p2/global/networks/n2

    To force PSC DNS reconciliation:

        $ {command} instance-foo --psc-dns --force
    """

DETAILED_HELP = {
    'DESCRIPTION': DESCRIPTION,
    'EXAMPLES': EXAMPLES_GA,
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class ReconcileNetworking(base.Command):
  """Reconciles network infrastructure for a Cloud SQL instance."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'instance',
        completer=flags.InstanceCompleter,
        help='Cloud SQL instance ID.',
    )
    parser.add_argument(
        '--psc-dns',
        action='store_true',
        help=(
            "Reconciles the instance's Private Service Connect (PSC) DNS"
            ' records. If the DNS zones or records associated with the PSC'
            ' endpoints are missing or incorrect, they will be recreated or'
            ' updated.'
        ),
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help=(
            'Forces service connection mapping disablement and enablement'
            ' during PSC networking reconciliation. Bypasses safety checks and'
            ' may cause transient connectivity disruption for connected VPCs'
            ' while the networking settings are reapplied.'
        ),
    )
    parser.add_argument(
        '--networks',
        type=arg_parsers.ArgList(),
        metavar='NETWORK',
        help=(
            'List of specific consumer VPC networks to reconcile, specified as'
            ' full resource paths (e.g.'
            ' `projects/my-consumer-project/global/networks/prod-vpc`). If'
            ' omitted, reconciles all consumer networks associated with the'
            ' instance.'
        ),
    )

  def Run(self, args):
    """Reconciles network infrastructure for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the
      reconcile operation if the reconciliation was successful.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages
    operation_ref = None

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances',
    )

    if not args.psc_dns:
      raise calliope_exceptions.InvalidArgumentException(
          '--psc-dns', 'Must specify --psc-dns to reconcile PSC DNS records.'
      )

    psc_dns_req = sql_messages.PscDnsReconcileNetworkingRequest(
        force=args.force,
        networks=args.networks or [],
    )
    body = sql_messages.SqlInstancesReconcileNetworkingRequest(
        pscDns=psc_dns_req,
    )
    req = sql_messages.SqlProjectsInstancesReconcileNetworkingRequest(
        instance=instance_ref.instance,
        project=instance_ref.project,
        sqlInstancesReconcileNetworkingRequest=body,
    )

    try:
      result = sql_client.projects_instances.ReconcileNetworking(req)

      operation_ref = client.resource_parser.Create(
          'sql.operations', operation=result.name, project=instance_ref.project
      )

      if args.async_:
        return sql_client.operations.Get(
            sql_messages.SqlOperationsGetRequest(
                project=operation_ref.project, operation=operation_ref.operation
            )
        )

      operations.OperationsV1Beta4.WaitForOperation(
          sql_client, operation_ref, 'Reconciling Cloud SQL instance networking'
      )

    except exceptions.HttpError:
      log.debug(
          'operation : %s', str(operation_ref) if operation_ref else 'None'
      )
      raise
