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
"""Shared reporting utilities for Device Run commands."""


def YieldSessionReportRows(session_report):
  """Yields table rows from a SessionReport message.

  Args:
    session_report: messages.SessionReport, the session report message to parse.

  Yields:
    dict: A row dictionary containing 'job_name', 'execution_name', and
      'result' keys.
  """
  if not session_report or not session_report.jobReports:
    return

  for job_report in session_report.jobReports:
    job_name = job_report.displayName or ''
    if job_report.executionReports:
      for exec_report in job_report.executionReports:
        exec_name = exec_report.displayName or ''
        result = (
            str(exec_report.result.resultType)
            if exec_report.result and exec_report.result.resultType
            else ''
        )
        if result != 'PASSED':
          if exec_report.status and exec_report.status.progressMessages:
            latest_progress = exec_report.status.progressMessages[-1]
            if latest_progress:
              if result:
                result = f'{result}: {latest_progress}'
              else:
                result = latest_progress
        yield {
            'job_name': job_name,
            'execution_name': exec_name,
            'result': result,
        }
    else:
      result = (
          str(job_report.result.resultType)
          if job_report.result and job_report.result.resultType
          else ''
      )
      if result != 'PASSED':
        if job_report.status and job_report.status.progressMessages:
          latest_progress = job_report.status.progressMessages[-1]
          if latest_progress:
            if result:
              result = f'{result}: {latest_progress}'
            else:
              result = latest_progress
      yield {
          'job_name': job_name,
          'execution_name': '',
          'result': result,
      }


def ExtractSessionReportRows(session_report):
  """Extracts table rows from a SessionReport message.

  Args:
    session_report: messages.SessionReport, the session report message to parse.

  Returns:
    list[dict]: A list of row dictionaries containing 'job_name',
      'execution_name', and 'result' keys.
  """
  return sorted(
      YieldSessionReportRows(session_report),
      key=lambda x: (x.get('job_name', ''), x.get('execution_name', '')),
  )

