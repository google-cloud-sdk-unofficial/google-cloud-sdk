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
"""Migrates a Cloud SQL instance to an AlloyDB cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import types

from apitools.base.protorpclite import messages
from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import cluster_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import cluster_helper
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


# TODO: b/312466999 - Change @base.DefaultUniverseOnly to
# @base.UniverseCompatible once b/312466999 is fixed.
# See go/gcloud-cli-running-tpc-tests.
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class MigrateCloudSqlBeta(base.RestoreCommand):
  """Migrate Cloud SQL instance to an AlloyDB cluster using an existing Cloud SQL backup."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To migrate a Cloud SQL instance to an AlloyDB cluster from a backup, run:

              $ {command} my-alloydb-cluster --region=us-central1 --cloud-sql-project-id=my-cloud-sql-project-id --cloud-sql-instance-id=my-cloud-sql-cluster-id --cloud-sql-backup-id=my-cloud-sql-backup-id
        """,
  }

  @classmethod
  def Args(cls, parser: argparse.PARSER) -> None:
    """Specifies additional command flags.

    Args:
      parser: Parser object for command line inputs.
    """
    alloydb_messages = api_util.GetMessagesModule(cls.ReleaseTrack())
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddRegion(parser)
    flags.AddCluster(parser)
    flags.AddNetwork(parser)
    flags.AddPassword(parser)
    flags.AddAllocatedIPRangeName(parser)
    kms_resource_args.AddKmsKeyResourceArg(
        parser,
        'cluster',
        permission_info=(
            "The 'AlloyDB Service Agent' service account must hold permission"
            " 'Cloud KMS CryptoKey Encrypter/Decrypter'"
        ),
    )
    flags.AddAutomatedBackupFlags(
        parser, alloydb_messages, cls.ReleaseTrack(), update=False
    )
    flags.AddContinuousBackupConfigFlags(parser, cls.ReleaseTrack())
    flags.AddDatabaseVersion(parser, alloydb_messages)
    flags.AddEnablePrivateServiceConnect(parser)
    flags.AddMaintenanceWindow(parser, alloydb_messages)
    flags.AddSubscriptionType(parser, alloydb_messages)
    flags.AddTags(parser)
    flags.AddMigrateCloudSqlFlags(parser)
    flags.AddDenyMaintenancePeriod(parser, alloydb_messages)

  def ConstructMigrateCloudSqlRequestFromArgs(
      self,
      alloydb_messages: types.ModuleType,
      location_ref: resources.Resource,
      args: argparse.Namespace,
  ) -> messages.Message:
    """Constructs the Migrate Cloud Sql request.

    Args:
      alloydb_messages: The AlloyDB messages module.
      location_ref: The location reference for the request.
      args: An object that contains the values for the arguments specified in
        the .Args() method.

    Returns:
      The Migrate Cloud Sql request based on args.
    """
    return cluster_helper.ConstructMigrateCloudSqlRequestFromArgsBeta(
        alloydb_messages, location_ref, args
    )

  def Run(self, args: argparse.Namespace) -> messages.Message:
    """Constructs request from args, and sends it to the server.

    Args:
      args: An object that contains the values for the arguments specified in
        the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """

    client = api_util.AlloyDBClient(self.ReleaseTrack())
    alloydb_client = client.alloydb_client
    alloydb_messages = client.alloydb_messages
    location_ref = client.resource_parser.Create(
        'alloydb.projects.locations',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region,
    )

    req = self.ConstructMigrateCloudSqlRequestFromArgs(
        alloydb_messages, location_ref, args
    )
    op = alloydb_client.projects_locations_clusters.RestoreFromCloudSQL(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations'
    )
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if not args.async_:
      cluster_operations.Await(
          op_ref, 'Migrating Cloud SQL', self.ReleaseTrack()
      )
    return op


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class MigrateCloudSqlAlpha(MigrateCloudSqlBeta):
  """Migrate Cloud SQL instance to an AlloyDB cluster using an existing Cloud SQL backup."""

  @classmethod
  def Args(cls, parser: argparse.PARSER) -> None:
    super(MigrateCloudSqlAlpha, cls).Args(parser)

  def ConstructMigrateCloudSqlRequestFromArgs(
      self,
      alloydb_messages: types.ModuleType,
      location_ref: resources.Resource,
      args: argparse.Namespace,
  ) -> messages.Message:
    """Constructs the Migrate Cloud Sql request.

    Args:
      alloydb_messages: The AlloyDB messages module.
      location_ref: The location reference for the request.
      args: An object that contains the values for the arguments specified in
        the .Args() method.

    Returns:
      The Migrate Cloud Sql request based on args.
    """
    return cluster_helper.ConstructMigrateCloudSqlRequestFromArgsAlpha(
        alloydb_messages, location_ref, args
    )
