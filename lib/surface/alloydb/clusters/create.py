# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Creates a new AlloyDB cluster."""


import random

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.api_lib.alloydb import cluster_operations
from googlecloudsdk.api_lib.backupdr.backup_plan_associations import BackupPlanAssociationsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
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
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a new AlloyDB cluster within a given project."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To create a new cluster, run:

          $ {command} my-cluster --region=us-central1 --password=postgres
        """,
  }

  @classmethod
  def Args(cls, parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
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
    flags.AddDenyMaintenancePeriod(parser, alloydb_messages)
    flags.AddSubscriptionType(parser, alloydb_messages)
    flags.AddTags(parser)
    flags.AddDataplexIntegrationFlags(parser)

  def ConstructCreateRequestFromArgs(self, alloydb_messages, location_ref,
                                     args):
    return cluster_helper.ConstructCreateRequestFromArgsGA(
        alloydb_messages, location_ref, args)

  def Run(self, args):
    """Constructs and sends request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      ProcessHttpResponse of the request made.
    """
    if getattr(args, 'backupdr_backup_plan', None) and args.async_:
      raise exceptions.InvalidArgumentException(
          '--backupdr-backup-plan',
          'Cannot use --async with --backupdr-backup-plan.')
    client = api_util.AlloyDBClient(self.ReleaseTrack())
    alloydb_client = client.alloydb_client
    alloydb_messages = client.alloydb_messages
    location_ref = client.resource_parser.Create(
        'alloydb.projects.locations',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region)
    req = self.ConstructCreateRequestFromArgs(alloydb_messages, location_ref,
                                              args)
    op = alloydb_client.projects_locations_clusters.Create(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='alloydb.projects.locations.operations')
    log.status.Print('Operation ID: {}'.format(op_ref.Name()))
    if getattr(args, 'backupdr_backup_plan', None):
      log.status.Print(
          'Waiting for cluster creation to complete before associating BackupDR'
          ' plan ...'
      )
      cluster_operations.Await(op_ref, 'Creating cluster', self.ReleaseTrack())
      cluster_ref = client.resource_parser.Create(
          'alloydb.projects.locations.clusters',
          projectsId=properties.VALUES.core.project.GetOrFail,
          locationsId=args.region,
          clustersId=args.cluster
      )
      cluster_uri = cluster_ref.RelativeName()

      bpa_client = BackupPlanAssociationsClient()

      backup_plan_ref = client.resource_parser.Parse(
          args.backupdr_backup_plan,
          collection='backupdr.projects.locations.backupPlans',
      )
      backup_plan_location = backup_plan_ref.Parent().Name()

      # Constructing BPA name. BPA is created in same project as cluster, but
      # in the same region as backup plan.
      # BPA ID is derived from the cluster ID.
      bpa_id = f'{args.cluster}-bpa-{random.randint(0, 100_000)}'
      bpa_ref = client.resource_parser.Create(
          'backupdr.projects.locations.backupPlanAssociations',
          projectsId=properties.VALUES.core.project.GetOrFail,
          locationsId=backup_plan_location,
          backupPlanAssociationsId=bpa_id
      )

      resource_type = 'alloydb.googleapis.com/Cluster'

      log.status.Print(
          f'Creating backup plan association {bpa_id} for cluster'
          f' {args.cluster} with plan {args.backupdr_backup_plan} ...'
      )
      try:
        bpa_op = bpa_client.Create(
            bpa_ref, backup_plan_ref, cluster_uri, resource_type
        )
        bpa_client.WaitForOperation(
            operation_ref=bpa_client.GetOperationRef(bpa_op),
            message=(
                'Creating backup plan association'
                f' [{bpa_ref.RelativeName()}] '
            ),
        )
        log.status.Print(
            f'\nSuccessfully associated BackupDR plan'
            f' {args.backupdr_backup_plan} with cluster {args.cluster}'
        )
      except apitools_exceptions.HttpError as e:
        error_message = (
            f'Failed to create Backup Plan Association {bpa_id}: {repr(e)}'
        )
        log.warning(error_message)
        retry_command = (
            'gcloud alpha backup-dr backup-plan-associations create'
            f' {bpa_id} \\ \n'
            f'\t --project={properties.VALUES.core.project.GetOrFail()} \\ \n'
            f'\t --location={args.region} \\ \n'
            f'\t --backup-plan={args.backupdr_backup_plan} \\ \n'
            f'\t --resource={cluster_uri} \\ \n'
            f'\t --resource-type={resource_type}'
        )
        log.info(f'To retry, you can run: \n  {retry_command}')

    elif not args.async_:
      cluster_operations.Await(op_ref, 'Creating cluster', self.ReleaseTrack())
    return op


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a new AlloyDB cluster within a given project."""

  @classmethod
  def Args(cls, parser):
    super(CreateBeta, cls).Args(parser)

  def ConstructCreateRequestFromArgs(
      self, alloydb_messages, location_ref, args
  ):
    return cluster_helper.ConstructCreateRequestFromArgsBeta(
        alloydb_messages, location_ref, args
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a new AlloyDB cluster within a given project."""

  @classmethod
  def Args(cls, parser):
    super(CreateAlpha, cls).Args(parser)
    flags.AddBackupDRBackupPlan(parser)

  def ConstructCreateRequestFromArgs(
      self, alloydb_messages, location_ref, args
  ):
    return cluster_helper.ConstructCreateRequestFromArgsAlpha(
        alloydb_messages, location_ref, args
    )
