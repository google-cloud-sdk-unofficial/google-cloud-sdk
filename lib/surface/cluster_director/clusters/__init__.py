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
"""Manage Cluster Director cluster resources."""

from googlecloudsdk.calliope import base
from surface.cluster_director.clusters import _init_extensions as extensions


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ClustersAlpha(extensions.ClustersAlpha):
  """Deploy and manage large-scale AI and high-performance computing (HPC) clusters.

  Cluster Director is a unified management plane that simplifies deploying and
  running large-scale AI and high-performance computing (HPC) clusters.

  The service automates complex infrastructure setup by integrating compute,
  networking, and storage to maximize performance and minimize downtimes.

  If you have your own configuration already:
  - Use `--config` to provide a complete JSON definition

  To start from a pre-configuration:
  - Use `--quickstart-cluster` to create and connect a managed Slurm cluster
  with basic defaults
  - Use `--reference-architecture` to choose from workload-optimized templates

  To fully customize:
  - Run the 'clusters create' command for the most granular configuration
  options


  Learn more at https://docs.cloud.google.com/cluster-director/
  """


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ClustersBeta(extensions.ClustersBeta):
  """Deploy and manage large-scale AI and high-performance computing (HPC) clusters.

  Cluster Director is a unified management plane that simplifies deploying and
  running large-scale AI and high-performance computing (HPC) clusters.

  The service automates complex infrastructure setup by integrating compute,
  networking, and storage to maximize performance and minimize downtimes.

  If you have your own configuration already:
  - Use `--config` to provide a complete JSON definition

  To start from a pre-configuration:
  - Use `--quickstart-cluster` to create and connect a managed Slurm cluster
  with basic defaults
  - Use `--reference-architecture` to choose from workload-optimized templates

  To fully customize:
  - Run the 'clusters create' command for the most granular configuration
  options


  Learn more at https://docs.cloud.google.com/cluster-director/
  """


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class ClustersGa(extensions.ClustersGa):
  """Deploy and manage large-scale AI and high-performance computing (HPC) clusters.

  Cluster Director is a unified management plane that simplifies deploying and
  running large-scale AI and high-performance computing (HPC) clusters.

  The service automates complex infrastructure setup by integrating compute,
  networking, and storage to maximize performance and minimize downtimes.

  If you have your own configuration already:
  - Use `--config` to provide a complete JSON definition

  To start from a pre-configuration:
  - Use `--quickstart-cluster` to create and connect a managed Slurm cluster
  with basic defaults
  - Use `--reference-architecture` to choose from workload-optimized templates

  To fully customize:
  - Run the 'clusters create' command for the most granular configuration
  options


  Learn more at https://docs.cloud.google.com/cluster-director/
  """
