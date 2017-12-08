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

"""The Delete command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.Command):
  """Delete a specific version of the given modules.

  This command is deprecated. Please use `gcloud app versions delete` instead.

  This command deletes the specified version of the given modules from the
  App Engine server.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete a version from a single module, run:

            $ {command} default --version=1

          To delete a single version from multiple modules, run:

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
             'Please use `gcloud app versions delete` instead.')
    api_client = appengine_api_client.GetApiClient()

    message = 'You are about to delete the following module versions:\n\t'
    message += '\n\t'.join(
        ['{0}/{1}/{2}'.format(api_client.project, m, args.version)
         for m in args.modules])
    console_io.PromptContinue(message=message, cancel_on_no=True)

    # Will delete each specified version.
    # In event of a failure, will still attempt to delete the remaining modules.
    # Prints out a warning or error as appropriate for each module deletion.
    delete_results = []
    for module in args.modules:
      delete_results.append(api_client.DeleteVersion(module, args.version))
    if not all(delete_results):
      raise exceptions.ToolException('Not all deletions succeeded.')
