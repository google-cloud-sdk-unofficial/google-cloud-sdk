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

"""The gcloud appengine group."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log


class List(base.ListCommand):
  """List your existing deployed modules and versions.

  This command is deprecated. Please use
  `gcloud app versions list` instead.

  This command lists all the modules and their versions that are currently
  deployed to the App Engine server.  The default serving version for each
  module is indicated with a '*'.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To list all modules and versions, run:

            $ {command}

          To list all versions for a specific set of modules, run:

            $ {command} module1 module2
          """,
  }

  @staticmethod
  def Args(parser):
    flags.SERVER_FLAG.AddToParser(parser)
    flags.MODULES_OPTIONAL_ARG.AddToParser(parser)

  def Collection(self):
    return 'appengine.module_versions'

  def Run(self, args):
    log.warn('This command is deprecated. '
             'Please use `gcloud app versions list` instead.')
    api_client = appengine_api_client.GetApiClient()
    services = api_client.ListServices()
    versions = api_client.ListVersions(services)
    service_versions = []
    for version in versions:
      if args.modules and version.service not in args.modules:
        continue
      service_versions.append({'module': version.service,
                               'version': version.id,
                               'traffic_split': version.traffic_split})

    # Sort so the order is deterministic for testing.
    return sorted(service_versions)
