# Copyright 2013 Google Inc. All Rights Reserved.
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

"""The set-managed-by command."""
from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log


class SetManagedBy(base.Command):
  """Sets the policy for the Flexible VMs of the given services and version.

  This command is deprecated. Please use the
  `gcloud app instances enable-debug` and
  `gcloud app instances disable-debug` commands instead.

  This command sets the policy for the App Engine Flexible VMs of the given
  services and version.  When your module uses VM runtimes, you can use this
  command to change the management mode for a set of your VMs.  If you switch to
  self-managed, SSH will be enabled on the VMs, and they will be removed from
  the health checking pools, but will still receive requests.  When you switch
  back to Google-managed mode, any local changes on the VMs are lost and they
  are restarted and added back into the normal pools.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To switch to self-managed mode for a module, run:

            $ {command} default --version=1 --self

          To switch back to Google-managed mode for a module, run:

            $ {command} default --version=1 --google

          To set just a single VM instance of a module to self-managed mode,
          run:

            $ {command} default --version=1 --self --instance=VM_NAME
          """,
  }

  @staticmethod
  def Args(parser):
    flags.SERVER_FLAG.AddToParser(parser)
    flags.VERSION_FLAG.AddToParser(parser)
    flags.MODULES_ARG.AddToParser(parser)
    flags.IGNORE_CERTS_FLAG.AddToParser(parser)

    parser.add_argument(
        '--instance',
        metavar='VM_NAME',
        required=False,
        help='The VM name for the instance  to set the management policy on.  '
        'If not given, all instances will be set.')
    parser_group = parser.add_mutually_exclusive_group(required=True)
    parser_group.add_argument(
        '--google', action='store_true',
        help='Switch the VMs back to being Google managed.  Any local changes '
        'on the VMs will be lost.')
    parser_group.add_argument(
        '--self', action='store_true',
        help='Switch the VMs to self managed mode.  This will allow you SSH '
        'into, and debug your app on these machines.')

  def Run(self, args):
    log.warn('This command is deprecated. Please use the '
             '`gcloud app instances enable-debug` and '
             '`gcloud app instances disable-debug` commands instead.')
    client = appengine_client.AppengineClient(args.server,
                                              args.ignore_bad_certs)
    func = client.SetManagedBySelf if args.self else client.SetManagedByGoogle
    for module in args.modules:
      func(service=module, version=args.version, vm_name=args.instance)
