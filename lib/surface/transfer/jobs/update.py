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
"""Command to update transfer jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transfer import jobs_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer import jobs_apitools_util
from googlecloudsdk.command_lib.transfer import jobs_flag_util


def _clear_fields(args, job):
  """Removes fields from TransferJob based on clear flags."""
  if args.clear_description:
    job.description = None
  if args.clear_source_creds_file:
    if getattr(job.transferSpec, 'awsS3DataSource', None):
      job.transferSpec.awsS3DataSource.awsAccessKey = None
    if getattr(job.transferSpec, 'azureBlobStorageDataSource', None):
      job.transferSpec.azureBlobStorageDataSource.azureCredentials = None
  if args.clear_schedule:
    job.schedule = None
  if args.clear_include_prefixes:
    job.transferSpec.objectConditions.includePrefixes = []
  if args.clear_exclude_prefixes:
    job.transferSpec.objectConditions.excludePrefixes = []
  if args.clear_include_modified_before_absolute:
    job.transferSpec.objectConditions.lastModifiedBefore = None
  if args.clear_include_modified_after_absolute:
    job.transferSpec.objectConditions.lastModifiedSince = None
  if args.clear_include_modified_before_relative:
    job.transferSpec.objectConditions.minTimeElapsedSinceLastModification = None
  if args.clear_include_modified_after_relative:
    job.transferSpec.objectConditions.maxTimeElapsedSinceLastModification = None
  if args.clear_delete_from:
    job.transferSpec.transferOptions.deleteObjectsFromSourceAfterTransfer = None
    job.transferSpec.transferOptions.deleteObjectsUniqueInSink = None
  if args.clear_notification_config:
    job.notificationConfig = None
  if args.clear_notification_event_types:
    job.notificationConfig.eventTypes = []


class Update(base.Command):
  """Update a Transfer Service transfer job."""

  # pylint:disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      Update a Transfer Service transfer job.
      """,
      'EXAMPLES':
          """\
      To disable transfer job 'foo', run:

        $ {command} foo --status=disabled

      To remove the schedule for transfer job 'foo' so that it will only run
      when you manually start it, run:

        $ {command} foo --clear-schedule

      To clear the values from the `include=prefixes` object condition in
      transfer job 'foo', run:

        $ {command} foo --clear-include-prefixes
      """
  }

  @staticmethod
  def Args(parser):
    jobs_flag_util.setup_parser(parser, is_update=True)

  def Run(self, args):
    client = apis.GetClientInstance('storagetransfer', 'v1')
    messages = apis.GetMessagesModule('storagetransfer', 'v1')

    existing_job = jobs_util.api_get(args.name)
    _clear_fields(args, existing_job)

    return client.transferJobs.Patch(
        jobs_apitools_util.generate_transfer_job_message(
            args, messages, existing_job=existing_job))
