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
"""Create Accelerator Network Profile command."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Accelerator Network Profile."""

  @classmethod
  def Args(cls, parser):
    _Args(parser, base.ReleaseTrack.GA)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)

    profile_ref = adapter.ParseAcceleratorNetworkProfile(args.name, location)

    operation_ref = adapter.CreateAcceleratorNetworkProfile(profile_ref, args)

    if args.async_:
      return adapter.GetOperation(operation_ref)

    adapter.WaitForOperation(
        operation_ref,
        f'Creating Accelerator Network Profile {profile_ref.Name()}',
        timeout_s=args.timeout,
    )

    profile = adapter.GetAcceleratorNetworkProfile(profile_ref)
    log.CreatedResource(profile_ref)
    return profile


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create an Accelerator Network Profile."""

  @classmethod
  def Args(cls, parser):
    _Args(parser, base.ReleaseTrack.BETA)


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create an Accelerator Network Profile."""

  @classmethod
  def Args(cls, parser):
    _Args(parser, base.ReleaseTrack.ALPHA)


def _Args(parser, _):
  """Shared arguments for across release tracks."""
  flags.AddAcceleratorNetworkProfileNameArg(
      parser, 'The name of the Accelerator Network Profile to create.'
  )
  # Hide the flags for all tracks for now until the backend is fully
  # ready and public.
  flags.AddAcceleratorNetworkProfileCreateFlags(parser, hidden=True)
  flags.AddAsyncFlag(parser)
  flags.AddTimeoutFlag(parser)


Create.detailed_help = {
    'DESCRIPTION': (
        """\
        *{command}* creates an Accelerator Network Profile in a Google
        Kubernetes Engine cluster.
        """
    ),
    'EXAMPLES': (
        """\
        To create a new Accelerator Network Profile "anp-1" in the
        cluster "sample-cluster" in zone "us-central1-a" for machine type
        "a3-ultragpu-8g", run:

          $ {command} anp-1 --cluster=sample-cluster --location=us-central1-a --auto-config-machine-type=a3-ultragpu-8g
        """
    ),
}
