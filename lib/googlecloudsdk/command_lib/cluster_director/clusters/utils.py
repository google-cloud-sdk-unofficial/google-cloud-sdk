# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Utility functions for clusters command group."""

from __future__ import annotations


from typing import Any, Optional, Set, Tuple

from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.cluster_director.clusters import _compute
from googlecloudsdk.command_lib.cluster_director.clusters import _networks
from googlecloudsdk.command_lib.cluster_director.clusters import _orchestrator
from googlecloudsdk.command_lib.cluster_director.clusters import _storage

from googlecloudsdk.command_lib.cluster_director.clusters import flag_types
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddClusterNameArgToParser(parser, api_version=None):
  """Adds a cluster name resource argument."""
  cluster_data = yaml_data.ResourceYAMLData.FromPath(
      "cluster_director.clusters.projects_locations_clusters"
  )
  resource_spec = concepts.ResourceSpec.FromYaml(
      cluster_data.GetData(), is_positional=True, api_version=api_version
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name="cluster",
      concept_spec=resource_spec,
      required=True,
      group_help="""
        Name of the cluster resource.
        Formats: cluster | projects/{project}/locations/{locations}/clusters/{cluster}
      """,
  )
  concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def GetClusterFlagType(api_version: Optional[str] = None) -> dict[str, Any]:  # pylint: disable=g-bare-generic
  """Returns the cluster spec for the given API version."""
  return flag_types.FlagTypes(api_version).GetClusterFlagType()


class ClusterUtil:
  """Represents a cluster utility class."""

  def __init__(
      self,
      args: Any,
      message_module: Any,
      existing_cluster: Optional[Any] = None,
      update_mask: Optional[Set[str]] = None,
  ):
    """Initializes the cluster utility class."""
    self.args = args
    self.message_module = message_module
    self.cluster_ref = self.args.CONCEPTS.cluster.Parse()
    self.existing_cluster = existing_cluster
    self.update_mask: Set[str] = update_mask if update_mask else set()

  def MakeClusterFromConfig(self) -> Any:
    """Returns a cluster message from the config JSON string."""
    config_dict = self.args.config
    return messages_util.DictToMessageWithErrorCheck(
        config_dict, self.message_module.Cluster
    )

  def MakeCluster(self) -> Any:
    """Returns a cluster message."""
    cluster = self.MakeClusterBasic()
    cluster.networkResources = _networks.MakeClusterNetworks(
        self.args, self.message_module, self.cluster_ref
    )
    cluster.storageResources = _storage.MakeClusterStorages(
        self.args, self.message_module, self.cluster_ref
    )
    cluster.computeResources = _compute.MakeClusterCompute(
        self.args, self.message_module, self.cluster_ref
    )
    cluster.orchestrator = self.message_module.Orchestrator(
        slurm=_orchestrator.MakeClusterSlurmOrchestrator(
            self.args, self.message_module, cluster
        )
    )
    return cluster

  def MakeClusterBasic(self) -> Any:
    """Makes a cluster message with basic fields."""
    cluster_ref = self.args.CONCEPTS.cluster.Parse()
    cluster = self.message_module.Cluster(name=cluster_ref.Name())
    if self.args.IsSpecified("description"):
      cluster.description = self.args.description
    if self.args.IsSpecified("labels"):
      cluster.labels = _orchestrator.MakeLabels(
          self.args.labels, self.message_module.Cluster.LabelsValue
      )
    return cluster

  def MakeClusterPatchFromConfig(self):
    """Returns the cluster message from the config."""
    cluster = self.MakeClusterFromConfig()
    return cluster, self.args.update_mask

  def MakeClusterPatch(self) -> Tuple[Any, str]:
    """Returns the cluster message with patch fields."""
    cluster = self.MakeClusterBasicPatch()
    cluster.storageResources = _storage.MakeClusterStoragesPatch(
        self.args,
        self.message_module,
        self.cluster_ref,
        self.existing_cluster,
        self.update_mask,
    )
    cluster.computeResources = _compute.MakeClusterComputePatch(
        self.args,
        self.message_module,
        self.cluster_ref,
        self.existing_cluster,
        self.update_mask,
    )
    cluster.orchestrator = self.message_module.Orchestrator(
        slurm=_orchestrator.MakeClusterSlurmOrchestratorPatch(
            self.args,
            self.message_module,
            self.existing_cluster,
            cluster,
            self.update_mask,
        )
    )
    return cluster, ",".join(sorted(self.update_mask))

  def MakeClusterBasicPatch(self) -> Any:
    """Makes a cluster patch message with basic fields."""
    cluster = self.message_module.Cluster()
    if self.args.IsSpecified("description"):
      cluster.description = self.args.description
      self.update_mask.add("description")
    labels = _orchestrator._ConvertMessageToDict(  # pylint: disable=protected-access
        self.existing_cluster.labels if self.existing_cluster else None
    )
    is_labels_updated = False
    exception_message = "Label with key={0} not found."
    if self.args.IsSpecified("remove_labels"):
      for key in self.args.remove_labels:
        _orchestrator._RemoveKeyFromDictSpec(key, labels, exception_message)  # pylint: disable=protected-access
        is_labels_updated = True
    if self.args.IsSpecified("add_labels"):
      labels.update(self.args.add_labels)
      is_labels_updated = True
    if is_labels_updated:
      cluster.labels = _orchestrator.MakeLabels(
          label_args=labels,
          label_cls=self.message_module.Cluster.LabelsValue,
      )
      self.update_mask.add("labels")
    return cluster


