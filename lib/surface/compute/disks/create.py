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

import argparse
import textwrap

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.api_lib.compute.regions import utils as region_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import create
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.core import log

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
        image (using `gcloud compute images create`) and creating a
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

  source_group.add_argument(
      '--image',
      help=AddImageHelp)

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
  Create.disks_arg.AddArgument(parser)
  parser.add_argument(
      '--description',
      help='An optional, textual description for the disks being created.')

  parser.add_argument(
      '--size',
      type=arg_parsers.BinarySize(
          lower_bound='1GB',
          suggested_binary_size_scales=['GB', 'GiB', 'TB', 'TiB', 'PiB', 'PB']),
      help="""\
      Indicates the size of the disks. The value must be a whole
      number followed by a size unit of ``KB'' for kilobyte, ``MB''
      for megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For
      example, ``10GB'' will produce 10 gigabyte disks.  Disk size
      must be a multiple of 10 GB.
      """)

  parser.add_argument(
      '--type',
      completion_resource='compute.diskTypes',
      help="""\
      Specifies the type of disk to create. To get a
      list of available disk types, run `gcloud compute disk-types list`.
      The default disk type is pd-standard.
      """)

  _SourceArgs(parser, source_snapshot_arg)

  csek_utils.AddCsekKeyArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Create(base.Command):
  """Create Google Compute Engine persistent disks."""

  def Format(self, args):
    return """table(name,
                    zone.basename(),
                    sizeGb,
                    type.basename(),
                    status)"""

  @staticmethod
  def Args(parser):
    Create.disks_arg = disks_flags.MakeDiskArg(plural=True)
    _CommonArgs(parser, disks_flags.SOURCE_SNAPSHOT_ARG)

  def ValidateAndParse(self, args, compute_holder):
    """Validate flags and parse disks references.

    Subclasses may override it to customize parsing.

    Args:
      args: The argument namespace
      compute_holder: base_classes.ComputeApiHolder instance

    Returns:
      List of compute.regionDisks resources.
    """
    return Create.disks_arg.ResolveAsResource(
        args,
        compute_holder.resources,
        scope_lister=flags.GetDefaultScopeLister(compute_holder.client))

  def Run(self, args):
    compute_holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = compute_holder.client

    disk_refs = self.ValidateAndParse(args, compute_holder)

    size_gb = utils.BytesToGb(args.size)

    from_image = args.image or args.image_family
    if not size_gb and not args.source_snapshot and not from_image:
      if args.type and 'pd-ssd' in args.type:
        size_gb = constants.DEFAULT_SSD_DISK_SIZE_GB
      else:
        size_gb = constants.DEFAULT_STANDARD_DISK_SIZE_GB

    utils.WarnIfDiskSizeIsTooSmall(size_gb, args.type)

    requests = []

    # Check if the zone is deprecated or has maintenance coming.
    zone_resource_fetcher = zone_utils.ZoneResourceFetcher(client)
    zone_resource_fetcher.WarnForZonalCreation(
        (ref for ref in disk_refs if ref.Collection() == 'compute.disks'))
    # Check if the region is deprecated or has maintenance coming.
    region_resource_fetcher = region_utils.RegionResourceFetcher(client)
    region_resource_fetcher.WarnForRegionalCreation(
        (ref for ref in disk_refs if ref.Collection() == 'compute.regionDisks'))

    project_to_source_image = {}

    image_expander = image_utils.ImageExpander(client, compute_holder.resources)

    for disk_ref in disk_refs:
      if from_image:
        if disk_ref.project not in project_to_source_image:
          source_image_uri, _ = image_expander.ExpandImageFlag(
              user_project=disk_ref.project,
              image=args.image,
              image_family=args.image_family,
              image_project=args.image_project,
              return_image_resource=False)
          project_to_source_image[disk_ref.project] = argparse.Namespace()
          project_to_source_image[disk_ref.project].uri = source_image_uri
      else:
        project_to_source_image[disk_ref.project] = argparse.Namespace()
        project_to_source_image[disk_ref.project].uri = None

    snapshot_ref = disks_flags.SOURCE_SNAPSHOT_ARG.ResolveAsResource(
        args, compute_holder.resources)
    if snapshot_ref:
      snapshot_uri = snapshot_ref.SelfLink()
    else:
      snapshot_uri = None

    # This feature is only exposed in alpha/beta
    allow_rsa_encrypted = self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                                  base.ReleaseTrack.BETA]
    csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)

    for project in project_to_source_image:
      source_image_uri = project_to_source_image[project].uri
      project_to_source_image[project].keys = (
          csek_utils.MaybeLookupKeyMessagesByUri(
              csek_keys, compute_holder.resources,
              [source_image_uri, snapshot_uri], client.apitools_client))

    for disk_ref in disk_refs:
      if args.type:
        if disk_ref.Collection() == 'compute.disks':
          type_ref = compute_holder.resources.Parse(
              args.type, collection='compute.diskTypes',
              params={'zone': disk_ref.zone})
        elif disk_ref.Collection() == 'compute.regionDisks':
          type_ref = compute_holder.resources.Parse(
              args.type, collection='compute.regionDiskTypes',
              params={'region': disk_ref.region})
        type_uri = type_ref.SelfLink()
      else:
        type_uri = None

      if csek_keys:
        disk_key_or_none = csek_keys.LookupKey(
            disk_ref, args.require_csek_key_create)
        disk_key_message_or_none = csek_utils.MaybeToMessage(
            disk_key_or_none, client.apitools_client)
        kwargs = {'diskEncryptionKey': disk_key_message_or_none,
                  'sourceImageEncryptionKey':
                      project_to_source_image[disk_ref.project].keys[0],
                  'sourceSnapshotEncryptionKey':
                      project_to_source_image[disk_ref.project].keys[1]}
      else:
        kwargs = {}

      if disk_ref.Collection() == 'compute.disks':
        request = client.messages.ComputeDisksInsertRequest(
            disk=client.messages.Disk(
                name=disk_ref.Name(),
                description=args.description,
                sizeGb=size_gb,
                sourceSnapshot=snapshot_uri,
                type=type_uri,
                **kwargs),
            project=disk_ref.project,
            sourceImage=project_to_source_image[disk_ref.project].uri,
            zone=disk_ref.zone)
        request = (client.apitools_client.disks, 'Insert', request)
      elif disk_ref.Collection() == 'compute.regionDisks':
        def SelfLink(zone, disk_ref):
          return compute_holder.resources.Parse(
              zone,
              collection='compute.zones',
              params={
                  'project': disk_ref.project
              }).SelfLink()
        zones = [SelfLink(zone, disk_ref) for zone in args.replica_zones]
        request = client.messages.ComputeRegionDisksInsertRequest(
            disk=client.messages.Disk(
                name=disk_ref.Name(),
                description=args.description,
                sizeGb=size_gb,
                sourceSnapshot=snapshot_uri,
                type=type_uri,
                replicaZones=zones,
                **kwargs),
            project=disk_ref.project,
            sourceImage=project_to_source_image[disk_ref.project].uri,
            region=disk_ref.region)
        request = (client.apitools_client.regionDisks, 'Insert', request)
      requests.append(request)

    return client.MakeRequests(requests)

  def Epilog(self, resources_were_displayed=True):
    message = """\

        New disks are unformatted. You must format and mount a disk before it
        can be used. You can find instructions on how to do this at:

        https://cloud.google.com/compute/docs/disks/add-persistent-disk#formatting
        """
    log.status.Print(textwrap.dedent(message))

Create.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create Google Compute Engine persistent disks."""

  @staticmethod
  def Args(parser):
    Create.disks_arg = disks_flags.MakeDiskArgZonalOrRegional(plural=True)
    parser.add_argument(
        '--replica-zones',
        type=arg_parsers.ArgList(),
        metavar='ZONE1, ZONE2',
        help=('The zones regional disk will be replicated to. Required when '
              'creating regional disk.'),
        hidden=True)

    _CommonArgs(parser, disks_flags.SOURCE_SNAPSHOT_ARG)

  def ValidateAndParse(self, args, compute_holder):
    if args.replica_zones is None and args.region is not None:
      raise exceptions.RequiredArgumentException(
          '--replica-zones',
          '--replica-zones is required for regional disk creation')
    if args.replica_zones is not None:
      if len(args.replica_zones) != 2:
        raise exceptions.InvalidArgumentException(
            '--replica-zones', 'Exactly two zones are required.')
      return create.ParseRegionDisksResources(
          compute_holder.resources, args.DISK_NAME, args.replica_zones,
          args.project, args.region)
    return Create.disks_arg.ResolveAsResource(
        args,
        compute_holder.resources,
        scope_lister=flags.GetDefaultScopeLister(compute_holder.client))
