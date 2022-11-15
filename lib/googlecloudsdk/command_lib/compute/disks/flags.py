# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Flags and helpers for the compute disks commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.core import properties

_DETAILED_SOURCE_SNAPSHOT_HELP = """\
      Source snapshot used to create the disks. It is safe to
      delete a snapshot after a disk has been created from the
      snapshot. In such cases, the disks will no longer reference
      the deleted snapshot. To get a list of snapshots in your
      current project, run `gcloud compute snapshots list`. A
      snapshot from an existing disk can be created using the
      `gcloud compute disks snapshot` command. This flag is mutually
      exclusive with *--image*.

      When using this option, the size of the disks must be at least
      as large as the snapshot size. Use *--size* to adjust the
      size of the disks.
"""

_DETAILED_SOURCE_INSTANT_SNAPSHOT_HELP = """\
      Source instant snapshot used to create the disks.
"""

_SOURCE_DISK_DETAILED_HELP = """\
      Source disk used to create the disk(s). It is safe to
      delete a source disk after a disk has been created from the
      source disk. To get a list of disks in your current project,
      run `gcloud compute disks list`. This flag is mutually
      exclusive with *--image* and *--source-snapshot*.

      When using this option, the size of the disks must be at least
      as large as the source disk size. Use *--size* to adjust the
      size of the disks.

      The source disk must be in the same zone/region as the disk to be created.
"""

_SOURCE_DISK_ZONE_EXPLANATION = """\
      Zone of the source disk. This argument is not required if the target disk
      is in the same zone as the source disk.
"""

_SOURCE_DISK_REGION_EXPLANATION = """\
      Region of the source disk. This argument is not required if the target
      disk is in the same region as the source disk.
"""

_ASYNC_PRIMARY_DISK_HELP = """\
      Primary disk for asynchronous replication. This flag is required when
      creating a secondary disk.
"""

_ASYNC_PRIMARY_DISK_ZONE_EXPLANATION = """\
      Zone of the primary disk for asynchronous replication. The primary and
      secondary disks must not be in the same region.
"""

_ASYNC_PRIMARY_DISK_REGION_EXPLANATION = """\
      Region of the primary disk for asynchronous replication. The primary and
      secondary disks must not be in the same region.
"""

_ASYNC_SECONDARY_DISK_HELP = """\
      Secondary disk for asynchronous replication. This flag is required when
      starting replication. It is also required when stopping replication on the
      primary disk. It must not be used when stopping replication on the
      secondary disk.
"""

_ASYNC_SECONDARY_DISK_ZONE_EXPLANATION = """\
      Zone of the secondary disk for asynchronous replication.
"""

_ASYNC_SECONDARY_DISK_REGION_EXPLANATION = """\
      Region of the secondary disk for asynchronous replication.
"""

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      zone.basename(),
      sizeGb,
      type.basename(),
      status
    )"""


MULTISCOPE_LIST_FORMAT = """
    table(
      name,
      location(),
      location_scope(),
      sizeGb,
      type.basename(),
      status
      )"""


class SnapshotsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(SnapshotsCompleter, self).__init__(
        collection='compute.snapshots',
        list_command='compute snapshots list --uri',
        **kwargs)


def MakeDiskArgZonal(plural):
  return compute_flags.ResourceArgument(
      resource_name='disk',
      completer=compute_completers.DisksCompleter,
      plural=plural,
      name='DISK_NAME',
      zonal_collection='compute.disks',
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)


def MakeDiskArg(plural):
  return compute_flags.ResourceArgument(
      resource_name='disk',
      completer=compute_completers.DisksCompleter,
      plural=plural,
      name='DISK_NAME',
      zonal_collection='compute.disks',
      regional_collection='compute.regionDisks',
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def AddMultiWriterFlag(parser):
  return parser.add_argument(
      '--multi-writer',
      action='store_true',
      help="""
      Create the disk in multi-writer mode so that it can be attached
      with read-write access to two VMs. The multi-writer feature requires
      specialized filesystems, among other restrictions. For more information,
      see
      https://cloud.google.com/compute/docs/disks/sharing-disks-between-vms.
      """)


def AddStopGroupAsyncReplicationArgs(parser):
  """Adds stop group async replication specific arguments to parser."""
  parser.add_argument(
      'DISK_CONSISTENCY_GROUP_POLICY',
      help='URL of the disk consistency group resource policy. The resource'
           'policy is always in the region of the primary disks.'
  )

  help_text = '{0} of the consistency group\'s primary or secondary disks. {1}'
  scope_parser = parser.add_mutually_exclusive_group()
  scope_parser.add_argument(
      '--zone',
      completer=compute_completers.ZonesCompleter,
      action=actions.StoreProperty(properties.VALUES.compute.zone),
      help=help_text.format('Zone', compute_flags.ZONE_PROPERTY_EXPLANATION))
  scope_parser.add_argument(
      '--region',
      completer=compute_completers.RegionsCompleter,
      action=actions.StoreProperty(properties.VALUES.compute.region),
      help=help_text.format(
          'Region',
          compute_flags.REGION_PROPERTY_EXPLANATION))


def AddBulkCreateArgs(parser):
  """Adds bulk create specific arguments to parser."""
  parser.add_argument(
      '--source-consistency-group-policy',
      help='''
      URL of the source consistency group resource policy. The resource policy
      is always in the region of the source disks.
      ''',
      # This argument is required because consistent cloning is only supported
      # feature under the BulkCreate now. May become optional in the future.
      required=True)

  help_text = """Target {0} of the created disks, which currently must be the same as the source {0}. {1}"""
  scope_parser = parser.add_mutually_exclusive_group(required=True)
  scope_parser.add_argument(
      '--zone',
      completer=compute_completers.ZonesCompleter,
      action=actions.StoreProperty(properties.VALUES.compute.zone),
      help=help_text.format('zone', compute_flags.ZONE_PROPERTY_EXPLANATION))
  scope_parser.add_argument(
      '--region',
      completer=compute_completers.RegionsCompleter,
      action=actions.StoreProperty(properties.VALUES.compute.region),
      help=help_text.format('region',
                            compute_flags.REGION_PROPERTY_EXPLANATION))


def AddProvisionedIopsFlag(parser, arg_parsers, constants):
  return parser.add_argument(
      '--provisioned-iops',
      type=arg_parsers.BoundedInt(constants.MIN_PROVISIONED_IOPS,
                                  constants.MAX_PROVISIONED_IOPS),
      help=(
          'Provisioned IOPS of pd-extreme disk to create. Only for use with '
          'disks of type pd-extreme. If specified, the value must be in the '
          'range between {min} and {max}. If not specified, the default value '
          'is {default}.').format(
              min=constants.MIN_PROVISIONED_IOPS,
              # TODO(b/246777440):
              # Replace max=120000 with max=constants.MAX_PROVISIONED_IOPS.
              # This is because the field is already GA, but hyperdisk-extreme
              # no yet, so we will use the old text with old iops range for
              # alpha.
              max=120000,
              default=constants.DEFAULT_PROVISIONED_IOPS))


def AddProvisionedThroughputFlag(parser, arg_parsers):
  return parser.add_argument(
      '--provisioned-throughput',
      type=arg_parsers.BoundedInt(),
      help=(
          'Provisioned throughput of disk to create. The throughput unit is  '
          'MB per sec.  Only for use with disks of type hyperdisk-throughput.'))


def AddArchitectureFlag(parser, messages):
  architecture_enum_type = messages.Disk.ArchitectureValueValuesEnum
  excluded_enums = [architecture_enum_type.ARCHITECTURE_UNSPECIFIED.name]
  architecture_choices = sorted(
      [e for e in architecture_enum_type.names() if e not in excluded_enums])
  return parser.add_argument(
      '--architecture',
      choices=architecture_choices,
      help=(
          'Specifies the architecture or processor type that this disk can support. For available processor types on Compute Engine, see https://cloud.google.com/compute/docs/cpu-platforms.'
      ))


def AddLocationHintArg(parser):
  parser.add_argument(
      '--location-hint',
      hidden=True,
      help="""\
      Used by internal tools to control sub-zone location of the disk.
      """)


def MakeSecondaryDiskArg(required=False):
  return compute_flags.ResourceArgument(
      resource_name='async secondary disk',
      name='--secondary-disk',
      completer=compute_completers.DisksCompleter,
      zonal_collection='compute.disks',
      regional_collection='compute.regionDisks',
      short_help='Secondary disk for asynchronous replication.',
      detailed_help=_ASYNC_SECONDARY_DISK_HELP,
      plural=False,
      required=required,
      use_existing_default_scope=False,
      zone_help_text=_ASYNC_SECONDARY_DISK_ZONE_EXPLANATION,
      region_help_text=_ASYNC_SECONDARY_DISK_REGION_EXPLANATION)


SOURCE_SNAPSHOT_ARG = compute_flags.ResourceArgument(
    resource_name='snapshot',
    completer=SnapshotsCompleter,
    name='--source-snapshot',
    plural=False,
    required=False,
    global_collection='compute.snapshots',
    short_help='Source snapshot used to create the disks.',
    detailed_help=_DETAILED_SOURCE_SNAPSHOT_HELP,)

SOURCE_INSTANT_SNAPSHOT_ARG = compute_flags.ResourceArgument(
    resource_name='source instant snapshot',
    completer=compute_completers.InstantSnapshotsCompleter,
    name='--source-instant-snapshot',
    zonal_collection='compute.instantSnapshots',
    regional_collection='compute.regionInstantSnapshots',
    plural=False,
    required=False,
    short_help='Source instant snapshot used to create the disks.',
    detailed_help=_DETAILED_SOURCE_INSTANT_SNAPSHOT_HELP,
    use_existing_default_scope=True)

SOURCE_DISK_ARG = compute_flags.ResourceArgument(
    resource_name='source disk',
    name='--source-disk',
    completer=compute_completers.DisksCompleter,
    short_help='Source disk used to create the disks. Source disk must be in'
    ' the same zone/region as the disk to be created.',
    detailed_help=_SOURCE_DISK_DETAILED_HELP,
    zonal_collection='compute.disks',
    regional_collection='compute.regionDisks',
    required=False,
    zone_help_text=_SOURCE_DISK_ZONE_EXPLANATION,
    region_help_text=_SOURCE_DISK_REGION_EXPLANATION)

ASYNC_PRIMARY_DISK_ARG = compute_flags.ResourceArgument(
    resource_name='async primary disk',
    name='--primary-disk',
    completer=compute_completers.DisksCompleter,
    zonal_collection='compute.disks',
    regional_collection='compute.regionDisks',
    short_help='Primary disk for asynchronous replication. This option creates'
    ' a secondary disk for a given primary disk.',
    detailed_help=_ASYNC_PRIMARY_DISK_HELP,
    plural=False,
    required=False,
    use_existing_default_scope=False,
    zone_help_text=_ASYNC_PRIMARY_DISK_ZONE_EXPLANATION,
    region_help_text=_ASYNC_PRIMARY_DISK_REGION_EXPLANATION)
