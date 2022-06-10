# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to create connection profiles for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.api_lib.database_migration import connection_profiles
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration import flags
from googlecloudsdk.command_lib.database_migration.connection_profiles import flags as cp_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DESCRIPTION = ('Create a Database Migration Service connection profile for '
               'MySQL.')
EXAMPLES = """\
    To create a connection profile for MySQL:

        $ {{command}} my-profile --region=us-central1 --password=123456
        --username=my-user --host=1.2.3.4 --port=3306

    If the source is a Cloud SQL database, run:

        $ {{command}} my-profile --region=us-central1 --password=123456
        --username=my-user --host=1.2.3.4 --port=3306
        --{instance}=my-instance --provider=CLOUDSQL
    """


class _MySQL(object):
  """Create a Database Migration Service connection profile for MySQL."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddConnectionProfileResourceArg(parser, 'to create')

    cp_flags.AddNoAsyncFlag(parser)
    cp_flags.AddDisplayNameFlag(parser)
    cp_flags.AddUsernameFlag(parser, required=True)
    cp_flags.AddPasswordFlagGroup(parser, required=True)
    cp_flags.AddHostFlag(parser, required=True)
    cp_flags.AddPortFlag(parser, required=True)
    cp_flags.AddProviderFlag(parser)
    flags.AddLabelsCreateFlags(parser)

  def Run(self, args):
    """Create a Database Migration Service connection profile.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    """
    connection_profile_ref = args.CONCEPTS.connection_profile.Parse()
    parent_ref = connection_profile_ref.Parent().RelativeName()

    if args.prompt_for_password:
      args.password = console_io.PromptPassword('Please Enter Password: ')

    cp_client = connection_profiles.ConnectionProfilesClient(
        self.ReleaseTrack())
    result_operation = cp_client.Create(
        parent_ref, connection_profile_ref.connectionProfilesId, 'MYSQL', args)

    client = api_util.GetClientInstance(self.ReleaseTrack())
    messages = api_util.GetMessagesModule(self.ReleaseTrack())
    resource_parser = api_util.GetResourceParser(self.ReleaseTrack())

    if args.IsKnownAndSpecified('no_async'):
      log.status.Print(
          'Waiting for connection profile [{}] to be created with [{}]'.format(
              connection_profile_ref.connectionProfilesId,
              result_operation.name))

      api_util.HandleLRO(client, result_operation,
                         client.projects_locations_connectionProfiles)

      log.status.Print('Created connection profile {} [{}]'.format(
          connection_profile_ref.connectionProfilesId, result_operation.name))
      return

    operation_ref = resource_parser.Create(
        'datamigration.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=connection_profile_ref.projectsId,
        locationsId=connection_profile_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatamigrationProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class MySQLAlpha(_MySQL, base.Command):
  """Create a Database Migration Service connection profile for MySQL."""

  detailed_help = {
      'DESCRIPTION': DESCRIPTION,
      'EXAMPLES': EXAMPLES.format(instance='instance')
  }

  @staticmethod
  def Args(parser):
    _MySQL.Args(parser)
    cp_flags.AddSslConfigGroup(parser, base.ReleaseTrack.ALPHA)
    cp_flags.AddInstanceFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class MySQLGA(_MySQL, base.Command):
  """Create a Database Migration Service connection profile for MySQL."""

  detailed_help = {
      'DESCRIPTION': DESCRIPTION,
      'EXAMPLES': EXAMPLES.format(instance='cloudsql-instance')
  }

  @staticmethod
  def Args(parser):
    _MySQL.Args(parser)
    cp_flags.AddSslConfigGroup(parser, base.ReleaseTrack.GA)
    cp_flags.AddCloudSQLInstanceFlag(parser)
