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
"""Command for describing a Device Run software version."""

import collections
from typing import Any

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.device_run import resource_args


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a Device Run software version."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    resource_args.AddSoftwareVersionResourceArg(parser, 'describe')

  def Run(self, args: parser_extensions.Namespace) -> dict[str, Any]:
    software_version_ref = args.CONCEPTS.software_version.Parse()
    client = device_run.SoftwareVersionsClient(api_version='v1alpha')
    software_version = client.Get(software_version_ref)

    summary = collections.OrderedDict()
    summary['id'] = software_version_ref.Name()
    summary['name'] = software_version.displayName or ''
    summary['version'] = software_version.version or ''
    if software_version.softwareType is not None:
      summary['softwareType'] = str(software_version.softwareType)
    if software_version.isDefault is not None:
      summary['isDefault'] = software_version.isDefault
    if software_version.lifecycle:
      lifecycle_dict = collections.OrderedDict()
      if software_version.lifecycle.state is not None:
        lifecycle_dict['state'] = str(software_version.lifecycle.state)
      if software_version.lifecycle.removalDate:
        d = software_version.lifecycle.removalDate
        lifecycle_dict['removalDate'] = (
            f'{d.year:04d}-{d.month:02d}-{d.day:02d}'
        )
      if lifecycle_dict:
        summary['lifecycle'] = lifecycle_dict
    if (
        software_version.xcodeDetails
        and software_version.xcodeDetails.supportedIosVersions
    ):
      summary['supportedIosVersions'] = list(
          software_version.xcodeDetails.supportedIosVersions
      )

    return summary


Describe.detailed_help = {
    'DESCRIPTION': 'Describe a Device Run software version.',
    'EXAMPLES': """\
The following command describes the Device Run software version
`orchestrator-1-4-1`:

  $ {command} orchestrator-1-4-1
""",
}
