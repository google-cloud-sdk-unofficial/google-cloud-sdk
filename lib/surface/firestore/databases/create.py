# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command to create Cloud Firestore Database in Native mode."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import admin_api
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import create_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.log import logging

PRODUCT_NAME = 'Google Cloud Firestore Native'
LOCATION_HELP_TEXT = (
    'The location to create the {product_name} database within. Available '
    'locations are listed at '
    'https://cloud.google.com/firestore/docs/locations.'.format(
        product_name=PRODUCT_NAME))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.Command):
  """Create a Google Cloud Firestore Native database via Firestore API.

  'EXAMPLES':
  To create Cloud Firestore Native database in nam5.

      $ {command} --location=nam5

  To create Cloud Datastore Mode database in us-east1.

      $ {command} --location=us-east1 --type=datastore-mode

  To create Cloud Datastore Mode database in us-east1 with a databaseId foo.

      $ {command} foo --location=us-east1 --type=datastore-mode
  """

  def DatabaseType(self, database_type):
    if database_type == 'firestore-native':
      return admin_api.GetMessages(
      ).GoogleFirestoreAdminV1Database.TypeValueValuesEnum.FIRESTORE_NATIVE
    elif database_type == 'datastore-mode':
      return admin_api.GetMessages(
      ).GoogleFirestoreAdminV1Database.TypeValueValuesEnum.DATASTORE_MODE
    else:
      raise ValueError('invalid database type: {}'.format(database_type))

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return admin_api.CreateDatabase(project, args.location, args.database,
                                    self.DatabaseType(args.type))

  @staticmethod
  def Args(parser):
    parser.add_argument('--location', help=LOCATION_HELP_TEXT, required=True)
    parser.add_argument(
        '--type',
        help='The type of the database.',
        default='firestore-native',
        choices=['firestore-native', 'datastore-mode'],
    )
    parser.add_argument(
        'database',
        help="""The ID to use for the database, which will become the final
        component of the database's resource name. If database ID is not
        provided, (default) will be used as database ID.

        This value should be 4-63 characters. Valid characters are /[a-z][0-9]-/
        with first character a letter and the last a letter or a number. Must
        not be UUID-like /[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/.

        Using "(default)" database ID is also allowed.
        """,
        type=str,
        nargs='?',
        default='(default)',
    )


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Create(base.Command):
  """Create a Google Cloud Firestore Native database."""
  enum_value = core_apis.GetMessagesModule(
      'appengine', 'v1').Application.DatabaseTypeValueValuesEnum.CLOUD_FIRESTORE
  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To create Google Cloud Firestore Native database

              $ {command}

          To create an app in the nam5 region (multi-region), run:

              $ {command} --region=nam5

          To create an app in the us-east1 region,  run:

              $ {command} --region=us-east1
          """,
  }

  def Run(self, args):
    if args.region:
      location_map = {'us-central': 'nam5', 'europe-west': 'eur3'}
      if args.region in location_map:
        logging.warning('Warning: {region} is not a valid Firestore location. '
                        'Please use {location} instead.'.format(
                            region=args.region,
                            location=location_map[args.region]))

    region = args.region
    if args.region == 'nam5':
      region = 'us-central'
    elif args.region == 'eur3':
      region = 'europe-west'

    create_util.create(region, PRODUCT_NAME, self.enum_value)

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--region',
        help=(
            'The region to create the {product_name} database within. '
            'Use `gcloud app regions list` to list available regions.').format(
                product_name=PRODUCT_NAME))
