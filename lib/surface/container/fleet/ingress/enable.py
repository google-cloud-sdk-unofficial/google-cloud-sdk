# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""The command to enable Multi-cluster Ingress Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap
import time

from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.features import info
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry


class Enable(base.EnableCommand):
  """Enable Multi-cluster Ingress Feature.

  This command enables Multi-cluster Ingress Feature in a fleet.

  ## EXAMPLES

  To enable the Ingress Feature, run:

    $ {command} --config-membership=CONFIG_MEMBERSHIP
  """

  feature_name = 'multiclusteringress'

  @classmethod
  def Args(cls, parser):
    if resources.UseRegionalMemberships(cls.ReleaseTrack()):
      resources.AddMembershipResourceArg(
          parser, flag_override='--config-membership')
    else:
      parser.add_argument(
          '--config-membership',
          type=str,
          help=textwrap.dedent("""\
              Membership resource representing the cluster which hosts
              the MultiClusterIngress and MultiClusterService
              CustomResourceDefinitions.
              """),
      )

  def Run(self, args):
    if resources.UseRegionalMemberships(self.ReleaseTrack()):
      config_membership = base.ParseMembership(
          args, prompt=True, flag_override='config_membership')
    else:
      if not args.config_membership:
        all_memberships = base.ListMemberships()
        if not all_memberships:
          raise exceptions.Error('No Memberships available in the fleet.')
        index = console_io.PromptChoice(
            options=all_memberships,
            message='Please specify a config membership:\n')
        config_membership = all_memberships[index]
      else:
        # Strip to the final path component to allow short and long names.
        # Assumes long names are for the same project and global location.
        # TODO(b/192580393): Use the resource args instead of this hack.
        config_membership = os.path.basename(args.config_membership)
      config_membership = self.MembershipResourceName(config_membership)

    # MCI requires MCSD. Enablement of the fleet feature for MCSD is taken care
    # of by CLH but we need to enable the OP API before that happens. If not,
    # CLH will return an error asking for the API to be enabled.
    mcsd_api = info.Get('multiclusterservicediscovery').api
    enable_api.EnableServiceIfDisabled(self.Project(), mcsd_api)

    f = self.messages.Feature(
        spec=self.messages.CommonFeatureSpec(
            multiclusteringress=self.messages.MultiClusterIngressFeatureSpec(
                configMembership=config_membership)))
    result = self.Enable(f)

    # We only want to poll for usability if everything above succeeded.
    if result is not None:
      self.PollForUsability()

  # Continuously poll the top-level Feature status until it has the "OK"
  # code. This ensures that MCI is actually usable and that the user gets
  # clear synchronous feedback on this.
  def PollForUsability(self):
    message = 'Waiting for controller to start...'
    aborted_message = 'Aborting wait for controller to start.\n'
    timeout = 120000
    timeout_message = ('Please use the `describe` command to check Feature'
                       'state for debugging information.\n')
    ok_code = self.messages.FeatureState.CodeValueValuesEnum.OK

    try:
      with progress_tracker.ProgressTracker(
          message, aborted_message=aborted_message) as tracker:

        # Sleeping before polling for usability ensures the Feature was created
        # in the backend.
        time.sleep(5)

        # Prints status update to console. We use the default spinning wheel.
        def _StatusUpdate(unused_result, unused_status):
          tracker.Tick()

        retryer = retry.Retryer(
            # It should take no more than 2 mins for the "OK" status to appear.
            max_wait_ms=timeout,
            # Wait no more than 1 seconds before retrying.
            wait_ceiling_ms=1000,
            status_update_func=_StatusUpdate)

        def _PollFunc():
          return self.GetFeature()

        def _IsNotDone(feature, unused_state):
          if feature.state is None or feature.state.state is None:
            return True
          return feature.state.state.code != ok_code

        return retryer.RetryOnResult(
            func=_PollFunc, should_retry_if=_IsNotDone, sleep_ms=500)

    except retry.WaitException:
      raise exceptions.Error(
          'Controller did not start in {} minutes. {}'.format(
              timeout / 60000, timeout_message))
