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
"""Command to tail logs for an instance."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.logs import read as read_logs_lib
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import streaming
from googlecloudsdk.core import properties


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Tail(base.BinaryBackedCommand):
  """Tail logs for a Cloud Run instance."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          {command} tails log-entries for a particular
          Cloud Run instance in real time.  The log entries are formatted for
          consumption in a terminal.
          """
      ),
      'EXAMPLES': (
          """\
          To tail log entries for a Cloud Run instance, run:

            $ {command} my-instance

          To tail log entries with severity ERROR or higher, run:

            $ {command} my-instance --log-filter="severity>=ERROR"

          Detailed information about filters can be found at:
          [](https://cloud.google.com/logging/docs/view/advanced_filters)
          """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('instance', help='Name for a Cloud Run instance.')
    read_logs_lib.LogFilterArgs(parser)

  def Run(self, args):
    filters = []
    if args.IsSpecified('log_filter'):
      filters.append(args.log_filter)
    filters.append('resource.type=%s' % 'cloud_run_instance')
    filters.append('resource.labels.instance_name=%s' % args.instance)
    filters.append(
        'resource.labels.location=%s' % flags.GetRegion(args, prompt=True)
    )
    filters.append('severity>=DEFAULT')
    project_id = properties.VALUES.core.project.Get(required=True)
    filter_str = ' '.join(filters)
    command_executor = streaming.LogStreamingWrapper()
    response = command_executor(
        project_id=project_id, log_format='run', log_filter=filter_str
    )
    return self._DefaultOperationResponseHandler(response)
