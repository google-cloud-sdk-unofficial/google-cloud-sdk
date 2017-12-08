# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Command to print version information for Cloud SDK components.
"""


from googlecloudsdk.calliope import base
from googlecloudsdk.core import config
from googlecloudsdk.core.updater import update_manager


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Version(base.Command):
  """Print version information for Cloud SDK components.

     This command prints version information for each installed Cloud SDK
     component and prints a message if updates are available.
  """

  def Run(self, args):
    if config.Paths().sdk_root:
      # Components are only valid if this is a built Cloud SDK.
      manager = update_manager.UpdateManager()
      versions = dict(manager.GetCurrentVersionsInformation())
    else:
      versions = {}
    versions['Google Cloud SDK'] = config.CLOUD_SDK_VERSION
    return versions

  def Format(self, args):
    return 'flattened[no-pad,separator=" "]'
