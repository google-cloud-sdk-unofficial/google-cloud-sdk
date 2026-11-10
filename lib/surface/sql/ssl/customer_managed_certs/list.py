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
"""List all customer managed certificate bundles for a Cloud SQL instance."""

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


class _BaseList(object):
  """Base class for sql ssl customer-managed-certs list."""

  @staticmethod
  def Args(parser):
    flags.AddInstance(parser)
    parser.display_info.AddFormat(flags.CUSTOMER_MANAGED_CERTS_FORMAT)

  def Run(self, args):
    """List all customer managed certificate bundles for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      An iterator over the CustomerManagedCertificateConfig resources if the API
      request was successful.
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

    result = sql_client.customerManagedCertificates.List(
        sql_messages.SqlCustomerManagedCertificatesListRequest(
            project=instance_ref.project, instance=instance_ref.instance
        )
    )
    return iter(result.customerManagedCertificates or [])


@base.RegionalEndpointsSupported
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
class List(_BaseList, base.ListCommand):
  """List all customer managed certificate bundles for a Cloud SQL instance."""

  detailed_help = {
      'EXAMPLES': (
          """\
          To list all customer managed certificate bundles for the Cloud SQL
          instance `my-instance`, run:

            $ {command} --instance=my-instance
          """
      ),
  }
