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

"""Command for starting an instance."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources


DETAILED_HELP = {
    'DESCRIPTION': """\
        Start a stopped virtual machine instance.

        *{command}* is used to start a stopped Google Compute Engine virtual
        machine. Only a stopped virtual machine can be started.
        """
}


def _CommonArgs(parser):
  """Add parser arguments common to all tracks."""
  flags.AddZoneFlag(
      parser,
      resource_type='instance',
      operation_type='start')

  parser.add_argument(
      'name',
      nargs='+',
      completion_resource='compute.instances',
      help='The names of the instances to start.')

  csek_utils.AddCsekKeyArgs(parser, flags_about_creation=False)


class FailedToFetchInstancesError(exceptions.Error):
  pass


class Start(base_classes.NoOutputAsyncMutator):
  """Start a stopped virtual machine instance."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'StartWithEncryptionKey'

  @property
  def resource_type(self):
    return 'instances'

  def GetInstances(self, refs):
    """Fetches instance objects corresponding to the given references."""
    instance_get_requests = []
    for ref in refs:
      request_protobuf = self.messages.ComputeInstancesGetRequest(
          instance=ref.Name(),
          zone=ref.zone,
          project=ref.project)
      instance_get_requests.append((self.service, 'Get', request_protobuf))

    errors = []
    instances = list(request_helper.MakeRequests(
        requests=instance_get_requests,
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None))
    if errors:
      utils.RaiseException(
          errors,
          FailedToFetchInstancesError,
          error_message='Failed to fetch some instances:')
    return instances

  def CreateRequests(self, args):
    csek_key_file = args.csek_key_file
    request_list = []
    instance_refs = [self.CreateZonalReference(name, args.zone)
                     for name in args.name]
    if csek_key_file:
      instances = self.GetInstances(instance_refs)
    else:
      instances = [None for _ in instance_refs]
    for name, instance_ref, instance in zip(args.name, instance_refs,
                                            instances):
      disks = []

      if csek_key_file:
        allow_rsa_encrypted = self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                                      base.ReleaseTrack.BETA]
        csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)
        for disk in instance.disks:
          disk_resource = resources.Parse(disk.source)

          disk_key_or_none = csek_utils.MaybeLookupKeyMessage(
              csek_keys, disk_resource, self.compute)

          if disk_key_or_none:
            disks.append(self.messages.CustomerEncryptionKeyProtectedDisk(
                diskEncryptionKey=disk_key_or_none,
                source=disk.source))

      if disks:
        encryption_req = self.messages.InstancesStartWithEncryptionKeyRequest(
            disks=disks)

        request = (
            self.compute.instances,
            'StartWithEncryptionKey',
            self.messages.ComputeInstancesStartWithEncryptionKeyRequest(
                instance=instance_ref.Name(),
                instancesStartWithEncryptionKeyRequest=encryption_req,
                project=self.project,
                zone=instance_ref.zone))
      else:
        request = (
            self.compute.instances,
            'Start',
            self.messages.ComputeInstancesStartRequest(
                instance=instance_ref.Name(),
                project=self.project,
                zone=instance_ref.zone))

      request_list.append(request)
    return request_list

  def Format(self, _):
    # There is no need to display anything when starting an
    # instance. Instead, format 'none' consumes the generator returned from
    # Run() # to invoke the logic that waits for the start to complete.
    return 'none'


Start.detailed_help = DETAILED_HELP
