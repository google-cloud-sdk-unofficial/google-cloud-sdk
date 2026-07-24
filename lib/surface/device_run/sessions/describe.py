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
"""Command to describe a Device Run session."""

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.device_run import resource_args
from googlecloudsdk.core import log


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe a Device Run session."""

  @staticmethod
  def Args(parser):
    resource_args.AddSessionResourceArg(parser, 'describe')
    parser.display_info.AddFormat(
        'table(job_name:label="JOB NAME", '
        'execution_name:label="EXECUTION NAME", '
        'result:label="EXECUTION RESULT")'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        default=False,
        help='Display full session details instead of the simplified summary.',
    )

  def Run(self, args):
    session_ref = args.CONCEPTS.session.Parse()
    client = device_run.SessionsClient(api_version='v1alpha')
    session = client.Get(session_ref)

    session_id = session_ref.Name()
    status_type = (
        str(session.sessionReport.status.statusType)
        if session.sessionReport and session.sessionReport.status
        else 'UNKNOWN'
    )

    if args.full:
      if not args.IsSpecified('format'):
        args.format = 'yaml'
      return session

    if status_type != 'DONE':
      log.status.Print(f'Session [{session_id}] status is [{status_type}].')

      if status_type == 'RUNNING':
        log.status.Print(session.sessionReport.status.progressMessages[0])
      return None

    result_type = session.sessionReport.result.resultType

    rows = []
    if session.sessionReport and session.sessionReport.jobReports:
      for job_report in session.sessionReport.jobReports:
        job_name = job_report.displayName
        if job_report.executionReports:
          for exec_report in job_report.executionReports:
            exec_name = exec_report.displayName
            result = str(exec_report.result.resultType)
            rows.append({
                'job_name': job_name,
                'execution_name': exec_name,
                'result': result,
            })
        else:
          result = str(job_report.result.resultType)
          rows.append({
              'job_name': job_name,
              'execution_name': '',
              'result': result,
          })

    # Print a blank line for spacing.
    log.status.Print()
    log.status.Print(
        f'Session [{session_id}] finished with result [{result_type}].'
    )

    return rows


Describe.detailed_help = {
    'DESCRIPTION':
        'Describe a Device Run session.',
    'EXAMPLES':
        """\
To describe a session named `my-session` in location `us-central1`, run:

  $ {command} my-session --location=us-central1

To display full details of a session, run:

  $ {command} my-session --location=us-central1 --full
""",
}

