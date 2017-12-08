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

"""Service Registry operations sub-group."""

from googlecloudsdk.calliope import base


class Operations(base.Group):
  """Commands for Service Registry operations.

  Commands to inspect and monitor Service Registry operations.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To print out a list of operations with some summary information about each:

            $ {command} list

          To limit the number of endpoints returned:

            $ {command} list --limit=100
          """,
  }
