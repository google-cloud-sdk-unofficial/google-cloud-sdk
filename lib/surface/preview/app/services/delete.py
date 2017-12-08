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
"""`gcloud app services delete` command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.api_lib.app.api import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import text


class ServicesDeleteError(exceptions.Error):
  pass


class VersionsDeleteError(exceptions.Error):
  pass


def DeleteVersions(api_client, services, version):
  """Delete the given version of the given services."""
  errors = {}
  for service in services:
    version_path = '{0}/{1}'.format(service.id, version)
    try:
      with console_io.ProgressTracker('Deleting [{0}]'.format(version_path)):
        api_client.DeleteVersion(service.id, version)
    except (calliope_exceptions.HttpException, operations.OperationError,
            operations.OperationTimeoutError) as err:
      errors[version_path] = str(err)

  if errors:
    printable_errors = {}
    for version_path, error_msg in errors.items():
      printable_errors[version_path] = '[{0}]: {1}'.format(version_path,
                                                           error_msg)
    raise VersionsDeleteError(
        'Issue deleting {0}: [{1}]\n\n'.format(
            text.Pluralize(len(printable_errors), 'version'),
            ', '.join(printable_errors.keys())) +
        '\n\n'.join(printable_errors.values()))


def DeleteServices(api_client, services):
  """Delete the given services."""
  errors = {}
  for service in services:
    try:
      with console_io.ProgressTracker('Deleting [{0}]'.format(service.id)):
        api_client.DeleteService(service.id)
    except (calliope_exceptions.HttpException, operations.OperationError,
            operations.OperationTimeoutError) as err:
      errors[service.id] = str(err)

  if errors:
    printable_errors = {}
    for service_id, error_msg in errors.items():
      printable_errors[service_id] = '[{0}]: {1}'.format(service_id,
                                                         error_msg)
    raise ServicesDeleteError(
        'Issue deleting {0}: [{1}]\n\n'.format(
            text.Pluralize(len(printable_errors), 'service'),
            ', '.join(printable_errors.keys())) +
        '\n\n'.join(printable_errors.values()))


class Delete(base.Command):
  """Delete services in the current project."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete a service (and all of its accompanying versions) in the
          current project, run:

            $ {command} service1

          To delete multiple services (and all of their accompanying versions)
          in the current project, run:

            $ {command} service1 service2
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('services', nargs='+', help='The service(s) to delete.')
    parser.add_argument(
        '--version', help='Delete a specific version of the given service(s).')

  def Run(self, args):
    api_client = appengine_api_client.GetApiClient(self.Http(timeout=None))
    # Why do this? It lets us know if we're missing services up front (fail
    # fast), and we get to control the error messages
    all_services = api_client.ListServices()

    services = service_util.GetMatchingServices(all_services, args.services,
                                                api_client.project)

    if args.version:
      console_io.PromptContinue(
          'Deleting version [{0}] of {1} [{2}].'.format(
              args.version, text.Pluralize(len(services), 'service'),
              ', '.join(map(str, services))),
          cancel_on_no=True)
      DeleteVersions(api_client, services, args.version)
    else:
      console_io.PromptContinue(
          'Deleting {0} [{1}].'.format(
              text.Pluralize(len(services), 'service'),
              ', '.join(map(str, services))),
          cancel_on_no=True)
      DeleteServices(api_client, services)
