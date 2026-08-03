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
"""Commands for interacting with the Cloud NetApp Files Trials API resource."""

from googlecloudsdk.api_lib.netapp import constants
from googlecloudsdk.api_lib.netapp import util as netapp_api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


class TrialsClient(object):
  """Wrapper for working with Trials in the Cloud NetApp Files API Client."""

  def __init__(self, release_track=base.ReleaseTrack.ALPHA):
    self.release_track = release_track
    if self.release_track == base.ReleaseTrack.ALPHA:
      self._adapter = AlphaTrialsAdapter()
    elif self.release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaTrialsAdapter()
    else:
      raise ValueError('[{}] is not a valid API version.'.format(
          netapp_api_util.VERSION_MAP[release_track]))

  @property
  def client(self):
    return self._adapter.client

  @property
  def messages(self):
    return self._adapter.messages

  def WaitForOperation(self, operation_ref):
    """Waits on the long-running operation until the done field is True.

    Args:
      operation_ref: the operation reference.

    Raises:
      waiter.OperationError: if the operation contains an error.

    Returns:
      the 'response' field of the Operation.
    """
    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(
            self.client.projects_locations_operations),
        operation_ref,
        'Waiting for [{0}] to finish'.format(operation_ref.Name()))

  def Subscribe(self, parent_ref, async_):
    """Subscribes a Trial."""
    request = self.messages.NetappProjectsLocationsTrialSubscribeTrialRequest(
        parent=f'{parent_ref.RelativeName()}/trial',
        subscribeTrialRequest=self.messages.SubscribeTrialRequest(),
    )
    subscribe_op = self.client.projects_locations_trial.SubscribeTrial(request)
    if async_:
      return subscribe_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        subscribe_op.name, collection=constants.OPERATIONS_COLLECTION)
    return self.WaitForOperation(operation_ref)

  def Get(self, parent_ref):
    """Gets a Trial."""
    request = self.messages.NetappProjectsLocationsGetTrialRequest(
        name=f'{parent_ref.RelativeName()}/trial'
    )
    return self.client.projects_locations.GetTrial(request)

  def End(self, parent_ref, exit_reason, opt_out_reasons, async_):
    """Ends a Trial."""
    end_trial_request = self.messages.EndTrialRequest(
        exitReason=exit_reason,
        optOutReasons=opt_out_reasons or []
    )
    request = self.messages.NetappProjectsLocationsTrialEndTrialRequest(
        name=f'{parent_ref.RelativeName()}/trial',
        endTrialRequest=end_trial_request,
    )
    end_op = self.client.projects_locations_trial.EndTrial(request)
    if async_:
      return end_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        end_op.name, collection=constants.OPERATIONS_COLLECTION)
    return self.WaitForOperation(operation_ref)


class BetaTrialsAdapter(object):
  """Adapter for the Beta Cloud NetApp Files API for Trials."""

  def __init__(self):
    self.release_track = base.ReleaseTrack.BETA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )


class AlphaTrialsAdapter(BetaTrialsAdapter):
  """Adapter for the Alpha Cloud NetApp Files API for Trials."""

  def __init__(self):
    super(AlphaTrialsAdapter, self).__init__()
    self.release_track = base.ReleaseTrack.ALPHA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )
