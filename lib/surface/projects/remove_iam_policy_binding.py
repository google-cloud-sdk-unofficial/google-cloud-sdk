# -*- coding: utf-8 -*- #
# Copyright 2023 Google Inc. All Rights Reserved.
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

"""Command to remove IAM policy binding for a resource."""


from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.util import http_retry
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.command_lib.resource_manager import completers
import six.moves.http_client


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class RemoveIamPolicyBinding(base.Command):
  """Remove IAM policy binding from the IAM policy of a project.

  Removes a policy binding from the IAM policy of a project, given a project ID
  and the binding.
  """

  detailed_help = command_lib_util.GetDetailedHelpForRemoveIamPolicyBinding()

  @classmethod
  def Args(cls, parser):
    flags.GetProjectResourceArg('remove IAM policy binding from').AddToParser(
        parser
    )
    iam_util.AddArgsForRemoveIamPolicyBinding(
        parser,
        role_completer=completers.ProjectsIamRolesCompleter,
        add_condition=True,
    )
    if cls.ReleaseTrack() != base.ReleaseTrack.GA:
      # No-op, kept so existing invocations keep working.
      flags.GetRecommendFlag().AddToParser(parser)

  @http_retry.RetryOnHttpStatus(six.moves.http_client.CONFLICT)
  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.project_id)
    condition = iam_util.ValidateAndExtractConditionMutexRole(args)
    result = projects_api.RemoveIamPolicyBindingWithCondition(
        project_ref, args.member, args.role, condition, args.all
    )
    iam_util.LogSetIamPolicy(args.project_id, 'project')
    return result
