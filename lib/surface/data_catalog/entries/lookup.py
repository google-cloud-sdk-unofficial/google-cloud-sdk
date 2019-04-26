# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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

"""Lookup entry command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_catalog import util


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Lookup(base.DescribeCommand):
  # pylint: disable=line-too-long
  """Lookup a Cloud Data Catalog entry by its target name.

  ## EXAMPLES

  To lookup the entry for a BigQuery table by its Google Cloud Platform resource
  name, run:

    $ {command} //bigquery.googleapis.com/projects/project1/datasets/dataset1/tables/table1

  To lookup the entry for a BigQuery table by its SQL name, run:

    $ {command} bigquery.project1.dataset1.table1
  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'resource',
        metavar='RESOURCE',
        help='The name of the target resource to lookup. This can be either '
             'the Google Cloud Platform resource name or the SQL name of a '
             'Google Cloud Platform resource.')

  def Run(self, args):
    client = util.GetClientInstance()
    messages = util.GetMessagesModule()
    request = messages.DatacatalogEntriesLookupRequest()
    if args.resource.startswith('//'):
      request.linkedResource = args.resource
    else:
      request.sqlResource = args.resource

    return client.entries.Lookup(request)
