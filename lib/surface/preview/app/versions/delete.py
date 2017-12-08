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

"""The Delete command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.app.api import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class VersionsDeleteError(exceptions.Error):
  """Errors occurring when deleting versions."""
  pass


class Delete(base.Command):
  """Delete a specified version.

  You cannot delete a version of a service that is currently receiving traffic.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete a specific version of a specific service, run:

            $ {command} --service myService v1

          or, using resource paths:

            $ {command} myService/v1

          To delete a named version accross all services, run:

            $ {command} v1

          To delete multiple versions of a specific service, run:

            $ {command} delete --service myService v1 v2

          To delete multiple named versions accross all services, run:

            $ {command} delete v1 v2
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('versions', nargs='+', help=(
        'The versions to delete (optionally filtered by the --service flag). '
        'Can also be a resource path (<service name>/<version name> or '
        '<project name>/<service name>/<version name>).'))
    parser.add_argument('--service', '-s',
                        help=('If specified, only delete versions from the '
                              'given service.'))

  def Run(self, args):
    client = appengine_api_client.GetApiClient(self.Http(timeout=None))
    services = client.ListServices()
    versions = version_util.GetMatchingVersions(client.ListVersions(services),
                                                args.versions, args.service,
                                                client.project)

    for version in versions:
      if version.traffic_split:
        # TODO(user): mention `set-traffic` after b/24008284 is fixed.
        # TODO(user): mention `migrate` it's implemented.
        # TODO(user): mention `services delete` after it's implemented.
        raise VersionsDeleteError(
            'Version [{version}] is currently serving {allocation:.2f}% of '
            'traffic for service [{service}].\n\n'
            'Please move all traffic away by deploying a new version with the'
            '`--promote` argument.'.format(
                version=version.id,
                allocation=version.traffic_split * 100,
                service=version.service))
    if versions:
      printer = console_io.ListPrinter('Deleting the following versions:')
      printer.Print(versions, output_stream=log.status)
      console_io.PromptContinue(cancel_on_no=True)
    else:
      log.warn('No matching versions found.')

    errors = {}
    for version in sorted(versions):
      try:
        with console_io.ProgressTracker('Deleting [{0}]'.format(version)):
          client.DeleteVersion(version.service, version.id)
      except (calliope_exceptions.HttpException, operations.OperationError,
              operations.OperationTimeoutError) as err:
        errors[version] = str(err)
    if errors:
      printable_errors = {}
      for version, error_msg in errors.items():
        short_name = '[{0}/{1}]'.format(version.service, version.id)
        printable_errors[short_name] = '{0}: {1}'.format(short_name, error_msg)
      raise VersionsDeleteError(
          'Issues deleting version(s): {0}\n\n'.format(
              ', '.join(printable_errors.keys())) +
          '\n\n'.join(printable_errors.values()))
