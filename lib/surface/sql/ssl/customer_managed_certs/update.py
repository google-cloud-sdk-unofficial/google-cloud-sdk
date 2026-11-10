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
"""Create or update a customer managed certificate bundle for a Cloud SQL instance."""


from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


def _ReadCertFile(file_path):
  """Reads raw PEM bytes from a local file path."""
  try:
    return files.ReadBinaryFileContents(file_path)
  except (files.Error, OSError) as e:
    raise exceptions.ArgumentError(
        'unable to read [{path}]: {error}'.format(path=file_path, error=str(e))
    )


class _BaseUpdate(object):
  """Base class for sql ssl customer-managed-certs update."""

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
    parser.add_argument(
        '--intent',
        choices=['PG_LOGICAL'],
        default='PG_LOGICAL',
        help=(
            'Intent for the customer managed certificate bundle configuration.'
        ),
    )
    parser.add_argument(
        '--server-ca-file',
        help=(
            'Path to a PEM-encoded file containing the peer server CA'
            ' certificate.'
        ),
    )
    parser.add_argument(
        '--client-cert-file',
        help=(
            'Path to a PEM-encoded file containing the peer client certificate.'
        ),
    )
    parser.add_argument(
        '--client-key-file',
        help=(
            'Path to a PEM-encoded file containing the peer client private key.'
        ),
    )
    parser.add_argument(
        '--primary-dns',
        help=(
            'DNS name associated with the primary instance in a replication'
            ' topology.'
        ),
    )
    parser.add_argument(
        '--primary-ipv4-address',
        help='IPv4 address for the primary DNS name.',
    )
    parser.add_argument(
        '--allow-missing',
        action='store_true',
        default=False,
        help=(
            'If set, and the customer managed certificate bundle configuration'
            ' is not found, a new customer managed certificate bundle'
            ' configuration will be created. In this situation, `--update-mask`'
            ' is ignored.'
        ),
    )
    parser.add_argument(
        '--update-mask',
        help=(
            'Comma-separated list of fields to be updated. Allowed values'
            ' include: `*`, `intent`, `primary_dns_record`,'
            ' `primary_dns_record.dns`, `primary_dns_record.ipv4_address`, and'
            ' `customer_managed_certificates`.'
        ),
    )

  def Run(self, args):
    """Create or update a customer managed certificate bundle for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      An Operation resource describing the update operation if `--async` is
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

    certs = []
    if args.server_ca_file:
      certs.append(
          sql_messages.CustomerManagedCertificate(
              certificateType=(
                  sql_messages.CustomerManagedCertificate.CertificateTypeValueValuesEnum.CERTIFICATE_TYPE_PEER_SERVER_CA
              ),
              content=_ReadCertFile(args.server_ca_file),
          )
      )
    if args.client_cert_file:
      certs.append(
          sql_messages.CustomerManagedCertificate(
              certificateType=(
                  sql_messages.CustomerManagedCertificate.CertificateTypeValueValuesEnum.CERTIFICATE_TYPE_PEER_CLIENT_CERTIFICATE
              ),
              content=_ReadCertFile(args.client_cert_file),
          )
      )
    if args.client_key_file:
      certs.append(
          sql_messages.CustomerManagedCertificate(
              certificateType=(
                  sql_messages.CustomerManagedCertificate.CertificateTypeValueValuesEnum.CERTIFICATE_TYPE_PEER_CLIENT_KEY
              ),
              content=_ReadCertFile(args.client_key_file),
          )
      )

    if args.primary_dns is not None or args.primary_ipv4_address is not None:
      primary_dns_record = sql_messages.DNSEntry(
          dns=args.primary_dns,
          ipv4Address=args.primary_ipv4_address,
      )
    else:
      primary_dns_record = None

    if args.intent:
      intent = (
          sql_messages.CustomerManagedCertificateConfig.IntentValueValuesEnum(
              args.intent
          )
      )
    else:
      intent = None

    config = sql_messages.CustomerManagedCertificateConfig(
        intent=intent,
        primaryDnsRecord=primary_dns_record,
        customerManagedCertificates=certs,
    )

    update_request = sql_messages.UpdateCustomerManagedCertificateRequest(
        allowMissing=args.allow_missing,
        customerManagedCertificateConfig=config,
        updateMask=args.update_mask,
    )

    result_operation = sql_client.customerManagedCertificates.Update(
        sql_messages.SqlCustomerManagedCertificatesUpdateRequest(
            project=instance_ref.project,
            instance=instance_ref.instance,
            certificateBundle=args.bundle,
            updateCustomerManagedCertificateRequest=update_request,
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
        sql_client, operation_ref, 'Updating customer managed certificate'
    )

    log.UpdatedResource(args.bundle, 'customer managed certificate bundle')


@base.RegionalEndpointsSupported
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
class Update(_BaseUpdate, base.UpdateCommand):
  """Create or update a customer managed certificate bundle for a Cloud SQL instance."""

  detailed_help = {
      'EXAMPLES': (
          """\
          To create or replace a customer managed certificate bundle `bundle1`
          for the Cloud SQL instance `my-instance`, run:

            $ {command} bundle1 --instance=my-instance --allow-missing --intent=PG_LOGICAL --server-ca-file=/path/to/server_ca.pem --client-cert-file=/path/to/client_cert.pem --client-key-file=/path/to/client_key.pem --primary-dns=primary.example.com --primary-ipv4-address=10.0.0.1

          To partially update the primary IPv4 address and client certificate of
          an existing bundle `bundle1` for `my-instance`, run:

            $ {command} bundle1 --instance=my-instance --update-mask=primary_dns_record.ipv4_address,customer_managed_certificates --primary-ipv4-address=10.0.0.2 --client-cert-file=/path/to/new_client_cert.pem
          """
      ),
  }
