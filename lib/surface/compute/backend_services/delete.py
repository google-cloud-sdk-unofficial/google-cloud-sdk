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

from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.backend_services import flags


class Delete(base.Command):
  """Delete backend services.

    *{command}* deletes one or more backend services.
  """

  @staticmethod
  def Args(parser):
    flags.AddBackendServiceName(parser, is_plural=True)

  def Run(self, args):
    refs = [
        self.context['resources'].Parse(backend_service_name,
                                        collection='compute.backendServices')
        for backend_service_name in args.names]
    utils.PromptForDeletion(refs)

    client = self.context['compute']
    messages = client.MESSAGES_MODULE

    requests = []
    for ref in refs:
      request = (
          client.backendServices,
          'Delete',
          messages.ComputeBackendServicesDeleteRequest(
              backendService=ref.Name(),
              project=ref.project))
      requests.append(request)

    errors = []
    resources = list(request_helper.MakeRequests(
        requests=requests,
        http=client.http,
        batch_url=self.context['batch-url'],
        errors=errors,
        custom_get_requests=None))

    if errors:
      utils.RaiseToolException(errors)
    return resources
