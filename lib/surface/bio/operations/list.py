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

"""Command to list bio operations associated with a project."""


from googlecloudsdk.api_lib.bio import bio
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bio import util as command_lib_util
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List bio operations associated with a project.

  You can specify the maximum number of operations to list using the `--limit`
  flag.

  ## EXAMPLES

  The following command lists a maximum of five operations:

    $ {command} --limit=5
  """

  def Collection(self):
    return command_lib_util.OPERATIONS_COLLECTION

  def Run(self, args):
    """Run the list command."""

    return bio.Operations(properties.VALUES.core.project.Get()).List()
