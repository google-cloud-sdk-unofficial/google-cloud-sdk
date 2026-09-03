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
"""API library for LookupConfiguredServicePerimeter."""

from googlecloudsdk.api_lib.accesscontextmanager import util
from googlecloudsdk.calliope import exceptions


class Client(object):
  """API client for LookupConfiguredServicePerimeter."""

  def __init__(self, client=None, messages=None, version=None):
    self.client = client or util.GetClient(version=version)
    self.messages = messages or self.client.MESSAGES_MODULE

  def LookupConfiguredServicePerimeter(self, resource):
    """Make API call to look up the configured service perimeter for a resource.

    Args:
      resource: The resource to look up, e.g. "projects/123" or "folders/456".

    Returns:
      LookupConfiguredServicePerimeterResponse message.
    """
    if not resource.startswith(('projects/', 'folders/')):
      raise exceptions.InvalidArgumentException(
          '--resource',
          'Resource must start with "projects/" or "folders/". Got: {}'.format(
              resource
          ),
      )

    collection = resource.split('/', 1)[0]
    service = getattr(self.client, collection)
    req_class = getattr(
        self.messages,
        'Accesscontextmanager{}LookupConfiguredServicePerimeterRequest'.format(
            collection.capitalize()
        ),
    )
    return service.LookupConfiguredServicePerimeter(
        req_class(resource=resource)
    )
