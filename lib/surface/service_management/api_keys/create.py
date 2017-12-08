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

"""Implementation of the service-management api-keys create command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


SHA_EXAMPLE = 'D8:AA:43:97:59:EE:C5:95:26:6A:07:EE:1C:37:8E:F4:F0:C8:05:C8'
API_KEY_TYPES = set(['browser', 'server', 'android', 'ios'])


class Create(base.Command, base_classes.BaseServiceManagementCommand):
  """Creates an API key for a project."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('--type',
                        '-t',
                        type=lambda x: str(x).lower(),
                        choices=API_KEY_TYPES,
                        default='server',
                        help=('The type of API key to create. '
                              'Choose from {0}. Default is server.'.format(
                                  ', '.join(sorted(API_KEY_TYPES)))))

    parser.add_argument('--name',
                        '-n',
                        dest='display_name',
                        help='The display name of the new API key.')

    parser.add_argument('--allowed-entities',
                        '-e',
                        nargs='*',
                        help=('The entities that should be allowed to use the '
                              'API key created by this command. The type of '
                              'entities to include here depends on the '
                              '--type parameter. If a browser key is to '
                              'be created, this list will be the regular '
                              'expressions of all possible referrer URLs. '
                              'If it\'s an iOS key, this list will be the '
                              'allowed bundle IDs. If it\'s a server key, '
                              'this list will be the allowed IPs. If it\'s an '
                              'Android key, the list will be a set of '
                              'package names and SHA fingerprints, with a '
                              'comma separating the package name and '
                              'fingerprint.'))

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'service-management api-keys create'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the api-keys API call.
    """
    # Verify Android command-line arguments, if applicable
    if args.type == 'android':
      self._VerifyAndroidPackageArgs(args)

    # Construct the Create API Key request object
    request = self._ConstructApiKeyRequest(self.project, args)

    return self.apikeys_client.projects_apiKeys.Create(request)

  def _VerifyAndroidPackageArgs(self, parsed_args):
    # Verify that each Android package is in the correct format
    for package in parsed_args.allowed_entities:
      try:
        _, fingerprint = package.split(',', 1)
      except ValueError:
        raise exceptions.ToolException(
            'Package %s has incorrect format. It should be of the form '
            '\'[PACKAGE_NAME],[FINGERPRINT]\'.' % package)

      # Validate the fingerprint against the regex
      if not services_util.ValidateFingerprint(fingerprint):
        raise exceptions.ToolException(
            'Invalid SHA fingerprint provided (%s).' % fingerprint)

  def _ConstructApiKeyRequest(self, project, parsed_args):
    if parsed_args.type == 'browser':
      key_details = self.apikeys_messages.BrowserKeyDetails()
      if parsed_args.allowed_entities:
        key_details.allowedReferrers.extend(parsed_args.allowed_entities)
      api_key = self.apikeys_messages.ApiKey(browserKeyDetails=key_details)
    elif parsed_args.type == 'server':
      key_details = self.apikeys_messages.ServerKeyDetails()
      if parsed_args.allowed_entities:
        key_details.allowedIps.extend(parsed_args.allowed_entities)
      api_key = self.apikeys_messages.ApiKey(serverKeyDetails=key_details)
    elif parsed_args.type == 'ios':
      key_details = self.apikeys_messages.IosKeyDetails()
      if parsed_args.allowed_entities:
        key_details.allowedBundleIds.extend(parsed_args.allowed_entities)
      api_key = self.apikeys_messages.ApiKey(iosKeyDetails=key_details)
    elif parsed_args.type == 'android':
      def _ConstructAndroidApplication(package, fingerprint):
        return self.apikeys_messages.AndroidApplication(
            sha1Fingerprint=services_util.GetByteStringFromFingerprint(
                fingerprint),
            packageName=package)

      if parsed_args.allowed_entities:
        apps = [p.split(',') for p in parsed_args.allowed_entities]

      key_details = self.apikeys_messages.AndroidKeyDetails()
      key_details.allowedApplications.extend(
          [_ConstructAndroidApplication(p, f) for (p, f) in apps])
      api_key = self.apikeys_messages.ApiKey(androidKeyDetails=key_details)

    api_key.displayName = parsed_args.display_name

    return self.apikeys_messages.ApikeysProjectsApiKeysCreateRequest(
        projectId=project,
        apiKey=api_key)
