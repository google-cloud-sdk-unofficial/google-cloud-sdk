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
"""Lists Cloud SQL blue-green deployments."""

import argparse
import textwrap
from collections.abc import Generator
from typing import Any
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """Lists Cloud SQL blue-green deployments."""

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        '--region',
        help='The region of the blue-green deployments.',
    )
    parser.display_info.AddFormat(textwrap.dedent("""
        table(
            name.basename(),
            sourceInstance.basename():label=SOURCE_INSTANCE,
            targetInstance.basename():label=TARGET_INSTANCE,
            state
        )
    """).strip())

  def Run(self, args: argparse.Namespace) -> Generator[Any, Any, Any]:
    """Lists Cloud SQL blue-green deployments.

    Args:
      args: The arguments that this command was invoked with.

    Returns:
      A generator of dictionary objects representing the blue-green deployment
      resources.
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

    try:
      return list_pager.YieldFromList(
          sql_client.blueGreenDeployments,
          sql_messages.SqlBlueGreenDeploymentsListRequest(
              parent=f'projects/{project}/locations/{region}',
              filter=args.filter,
              orderBy=args.sort_by,
          ),
          limit=args.limit,
          batch_size_attribute='pageSize',
          batch_size=args.page_size,
          method='List',
          field='blueGreenDeployments',
      )
    except apitools_exceptions.HttpError as error:
      raise calliope_exceptions.HttpException(error) from error
