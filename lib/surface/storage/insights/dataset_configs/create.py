# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Implementation of create command for insights dataset config."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create a new dataset config for insights."""

  detailed_help = {
      'DESCRIPTION': """
       Create a new dataset config for insights.
      """,
      'EXAMPLES': """
      To create a dataset config with config name as "my-config" in location
      "us-central1" and project numbers "project_num1" and "project_num2"
      which comes under organization "google":

         $ {command} my-config --location=us-central1
         --source-projects=project_num1,project_num2 --organization=google

      To create the dataset config, that automatically addes new buckets into
      config:

         $ {command} my-config --location=us-central1
         --source-projects=project_num1,project_num2 --organization=google
         --auto-add-new-buckets
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'DATASET_CONFIG_NAME',
        type=str,
        help='Provide human readable config name.',
    )
    source_projects_group = parser.add_group(
        mutex=True,
        required=True,
        help=(
            'List of source project numbers or the file containing list of'
            ' project numbers.'
        ),
    )
    source_projects_group.add_argument(
        '--source-projects',
        type=arg_parsers.ArgList(),
        metavar='SOURCE_PROJECT_NUMBERS',
        help='List of source project numbers.',
    )
    source_projects_group.add_argument(
        '--source-projects-file',
        type=str,
        metavar='SOURCE_PROJECT_NUMBERS_IN_FILE',
        help='File containing list of source project numbers.',
    )
    parser.add_argument(
        '--organization',
        type=str,
        required=True,
        metavar='SOURCE_ORG_NUMBER',
        help='Provide the source organization number.',
    )
    parser.add_argument(
        '--identity',
        type=str,
        metavar='IDENTITY_TYPE',
        choices=['IDENTITY_TYPE_PER_CONFIG', 'IDENTITY_TYPE_PER_PROJECT'],
        default='IDENTITY_TYPE_PER_CONFIG',
        help='The type of service account used in the dataset config.',
    )

    include_exclude_buckets_group = parser.add_group(
        mutex=True,
        help=(
            'Specify the list of buckets to be included or excluded, both a'
            ' list of bucket names and prefix regexes can be specified for'
            ' either include or exclude buckets.'
        ),
    )
    include_buckets_group = include_exclude_buckets_group.add_group(
        help='Specify the list of buckets to be included.',
    )
    include_buckets_group.add_argument(
        '--include-bucket-names',
        type=arg_parsers.ArgList(),
        metavar='BUCKETS_NAMES',
        help='List of bucket names be included.',
    )
    include_buckets_group.add_argument(
        '--include-bucket-prefix-regexes',
        type=arg_parsers.ArgList(),
        metavar='BUCKETS_REGEXES',
        help=(
            'List of bucket prefix regexes to be included. The dataset config'
            ' will include all the buckets that match with the prefix regex.'
            ' Examples of allowed prefix regex patterns can be'
            ' testbucket```*```, testbucket.```*```foo, testb.+foo```*``` . It'
            ' should follow syntax specified in google/re2 on GitHub. '
        ),
    )
    exclude_buckets_group = include_exclude_buckets_group.add_group(
        help='Specify the list of buckets to be excluded.',
    )
    exclude_buckets_group.add_argument(
        '--exclude-bucket-names',
        type=arg_parsers.ArgList(),
        metavar='BUCKETS_NAMES',
        help='List of bucket names to be excluded.',
    )
    exclude_buckets_group.add_argument(
        '--exclude-bucket-prefix-regexes',
        type=arg_parsers.ArgList(),
        metavar='BUCKETS_REGEXES',
        help=(
            'List of bucket prefix regexes to be excluded. Allowed regex'
            ' patterns are similar to those for the'
            ' --include-bucket-prefix-regexes flag.'
        ),
    )

    include_exclude_locations_group = parser.add_group(
        mutex=True,
        help=(
            'Specify the list of locations for source projects to be included'
            ' or excluded.'
        ),
    )
    include_exclude_locations_group.add_argument(
        '--include-source-locations',
        type=arg_parsers.ArgList(),
        metavar='LIST_OF_SOURCE_LOCATIONS',
        help='List of locations for projects to be included.',
    )
    include_exclude_locations_group.add_argument(
        '--exclude-source-locations',
        type=arg_parsers.ArgList(),
        metavar='LIST_OF_SOURCE_LOCATIONS',
        help='List of locations for projects to be excluded.',
    )

    parser.add_argument(
        '--auto-add-new-buckets',
        action='store_true',
        help=(
            'Automatically include any new buckets created within criteria'
            ' defined in the given config.'
        ),
    )
    flags.add_dataset_config_location_flag(parser)
    flags.add_dataset_config_create_update_flags(parser)

  def Run(self, args):
    # TODO(b/277754365): Add when API function available.
    raise NotImplementedError
