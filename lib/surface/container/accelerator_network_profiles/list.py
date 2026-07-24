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
"""List Accelerator Network Profiles command."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION': (
        """\
        *{command}* displays all Accelerator Network Profiles in Google
        Kubernetes Engine.
        """
    ),
    'EXAMPLES': (
        """\
        To list all Accelerator Network Profiles in a specific location, run:

          $ {command} --location=us-central1-a
        """
    ),
}


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Accelerator Network Profiles."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(util.ACCELERATOR_NETWORK_PROFILES_FORMAT)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args, required=True)
    project = properties.VALUES.core.project.Get(required=True)

    try:
      res = adapter.ListAcceleratorNetworkProfiles(project, location)
      return res.acceleratorNetworkProfiles
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT) from error


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Accelerator Network Profiles."""


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List Accelerator Network Profiles."""


List.detailed_help = DETAILED_HELP
