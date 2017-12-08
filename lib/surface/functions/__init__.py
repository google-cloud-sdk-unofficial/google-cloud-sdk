# Copyright 2015 Google Inc. All Rights Reserved.
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

"""The main command group for Google Cloud Functions."""

import argparse

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Functions(base.Group):
  """Manages Google Cloud Functions."""

  @staticmethod
  def Args(parser):
    """Add command flags that are global to this group.

    Per command flags should be added in the Args() method of that specific
    command.

    Args:
      parser: argparse.ArgumentParser, This is a standard argparser parser with
        which you can register arguments.  See the public argparse documentation
        for its capabilities.
    """
    parser.add_argument(
        '--region',
        default='us-central1',
        help='The compute region (e.g. us-central1) to use')

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: The current context.
      args: The argparse namespace given to the corresponding .Run() invocation.

    Returns:
      The updated context.
    """
    context['functions_client'] = apis.GetClientInstance(
        'cloudfunctions', 'v1beta2')
    context['functions_messages'] = apis.GetMessagesModule(
        'cloudfunctions', 'v1beta2')
    context['registry'] = resources.REGISTRY
    return context
