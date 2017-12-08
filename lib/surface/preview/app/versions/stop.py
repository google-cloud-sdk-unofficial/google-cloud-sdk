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

"""The Stop command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class VersionsStopError(exceptions.Error):
  """Errors occurring when stopping versions."""
  pass


class Stop(base.Command):
  """Stop serving specified versions.

  This command stops serving the specified versions. It may only be used if the
  scaling module for your service has been set to manual.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To stop a specific version across all services, run:

            $ {command} v1

          To stop multiple named versions across all services, run:

            $ {command} v1 v2

          To stop a single version on a single service, run:

            $ {command} servicename/v1

          or

            $ {command} --service servicename v1

          To stop multiple versions in a single service, run:

            $ {command} --service servicename v1 v2

          Note that that last example may be more simply written using the
          `services stop` command (see its documentation for details).
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('versions', nargs='+', help=(
        'The versions to stop (optionally filtered by the --service flag). '
        'Can also be a resource path (<service name>/<version name> or '
        '<project name>/<service name>/<version name>).'))
    parser.add_argument('--service', '-s',
                        help=('If specified, only stop versions from the '
                              'given service.'))

  def Run(self, args):
    # TODO(user): This fails with "module/version does not exist" even
    # when it exists if the scaling mode is set to auto.  It would be good
    # to improve that error message.
    api_client = appengine_api_client.GetApiClient()
    services = api_client.ListServices()
    versions = version_util.GetMatchingVersions(
        api_client.ListVersions(services),
        args.versions, args.service)

    if versions:
      printer = console_io.ListPrinter('Stopping the following versions:')
      printer.Print(versions, output_stream=log.status)
      console_io.PromptContinue(cancel_on_no=True)
    else:
      log.warn('No matching versions found.')

    client = appengine_client.AppengineClient()
    errors = []
    for version in sorted(versions):
      try:
        with console_io.ProgressTracker('Stopping [{0}]'.format(version)):
          client.StopModule(module=version.service, version=version.id)
      except util.RPCError as err:
        errors.append(str(err))
    if errors:
      raise VersionsStopError('\n\n'.join(errors))
