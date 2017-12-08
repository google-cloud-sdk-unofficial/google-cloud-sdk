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

"""Command to add IAM policy binding for a resource."""

import httplib

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.api_lib.util import http_retry
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.core.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class AddIamPolicyBinding(base.Command):
  """Add IAM policy binding for a project.

  Adds a policy binding to the IAM policy of a project,
  given a project ID and the binding.
  """

  detailed_help = iam_util.GetDetailedHelpForAddIamPolicyBinding(
      'project', 'example-project-id-1')

  def Collection(self):
    return command_lib_util.PROJECTS_COLLECTION

  def GetUriFunc(self):
    return command_lib_util.ProjectsUriFunc

  @staticmethod
  def Args(parser):
    flags.GetProjectFlag('add IAM policy binding to').AddToParser(parser)
    iam_util.AddArgsForAddIamPolicyBinding(
        parser, 'id', 'cloudresourcemanager.projects')

  # HandleKnownHttpErrors needs to be the first one to handle errors.
  # It needs to be placed after http_error_handler.HandleHttpErrors.
  @http_error_handler.HandleHttpErrors
  @projects_util.HandleKnownHttpErrors
  @http_retry.RetryOnHttpStatus(httplib.CONFLICT)
  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    return projects_api.AddIamPolicyBinding(project_ref, args.member, args.role)
