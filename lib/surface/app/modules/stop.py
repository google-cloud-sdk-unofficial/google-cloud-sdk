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

"""The Stop command."""

from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log


class Stop(base.Command):
  """Stop serving a specific version of the given modules.

  This command is deprecated. Please use `gcloud app versions stop` instead.

  This command stops serving a specific version of the given modules.  It may
  only be used if the scaling module for your module has been set to manual.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To stop serving a single module, run:

            $ {command} default --version=1

          To stop serving multiple modules, run:

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
             'Please use `gcloud app versions stop` instead.')
    # TODO(user): This fails with "module/version does not exist" even
    # when it exists if the scaling mode is set to auto.  It would be good
    # to improve that error message.
    client = appengine_client.AppengineClient(args.server)
    for module in args.modules:
      client.StopService(service=module, version=args.version)
      log.status.Print('Stopped: {0}/{1}/{2}'.format(
          client.project, module, args.version))
