# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Command for getting health status of backend(s) in a backend service."""

from googlecloudsdk.api_lib.compute.backend_services import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags


class GetHealth(base.ListCommand):
  """Get backend health statuses from a backend service.

  *{command}* is used to request the current health status of
  instances in a backend service. Every group in the service
  is checked and the health status of each configured instance
  is printed.

  If a group contains names of instances that don't exist or
  instances that haven't yet been pushed to the load-balancing
  system, they will not show up. Those that are listed as
  ``HEALTHY'' are able to receive load-balanced traffic. Those that
  are marked as ``UNHEALTHY'' are either failing the configured
  health-check or not responding to it.

  Since the health checks are performed continuously and in
  a distributed manner, the state returned by this command is
  the most recent result of a vote of several redundant health
  checks. Backend services that do not have a valid global
  forwarding rule referencing it will not be health checked and
  so will have no health status.
  """

  _BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
      resource_name='backend service',
      completion_resource_id='compute.backendService',
      global_collection='compute.backendServices')

  @staticmethod
  def Args(parser):
    GetHealth._BACKEND_SERVICE_ARG.AddArgument(parser)

  def Run(self, args):
    """Returns a list of backendServiceGroupHealth objects."""
    if args.uri:
      args.uri = False
      self.SetFormat('value(status.healthStatus[].instance)')

    ref = GetHealth._BACKEND_SERVICE_ARG.ResolveAsResource(
        args, self.context['resources'], default_scope='global')

    backend_service = client.BackendService(
        ref, compute_client=self.context['client'])

    return backend_service.GetHealth()