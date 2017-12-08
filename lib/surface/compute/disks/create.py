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
"""Command for creating disks."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags

DETAILED_HELP = {
    'brief': 'Create Google Compute Engine persistent disks',
    'DESCRIPTION': """\
        *{command}* creates one or more Google Compute Engine
        persistent disks. When creating virtual machine instances,
        disks can be attached to the instances through the
        `gcloud compute instances create` command. Disks can also be
        attached to instances that are already running using
        `gcloud compute instances attach-disk`.

        Disks are zonal resources, so they reside in a particular zone
        for their entire lifetime. The contents of a disk can be moved
        to a different zone by snapshotting the disk (using
        `gcloud compute disks snapshot`) and creating a new disk using
        `--source-snapshot` in the desired zone. The contents of a
        disk can also be moved across project or zone by creating an
        image (using 'gcloud compute images create') and creating a
        new disk using `--image` in the desired project and/or
        zone.

        When creating disks, be sure to include the `--zone` option:

          $ {command} my-disk-1 my-disk-2 --zone us-east1-a
        """,
}


def _SourceArgs(parser, source_snapshot_arg):
  """Add mutually exclusive source args."""

  source_group = parser.add_mutually_exclusive_group()

  def AddImageHelp():
    """Returns detailed help for `--image` argument."""
    template = """\
        An image to apply to the disks being created. When using
        this option, the size of the disks must be at least as large as
        the image size. Use ``--size'' to adjust the size of the disks.

        This flag is mutually exclusive with ``--source-snapshot'' and
        ``--image-family''.
        """
    return template

  image = source_group.add_argument(
      '--image',
      help='An image to apply to the disks being created.')
  image.detailed_help = AddImageHelp

  image_utils.AddImageProjectFlag(parser)

  source_group.add_argument(
      '--image-family',
      help=('The family of the image that the boot disk will be initialized '
            'with. When a family is used instead of an image, the latest '
            'non-deprecated image associated with that family is used.')
  )
  source_snapshot_arg.AddArgument(source_group)


def _CommonArgs(parser, source_snapshot_arg):
  """Add arguments used for parsing in all command tracks."""
  parser.add_argument(
      '--description',
      help=(
          'An optional, textual description for the disks being created.'))

  size = parser.add_argument(
      '--size',
      type=arg_parsers.BinarySize(
          lower_bound='1GB',
          suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB', 'PiB', 'PB']),
      help='Indicates the size of the disks.')
  size.detailed_help = """\
      Indicates the size of the disks. The value must be a whole
      number followed by a size unit of ``KB'' for kilobyte, ``MB''
      for megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For
      example, ``10GB'' will produce 10 gigabyte disks.  Disk size
      must be a multiple of 10 GB.
      """

  disk_type = parser.add_argument(
      '--type',
      help='Specifies the type of disk to create.')
  disk_type.detailed_help = """\
      Specifies the type of disk to create. To get a
      list of available disk types, run 'gcloud compute
      disk-types list'. The default disk type is pd-standard.
      """

  _SourceArgs(parser, source_snapshot_arg)

  csek_utils.AddCsekKeyArgs(parser)


class Create(base_classes.BaseAsyncCreator, image_utils.ImageExpander,
             zone_utils.ZoneResourceFetcher):
  """Create Google Compute Engine persistent disks."""

  @staticmethod
  def Args(parser):
    disks_flags.DISKS_ARG.AddArgument(parser)
    _CommonArgs(parser, disks_flags.SOURCE_SNAPSHOT_ARG)

  @property
  def service(self):
    return self.compute.disks

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'disks'

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding disks."""
    size_gb = utils.BytesToGb(args.size)

    from_image = args.image or args.image_family
    if not size_gb and not args.source_snapshot and not from_image:
      if args.type and 'pd-ssd' in args.type:
        size_gb = constants.DEFAULT_SSD_DISK_SIZE_GB
      else:
        size_gb = constants.DEFAULT_STANDARD_DISK_SIZE_GB

    utils.WarnIfDiskSizeIsTooSmall(size_gb, args.type)

    requests = []
    disk_refs = disks_flags.DISKS_ARG.ResolveAsResource(
        args, self.resources,
        default_scope=flags.ScopeEnum.ZONE,
        scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))

    # Check if the zone is deprecated or has maintenance coming.
    self.WarnForZonalCreation(disk_refs)

    if from_image:
      source_image_uri, _ = self.ExpandImageFlag(
          args, return_image_resource=False)
    else:
      source_image_uri = None

    snapshot_ref = disks_flags.SOURCE_SNAPSHOT_ARG.ResolveAsResource(
        args, self.resources, default_scope=flags.ScopeEnum.GLOBAL)
    if snapshot_ref:
      snapshot_uri = snapshot_ref.SelfLink()
    else:
      snapshot_uri = None

    # This feature is only exposed in alpha/beta
    allow_rsa_encrypted = self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                                  base.ReleaseTrack.BETA]
    csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)

    image_key_message_or_none, snapshot_key_message_or_none = (
        csek_utils.MaybeLookupKeyMessagesByUri(
            csek_keys, self.resources, [source_image_uri, snapshot_uri],
            self.compute))

    for disk_ref in disk_refs:
      if args.type:
        type_ref = self.CreateZonalReference(
            args.type, disk_ref.zone,
            resource_type='diskTypes')
        type_uri = type_ref.SelfLink()
      else:
        type_uri = None

      if csek_keys:
        disk_key_or_none = csek_keys.LookupKey(
            disk_ref, args.require_csek_key_create)
        disk_key_message_or_none = csek_utils.MaybeToMessage(
            disk_key_or_none, self.compute)
        kwargs = {'diskEncryptionKey': disk_key_message_or_none,
                  'sourceImageEncryptionKey': image_key_message_or_none,
                  'sourceSnapshotEncryptionKey': snapshot_key_message_or_none}
      else:
        kwargs = {}

      request = self.messages.ComputeDisksInsertRequest(
          disk=self.messages.Disk(
              name=disk_ref.Name(),
              description=args.description,
              sizeGb=size_gb,
              sourceSnapshot=snapshot_uri,
              type=type_uri,
              **kwargs),
          project=self.project,
          sourceImage=source_image_uri,
          zone=disk_ref.zone)
      requests.append(request)

    return requests


Create.detailed_help = DETAILED_HELP
