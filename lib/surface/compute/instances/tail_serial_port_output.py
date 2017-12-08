# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for tailing the serial port output of an instance."""

import time

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class TailSerialPortOutputException(exceptions.Error):
  """An error occurred while tailing the serial port."""


class TailSerialPortOutput(base_classes.BaseCommand):
  """Tail output from a virtual machine instance's serial port."""

  POLL_SLEEP_SECS = 10

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--port',
        type=arg_parsers.BoundedInt(1, 4),
        help="""\
        Instances can support up to four serial port outputs, numbered 1 through
        4. By default, this command will return the output of the first serial
        port. Setting this flag will return the output of the requested serial
        port.
        """)

  @property
  def resource_type(self):
    return 'instances'

  def Run(self, args):
    instance_ref = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))

    start = None
    while True:
      request = (self.compute.instances,
                 'GetSerialPortOutput',
                 self.messages.ComputeInstancesGetSerialPortOutputRequest(
                     instance=instance_ref.Name(),
                     project=self.project,
                     port=args.port,
                     start=start,
                     zone=instance_ref.zone))

      errors = []
      objects = list(request_helper.MakeRequests(
          requests=[request],
          http=self.http,
          batch_url=self.batch_url,
          errors=errors))
      if errors:
        raise TailSerialPortOutputException(
            'Could not fetch serial port output: ' +
            ','.join([error[1] for error in errors]))

      result = objects[0]
      log.out.write(result.contents)
      start = result.next

      # If we didn't get any results, we sleep for a short time before the next
      # call.
      if not result.contents:
        time.sleep(self.POLL_SLEEP_SECS)


TailSerialPortOutput.detailed_help = {
    'brief': """Periodically fetch new output from a virtual machine instance's
    serial port and display it as it becomes available""",
    'DESCRIPTION': """\
        {command} is used to tail the output from a Google Compute
        Engine virtual machine instance's serial port. The serial port output
        from the instance will be printed to standard output. This
        information can be useful for diagnostic purposes.
        """,
}
