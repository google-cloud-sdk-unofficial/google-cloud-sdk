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

"""The Set Default command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class SetDefault(base.Command):
  """Set the default serving version for the given modules.

  This command is deprecated. Please use
  `gcloud app services set-traffic` instead.

  This command sets the default serving version for the given modules.
  The default version for a module is served when you visit
  mymodule.myapp.appspot.com.'
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To set the default version for a single module, run:

            $ {command} default --version=1

          To set the default version for multiple modules, run:

            $ {command} module1 module2 --version=1
          """,
  }

  @staticmethod
  def Args(parser):
    flags.SERVER_FLAG.AddToParser(parser)
    flags.VERSION_FLAG.AddToParser(parser)
    flags.MODULES_ARG.AddToParser(parser)

  def Run(self, args):
    log.warn('This command is deprecated. '
             'Please use `gcloud app services set-traffic` instead.')
    client = appengine_api_client.GetApiClient()

    message = ('You are about to set the default serving version to [{version}]'
               ' for the following modules:\n\t'.format(version=args.version))
    message += '\n\t'.join([client.project + '/' + m for m in args.modules])
    console_io.PromptContinue(message=message, cancel_on_no=True)

    for module in args.modules:
      client.SetDefaultVersion(module, args.version)
    log.status.Print('Default serving version set to: ' + args.version)
