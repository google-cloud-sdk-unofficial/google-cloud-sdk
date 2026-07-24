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
"""Delete Accelerator Network Profile command."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete an Accelerator Network Profile."""

  @classmethod
  def Args(cls, parser):
    _Args(parser, base.ReleaseTrack.GA)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)

    profile_ref = adapter.ParseAcceleratorNetworkProfile(args.name, location)

    console_io.PromptContinue(
        message=(
            'The following Accelerator Network Profile will be deleted.\n'
            '[{name}] in [{location}]'
        ).format(
            name=profile_ref.Name(),
            location=profile_ref.locationsId,
        ),
        throw_if_unattended=True,
        cancel_on_no=True,
    )

    try:
      operation_ref = adapter.DeleteAcceleratorNetworkProfile(profile_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    if args.async_:
      return adapter.GetOperation(operation_ref)

    adapter.WaitForOperation(
        operation_ref,
        f'Deleting Accelerator Network Profile {profile_ref.Name()}',
        timeout_s=args.timeout,
    )

    log.DeletedResource(profile_ref)
    return operation_ref


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Delete an Accelerator Network Profile."""

  @classmethod
  def Args(cls, parser):
    _Args(parser, base.ReleaseTrack.BETA)


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(Delete):
  """Delete an Accelerator Network Profile."""

  @classmethod
  def Args(cls, parser):
    _Args(parser, base.ReleaseTrack.ALPHA)


def _Args(parser, _):
  """Shared arguments for across release tracks."""
  flags.AddAcceleratorNetworkProfileNameArg(
      parser, 'The name of the Accelerator Network Profile to delete.'
  )
  # Hide the flags for all tracks for now until the backend is fully
  # ready and public.
  flags.AddAsyncFlag(parser)
  flags.AddTimeoutFlag(parser)

Delete.detailed_help = {
    'DESCRIPTION': (
        """\
        *{command}* deletes a location-scoped Accelerator Network Profile.
        """
    ),
    'EXAMPLES': (
        """\
        To delete the Accelerator Network Profile `anp-1` in zone
        `us-central1-a`, run:

          $ {command} anp-1 --location=us-central1-a
        """
    ),
}
