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
"""Command for reading the serial port output of an instance."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class GetSerialPortOutputException(exceptions.Error):
  """An error occurred while tailing the serial port."""


class GetSerialPortOutputBase(object):
  """Base class for all GetSerialPortOutput implementations."""

  @staticmethod
  def Args(parser):
    """Add expected arguments."""

    utils.AddZoneFlag(
        parser,
        resource_type='instance',
        operation_type='get serial port output for')

    port = parser.add_argument(
        '--port',
        help=('The number of the requested serial port. '
              'Can be 1-4, default is 1.'),
        type=arg_parsers.BoundedInt(1, 4))
    port.detailed_help = """\
        Instances can support up to four serial port outputs, numbered 1 through
        4. By default, this command will return the output of the first serial
        port. Setting this flag will return the output of the requested serial
        port.
        """

    parser.add_argument(
        'name',
        completion_resource='compute.instances',
        help='The name of the instance.')

  @property
  def resource_type(self):
    return 'instances'


GetSerialPortOutputBase.detailed_help = {
    'brief': "Read output from a virtual machine instance's serial port",
    'DESCRIPTION': """\
        {command} is used to get the output from a Google Compute
        Engine virtual machine's serial port. The serial port output
        from the virtual machine will be printed to standard output. This
        information can be useful for diagnostic purposes.
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base_classes.BaseCommand)
class GetSerialPortOutputAlpha(GetSerialPortOutputBase,
                               base_classes.BaseCommand):
  """Read output from a virtual machine instance's serial port."""

  @staticmethod
  def Args(parser):
    """Add expected arguments."""

    GetSerialPortOutputBase.Args(parser)

    start = parser.add_argument(
        '--start',
        help=('The starting byte position of serial port data requested.'),
        type=int)

    start.detailed_help = """\
        Specifies the byte index (zero-based) of the first byte you want
        returned.  Use this flag if you want to continue getting the output from
        a previous request that was too long to return in one attempt.  The last
        byte returned in a request will be reported on STDERR.
        """

  def Format(self, args):
    # no Display-driven formatting; output is handled in Run method in order to
    # display warnings at end
    return None

  def Run(self, args):
    instance_ref = self.CreateZonalReference(args.name, args.zone)

    request = (self.compute.instances,
               'GetSerialPortOutput',
               self.messages.ComputeInstancesGetSerialPortOutputRequest(
                   instance=instance_ref.Name(),
                   project=self.project,
                   port=args.port,
                   start=args.start,
                   zone=instance_ref.zone))

    errors = []
    objects = list(request_helper.MakeRequests(
        requests=[request],
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None))
    if errors:
      raise GetSerialPortOutputException(
          'Could not fetch serial port output: ' +
          ','.join([error[1] for error in errors]))

    response = objects[0]
    if not args.format:
      log.out.write(response.contents)
      if args.start and response.start != args.start:
        log.warn(
            'Some serial port output was lost due to a limited buffer. The '
            'oldest byte of output returned was at offset {0}.'.format(
                response.start))
      log.status.Print(
          '\nSpecify --start={0} in the next get-serial-port-output invocation '
          'to get only the new output starting from here.'.format(
              response.next))

    return response


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class GetSerialPortOutput(GetSerialPortOutputBase,
                          base_classes.BaseCommand):
  """Read output from a virtual machine instance's serial port."""

  def Run(self, args):
    instance_ref = self.CreateZonalReference(args.name, args.zone)

    request = (self.compute.instances,
               'GetSerialPortOutput',
               self.messages.ComputeInstancesGetSerialPortOutputRequest(
                   instance=instance_ref.Name(),
                   project=self.project,
                   port=args.port,
                   zone=instance_ref.zone))

    errors = []
    objects = list(request_helper.MakeRequests(
        requests=[request],
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None))
    if errors:
      raise GetSerialPortOutputException(
          'Could not fetch serial port output: ' +
          ','.join([error[1] for error in errors]))

    return objects[0].contents

  def Display(self, _, response):
    log.out.write(response)
