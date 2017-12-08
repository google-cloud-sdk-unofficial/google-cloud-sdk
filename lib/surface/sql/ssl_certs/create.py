# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Creates an SSL certificate for a Cloud SQL instance."""

import os
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


class _BaseAddCert(object):
  """Base class for sql ssl_certs create."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'common_name',
        help='User supplied name. Constrained to ```[a-zA-Z.-_ ]+```.')
    parser.add_argument(
        'cert_file',
        default=None,
        help=('Location of file which the private key of the created ssl-cert'
              ' will be written to.'))
    flags.INSTANCE_FLAG.AddToParser(parser)

  def Collection(self):
    return 'sql.sslCerts'

  def Format(self, args):
    return self.ListFormat(args)

  def Run(self, args):
    """Creates an SSL certificate for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """

    if os.path.exists(args.cert_file):
      raise exceptions.ToolException('file [{path}] already exists'.format(
          path=args.cert_file))

    # First check if args.out_file is writeable. If not, abort and don't create
    # the useless cert.
    try:
      with files.OpenForWritingPrivate(args.cert_file) as cf:
        cf.write('placeholder\n')
    except (files.Error, OSError) as e:
      raise exceptions.ToolException('unable to write [{path}]: {error}'.format(
          path=args.cert_file, error=str(e)))

    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    # TODO(user): figure out how to rectify the common_name and the
    # sha1fingerprint, so that things can work with the resource parser.

    result = sql_client.sslCerts.Insert(
        sql_messages.SqlSslCertsInsertRequest(
            project=instance_ref.project,
            instance=instance_ref.instance,
            sslCertsInsertRequest=sql_messages.SslCertsInsertRequest(
                commonName=args.common_name)))

    private_key = result.clientCert.certPrivateKey

    with files.OpenForWritingPrivate(args.cert_file) as cf:
      cf.write(private_key)
      cf.write('\n')

    cert_ref = resources.Create(
        collection='sql.sslCerts',
        project=instance_ref.project,
        instance=instance_ref.instance,
        sha1Fingerprint=result.clientCert.certInfo.sha1Fingerprint)

    log.CreatedResource(cert_ref)
    return result.clientCert.certInfo


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AddCert(_BaseAddCert, base.Command):
  """Creates an SSL certificate for a Cloud SQL instance."""
  pass


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AddCertBeta(_BaseAddCert, base.Command):
  """Creates an SSL certificate for a Cloud SQL instance."""
  pass
