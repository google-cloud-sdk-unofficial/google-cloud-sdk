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
"""Command to wait for a Device Run session to complete."""

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.device_run import reports
from googlecloudsdk.command_lib.device_run import resource_args
from googlecloudsdk.command_lib.device_run import session_submit_ops
from googlecloudsdk.core import log


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Wait(base.DescribeCommand):
  """Wait for a Device Run session to complete."""

  @staticmethod
  def Args(parser):
    resource_args.AddSessionResourceArg(parser, 'wait for')
    parser.display_info.AddFormat(
        'table(job_name:label="JOB NAME", '
        'execution_name:label="EXECUTION NAME", '
        'result:label="EXECUTION RESULT")'
    )

  def Run(self, args):
    session_ref = args.CONCEPTS.session.Parse()
    client = device_run.SessionsClient(api_version='v1alpha')
    poller = device_run.DeviceRunSessionPoller(client)

    session = device_run.WaitForSession(
        poller,
        session_ref,
        'Waiting for session [{}] to complete.'.format(session_ref.Name()),
    )

    session_id = session_ref.Name()

    result_type = session.sessionReport.result.resultType
    rows = reports.ExtractSessionReportRows(session.sessionReport)

    log.status.Print(
        f'Session [{session_id}] finished with result [{result_type}].'
    )

    if (
        session.sessionConfig
        and session.sessionConfig.outputDirectoryConfig
        and session.sessionConfig.outputDirectoryConfig.gcsOutputDirectory
    ):
      session_submit_ops.PrintResultFilesLink(
          session.sessionConfig.outputDirectoryConfig.gcsOutputDirectory.path,
          session_id,
          is_completed=True,
      )

    return rows


Wait.detailed_help = {
    'DESCRIPTION': 'Wait for a Device Run session to complete.',
    'EXAMPLES': (
        """\
To wait for a session named `my-session` in location `us-central1` to complete, run:

  $ {command} my-session --location=us-central1
"""
    ),
}
