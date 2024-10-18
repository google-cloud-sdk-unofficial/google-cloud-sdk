# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command for converting a disk to a different type."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Convert(base.RestoreCommand):
  """Convert a Compute Engine disk into a new disk type or new format."""

  _DISK_ARG = disks_flags.MakeDiskArg(plural=False)

  @staticmethod
  def Args(parser):
    Convert._DISK_ARG.AddArgument(parser)
    parser.add_argument(
        '--target-disk-type',
        completer=completers.DiskTypesCompleter,
        required=True,
        help="""Specifies the type of disk to convert to. To get a
        list of available disk types, run `gcloud compute disk-types list`.
        """,
    )
    disks_flags.AddProvisionedThroughputFlag(parser, arg_parsers)
    disks_flags.AddProvisionedIopsFlag(parser, arg_parsers)
    disks_flags.AddKeepOldDiskArgs(parser)

  def Run(self, args):
    return None
