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

"""Command to create a new project."""

import httplib
import sys

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.command_lib.util import labels_util

from googlecloudsdk.core import log


ID_DESCRIPTION = ('Project IDs must start with a lowercase letter and can '
                  'have lowercase ASCII letters, digits or hyphens. '
                  'Project IDs must be between 6 and 30 characters.')


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new project.

  Creates a new project with the given project ID.

  ## EXAMPLES

  The following command creates a project with ID `example-foo-bar-1`, name
  `Happy project` and label `type=happy`:

    $ {command} example-foo-bar-1 --name="Happy project" --labels=type=happy
  """

  def Collection(self):
    return command_lib_util.PROJECTS_COLLECTION

  def GetUriFunc(self):
    return command_lib_util.ProjectsUriFunc

  @staticmethod
  def Args(parser):
    labels_util.AddCreateLabelsFlags(parser)
    type_ = arg_parsers.RegexpValidator(
        r'[a-z][a-z0-9-]{5,29}',
        ID_DESCRIPTION)
    project_id = parser.add_argument(
        'id', metavar='PROJECT_ID', type=type_,
        help='ID for the project you want to create.')
    project_id.detailed_help = ('ID for the project you want to create.'
                                '\n\n{0}'.format(ID_DESCRIPTION))
    parser.add_argument('--name',
                        help='Name for the project you want to create. '
                             'If not specified, will use project id as name.')
    parser.add_argument('--enable-cloud-apis',
                        action='store_true',
                        default=True,
                        help='Enable cloudapis.googleapis.com during creation.')

  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    try:
      result = projects_api.Create(
          project_ref,
          args.name,
          args.enable_cloud_apis,
          update_labels=labels_util.GetUpdateLabelsDictFromArgs(args))
    except apitools_exceptions.HttpError as error:
      if error.status_code == httplib.CONFLICT:
        msg = ('Project creation failed. The project ID you specified is '
               'already in use by another project. Please try an alternative '
               'ID.')
        unused_type, unused_value, traceback = sys.exc_info()
        raise exceptions.HttpException, msg, traceback
      raise
    log.CreatedResource(project_ref)
    return result

