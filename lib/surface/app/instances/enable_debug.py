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

"""The `app instances enable-debug` command."""

import operator

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class EnableDebug(base.Command):
  """Enables debug mode for an instance.

  When in debug mode, SSH will be enabled on the VMs, and you can use
  `gcloud compute ssh` to login to them. They will be removed from the health
  checking pools, but they still receive requests.

  Note that any local changes to an instance will be **lost** and the instance
  restarted if debug mode is disabled on the instance.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To enable debug mode for a particular instance, run:

              $ {command} --service=service --version=version gae-default-v1-nwz0

          To enable debug mode for an instance chosen interactively, run:

              $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    flags.SERVER_FLAG.AddToParser(parser)
    flags.IGNORE_CERTS_FLAG.AddToParser(parser)
    instance = parser.add_argument(
        'instance', nargs='?',
        help=('The instance to enable debug mode on.'))
    instance.detailed_help = (
        'The instance ID to enable debug mode on. If not specified, '
        'select instance interactively. Must uniquely specify (with other '
        'flags) exactly one instance')

    service = parser.add_argument(
        '--service', '-s',
        help='Only match instances belonging to this service.')
    service.detailed_help = (
        'If specified, only match instances belonging to the given service. '
        'This affects both interactive and non-interactive selection.')

    version = parser.add_argument(
        '--version', '-v',
        help='Only match instances belonging to this version.')
    version.detailed_help = (
        'If specified, only match instances belonging to the given version. '
        'This affects both interactive and non-interactive selection.')

  def Run(self, args):
    api_client = appengine_api_client.GetApiClient()
    client = appengine_client.AppengineClient(args.server,
                                              args.ignore_bad_certs)

    all_instances = api_client.GetAllInstances(args.service, args.version)
    # Only VM instances can be placed in debug mode for now.
    all_instances = filter(operator.attrgetter('instance.vmName'),
                           all_instances)
    instance = instances_util.GetMatchingInstance(
        all_instances, service=args.service, version=args.version,
        instance=args.instance)

    console_io.PromptContinue(
        'Enabling debug mode for instance [{0}].'.format(instance),
        cancel_on_no=True)
    # TODO(b/29059251): When switching to Zeus, stop using vm_name and use id
    # directly.
    client.SetManagedBySelf(service=instance.service,
                            version=instance.version,
                            vm_name=instance.instance.vmName)
    log.status.Print('Enabled debug mode for instance [{0}].'.format(instance))
