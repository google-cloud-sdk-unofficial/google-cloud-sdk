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
"""Connects to an AlloyDB instance."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import connect
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import properties


DEFAULT_PROXY_PORT_NUMBER = 9471  # Generally unassigned port number


def AddConnectArgs(parser) -> None:
  """Declare flag arguments for the AlloyDB Auth Proxy invocation."""

  user_group = parser.add_mutually_exclusive_group()
  user_group.add_argument(
      '--user',
      '-u',
      required=False,
      help='Built-in database user to connect to the database as',
  )
  user_group.add_argument(
      '--auto-iam-authn',
      action='store_true',
      help='Enables Auto IAM authentication',
  )

  parser.add_argument(
      '--database',
      '-d',
      required=False,
      help='The AlloyDB database to connect to',
  )

  parser.add_argument(
      '--port',
      type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=65535),
      default=DEFAULT_PROXY_PORT_NUMBER,
      help=(
          'Port number used by the AlloyDB Auth Proxy to start a localhost'
          ' listener'
      ),
  )

  ip_group = parser.add_mutually_exclusive_group()
  ip_group.add_argument(
      '--psc',
      action='store_true',
      help='Connect to the AlloyDB instance using Private Service Connect.',
  )
  ip_group.add_argument(
      '--public-ip',
      action='store_true',
      help='Connect to the AlloyDB instance with Public IP',
  )


DETAILED_HELP = {
    'DESCRIPTION': (
        """
        Connects to an AlloyDB instance using the AlloyDB Auth Proxy and psql.
        """
    ),
    'EXAMPLES': (
        """
        To connect to an AlloyDB instance using the postgres user and database
        over private IP, run:

        $ {command} my-instance --cluster=my-cluster --region=us-central1

        To connect over public IP, run:

        $ {command} my-instance --cluster=my-cluster --region=us-central1 \
            --public-ip

        To connect over Private Service Connect, run:

        $ {command} my-instance --cluster=my-cluster --region=us-central1 \
            --psc

        To connect with a particular user and database, run:

        $ {command} my-instance --cluster=my-cluster --region=us-central1 \
            --user mydbuser \
            --database mydatabase

        To connect with Auto IAM Authentication using your authenticated gcloud
        user, run

        $ {command} my-instance --cluster=my-cluster --region=us-central1 \
            --auto-iam-authn

        To use an impersonated service account with the AlloyDB Auth Proxy,
        run:

        $ {command} my-instance --cluster=my-cluster --region=us-central1 \
            --impersonate-service-account impersonated@myproject.iam.gserviceaccount.com

        NOTE: the impersonated service account will be used by the Auth Proxy
        to retrieve connection info, but will not be used for authenticating to
        the database. To also authenticate to the database as the impersonated
        user, add the --auto-iam-authn flag.

        To use an impersonated service account with the AlloyDB Auth Proxy and
        authenticate to your database with the same impersonated user, run:

        $ {command} my-instance --cluster=my-cluster --region=us-central1 \
            --impersonate-service-account impersonated@myproject.iam.gserviceaccount.com \
            --auto-iam-authn

        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ConnectBeta(base.Command):
  """Connect to an AlloyDB instance using the AlloyDB Auth Proxy."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddCluster(parser, False)
    flags.AddInstance(parser)
    flags.AddRegion(parser)
    AddConnectArgs(parser)

  def Run(self, args, process_manager=connect.ProcessManager()):
    account = properties.VALUES.core.account.Get(required=True)
    project = properties.VALUES.core.project.GetOrFail()
    impersonate_service_account = (
        properties.VALUES.auth.impersonate_service_account.Get()
    )
    return connect.RunConnectCommand(
        connect.Config(args, account, project, impersonate_service_account),
        process_manager=process_manager,
    )


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ConnectAlpha(ConnectBeta):
  """Connect to an AlloyDB instance using the AlloyDB Auth Proxy."""

  @classmethod
  def Args(cls, parser):
    super(ConnectAlpha, cls).Args(parser)

  def Run(self, args, process_manager=connect.ProcessManager()):
    return super().Run(args, process_manager)
