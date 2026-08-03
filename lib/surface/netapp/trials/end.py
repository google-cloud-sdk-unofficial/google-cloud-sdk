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
"""Ends a Cloud NetApp Trial."""

from googlecloudsdk.api_lib.netapp.trials import client as trials_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp import util as command_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.Hidden
class End(base.Command):
  """End a Cloud NetApp Trial."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': (
          """\
          End a Cloud NetApp Trial.
          """
      ),
      'EXAMPLES': (
          """\
          The following command ends a Trial with reason upgraded:

              $ {command} --location=us-central1 --exit-reason=upgraded

          The following command ends a Trial with reason opt-out and reasons:

              $ {command} --location=us-central1 --exit-reason=opt-out --opt-out-reasons="reason"
          """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.AddEndTrialArgs(parser, End._RELEASE_TRACK)

  def Run(self, args):
    """Run the end command."""
    if args.IsSpecified('opt_out_reasons'):
      if args.exit_reason != 'opt-out':
        raise exceptions.InvalidArgumentException(
            '--opt-out-reasons',
            'Opt-out reasons can only be specified if --exit-reason is opt-out.'
        )

    location_ref = command_util.ParseLocationForTrials(
        args, self._RELEASE_TRACK
    )

    client = trials_client.TrialsClient(release_track=self._RELEASE_TRACK)

    end_reason_enum = arg_utils.ChoiceToEnum(
        args.exit_reason or 'opt-out',
        client.messages.EndTrialRequest.ExitReasonValueValuesEnum,
    )

    result = client.End(
        location_ref,
        exit_reason=end_reason_enum,
        opt_out_reasons=args.opt_out_reasons,
        async_=args.async_
    )
    if args.async_:
      log.status.Print('Ending of Trial in progress.')
    return result


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class EndAlpha(End):
  """End a Cloud NetApp Trial."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

  @staticmethod
  def Args(parser):
    flags.AddEndTrialArgs(parser, EndAlpha._RELEASE_TRACK)
