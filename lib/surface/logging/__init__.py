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

"""The super-group for the logging CLI."""

import argparse
from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources
from googlecloudsdk.third_party.apis.logging import v1beta3
from googlecloudsdk.third_party.apis.logging import v2beta1


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Logging(base.Group):
  """Manage Google Cloud Logging."""

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: The current context.
      args: The argparse namespace given to the corresponding .Run() invocation.

    Returns:
      The updated context.
    """
    url = properties.VALUES.api_endpoint_overrides.logging.Get()

    # All logging collections use projectId, so we can set a default value.
    resources.SetParamDefault(
        api='logging', collection=None, param='projectsId',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))

    client_v1beta3 = v1beta3.LoggingV1beta3(
        url=url,
        http=self.Http(),
        get_credentials=False)

    context['logging_client_v1beta3'] = client_v1beta3
    context['logging_messages_v1beta3'] = v1beta3

    client_v2beta1 = v2beta1.LoggingV2beta1(
        url=url,
        http=self.Http(),
        get_credentials=False)

    context['logging_client_v2beta1'] = client_v2beta1
    context['logging_messages_v2beta1'] = v2beta1

    context['logging_resources'] = resources
    return context
