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
"""Creates a Cloud SQL blue-green deployment."""

import argparse
from typing import Any, Dict

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Creates a Cloud SQL blue-green deployment."""

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    del cls  # Unused.
    parser.add_argument(
        'deployment',
        help='The ID of the blue-green deployment.',
    )
    parser.add_argument(
        '--source-instance',
        required=True,
        help=(
            'Cloud SQL instance to be used as source for the blue-green'
            ' deployment.'
        ),
    )
    parser.add_argument(
        '--region',
        help='The region of the blue-green deployment.',
    )
    parser.add_argument(
        '--description',
        help='User-provided description for the blue-green deployment.',
    )
    parser.add_argument(
        '--target-database-version',
        help=(
            'Database version for the target instance, for major version'
            ' upgrade.'
        ),
    )
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat('default')

  def Run(self, args: argparse.Namespace) -> Dict[str, Any]:
    """Creates a Cloud SQL blue-green deployment.

    Args:
      args: The arguments that this command was invoked with.

    Returns:
      A dictionary object representing the long-running operation resource if
      the create was successful.
    Raises:
      HttpException: An HTTP error response was received while executing API
          request.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages
    project = properties.VALUES.core.project.GetOrFail()
    region = args.region
    if not region:
      region = properties.VALUES.compute.region.Get()
    if not region:
      raise calliope_exceptions.RequiredArgumentException(
          '--region',
          'Region not chosen. Specify command-line flag --region or region'
          ' property.'
      )
    parent = f'projects/{project}/locations/{region}'
    source_instance_name = args.source_instance

    console_io.PromptContinue(
        message=(
            f'Blue green deployment {args.deployment} will be created in'
            f' project {project} and region {region}.'
        ),
        cancel_on_no=True,
    )

    try:
      deployment_resource = sql_messages.BlueGreenDeployment(
          sourceInstance=source_instance_name,
          description=args.description,
          targetConfig=sql_messages.TargetConfig(
              databaseVersion=args.target_database_version
          )
          if args.target_database_version
          else None,
      )

      request = sql_messages.SqlBlueGreenDeploymentsCreateRequest(
          parent=parent,
          blueGreenDeploymentId=args.deployment,
          blueGreenDeployment=deployment_resource,
      )

      result_operation = sql_client.blueGreenDeployments.Create(request)
      operation_ref = client.resource_parser.Create(
          'sql.operations', operation=result_operation.name, project=project
      )

      if args.async_:
        return result_operation

      operations.OperationsV1Beta4.WaitForOperation(
          sql_client, operation_ref, 'Creating blue-green deployment'
      )

      return sql_client.blueGreenDeployments.Get(
          sql_messages.SqlBlueGreenDeploymentsGetRequest(
              name=f'{parent}/blueGreenDeployments/{args.deployment}'
          )
      )

    except apitools_exceptions.HttpError as error:
      raise calliope_exceptions.HttpException(error) from error
