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

"""config command group."""

import argparse

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import config
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Config(base.Group):
  """View and edit Cloud SDK properties.

  A configuration is a set of properties that govern the behavior of gcloud
  and other tools in the Cloud SDK. The SDK provides a configuration named
  `default` whose initial properties are set when you run the `gcloud init`
  command. You can create any number of additional named configurations using
  `gcloud init` or `gcloud config configurations create`, and switch between
  configurations using `gcloud config configurations activate`.

  gcloud supports several flags that have the same effect as properties in
  a configuration (for example, gcloud supports both the `--project` flag and
  `project` property). Properties differ from flags in that flags affect command
  behavior on a per-invocation basis. Properties allow you to maintain the same
  settings across command executions.

  For more information on configurations, see `gcloud topic configurations`.

  ## AVAIABLE PROPERTIES

  {properties}
  """

  detailed_help = {
      'properties': properties.VALUES.GetHelpString(),
  }
