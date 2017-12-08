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


class Config(base.Group):
  """View and edit Google Cloud SDK properties.

  Configuration properties are used to modify the behavior of gcloud and other
  Cloud SDK commands.  Most behavior can be controlled via the use of flags,
  but setting properties provides a way to maintain the same settings across
  command executions.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      '+AVAILABLE PROPERTIES': properties.VALUES.GetHelpString(),
  }
