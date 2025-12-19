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

"""List Entra ID certificates for a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.api_lib.sql.ssl import entraid_certs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


class _BaseList(object):
  """Base class for sql ssl entraid_certs list."""

  @staticmethod
  def Args(parser):
    flags.AddInstance(parser)
    parser.display_info.AddFormat(flags.ENTRAID_CERTS_FORMAT)

  def Run(self, args):
    """List all Entra ID certificates for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object that has the list of Entra ID Certs resources if the api
      request was successful.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    resp = entraid_certs.ListEntraIdCertificates(
        sql_client, sql_messages, instance_ref
    )
    if not resp.certs:
      return iter([flags.EntraIdCertForPrint(None, None)])
    entraid_cert_types = entraid_certs.GetEntraIdCertificateTypeDict(resp)
    hash2status = {
        cert.sha1Fingerprint: status
        for status, cert in entraid_cert_types.items()
    }
    result = [
        flags.EntraIdCertForPrint(
            cert, hash2status[cert.sha1Fingerprint]
        )
        for cert in resp.certs
    ]
    return iter(result)


@base.ReleaseTracks(
    base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
class List(_BaseList, base.ListCommand):
  """List all Entra ID certificates for a Cloud SQL instance."""
  pass
