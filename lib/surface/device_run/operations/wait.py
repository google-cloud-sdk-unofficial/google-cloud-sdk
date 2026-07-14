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
"""Command to wait for Device Run operation completion."""

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.device_run import resource_args


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Wait(base.SilentCommand):
  """Wait for asynchronous operation to complete."""

  @staticmethod
  def Args(parser):
    resource_args.AddOperationResourceArg(parser, 'wait for')

  def Run(self, args):
    operation_ref = args.CONCEPTS.operation.Parse()
    client = device_run.OperationsClient(api_version='v1alpha')
    poller = device_run.DeviceRunOperationPoller(
        resource_service=None,
        operations_service=client.service,
        resource_ref=None,
    )
    waiter.WaitFor(
        poller,
        operation_ref,
        'Waiting for operation [{}] to complete.'.format(operation_ref.Name()),
    )
