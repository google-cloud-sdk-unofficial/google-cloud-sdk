# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implements the command to list vulnerabilities from Artifact Registry."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from googlecloudsdk.api_lib.artifacts import exceptions as ar_exceptions
from googlecloudsdk.api_lib.artifacts.vulnerabilities import GetLatestScan
from googlecloudsdk.api_lib.artifacts.vulnerabilities import GetVulnerabilities
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import format_util
from googlecloudsdk.core import properties


DEFAULT_LIST_FORMAT = """\
     table[box, title="%TITLE%"](
      vulnerability.shortDescription:label=CVE,
      vulnerability.effectiveSeverity:label=EFFECTIVE_SEVERITY,
      vulnerability.cvssScore:label=CVSS:sort=-1:reverse,
      vulnerability.packageIssue.fixAvailable:label=FIX_AVAILABLE,
      vulnerability.vexAssessment.state:label=VEX_STATUS,
      vulnerability.packageIssue.affectedPackage:sort=3:label=PACKAGE,
      vulnerability.packageIssue.packageType:label=PACKAGE_TYPE,
      {}
    )
    """.format(format_util.CONTAINER_ANALYSIS_METADATA_FORMAT)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Command for listing vulnerabilities. To see all fields, use --format=json.
  """

  @staticmethod
  def Args(parser):
    flags.GetListURIArg().AddToParser(parser)
    flags.GetVulnerabilitiesOccurrenceFilterFlag().AddToParser(parser)
    parser.display_info.AddFlatten(['vulnerability.packageIssue'])
    return

  def Run(self, args):
    project = properties.VALUES.core.project.Get()
    occurrence_filter = args.occurrence_filter
    resource = self.replaceTags(args.URI)
    latest_scan = GetLatestScan(project, resource)
    self.setTitle(args, latest_scan)
    vulnerabilities = GetVulnerabilities(project, resource, occurrence_filter)
    vulnerabilities = list(vulnerabilities)
    if len(vulnerabilities) < 1:
      vulnerabilities = {}
    return vulnerabilities

  def replaceTags(self, original_uri):
    updated_uri = original_uri
    if not updated_uri.startswith('https://'):
      updated_uri = 'https://{}'.format(updated_uri)
    found = re.findall(docker_util.DOCKER_URI_REGEX, updated_uri)
    if found:
      resource_uri_str = found[0][2]
      _, version = docker_util.DockerUrlToVersion(resource_uri_str)
      docker_html_str_digest = 'https://{}'.format(version.GetDockerString())
      updated_uri = re.sub(
          docker_util.DOCKER_URI_REGEX,
          docker_html_str_digest,
          updated_uri,
          1,
      )
    if not found:
      raise ar_exceptions.InvalidInputValueError(
          'Received invalid URI {}'.format(original_uri)
      )
    return updated_uri

  def setTitle(self, args, latest_scan):
    title = ''
    if (
        not latest_scan
        or latest_scan.discovery is None
        or latest_scan.discovery.lastScanTime is None
    ):
      title = 'Scan status unknown'
    else:
      last_scan_time = latest_scan.discovery.lastScanTime[:-11]
      title = 'Latest scan was at {}'.format(last_scan_time)
    list_format = DEFAULT_LIST_FORMAT.replace('%TITLE%', title)
    args.GetDisplayInfo().AddFormat(list_format)
