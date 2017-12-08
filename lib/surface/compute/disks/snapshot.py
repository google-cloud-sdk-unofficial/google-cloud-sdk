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
"""Command for snapshotting disks."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import name_generator
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags

DETAILED_HELP = {
    'DESCRIPTION': """\
        Create snapshots of Google Compute Engine persistent disks.

        *{command}* creates snapshots of persistent disks. Snapshots are useful
        for backing up data or copying a persistent disk. Once created,
        snapshots may be managed (listed, deleted, etc.) via
        ``gcloud compute snapshots''.
        """
}


def _CommonArgs(parser):
  """Add parser arguments common to all tracks."""
  parser.add_argument(
      '--description',
      help=('An optional, textual description for the snapshots being '
            'created.'))

  snapshot_names = parser.add_argument(
      '--snapshot-names',
      type=arg_parsers.ArgList(min_length=1),
      action=arg_parsers.FloatingListValuesCatcher(),
      metavar='SNAPSHOT_NAME',
      help='Names to assign to the snapshots.')
  snapshot_names.detailed_help = """\
      Names to assign to the snapshots. Without this option, the
      name of each snapshot will be a random, 16-character
      hexadecimal number that starts with a letter. The values of
      this option run parallel to the disks specified. For example,

        $ {command} my-disk-1 my-disk-2 my-disk-3 --snapshot-names snapshot-1,snapshot-2,snapshot-3

      will result in ``my-disk-1'' being snapshotted as
      ``snapshot-1'', ``my-disk-2'' as ``snapshot-2'', and so on.
      """

  parser.add_argument(
      'disk_names',
      metavar='DISK_NAME',
      nargs='+',
      completion_resource='compute.disks',
      help='The names of the disks to snapshot.')

  flags.AddZoneFlag(
      parser,
      resource_type='disks',
      operation_type='snapshot')

  csek_utils.AddCsekKeyArgs(parser, flags_about_creation=False)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class SnapshotDisks(base_classes.NoOutputAsyncMutator):
  """Create snapshots of Google Compute Engine persistent disks."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  @property
  def service(self):
    return self.compute.disks

  @property
  def custom_get_requests(self):
    return self._target_to_get_request

  @property
  def method(self):
    return 'CreateSnapshot'

  @property
  def resource_type(self):
    return 'snapshots'

  def CreateRequests(self, args):
    """Returns a list of requests necessary for snapshotting disks."""
    if args.snapshot_names:
      if len(args.disk_names) != len(args.snapshot_names):
        raise exceptions.ToolException(
            '[--snapshot-names] must have the same number of values as disks '
            'being snapshotted.')
      snapshot_names = args.snapshot_names
    else:
      # Generates names like "d52jsqy3db4q".
      snapshot_names = [name_generator.GenerateRandomName()
                        for _ in args.disk_names]

    snapshot_refs = [
        self.CreateGlobalReference(snapshot_name, resource_type='snapshots')
        for snapshot_name in snapshot_names]

    self._target_to_get_request = {}

    requests = []
    disk_refs = self.CreateZonalReferences(
        args.disk_names, args.zone, resource_type='disks')

    for disk_ref, snapshot_ref in zip(disk_refs, snapshot_refs):
      # This feature is only exposed in alpha/beta
      allow_rsa_encrypted = self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                                    base.ReleaseTrack.BETA]
      csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)
      disk_key_or_none = csek_utils.MaybeLookupKeyMessage(csek_keys, disk_ref,
                                                          self.compute)

      # TODO(user) drop test after 'guestFlush' goes GA
      if hasattr(args, 'guest_flush') and args.guest_flush:
        request_kwargs = {'guestFlush': True}
      else:
        request_kwargs = {}

      request = self.messages.ComputeDisksCreateSnapshotRequest(
          disk=disk_ref.Name(),
          snapshot=self.messages.Snapshot(
              name=snapshot_ref.Name(),
              description=args.description,
              sourceDiskEncryptionKey=disk_key_or_none
          ),
          project=self.project,
          zone=disk_ref.zone,
          **request_kwargs)
      requests.append(request)

      self._target_to_get_request[disk_ref.SelfLink()] = (
          snapshot_ref.SelfLink(),
          self.compute.snapshots,
          self.messages.ComputeSnapshotsGetRequest(
              snapshot=snapshot_ref.Name(),
              project=self.project))

    return requests


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SnapshotDisksAlpha(SnapshotDisks):
  """Create snapshots of Google Compute Engine persistent disks."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)
    parser.add_argument(
        '--guest-flush',
        action='store_true',
        default=False,
        help=('Create an application consistent snapshot by informing the OS '
              'to prepare for the snapshot process. Currently only supported '
              'on Windows instances using the Volume Shadow Copy Service '
              '(VSS).'))


SnapshotDisks.detailed_help = DETAILED_HELP
SnapshotDisksAlpha.detailed_help = DETAILED_HELP
