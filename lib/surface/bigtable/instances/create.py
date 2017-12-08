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
"""bigtable instances create command."""

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import resources


class CreateInstance(base.CreateCommand):
  """Create a new Bigtable instance."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    (arguments.ArgAdder(parser).AddInstance()
     .AddInstanceDescription(required=True)
     .AddCluster(positional=False).AddClusterNodes(in_instance=True)
     .AddClusterStorage(in_instance=True).AddClusterZone(in_instance=True)
     .AddAsync())

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
    ref = resources.Parse(args.instance,
                          collection='bigtableadmin.projects.instances')
    msgs = util.GetAdminMessages()
    msg = msgs.BigtableadminProjectsInstancesCreateRequest(
        projectsId=ref.projectsId,
        createInstanceRequest=msgs.CreateInstanceRequest(
            instanceId=ref.Name(),
            instance=msgs.Instance(displayName=args.description),
            clusters=msgs.CreateInstanceRequest.ClustersValue(
                additionalProperties=[
                    msgs.CreateInstanceRequest.ClustersValue.AdditionalProperty(
                        key=args.cluster,
                        value=msgs.Cluster(
                            serveNodes=args.cluster_num_nodes,
                            defaultStorageType=(
                                msgs.Cluster.DefaultStorageTypeValueValuesEnum(
                                    args.cluster_storage_type)),
                            # TODO(user): switch location to resource
                            # when b/29566669 is fixed on API
                            location=util.LocationUrl(args.cluster_zone)))
                ])))
    result = cli.projects_instances.Create(msg)
    if not args.async:
      # TODO(user): enable this line when b/29563942 is fixed in apitools
      pass
      # util.WaitForOpV2(result, 'Creating instance')
    return result
