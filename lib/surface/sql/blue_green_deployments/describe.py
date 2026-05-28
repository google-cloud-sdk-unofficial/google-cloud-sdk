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
"""Retrieves information about a Cloud SQL blue-green deployment."""

import argparse
from typing import Any

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Retrieves information about a Cloud SQL blue-green deployment."""

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    """Specifies arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        'deployment',
        metavar='DEPLOYMENT',
        help='The ID of the blue-green deployment.',
    )
    parser.add_argument(
        '--region',
        help='The region of the blue-green deployment.',
    )
    parser.add_argument(
        '--show-config-diff',
        action='store_true',
        default=False,
        help=(
            'Show the configuration difference between source and target'
            ' instances.'
        ),
    )

  def Run(self, args: argparse.Namespace) -> Any:
    """Retrieves information about a Cloud SQL blue-green deployment.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A message object representing the blue-green deployment resource if
      fetching it was successful.
    Raises:
      calliope_exceptions.HttpException: An HTTP error response was received
        while executing API request.
    """
    sql_client = self.client.sql_client
    sql_messages = self.client.sql_messages

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
    view = (
        sql_messages.SqlBlueGreenDeploymentsGetRequest.ViewValueValuesEnum.DETAILED
        if args.show_config_diff
        else sql_messages.SqlBlueGreenDeploymentsGetRequest.ViewValueValuesEnum.BASIC
    )

    try:
      request = sql_messages.SqlBlueGreenDeploymentsGetRequest(
          name=deployment_name, view=view
      )
      return sql_client.blueGreenDeployments.Get(request)
    except apitools_exceptions.HttpError as error:
      raise calliope_exceptions.HttpException(error) from error
