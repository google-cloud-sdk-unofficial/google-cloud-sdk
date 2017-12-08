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
"""The app create command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Create(base.Command):
  """Create an App Engine app within the current Google Cloud Project."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To create an app in the us-central region, run:

              $ {command} --region=us-central

          """,
  }

  @staticmethod
  def Args(parser):
    # TODO(b/29635126): Optional if interactive when `app regions list` is
    # available
    parser.add_argument(
        '--region',
        help=('The region to create the app within.  '
              'Use `gcloud app regions list` to list available regions.'),
        required=True)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    api_client = appengine_api_client.GetApiClient()
    message = 'Creating App Engine application in project [{0}]'.format(project)
    with console_io.ProgressTracker(message):
      api_client.CreateApp(args.region)
    log.status.Print('Success! The app is now created. Please use '
                     '`gcloud app deploy` to deploy your first app.')
