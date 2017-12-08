# Copyright 2016 Google Inc. All Rights Reserved.
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
"""List builds command."""

from apitools.base.py import list_pager

from googlecloudsdk.calliope import base
from googlecloudsdk.core import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times


# TODO(user): allow a longer threshold, set by property?
_ONGOING_THRESHOLD_SECONDS = 60*60*2  # 2 hours.


class List(base.ListCommand):
  """List builds."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--ongoing',
        help='Only list builds that are currently QUEUED or WORKING, and were '
             'created less than %d seconds ago.' % _ONGOING_THRESHOLD_SECONDS,
        action='store_true')
    base.LIMIT_FLAG.SetDefault(parser, 50)

  def Collection(self):
    return 'cloudbuild.projects.builds'

  # TODO(user,b/29048700): Until resolution of this bug, the error message
  # printed by gcloud (for 404s, eg) will be really terrible.
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      Some value that we want to have printed later.
    """

    client = core_apis.GetClientInstance('cloudbuild', 'v1')
    messages = core_apis.GetMessagesModule('cloudbuild', 'v1')

    if args.ongoing:
      tz = times.GetTimeZone('UTC')
      now = times.Now(tz)
      now_seconds = times.GetTimeStampFromDateTime(now)

    # We are wrapping list_pager.YieldFromList in another yield loop so that
    # we can use custom exit-early and filtering functionality. This code will
    # be simplified once the cloudbuild service supports server-side filtering.
    #
    # The exit-early is to ensure that, when listing ongoing builds, the command
    # doesn't page through the entire history of terminated builds to find out
    # that there weren't any. The build list will always be delivered in sorted
    # order with createTime descending.
    #
    # The custom filtering checks build.status to see if a build is ongoing or
    # not, and skips those that are terminated.
    #
    # We copy and decrement the limit, because otherwise YieldFromList would
    # not understand when to stop, due to skipping terminated builds.
    #
    # We cannot give YieldFromList a predicate, because it would not know that
    # it needs to stop paging after a certain time threshold - with no ongoing
    # builds it would page through the entire build history.

    limit = args.limit

    for build in list_pager.YieldFromList(
        client.projects_builds,
        messages.CloudbuildProjectsBuildsListRequest(
            pageSize=args.page_size,
            projectId=properties.VALUES.core.project.Get()),
        field='builds',
        batch_size_attribute='pageSize'):
      if args.ongoing:
        tz_create_time = build.createTime
        create_time = times.ParseDateTime(tz_create_time, tz)
        create_seconds = times.GetTimeStampFromDateTime(create_time)
        delta_seconds = now_seconds - create_seconds
        if delta_seconds > _ONGOING_THRESHOLD_SECONDS:
          break
        if build.status not in [
            messages.Build.StatusValueValuesEnum.QUEUED,
            messages.Build.StatusValueValuesEnum.WORKING]:
          continue
      yield build
      limit -= 1
      if limit == 0:
        break
