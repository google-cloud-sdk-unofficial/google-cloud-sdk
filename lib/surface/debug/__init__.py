# Copyright 2016 Google Inc. All Rights Reserved.
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

"""The main command group for the gcloud debug command group."""

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import store as c_store


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Debug(base.Group):
  """Commands for interacting with the Cloud Debugger.

  Commands that allow interacting with the Cloud Debugger to list and
  manipulate debug targets, snapshots, and logpoints.
  """

  detailed_help = {
      'EXAMPLES': """\
          To view all available debug targets, run:

              $ {command} targets list
              NAME           ID             DESCRIPTION
              default-test   gcp:1234:5678  myproject-test-9876543
              default-test2  gcp:9012:3456  myproject-test2-1234567

          To create a snapshot in a for a particular target:

              $ {command} snapshots create --target=default-test foo.py:12
              ...

          Note that if there is not a target with the exact name or ID
          specified, the target is treated as a regular expression to match
          against the name or description:

              $ {command} snapshots create --target=test foo.py:12
              ERROR: (gcloud.beta.debug.snapshots.create) Multiple possible
              targets found.
              Use the --target option to select one of the following targets:
                  default-test
                  default-test2

          In the above case, "test" matches both targets' names. Specifying
          'test$' would match only "default-test" (by name), while "9876" would
          match "default-test" by description.
       """
  }

  def Filter(self, context, args):
    """Initialize context for Cloud Debugger commands.

    Args:
      context: The current context.
      args: The argparse namespace that was specified on the CLI or API.

    Returns:
      The updated context.
    """
    resources.SetParamDefault(
        api='debug', collection=None, param='projectId',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))

    debug.DebugObject.InitializeApiClients()
