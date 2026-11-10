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
"""Delete a customer managed certificate bundle for a Cloud SQL instance."""

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class _BaseDelete(object):
  """Base class for sql ssl customer-managed-certs delete."""

  @staticmethod
  def Args(parser):
    """Declare flag and positional arguments for the command parser."""
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'bundle',
        help=(
            'Customer managed certificate bundle name. Constrained to'
            ' `[a-zA-Z0-9]+` with a maximum length of 10 characters.'
        ),
    )
    flags.AddInstance(parser)

  def Run(self, args):
    """Delete a customer managed certificate bundle for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      An Operation resource describing the delete operation if `--async` is
      specified, or None otherwise.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances',
    )

    console_io.PromptContinue(
        message=(
            'Customer managed certificate bundle [{0}] will be deleted.'.format(
                args.bundle
            )
        ),
        default=True,
        cancel_on_no=True,
    )

    result_operation = sql_client.customerManagedCertificates.Delete(
        sql_messages.SqlCustomerManagedCertificatesDeleteRequest(
            project=instance_ref.project,
            instance=instance_ref.instance,
            certificateBundle=args.bundle,
        )
    )

    operation_ref = client.resource_parser.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project,
    )

    if args.async_:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project,
              operation=operation_ref.operation,
          )
      )

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Deleting customer managed certificate'
    )

    log.DeletedResource(args.bundle, 'customer managed certificate bundle')


@base.RegionalEndpointsSupported
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
class Delete(_BaseDelete, base.DeleteCommand):
  """Delete a customer managed certificate bundle for a Cloud SQL instance."""

  detailed_help = {
      'EXAMPLES': (
          """\
          To delete the customer managed certificate bundle `bundle1` for the
          Cloud SQL instance `my-instance`, run:

            $ {command} bundle1 --instance=my-instance
          """
      ),
  }
