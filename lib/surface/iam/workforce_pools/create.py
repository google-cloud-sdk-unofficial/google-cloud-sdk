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
"""Command to create a new workforce pool under a parent organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.iam.workforce_pools import flags
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  r"""Create a new workforce pool under an organization.

  Creates a workforce pool under an organization given a valid organization ID.

  ## EXAMPLES

  The following command creates a workforce pool with ID ``my-workforce-pool''
  in the organization ``12345'':

    $ {command} my-workforce-pool --organization=12345

  The following command creates a workforce pool with ID ``my-workforce-pool''
  with explicit values for all required and optional parameters:

    $ {command} my-workforce-pool --organization=12345 --location=global
    --display-name="My Workforce Pool" --description="My workforce pool
    description." --session-duration="7200s" --disabled
  """

  @staticmethod
  def Args(parser):
    workforce_pool_data = yaml_data.ResourceYAMLData.FromPath(
        'iam.positional_workforce_pool')
    concept_parsers.ConceptParser.ForResource(
        'workforce_pool',
        concepts.ResourceSpec.FromYaml(workforce_pool_data.GetData()),
        'The workforce pool to create.',
        required=True).AddToParser(parser)
    flags.AddParentFlags(parser, 'create')
    parser.add_argument(
        '--display-name',
        help=('A display name for the workforce pool. Cannot exceed 32 ' +
              'characters in length.')
    )
    parser.add_argument(
        '--description',
        help=('A description for the workforce pool. Cannot exceed 256 ' +
              'characters in length.')
    )
    parser.add_argument(
        '--disabled',
        action='store_true',
        help='Whether or not the workforce pool is disabled.')
    parser.add_argument(
        '--session-duration',
        help=('How long the Google Cloud access tokens, console sign-in ' +
              'sessions, and gcloud sign-in sessions from this workforce ' +
              'pool are valid. Must be greater than 15 minutes (900s) and ' +
              'less than 12 hours (43200s). If not configured, minted ' +
              'credentials will have a default duration of one hour (3600s).')
    )

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    if not args.organization:
      raise gcloud_exceptions.RequiredArgumentException(
          '--organization',
          'Should specify the organization for workforce pools.')
    parent_name = iam_util.GetParentName(args.organization, None,
                                         'workforce pool')
    workforce_pool_ref = args.CONCEPTS.workforce_pool.Parse()
    new_workforce_pool = messages.WorkforcePool(
        parent=parent_name,
        displayName=args.display_name,
        description=args.description,
        disabled=args.disabled,
        sessionDuration=args.session_duration)
    lro_ref = client.locations_workforcePools.Create(
        messages.IamLocationsWorkforcePoolsCreateRequest(
            location=flags.ParseLocation(args),
            workforcePoolId=workforce_pool_ref.workforcePoolsId,
            workforcePool=new_workforce_pool))
    log.status.Print('Create request issued for: [{}]'.format(
        workforce_pool_ref.workforcePoolsId))
    log.status.Print('Check operation [{}] for status.'.format(lro_ref.name))
    return lro_ref
