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

"""The command group for gcloud bigquery datasets.
"""

from googlecloudsdk.calliope import base


class Datasets(base.Group):
  """A group of subcommands for working with datasets.

  A dataset is a collection of related tables.
  """

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    The context is a dictionary into which you can insert whatever you like.
    The context is given to each command under this group.  You can do common
    initialization here and insert it into the context for later use.  Of course
    you can also do common initialization as a function that can be called in a
    library.

    Args:
      context: {str:object}, A set of key-value pairs that can be used for
          common initialization among commands.
      args: argparse.Namespace: The same namespace given to the corresponding
          .Run() invocation.
    """
    pass
