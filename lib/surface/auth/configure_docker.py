# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Register gcloud as a Docker credential helper."""

import json

from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.docker import credential_utils as cred_utils
from googlecloudsdk.core.util import files as file_utils


class ConfigureDockerError(exceptions.Error):
  """General command error class."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA)
class ConfigureDocker(base.Command):
  """Registers gcloud as a Docker credential helper.

  Adds Docker `credHelper` entry to Docker's configuration file, or creates the
  file if it doesn't exist, which will register gcloud as the credential helper
  for all Google supported Docker registries.

  If Docker configuration already contains a `credHelper` entry it will be
  overwritten.

  See
  https://docs.docker.com/engine/reference/commandline/login/#credential-helpers
  for more details on Docker credential helpers.
  """

  def Run(self, args):
    """Run the configure-docker command."""
    if not file_utils.SearchForExecutableOnPath('gcloud'):
      log.warning('gcloud not in system PATH.\n'
                  'gcloud Docker Credential Helper can be configured but it '
                  'will not work until this is corrected.')

    current_config = cred_utils.Configuration.ReadFromDisk()

    if not current_config.SupportsRegistryHelpers():
      raise ConfigureDockerError(
          'Invalid Docker Version: The version of your Docker client is [{}]; '
          'version [{}] or higher is required to support Docker credential '
          'helpers.'.format(current_config.version,
                            cred_utils.MIN_DOCKER_CONFIG_HELPER_VERSION))

    current_helpers = current_config.GetRegisteredCredentialHelpers()
    new_helpers = cred_utils.GetGcloudCredentialHelperConfig()

    if new_helpers == current_helpers:
      log.status.Print('gcloud credential helpers '
                       'already registered correctly.')
      return

    if current_helpers:
      log.warning(
          'Your config file at [{0}] contains these credential helper '
          'entries:\n\n{1}\nThese will be overwritten.'.format(
              current_config.path, json.dumps(current_helpers, indent=2)))

    console_io.PromptContinue(
        message='The following settings will be added to your Docker '
        'config file located at [{0}]:\n {1}'.format(
            current_config.path,
            json.dumps(new_helpers, indent=2)),
        cancel_on_no=True)

    current_config.RegisterCredentialHelpers()
    log.status.Print('Docker configuration file updated.')
