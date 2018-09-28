# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Import cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core.util import files

SCHEMA_PATH = 'v1beta2/Cluster.yaml'


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Import(base.UpdateCommand):
  """Import a cluster.

  This will create a new cluster with the given configuration. If a cluster with
  this name already exists, an error will be thrown.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='The name of the cluster to import.')
    flags.AddClusterSourceFlag(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    # 30m is backend timeout + 5m for safety buffer.
    flags.AddTimeoutFlag(parser, default='35m')

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    msgs = dataproc.messages

    if args.source:
      with files.FileReader(args.source) as stream:
        cluster = util.ReadYaml(
            message_type=msgs.Cluster, stream=stream, schema_path=SCHEMA_PATH)
    else:
      cluster = util.ReadYaml(
          message_type=msgs.Cluster, stream=sys.stdin, schema_path=SCHEMA_PATH)

    cluster_ref = util.ParseCluster(args.name, dataproc)
    cluster.clusterName = cluster_ref.clusterName
    cluster.projectId = cluster_ref.projectId

    # Import only supports create, not update (for now).
    return clusters.CreateCluster(dataproc, cluster, args.async, args.timeout)
