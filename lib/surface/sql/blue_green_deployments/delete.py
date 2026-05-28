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
"""Deletes a Cloud SQL blue-green deployment."""

import argparse
import textwrap
from typing import Any
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Deletes a Cloud SQL blue-green deployment."""

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        'deployment',
        help='The ID of the blue-green deployment.',
    )
    parser.add_argument(
        '--region',
        help='The region of the blue-green deployment.',
    )
    parser.add_argument(
        '--delete-old-source',
        action='store_true',
        help=textwrap.dedent("""
        Delete the old source instance. This flag is only applicable when
        deleting a deployment after a switchover has been successfully
        completed.

        If deleting a deployment before switchover or after a failed
        switchover, the target instance will be deleted by default, and this
        flag will be ignored.
        """).strip(),
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args: argparse.Namespace) -> dict[str, Any] | None:
    """Deletes a Cloud SQL blue-green deployment.

    Args:
      args: The arguments that this command was invoked with.

    Returns:
      A dictionary object representing the long-running operation resource if
      the delete was successful.
    Raises:
      HttpException: An HTTP error response was received while executing API
          request.
    """
    del self  # Unused.
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
          ' property.',
      )
    deployment_name = f'projects/{project}/locations/{region}/blueGreenDeployments/{args.deployment}'

    if not console_io.PromptContinue(
        f'Deployment [{args.deployment}] will be deleted.'
    ):
      return None

    try:
      request = sql_messages.SqlBlueGreenDeploymentsDeleteRequest(
          name=deployment_name, deleteOldSource=args.delete_old_source
      )
      result_operation = sql_client.blueGreenDeployments.Delete(request)
      operation_ref = client.resource_parser.Create(
          'sql.operations', operation=result_operation.name, project=project
      )

      if args.async_:
        return result_operation

      operations.OperationsV1Beta4.WaitForOperation(
          sql_client, operation_ref, 'Deleting blue-green deployment'
      )
      log.DeletedResource(deployment_name, 'blue-green deployment')
    except apitools_exceptions.HttpError as error:
      raise calliope_exceptions.HttpException(error) from error
