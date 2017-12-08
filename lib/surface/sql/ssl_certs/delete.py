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
"""Deletes an SSL certificate for a Cloud SQL instance."""


from googlecloudsdk.api_lib.sql import cert
from googlecloudsdk.api_lib.sql import errors
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log


class _BaseDelete(object):
  """Base class for sql ssl_certs delete."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'common_name',
        help='User supplied name. Constrained to [a-zA-Z.-_ ]+.')
    flags.INSTANCE_FLAG.AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(_BaseDelete, base.Command):
  """Deletes an SSL certificate for a Cloud SQL instance."""

  @errors.ReraiseHttpException
  def Run(self, args):
    """Deletes an SSL certificate for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the delete
      operation if the api request was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    # TODO(user): figure out how to rectify the common_name and the
    # sha1fingerprint, so that things can work with the resource parser.

    cert_ref = cert.GetCertRefFromName(sql_client, sql_messages, resources,
                                       instance_ref, args.common_name)
    if not cert_ref:
      raise exceptions.ToolException(
          'no ssl cert named [{name}] for instance [{instance}]'.format(
              name=args.common_name,
              instance=instance_ref))

    result = sql_client.sslCerts.Delete(
        sql_messages.SqlSslCertsDeleteRequest(
            project=cert_ref.project,
            instance=cert_ref.instance,
            sha1Fingerprint=cert_ref.sha1Fingerprint))

    operation_ref = resources.Create(
        'sql.operations',
        operation=result.operation,
        project=cert_ref.project,
        instance=cert_ref.instance,
    )

    if args.async:
      return sql_client.operations.Get(operation_ref.Request())

    operations.OperationsV1Beta3.WaitForOperation(
        sql_client, operation_ref, 'Deleting sslCert')

    log.DeletedResource(cert_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(_BaseDelete, base.Command):
  """Deletes an SSL certificate for a Cloud SQL instance."""

  @errors.ReraiseHttpException
  def Run(self, args):
    """Deletes an SSL certificate for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the delete
      operation if the api request was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    # TODO(user): figure out how to rectify the common_name and the
    # sha1fingerprint, so that things can work with the resource parser.

    cert_ref = cert.GetCertRefFromName(sql_client, sql_messages, resources,
                                       instance_ref, args.common_name)
    if not cert_ref:
      raise exceptions.ToolException(
          'no ssl cert named [{name}] for instance [{instance}]'.format(
              name=args.common_name,
              instance=instance_ref))

    result = sql_client.sslCerts.Delete(
        sql_messages.SqlSslCertsDeleteRequest(
            project=cert_ref.project,
            instance=cert_ref.instance,
            sha1Fingerprint=cert_ref.sha1Fingerprint))

    operation_ref = resources.Create(
        'sql.operations',
        operation=result.name,
        project=cert_ref.project,
        instance=cert_ref.instance,
    )

    if args.async:
      return sql_client.operations.Get(operation_ref.Request())

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Deleting sslCert')

    log.DeletedResource(cert_ref)
