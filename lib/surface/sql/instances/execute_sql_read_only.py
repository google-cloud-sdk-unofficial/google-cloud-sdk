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
"""Executes a read-only statement on a Cloud SQL instance."""

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files

DESCRIPTION = """\
    Executes a read-only statement on a Cloud SQL instance. Statements that
    modify data or schema are rejected. Before executing statements, follow
    Cloud SQL Data API's instructions to configure your database user and
    permissions.
    Note: The requests and responses might transit through intermediate
    locations between your client and the location of the target instance.
    """

EXAMPLES = """\
    To execute a read-only statement on a Cloud SQL instance using IAM
    database authentication, run:

    $ {command} my-instance-name --sql="SELECT * FROM employees;" --database=my-db

    To execute a read-only statement on a Cloud SQL instance using password
    authentication, run:

    $ {command} my-instance-name --sql="SELECT * FROM employees;" --database=my-db --user=my-user --password-secret-version=projects/my-project/locations/secret-location/secrets/my-secret/versions/latest
    """

DETAILED_HELP = {
    'DESCRIPTION': DESCRIPTION,
    'EXAMPLES': EXAMPLES,
}


# TODO(b/541410464): Remove Hidden once ExecuteSqlReadOnly launches.
@base.Hidden
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
class ExecuteSqlReadOnly(base.Command):
  """Executes a read-only statement on a Cloud SQL instance."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        'instance',
        completer=flags.InstanceCompleter,
        help='Cloud SQL instance ID.',
    )
    parser.add_argument(
        '--sql',
        required=True,
        help=(
            'Read-only SQL statement(s) to execute. It supports multiple'
            " statements as well. When it starts with the character '@', the"
            ' rest should be a filepath to read the SQL statement(s) from. For'
            ' example, --sql=@my_script.sql.'
        ),
    )
    parser.add_argument(
        '--row-limit',
        type=int,
        required=False,
        help='Maximum number of rows to return. The default is unlimited.',
    )
    flags.AddDatabase(
        parser,
        'Database on which the statement is executed.',
    )
    parser.add_argument(
        '--password-secret-version',
        required=False,
        help=(
            'The resource name of the Secret Manager secret holding the'
            ' password for the database user. The secret should be created'
            ' using the regional endpoint and stored in the same region as'
            ' the Cloud SQL instance. The expected resource name format is'
            ' <code>projects/{project}/locations/{location}/secrets/{secret}/versions/{secret_version}</code>.'
            ' Used together with <code>--user</code>. If not specified, IAM'
            ' database authentication is used.'
        ),
    )
    parser.add_argument(
        '--user',
        required=False,
        help=(
            'The database user to authenticate as. Used together with'
            ' <code>--password-secret-version</code>. If not specified, IAM'
            ' database authentication is used.'
        ),
    )

  def Run(self, args):
    """Executes a read-only statement on a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the execution result.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    if args.password_secret_version and not args.user:
      raise exceptions.RequiredArgumentException(
          '--user',
          '`--user` is required when `--password-secret-version` is specified.',
      )

    if args.user and not args.password_secret_version:
      raise exceptions.RequiredArgumentException(
          '--password-secret-version',
          '`--password-secret-version` is required when `--user` is specified.',
      )

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances',
    )
    if args.sql.startswith('@'):
      sql = files.ReadFileContents(args.sql[1:])
    else:
      sql = args.sql
    if args.password_secret_version:
      # Password authentication via Secret Manager
      req_body = sql_messages.ExecuteSqlReadOnlyPayload(
          sqlStatement=sql,
          database=args.database,
          rowLimit=args.row_limit,
          user=args.user,
          passwordSecretVersion=args.password_secret_version,
      )
    else:
      # IAM authentication
      req_body = sql_messages.ExecuteSqlReadOnlyPayload(
          sqlStatement=sql,
          database=args.database,
          rowLimit=args.row_limit,
          autoIamAuthn=True,
      )
    return sql_client.instances.ExecuteSqlReadOnly(
        sql_messages.SqlInstancesExecuteSqlReadOnlyRequest(
            instance=instance_ref.instance,
            project=instance_ref.project,
            executeSqlReadOnlyPayload=req_body,
        ),
    )
