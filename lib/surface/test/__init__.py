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

"""The main command group for gcloud test."""

import argparse

from googlecloudsdk.api_lib.test import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Test(base.Group):
  """Interact with Firebase Test Lab.

  Explore devices and OS versions available as test targets, run tests, monitor
  test progress, and view detailed test results.
  """

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: {str:object}, The current context, which is a set of key-value
          pairs that can be used for common initialization among commands.
      args: argparse.Namespace: The same Namespace given to the corresponding
          .Run() invocation.

    Returns:
      The refined command context.
    """
    # Get service endpoints and ensure they are compatible with each other
    testing_url = properties.VALUES.api_endpoint_overrides.testing.Get()
    toolresults_url = properties.VALUES.api_endpoint_overrides.toolresults.Get()
    log.info('Test Service endpoint: [{0}]'.format(testing_url))
    log.info('Tool Results endpoint: [{0}]'.format(toolresults_url))
    if ((toolresults_url is None or 'apis.com/toolresults' in toolresults_url)
        != (testing_url is None or 'testing.googleapis' in testing_url)):
      raise exceptions.ToolException(
          'Service endpoints [{0}] and [{1}] are not compatible.'
          .format(testing_url, toolresults_url))

    # Create the client for the Testing service.
    context['testing_client'] = apis.GetClientInstance('testing', 'v1')
    context['testing_messages'] = apis.GetMessagesModule('testing', 'v1')

    # Create the client for the Tool Results service.
    context['toolresults_client'] = apis.GetClientInstance(
        'toolresults', 'v1beta3')
    context['toolresults_messages'] = apis.GetMessagesModule(
        'toolresults', 'v1beta3')

    # Create the client for the Storage service.
    context['storage_client'] = apis.GetClientInstance('storage', 'v1')

    log.status.Print(
        '\nHave questions, feedback, or issues? Get support by '
        'visiting:\n  https://firebase.google.com/support/\n')

    return context
