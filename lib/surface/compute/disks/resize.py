# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for setting size of instance group manager."""

import textwrap
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.core.console import console_io

CONTINUE_WITH_RESIZE_PROMPT = textwrap.dedent("""
    This command increases disk size. This change is not reversible.
    For more information, see:
    https://cloud.google.com/sdk/gcloud/reference/compute/disks/resize""")


def _CommonArgs(parser):
  Resize.disks_arg.AddArgument(parser)
  size = parser.add_argument(
      '--size',
      required=True,
      type=arg_parsers.BinarySize(lower_bound='1GB'),
      help='Indicates the new size of the disks.')
  size.detailed_help = """\
        Indicates the new size of the disks. The value must be a whole
        number followed by a size unit of ``KB'' for kilobyte, ``MB''
        for megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For
        example, ``10GB'' will produce 10 gigabyte disks.  Disk size
        must be a multiple of 10 GB.
        """


@base.ReleaseTracks(base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Resize(base_classes.BaseAsyncMutator):
  """Set size of a persistent disk."""

  @property
  def service(self):
    return self.compute.disks

  @property
  def resource_type(self):
    return 'projects'

  @property
  def method(self):
    return 'Resize'

  @classmethod
  def Args(cls, parser):
    Resize.disks_arg = disks_flags.MakeDiskArg(plural=True)
    _CommonArgs(parser)

  def CreateRequests(self, args):
    """Returns a request for resizing a disk."""

    size_gb = utils.BytesToGb(args.size)
    disk_refs = Resize.disks_arg.ResolveAsResource(
        args, self.resources)

    console_io.PromptContinue(
        message=CONTINUE_WITH_RESIZE_PROMPT,
        cancel_on_no=True)

    requests = []

    for disk_ref in disk_refs:
      if disk_ref.Collection() == 'compute.disks':
        request = self.messages.ComputeDisksResizeRequest(
            disk=disk_ref.Name(),
            project=self.project,
            zone=disk_ref.zone,
            disksResizeRequest=self.messages.DisksResizeRequest(sizeGb=size_gb))
      elif disk_ref.Collection() == 'compute.regionDisks':
        request = self.messages.ComputeRegionDisksResizeRequest(
            disk=disk_ref.Name(),
            project=self.project,
            region=disk_ref.region,
            regionDisksResizeRequest=self.messages.RegionDisksResizeRequest(
                sizeGb=size_gb))
        request = (self.compute.regionDisks, self.method, request)
      requests.append(request)

    return requests

Resize.detailed_help = {
    'brief': 'Resize a disk or disks',
    'DESCRIPTION': """\
        *{command}* resizes a Google Compute Engine disk(s).

        Only increasing disk size is supported. Disks can be resized
        regardless of whether they are attached.

    """,
    'EXAMPLES': """\
        To resize a disk called example-disk-1 to new size 6TB, run:

           $ {command} example-disk-1 --size=6TB

        To resize two disks called example-disk-2 and example-disk-3 to
        new size 6TB, run:

           $ {command} example-disk-2 example-disk-3 --size=6TB

        This assumes that original size of each of these disks is 6TB or less.
        """}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ResizeAlpha(Resize):

  @classmethod
  def Args(cls, parser):
    Resize.disks_arg = disks_flags.MakeDiskArgZonalOrRegional(plural=True)
    _CommonArgs(parser)


ResizeAlpha.detailed_help = Resize.detailed_help
