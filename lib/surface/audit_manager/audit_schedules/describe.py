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
"""Command to describe an Audit Schedule."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.audit_manager import audit_schedules
from googlecloudsdk.api_lib.audit_manager import constants
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.audit_manager import exception_utils
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties

_DETAILED_HELP = {
    "DESCRIPTION": "Describe an Audit Schedule.",
    "EXAMPLES": (
        """ \
        To describe an Audit Schedule, run:

          $ {command} projects/123/locations/us-central1/auditSchedules/my-schedule
        """
    ),
}


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.RegionalEndpointsSupported
class Describe(base.DescribeCommand):
  """Describe Audit Schedule."""

  detailed_help = _DETAILED_HELP
  api_version = constants.ApiVersion.V1

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    parser.add_argument(
        "audit_schedule",
        help="Full resource name of the audit schedule.",
    )
    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    """Run the describe command."""
    client = audit_schedules.AuditSchedulesClient(api_version=self.api_version)

    try:
      return client.Get(
          args.audit_schedule,
      )
    except apitools_exceptions.HttpError as error:
      exc = exception_utils.AuditManagerError(error)
      core_exceptions.reraise(exc)


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
class DescribeAlpha(Describe):
  """Describe Audit Schedule."""

  api_version = constants.ApiVersion.V1_ALPHA
