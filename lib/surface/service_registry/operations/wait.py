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

"""'opertaions wait' command."""

from googlecloudsdk.api_lib.service_registry import constants
from googlecloudsdk.api_lib.service_registry import write_support
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class Wait(base.Command):
  """Waits on operations in Service Registry to complete.

  Polls until specified Service Registry operations finish or it times out,
  throwing an error if any operations fail or any are left unfinished on
  timeout. The command will wait up to 10 minutes for each operation, polling
  them sequentially.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To wait on a single operation

            $ {command} operation-123

          To wait on multiple operations use a comma separated list

            $ {command} operation-123 operation-456
          """,
  }

  @staticmethod
  def Args(parser):
    """Called by calliope to gather arguments for this command.

    Args:
      parser: argparse parser for specifying command line arguments
    """
    parser.add_argument('operations',
                        help='Names of operations to wait on.',
                        nargs='+')

  def Run(self, args):
    """Runs 'operations wait'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.
    Raises:
      ServiceRegistryError: One or more operations finished with error(s) or
        the wait timed out.
    """
    client = self.context[constants.CLIENT]
    resources = self.context[constants.RESOURCES]
    writer = write_support.ServiceRegistryClient(client, resources)

    failed_operations = []
    for operation in args.operations:
      operation_ref = resources.Parse(
          operation, collection=constants.OPERATIONS_COLLECTION)
      try:
        writer.wait_for_operation(operation_ref)
      except write_support.ServiceRegistryError as error:
        log.Print(error)
        failed_operations.append(operation)

    if failed_operations:
      raise write_support.ServiceRegistryError(
          'There were operations with errors: {0}'.format(failed_operations))

    log.Print('All operations completed successfully.')
