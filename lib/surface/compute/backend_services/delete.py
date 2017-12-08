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

"""Command for deleting backend services."""

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.backend_services import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags


class Delete(base.Command):
  """Delete backend services.

    *{command}* deletes one or more backend services.
  """

  _BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
      resource_name='backend service',
      completion_resource_id='compute.backendServices',
      plural=True,
      global_collection='compute.backendServices')

  @staticmethod
  def Args(parser):
    Delete._BACKEND_SERVICE_ARG.AddArgument(parser)

  def Run(self, args):
    refs = Delete._BACKEND_SERVICE_ARG.ResolveAsResource(
        args, self.context['resources'], default_scope='global')
    utils.PromptForDeletion(refs)

    compute_client = self.context['client']

    requests = []
    for ref in refs:
      backend_service = client.BackendService(
          ref, compute_client=compute_client)
      requests.extend(backend_service.Delete(only_generate_request=True))

    errors = []
    resources = compute_client.MakeRequests(requests, errors)

    if errors:
      utils.RaiseToolException(errors)
    return resources
