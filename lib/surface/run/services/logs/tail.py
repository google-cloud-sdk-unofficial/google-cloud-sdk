# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to tail logs for a service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import logs as logs_util
from googlecloudsdk.api_lib.logging.formatter import FormatLog
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.logs import read as read_logs_lib
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Tail(base.Command):
  """Tail logs for a service."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {command} tails log-entries for a particular
          Cloud Run service in real time.  The log entries are formatted for
          consumption in a terminal.
          """,
      'SYNOPSIS':
          """\
          {command} (SERVICE)
          """,
      'FLAGS':
          """\
          --region=REGION
          Region of the Cloud Run service.
          If not specified, will take its value from the gcloud property
          "run/region" or prompt.
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('service', help='Name for a Cloud Run service.')
    read_logs_lib.LogFilterArgs(parser)

  def Run(self, args):
    filters = []
    if args.IsSpecified('log_filter'):
      filters.append(args.log_filter + ' \n')
    filters.append('resource.type = %s \n' % 'cloud_run_revision')
    filters.append('resource.labels.service_name = %s \n' % args.service)
    filters.append('resource.labels.location = %s \n' %
                   flags.GetRegion(args, prompt=False))
    filters.append('severity >= DEFAULT')
    parent = 'projects/{project_id}'.format(
        project_id=properties.VALUES.core.project.Get(required=True))
    filter_str = ''.join(str(filter) for filter in filters)
    tailer = logs_util.GetGCLLogTailer()
    logs = tailer.TailLogs([parent], filter_str)

    for log_line in logs:
      output_log = FormatLog(log_line)
      if output_log:
        log.out.Print(output_log)
