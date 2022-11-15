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
"""This file provides the implementation of the `functions list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.functions.v1 import util as api_v1_util
from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.command_lib.functions.v1.list import command
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _YieldFromLocations(locations, project, limit, messages, client):
  """Yield the functions from the given locations.

  Args:
    locations: List[str], list of gcp regions.
    project: str, Name of the API to modify. E.g. "cloudfunctions"
    limit: int, List messages limit.
    messages: module, Generated messages module.
    client: base_api.BaseApiClient, cloud functions client library.

  Yields:
    protorpc.message.Message, The resources listed by the service.
  """

  def _ReadAttrAndLogUnreachable(message, attribute):
    if message.unreachable:
      log.warning(
          'The following regions were fully or partially unreachable '
          'for query: %s', ', '.join(message.unreachable))
    return getattr(message, attribute)

  for location in locations:
    location_ref = resources.REGISTRY.Parse(
        location,
        params={'projectsId': project},
        collection='cloudfunctions.projects.locations')
    for function in list_pager.YieldFromList(
        service=client.projects_locations_functions,
        request=messages.CloudfunctionsProjectsLocationsFunctionsListRequest(
            parent=location_ref.RelativeName(), filter='environment="GEN_2"'),
        limit=limit,
        field='functions',
        batch_size_attribute='pageSize',
        get_field_func=_ReadAttrAndLogUnreachable):
      yield function


def Run(args, release_track):
  """List Google Cloud Functions."""
  client = api_util.GetClientInstance(release_track=release_track)
  messages = api_util.GetMessagesModule(release_track=release_track)
  project = properties.VALUES.core.project.GetOrFail()
  limit = args.limit

  list_v2_generator = _YieldFromLocations(args.regions, project, limit,
                                          messages, client)

  # v1 autopush and staging are the same in routing perspective, they share the
  # staging-cloudfunctions endpoint. The mixer will route the request to the
  # corresponding manager instances in autopush and staging.
  # autopush-cloudfunctions.sandbox.googleapi.com endpoint is not used by v1
  # at all, the GFE will route the traffic to 2nd Gen frontend even if you
  # specifed v1.  it's safe to assume when user specified this override,
  # they are tending to talk to v2 only
  if api_util.GetCloudFunctionsApiEnv() == api_util.ApiEnv.AUTOPUSH:
    return list_v2_generator
  # respect the user overrides for all other cases.
  else:
    client = api_v1_util.GetApiClientInstance()
    messages = api_v1_util.GetApiMessagesModule()
    list_v1_generator = command.YieldFromLocations(args.regions, project, limit,
                                                   messages, client)
    return itertools.chain(list_v2_generator, list_v1_generator)
