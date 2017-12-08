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
"""bigtable instances list command."""

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class ListInstances(base.ListCommand):
  """List existing Bigtable instances."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    pass

  @util.MapHttpError
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    cli = util.GetAdminClient()
    msg = util.GetAdminMessages().BigtableadminProjectsInstancesListRequest(
        projectsId=properties.VALUES.core.project.Get())
    instances = cli.projects_instances.List(msg).instances
    return instances

  def Collection(self):
    return 'bigtable.instances.list'
