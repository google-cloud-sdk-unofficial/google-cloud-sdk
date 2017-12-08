# Copyright 2015 Google Inc. All Rights Reserved.
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

"""'functions list' command."""

import sys
from apitools.base.py import exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as base_exceptions
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class List(base.ListCommand):
  """Lists Google Cloud Functions."""

  @staticmethod
  def Args(parser):
    regions_group = parser.add_mutually_exclusive_group()
    flags.AddDeprecatedRegionFlag(regions_group)
    regions_group.add_argument(
        '--regions',
        metavar='REGION',
        help=('Regions containing functions to list. By default functions from '
              'the region configured in functions/region property are listed. '
              'You can check value of the property with '
              '`gcloud config get-value functions/region` command.'),
        type=arg_parsers.ArgList(min_length=1),
        default=[])
    parser.display_info.AddFormat(
        'table(name.basename(), status, trigger():label=TRIGGER, '
        'name.scope("locations").segment(0):label=REGION)')

  def Run(self, args):
    client = util.GetApiClientInstance()
    messages = util.GetApiMessagesModule()
    locations = []
    if args.regions:
      locations = args.regions
    if args.region:
      locations += [args.region]
    if not locations:
      locations = ['-']
    project = properties.VALUES.core.project.GetOrFail()
    limit = args.limit

    return self._YieldFromLocations(locations, project, limit, messages, client)

  def _YieldFromLocations(self, locations, project, limit, messages, client):
    for location in locations:
      location_ref = resources.REGISTRY.Parse(
          location,
          params={'projectsId': project},
          collection='cloudfunctions.projects.locations')
      for function in self._YieldFromLocation(
          location_ref, limit, messages, client):
        yield function

  def _YieldFromLocation(self, location_ref, limit, messages, client):
    list_generator = list_pager.YieldFromList(
        service=client.projects_locations_functions,
        request=self.BuildRequest(location_ref, messages),
        limit=limit, field='functions',
        batch_size_attribute='pageSize')
    # Decorators (e.g. util.CatchHTTPErrorRaiseHTTPException) don't work
    # for generators. We have to catch the exception above the iteration loop,
    # but inside the function.
    try:
      for item in list_generator:
        yield item
    except exceptions.HttpError as error:
      msg = util.GetHttpErrorMessage(error)
      unused_type, unused_value, traceback = sys.exc_info()
      raise base_exceptions.HttpException, msg, traceback

  def BuildRequest(self, location_ref, messages):
    return messages.CloudfunctionsProjectsLocationsFunctionsListRequest(
        parent=location_ref.RelativeName())
