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

"""Flag utils for clusters command group."""

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.cluster_director.clusters import flag_types


def AddConfig(parser, api_version=None, required=False, hidden=False):
  """Adds a config flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(f"Unsupported API version for config: {api_version!r}")
  parser.add_argument(
      "--config",
      help="Configuration of the cluster specs in the form of a JSON object.",
      type=arg_parsers.ArgObject(
          spec=flag_types.FlagTypes(api_version).GetClusterFlagType(),
          enable_shorthand=True,
      ),
      required=required,
      hidden=hidden,
  )


def AddUpdateMask(parser, api_version=None, required=False, hidden=False):
  """Adds an update mask flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for update-mask: {api_version!r}"
    )
  parser.add_argument(
      "--update-mask",
      help=textwrap.dedent("""
        Update mask to specify the fields to update.

        For e.g. --update-mask "description,labels"
      """),
      type=flag_types.UPDATE_MASK_OBJECT,
      required=required,
      hidden=hidden,
  )


def AddDescription(parser, api_version=None, hidden=False):
  """Adds a description flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for description: {api_version!r}"
    )
  parser.add_argument(
      "--description",
      help=textwrap.dedent("""
        Description of the cluster.

        For e.g. --description {description}
      """),
      type=str,
      hidden=hidden,
  )


def AddLabels(
    parser,
    name="labels",
    api_version=None,
    hidden=False,
    include_update_flags=False,
):
  """Adds a labels flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(f"Unsupported API version for labels: {api_version!r}")
  remove_flag_name = f"remove-{name}"
  if include_update_flags:
    name = f"add-{name}"
  parser.add_argument(
      f"--{name}",
      help=textwrap.dedent(f"""
        Cluster labels as key value pairs.

        For e.g. --{name} key1=value1,key2=value2
      """),
      type=flag_types.LABEL,
      hidden=hidden,
  )
  if include_update_flags:
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove cluster label by key.

          For e.g. --{remove_flag_name} {{key1}},{{key2}},...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        hidden=hidden,
    )


def AddCreateNetwork(parser, api_version=None, hidden=False):
  """Adds a create network flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for create-network: {api_version!r}"
    )
  parser.add_argument(
      "--create-network",
      help=textwrap.dedent("""
        Parameters to create a network.
        Name: Must match the regex `[a-z]([-a-z0-9]*[a-z0-9])?`, be 1-63
        characters in length, and comply with RFC1035.

        Description: A description of the network. Maximum of 2048 characters.

        For e.g. --create-network name={network},description={description}
      """),
      type=flag_types.NETWORK_OBJECT,
      hidden=hidden,
  )


def AddNetworkSource(parser, api_version=None, required=False, hidden=False):
  """Adds a network flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(f"Unsupported API version for network: {api_version!r}")
  parser.add_argument(
      "--network",
      help=textwrap.dedent("""
        Reference of existing network name.
        If the network is in a different project (Shared VPC), specify
        the project ID using --network-project.

        For e.g. --network {network}
      """),
      type=str,
      required=required,
      hidden=hidden,
  )


def AddNetworkProject(parser, api_version=None, hidden=False):
  """Adds a network project flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for network-project: {api_version!r}"
    )
  parser.add_argument(
      "--network-project",
      help=textwrap.dedent("""\
        Project ID of the project containing the network and subnetwork
        resources, if different from the cluster project (e.g. for Shared VPC).
      """),
      type=str,
      hidden=hidden,
  )


def AddSubnetSource(parser, api_version=None, required=False, hidden=False):
  """Adds a subnet flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(f"Unsupported API version for subnet: {api_version!r}")
  parser.add_argument(
      "--subnet",
      help=textwrap.dedent("""
        Reference of existing subnetwork name.
        If the subnetwork is in a different project (Shared VPC), specify
        the project ID using --network-project.

        For e.g. --subnet regions/{region}/subnetworks/{subnetwork}
      """),
      type=str,
      required=required,
      hidden=hidden,
  )


def AddCreateFilestores(
    parser,
    name="create-filestores",
    api_version=None,
    hidden=False,
    include_update_flags=False,
):
  """Adds a create filestores flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for create-filestores: {api_version!r}"
    )
  if include_update_flags:
    name = "add-new-filestore-instances"
  parser.add_argument(
      f"--{name}",
      help=textwrap.dedent("""
        Parameters to create a filestore instance.

        For e.g. --create-filestores name=locations/{location}/instances/{filestore},tier=REGIONAL,capacityGb={filestoreSize},fileshare={fileshare}

        capacityGb: Size of the filestore in GB. Must be between 1024 and 102400, and must meet scalability requirements described at
        https://cloud.google.com/filestore/docs/service-tiers.

        fileshare: The directory on a Filestore instance where all shared files
        are stored. Must match the regex `[a-z]([-a-z0-9]*[a-z0-9])?`, be 1-63
        characters in length, and comply with RFC1035.
        Supported tier values:
        - ZONAL
        - REGIONAL

        Supported protocol values:
        - NFSV3
        - NFSV41
        - If not specified, defaults to NFSV3

        Defaults:
        - protocol: NFSV3
      """),
      type=flag_types.FlagTypes(api_version).GetFilestoresObject(),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )


def AddFilestores(
    parser,
    name="filestores",
    api_version=None,
    hidden=False,
    include_update_flags=False,
):
  """Adds a filestores flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(f"Unsupported API version for filestores: {api_version!r}")
  remove_flag_name = "remove-filestore-instances"
  if include_update_flags:
    name = "add-filestore-instances"
  parser.add_argument(
      f"--{name}",
      help=textwrap.dedent(f"""
        Reference of existing filestore instance.

        For e.g. --{name} locations/{{location}}/instances/{{filestore}}
      """),
      type=arg_parsers.ArgList(element_type=str),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )
  if include_update_flags:
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove filestore instance config by filestore name.

          For e.g. --{remove_flag_name} locations/{{location}}/instances/{{filestore1}},locations/{{location}}/instances/{{filestore2}},...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        hidden=hidden,
    )


def AddCreateGcsBuckets(
    parser: parser_arguments.ArgumentInterceptor,
    name: str = "create-buckets",
    api_version: str = None,
    hidden: bool = False,
    include_update_flags: bool = False,
):
  """Adds a create Google Cloud Storage buckets flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for create-buckets: {api_version!r}"
    )
  if include_update_flags:
    name = "add-new-storage-buckets"
  alpha_help = textwrap.dedent(f"""
        Parameters to create a Google Cloud Storage bucket.

        For e.g. --{name} name={{bucket-path}},storageClass=STANDARD,terminalStorageClass=TERMINAL_STORAGE_CLASS_NEARLINE,enableHNS=true

        Supported storageClass values:
        - STANDARD
        - NEARLINE
        - COLDLINE
        - ARCHIVE

        Supported terminalStorageClass values:
        - TERMINAL_STORAGE_CLASS_NEARLINE
        - TERMINAL_STORAGE_CLASS_ARCHIVE

        Defaults:
        - storageClass: STANDARD

        Note:
        - Either storageClass or enableAutoclass can be set.
        - HNS: Hierarchical namespace
      """)
  beta_help = textwrap.dedent(f"""
        Parameters to create a Google Cloud Storage bucket.

        For e.g. --{name} name={{bucket-path}},storageClass=STANDARD,enableHNS=true

        Supported storageClass values:
        - STANDARD
        - NEARLINE
        - COLDLINE
        - ARCHIVE

        Defaults:
        - storageClass: STANDARD

        Note:
        - Either storageClass or enableAutoclass can be set.
        - HNS: Hierarchical namespace
      """)
  parser.add_argument(
      f"--{name}",
      help=alpha_help if api_version == "v1alpha" else beta_help,
      type=flag_types.FlagTypes(api_version).GetGcsBucketsObject(),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )


def AddGcsBuckets(
    parser: parser_arguments.ArgumentInterceptor,
    name: str = "buckets",
    api_version: str = None,
    hidden: bool = False,
    include_update_flags: bool = False,
):
  """Adds a Google Cloud Storage buckets flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(f"Unsupported API version for buckets: {api_version!r}")
  remove_flag_name = f"remove-storage-{name}"
  if include_update_flags:
    name = f"add-storage-{name}"
  parser.add_argument(
      f"--{name}",
      help=textwrap.dedent(f"""
        Reference of existing Google Cloud Storage bucket.

        For e.g. --{name} {{existing-bucket-name eg. my-bucket}}
      """),
      type=arg_parsers.ArgList(element_type=str),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )
  if include_update_flags:
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove Google Cloud Storage bucket by bucket name.

          For e.g. --{remove_flag_name} {{bucket1}},{{bucket2}},...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        hidden=hidden,
    )


def AddCreateLustres(
    parser: parser_arguments.ArgumentInterceptor,
    name: str = "create-lustres",
    api_version: str = None,
    hidden: bool = False,
    include_update_flags: bool = False,
):
  """Adds a create lustres flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for create-lustres: {api_version!r}"
    )
  if include_update_flags:
    name = "add-new-lustre-instances"
  parser.add_argument(
      f"--{name}",
      help=textwrap.dedent(f"""
        Parameters to create a Lustre instance.

        For e.g. --{name} name=locations/{{location}}/instances/{{lustre}},capacityGb={{lustreSize}},filesystem={{filesystem}},perUnitStorageThroughput=1000

        Values for perUnitStorageThroughput: 125, 250, 500, 1000
      """),
      type=flag_types.LUSTRES_OBJECT,
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )


def AddLustres(
    parser,
    name="lustres",
    api_version=None,
    hidden=False,
    include_update_flags=False,
):
  """Adds a lustres flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(f"Unsupported API version for lustres: {api_version!r}")
  remove_flag_name = "remove-lustre-instances"
  if include_update_flags:
    name = "add-lustre-instances"
  parser.add_argument(
      f"--{name}",
      help=textwrap.dedent(f"""
        Reference of existing Lustre instance.

        For e.g. --{name} locations/{{location}}/instances/{{lustre}}
      """),
      type=arg_parsers.ArgList(element_type=str),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )
  if include_update_flags:
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove lustre instance config by lustre name.

          For e.g. --{remove_flag_name} locations/{{location}}/instances/{{lustre1}},locations/{{location}}/instances/{{lustre2}},...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        hidden=hidden,
    )


def AddOnDemandInstances(
    parser,
    name="on-demand-instances",
    api_version=None,
    hidden=False,
    include_update_flags=False,
):
  """Adds an on demand instances flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for on-demand-instances: {api_version!r}"
    )
  remove_flag_name = f"remove-{name}"
  if include_update_flags:
    name = f"add-{name}"
  alpha_help = textwrap.dedent(f"""
        Parameters to define cluster on demand instances.

        For e.g. --{name} id={{computeId}},zone={{zone}},machineType={{machineType}},atmTags="tag1=val1"
      """)
  beta_help = textwrap.dedent(f"""
        Parameters to define cluster on demand instances.

        For e.g. --{name} id={{computeId}},zone={{zone}},machineType={{machineType}}
      """)
  parser.add_argument(
      f"--{name}",
      help=alpha_help if api_version == "v1alpha" else beta_help,
      type=flag_types.FlagTypes(api_version).GetOnDemandInstancesObject(),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )
  if include_update_flags:
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove on demand instances config by compute id.

          For e.g. --{remove_flag_name} {{computeId1}},{{computeId2}},...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        hidden=hidden,
    )


def AddSpotInstances(
    parser,
    name="spot-instances",
    api_version=None,
    hidden=False,
    include_update_flags=False,
):
  """Adds an spot instances flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for spot-instances: {api_version!r}"
    )
  remove_flag_name = f"remove-{name}"
  if include_update_flags:
    name = f"add-{name}"
  alpha_help = textwrap.dedent(f"""
        Parameters to define cluster spot instances.

        For e.g. --{name} id={{computeId}},zone={{zone}},machineType={{machineType}},atmTags="tag1=val1"
      """)
  beta_help = textwrap.dedent(f"""
        Parameters to define cluster spot instances.

        For e.g. --{name} id={{computeId}},zone={{zone}},machineType={{machineType}}
      """)
  parser.add_argument(
      f"--{name}",
      help=alpha_help if api_version == "v1alpha" else beta_help,
      type=flag_types.FlagTypes(api_version).GetSpotInstancesObject(),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )
  if include_update_flags:
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove spot instance config by compute id.

          For e.g. --{remove_flag_name} {{computeId1}},{{computeId2}},...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        hidden=hidden,
    )


def AddReservedInstances(
    parser,
    name="reserved-instances",
    api_version=None,
    hidden=False,
    include_update_flags=False,
):
  """Adds an reserved instances flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for reserved-instances: {api_version!r}"
    )
  remove_flag_name = f"remove-{name}"
  if include_update_flags:
    name = f"add-{name}"
  alpha_help = textwrap.dedent(f"""
        Parameters to define cluster reserved instances.

        For e.g. --{name} id={{computeId}},reservation=zones/{{zone}}/reservations/{{reservation}}

        Exactly one of reservation, reservation-block, or reservation-sub-block must be provided.
        reservation: The name of the reservation to use, in the format zones/{{zone}}/reservations/{{reservation}}.
        reservationBlock: The name of the reservation block to use, in the format zones/{{zone}}/reservations/{{reservation}}/reservationBlocks/{{reservation_block}}.
        reservationSubBlock: The name of the reservation sub-block to use, in the format zones/{{zone}}/reservations/{{reservation}}/reservationBlocks/{{reservation_block}}/reservationSubBlocks/{{reservation_sub_block}}.
      """)
  beta_help = textwrap.dedent(f"""
        Parameters to define cluster reserved instances.

        For e.g. --{name} id={{computeId}},reservation=zones/{{zone}}/reservations/{{reservation}}
      """)
  parser.add_argument(
      f"--{name}",
      help=alpha_help if api_version == "v1alpha" else beta_help,
      type=flag_types.FlagTypes(api_version).GetReservedInstancesObject(),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )
  if include_update_flags:
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove reserved instance config by compute id.

          For e.g. --{remove_flag_name} {{computeId1}},{{computeId2}},...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        hidden=hidden,
    )


def AddFlexStartInstances(
    parser,
    name="flex-start-instances",
    api_version=None,
    hidden=False,
    include_update_flags=False,
):
  """Adds an Flex Start instances flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for flex-start-instances: {api_version!r}"
    )
  remove_flag_name = f"remove-{name}"
  if include_update_flags:
    name = f"add-{name}"
  alpha_help = textwrap.dedent(f"""
        Parameters to define cluster Flex Start instances.

        For e.g. --{name} id={{computeId}},zone={{zone}},machineType={{machineType}},maxDuration=10000s,atmTags="tag1=val1"
      """)
  beta_help = textwrap.dedent(f"""
        Parameters to define cluster Flex Start instances.

        For e.g. --{name} id={{computeId}},zone={{zone}},machineType={{machineType}},maxDuration=10000s
      """)
  parser.add_argument(
      f"--{name}",
      help=alpha_help if api_version == "v1alpha" else beta_help,
      type=flag_types.FlagTypes(api_version).GetFlexStartInstancesObject(),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )
  if include_update_flags:
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove Flex Start instance config by compute id.

          For e.g. --{remove_flag_name} {{computeId1}},{{computeId2}},...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        hidden=hidden,
    )


def AddSlurmNodeSets(
    parser,
    name="slurm-node-sets",
    api_version=None,
    required=False,
    hidden=False,
    include_update_flags=False,
):
  """Adds a slurm node sets flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for slurm-node-sets: {api_version!r}"
    )
  update_flag_name = f"update-{name}"
  remove_flag_name = f"remove-{name}"
  if include_update_flags:
    name = f"add-{name}"
  alpha_help = textwrap.dedent(f"""
        Parameters to define slurm cluster nodeset config.

        For e.g. --{name} id={{nodesetId}},computeId={{computeId}},type=gce,staticNodeCount={{staticNodeCount}},maxDynamicNodeCount={{maxDynamicNodeCount}},startupScript="echo hello",labels="{{key1=value1,key2=value2}}"

        To configure a node set backed by Google Kubernetes Engine, use type=gke. If type=gke is
        specified, Compute Engine specific fields (labels, startupScript, bootDisk,
        startupScriptTimeout) cannot be used, but container-specific fields
        (container-resource-labels, container-startup-script) may be used.
        For e.g. --{name} id={{nodesetId}},computeId={{computeId}},type=gke
        For e.g. --{name} id={{nodesetId}},computeId={{computeId}},type=gke,container-resource-labels="key1=val1",container-startup-script="echo hello"

        Defaults:
        - staticNodeCount: 1
        - type: gce

        Note:
        - startupScript:
          - Either str or file_path
          - For file_path, only bash file format (.sh or .bash) is supported.
          - For file_path, only absolute path is supported.
      """)
  beta_help = textwrap.dedent(f"""
        Parameters to define slurm cluster nodeset config.

        For e.g. --{name} id={{nodesetId}},computeId={{computeId}},staticNodeCount={{staticNodeCount}},maxDynamicNodeCount={{maxDynamicNodeCount}},computeInstance=[startupScript="echo hello",labels="key1=value1,key2=value2"]

        Defaults:
        - staticNodeCount: 1

        Note:
        - startupScript:
          - Either str or file_path
          - For file_path, only bash file format (.sh or .bash) is supported.
          - For file_path, only absolute path is supported.
      """)
  parser.add_argument(
      f"--{name}",
      help=alpha_help if api_version == "v1alpha" else beta_help,
      type=flag_types.FlagTypes(api_version).GetSlurmNodeSetsObject(),
      action=arg_parsers.FlattenAction(),
      required=required,
      hidden=hidden,
  )
  if include_update_flags:
    alpha_update_help = textwrap.dedent(f"""
          Parameters to define and update slurm cluster nodeset config.

          For e.g. --{update_flag_name} id={{nodesetId}},staticNodeCount={{staticNodeCount}},maxDynamicNodeCount={{maxDynamicNodeCount}}

          To update a node set backed by GKE, use container-resource-labels or container-startup-script.
          For e.g. --{update_flag_name} id={{nodesetId}},type=gke,container-resource-labels="key1=val1",container-startup-script="echo hello"
        """)
    beta_update_help = textwrap.dedent(f"""
          Parameters to define and update slurm cluster nodeset config.

          For e.g. --{update_flag_name} id={{nodesetId}},staticNodeCount={{staticNodeCount}},maxDynamicNodeCount={{maxDynamicNodeCount}},computeInstance=[startupScript="echo hello"]
        """)
    parser.add_argument(
        f"--{update_flag_name}",
        help=alpha_update_help
        if api_version == "v1alpha"
        else beta_update_help,
        type=flag_types.FlagTypes(api_version).GetSlurmNodeSetsObject(),
        action=arg_parsers.FlattenAction(),
        required=required,
        hidden=hidden,
    )
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove slurm nodeset config by nodeset id.

          For e.g. --{remove_flag_name} {{nodesetId1}},{{nodesetId2}},...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        required=required,
        hidden=hidden,
    )


def AddSlurmPartitions(
    parser,
    name="slurm-partitions",
    api_version=None,
    required=False,
    hidden=False,
    include_update_flags=False,
):
  """Adds a slurm partitions flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for slurm-partitions: {api_version!r}"
    )
  update_flag_name = f"update-{name}"
  remove_flag_name = f"remove-{name}"
  if include_update_flags:
    name = f"add-{name}"
  alpha_help = textwrap.dedent(f"""
        Parameters to define slurm cluster partitions.

        For e.g. --{name} id=p1,nodesetIds=[ns1,ns2],exclusive=false
      """)
  beta_help = textwrap.dedent(f"""
        Parameters to define slurm cluster partitions.

        For e.g. --{name} id=p1,nodesetIds=[ns1,ns2]
      """)
  parser.add_argument(
      f"--{name}",
      help=alpha_help if api_version == "v1alpha" else beta_help,
      type=flag_types.FlagTypes(api_version).GetSlurmPartitionsObject(),
      action=arg_parsers.FlattenAction(),
      required=required,
      hidden=hidden,
  )
  if include_update_flags:
    alpha_update_help = textwrap.dedent(f"""
          Parameters to define and update slurm cluster partition config.

          For e.g. --{update_flag_name} id=p1,nodesetIds=[ns1,ns2],exclusive=false
        """)
    beta_update_help = textwrap.dedent(f"""
          Parameters to define and update slurm cluster partition config.

          For e.g. --{update_flag_name} id=p1,nodesetIds=[ns1,ns2]
        """)
    parser.add_argument(
        f"--{update_flag_name}",
        help=alpha_update_help
        if api_version == "v1alpha"
        else beta_update_help,
        type=flag_types.FlagTypes(api_version).GetSlurmPartitionsUpdateObject(),
        action=arg_parsers.FlattenAction(),
        required=required,
        hidden=hidden,
    )
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Parameters to remove slurm partition config by partition id.

          For e.g. --{remove_flag_name} p1,p2,...
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        required=required,
        hidden=hidden,
    )


def AddSlurmDefaultPartition(parser, api_version=None, hidden=False):
  """Adds a slurm default partition flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for slurm-default-partition: {api_version!r}"
    )
  parser.add_argument(
      "--slurm-default-partition",
      help=textwrap.dedent("""
        Parameters to define slurm cluster default partition.

        For e.g. --slurm-default-partition {partitionId}
      """),
      type=str,
      hidden=hidden,
  )


def AddSlurmLoginNode(
    parser,
    name="slurm-login-node",
    api_version=None,
    required=False,
    hidden=False,
    include_update_flags=False,
):
  """Adds a slurm login node flag for the given API version."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for slurm-login-node: {api_version!r}"
    )
  ft = flag_types.FlagTypes(api_version)
  alpha_create_help = """
        Parameters to define slurm cluster login node.

        For e.g. --slurm-login-node machineType={machineType},zone={zone},count={count},enableOSLogin=true,enablePublicIPs=true,startupScript="echo hello",labels="{key1=value1,key2=value2}"

          If bootDisk is specified, sizeGb must be greater than 50.

        Defaults:
        - count: 1
        - enableOSLogin: true
        - enablePublicIPs: true
        - bootDisk.sizeGb: 100

        Note:
        - startupScript:
          - Either str or file_path
          - For file_path, only bash file format (.sh or .bash) is supported.
          - For file_path, only absolute path is supported.
      """
  beta_create_help = """
        Parameters to define slurm cluster login node.

      For e.g. --slurm-login-node machineType={machineType},zone={zone},count={count},enableOSLogin=true,enablePublicIPs=true,startupScript="echo hello",bootDisk={type=pd-standard,sizeGb=100}

        If bootDisk is specified, sizeGb must be greater than 50.

      Defaults:
      - count: 1
      - enableOSLogin: true
      - enablePublicIPs: true
      - bootDisk.sizeGb: 100

      Note:
      - startupScript:
        - Either str or file_path
        - For file_path, only bash file format (.sh or .bash) is supported.
        - For file_path, only absolute path is supported.
    """
  flag_name = name
  if include_update_flags:
    flag_name = f"update-{name}"
    help_text = f"""
        Parameters to update slurm cluster login node.
        Only bootDisk, count and startupScript can be updated.

        For e.g. --{flag_name} count=2,startupScript="echo hello"
    """
    flag_type = ft.GetSlurmLoginNodeUpdateObject()
  else:
    help_text = (
        alpha_create_help if api_version == "v1alpha" else beta_create_help
    )
    flag_type = ft.GetSlurmLoginNodeObject()

  parser.add_argument(
      f"--{flag_name}",
      help=help_text,
      type=flag_type,
      required=required,
      hidden=hidden,
  )


def _AddScriptFlags(
    parser, name, help_kind, api_version, hidden, include_update_flags
):
  """Helper to add script flags."""
  if api_version not in ["v1alpha", "v1beta"]:
    raise ValueError(
        f"Unsupported API version for {help_kind}: {api_version!r}"
    )
  remove_flag_name = f"remove-{name}"
  if include_update_flags:
    flag_name = f"add-{name}"
  else:
    flag_name = name
  parser.add_argument(
      f"--{flag_name}",
      help=textwrap.dedent(f"""
        {help_kind}.

        For e.g. --{flag_name} script1.sh,script2.sh
      """),
      type=arg_parsers.ArgList(element_type=str),
      action=arg_parsers.FlattenAction(),
      hidden=hidden,
  )
  if include_update_flags:
    parser.add_argument(
        f"--{remove_flag_name}",
        help=textwrap.dedent(f"""
          Scripts to remove from {help_kind}.

          For e.g. --{remove_flag_name} script1.sh,script2.sh
        """),
        type=arg_parsers.ArgList(element_type=str),
        action=arg_parsers.FlattenAction(),
        hidden=hidden,
    )


def AddSlurmPrologBashScripts(
    parser, api_version=None, hidden=False, include_update_flags=False
):
  """Adds a slurm prolog bash scripts flag for the given API version."""
  _AddScriptFlags(
      parser,
      "slurm-prolog-scripts",
      "Slurm prolog bash scripts",
      api_version,
      hidden,
      include_update_flags,
  )


def AddSlurmEpilogBashScripts(
    parser, api_version=None, hidden=False, include_update_flags=False
):
  """Adds a slurm epilog bash scripts flag for the given API version."""
  _AddScriptFlags(
      parser,
      "slurm-epilog-scripts",
      "Slurm epilog bash scripts",
      api_version,
      hidden,
      include_update_flags,
  )


def AddSlurmTaskPrologBashScripts(
    parser, api_version=None, hidden=False, include_update_flags=False
):
  """Adds a slurm task prolog bash scripts flag for the given API version.

  Args:
    parser: The argparse parser.
    api_version: The API version to use (e.g., "v1alpha").
    hidden: Whether the flag should be hidden.
    include_update_flags: Whether to include flags for update commands.

  Raises:
    ValueError: If the api_version is not supported.
  """
  if api_version not in ["v1alpha"]:
    raise ValueError(
        "Unsupported API version for slurm-task-prolog-scripts:"
        f" {api_version!r}"
    )
  _AddScriptFlags(
      parser,
      "slurm-task-prolog-scripts",
      "Slurm task prolog bash scripts",
      api_version,
      hidden,
      include_update_flags,
  )


def AddSlurmTaskEpilogBashScripts(
    parser, api_version=None, hidden=False, include_update_flags=False
):
  """Adds a slurm task epilog bash scripts flag for the given API version.

  Args:
    parser: The argparse parser.
    api_version: The API version to use (e.g., "v1alpha").
    hidden: Whether the flag should be hidden.
    include_update_flags: Whether to include flags for update commands.

  Raises:
    ValueError: If the api_version is not supported.
  """
  if api_version not in ["v1alpha"]:
    raise ValueError(
        "Unsupported API version for slurm-task-epilog-scripts:"
        f" {api_version!r}"
    )
  _AddScriptFlags(
      parser,
      "slurm-task-epilog-scripts",
      "Slurm task epilog bash scripts",
      api_version,
      hidden,
      include_update_flags,
  )


def AddSlurmConfig(
    parser, api_version=None, hidden=False, include_update_flags=False
):
  """Adds a slurm config flag for the given API version."""
  if api_version not in ["v1alpha"]:
    raise ValueError(
        f"Unsupported API version for slurm-config: {api_version!r}"
    )
  flag_name = "slurm-config"
  if include_update_flags:
    flag_name = f"update-{flag_name}"
  parser.add_argument(
      f"--{flag_name}",
      help=textwrap.dedent(f"""
        Parameters to define slurm cluster config.

        For e.g. --{flag_name} healthCheckInterval=10,healthCheckNodeState=IDLE,healthCheckProgram=/usr/bin/true
      """),
      type=flag_types.SLURM_CONFIG_TYPE,
      hidden=hidden,
  )


def AddSlurmDisableHealthCheckProgram(
    parser, api_version=None, hidden=False, include_update_flags=False
):
  """Adds a slurm disable health check program flag for the given API version."""
  if api_version not in ["v1alpha"]:
    raise ValueError(
        "Unsupported API version for slurm-disable-health-check-program:"
        f" {api_version!r}"
    )
  flag_name = "slurm-disable-health-check-program"
  if include_update_flags:
    flag_name = f"update-{flag_name}"
  parser.add_argument(
      f"--{flag_name}",
      help=textwrap.dedent(f"""
        If true, health checking is disabled, and health_check_interval,
        health_check_node_state, and health_check_program should not be passed in.

        For e.g. --{flag_name}
      """),
      action="store_true",
      hidden=hidden,
  )
