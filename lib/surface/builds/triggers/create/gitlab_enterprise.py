# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Create GitLab Enterprise trigger command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import trigger_config as trigger_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateGitLab(base.CreateCommand):
  """Create a build trigger for a GitLab Enterprise repository."""

  detailed_help = {
      'EXAMPLES':
          """\
            To create a push trigger for all branches:

              $ {command} --name="my-trigger" --service-account="projects/my-project/serviceAccounts/my-byosa@my-project.iam.gserviceaccount.com" --project-namespace="cloud-builders" --gitlab-config-resource="projects/1234/locations/global/gitLabConfigs/5678" --branch-pattern=".*" --build-config="cloudbuild.yaml"

            To create a pull request trigger for main:

              $ {command} --name="my-trigger" --service-account="projects/my-project/serviceAccounts/my-byosa@my-project.iam.gserviceaccount.com" --project-namespace="cloud-builders" --gitlab-config-resource="projects/1234/locations/global/gitLabConfigs/5678" --pull-request-pattern="^main$" --build-config="cloudbuild.yaml"
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    messages = cloudbuild_util.GetMessagesModule()
    flag_config = trigger_utils.AddGitLabEnterpriseTriggerArgs(parser)
    flag_config.add_argument(
        '--project-namespace', help='GitLab project namespace.', required=True)
    flag_config.add_argument(
        '--gitlab-config-resource',
        help='GitLab config resource name.',
        required=True)
    ref_config = flag_config.add_mutually_exclusive_group(required=True)
    trigger_utils.AddBranchPattern(ref_config)
    trigger_utils.AddTagPattern(ref_config)
    pr_config = ref_config.add_argument_group(help='Pull Request settings')
    pr_config.add_argument(
        '--pull-request-pattern',
        metavar='REGEX',
        required=True,
        help="""\
Regular expression specifying which base git branch to match for
pull request events.

This pattern is used as a regex search for the base branch (the branch you are
trying to merge into) for pull request updates.
For example, --pull-request-pattern=foo will match "foo", "foobar", and "barfoo".

The syntax of the regular expressions accepted is the syntax accepted by
RE2 and described at https://github.com/google/re2/wiki/Syntax.
""")
    pr_config.add_argument(
        '--comment-control',
        default=messages.PullRequestFilter.CommentControlValueValuesEnum
        .COMMENTS_ENABLED,
        help='Require a repository collaborator or owner to comment \'/gcbrun\' on a pull request before running the build.'
    )

    trigger_utils.AddGitLabEnterpriseBuildConfigArgs(flag_config)
    trigger_utils.AddRepoEventArgs(flag_config)

  def ParseTriggerFromFlags(self, args):
    """Parses command line arguments into a build trigger.

    Args:
      args: An argparse arguments object.

    Returns:
      A build trigger object.

    Raises:
      RequiredArgumentException: If comment_control is defined but
      pull_request_pattern isn't.
    """
    project = properties.VALUES.core.project.Get(required=True)
    messages = cloudbuild_util.GetMessagesModule()

    trigger, done = trigger_utils.ParseTriggerArgs(args, messages)
    if done:
      return trigger

    # GitLab Enterprise config
    gl = messages.GitLabEventsConfig(
        projectNamespace=args.project_namespace,
        gitlabConfigResource=args.gitlab_config_resource)
    if args.pull_request_pattern:
      gl.pullRequest = messages.PullRequestFilter(
          branch=args.pull_request_pattern)
      if args.comment_control:
        gl.pullRequest.commentControl = messages.PullRequestFilter.CommentControlValueValuesEnum(
            args.comment_control)
    else:
      # Push event
      gl.push = messages.PushFilter(
          branch=args.branch_pattern, tag=args.tag_pattern)
    trigger.gitlabEnterpriseEventsConfig = gl

    default_image = 'gcr.io/%s/gitlab-%s:$COMMIT_SHA' % (project,
                                                         args.project_namespace)
    trigger_utils.ParseBuildConfigArgs(trigger, args, messages, default_image)
    trigger_utils.ParseRepoEventArgs(trigger, args)

    return trigger

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some values that we want to print later.
    """

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()

    trigger = self.ParseTriggerFromFlags(args)

    # Send the Create request
    project = properties.VALUES.core.project.Get(required=True)
    regionprop = properties.VALUES.builds.region.Get()
    location = args.region or regionprop or cloudbuild_util.DEFAULT_REGION
    parent = resources.REGISTRY.Create(
        collection='cloudbuild.projects.locations',
        projectsId=project,
        locationsId=location).RelativeName()
    created_trigger = client.projects_locations_triggers.Create(
        messages.CloudbuildProjectsLocationsTriggersCreateRequest(
            parent=parent, buildTrigger=trigger))

    trigger_resource = resources.REGISTRY.Parse(
        None,
        collection='cloudbuild.projects.locations.triggers',
        api_version='v1',
        params={
            'projectsId': project,
            'locationsId': args.region,
            'triggersId': created_trigger.id,
        })
    log.CreatedResource(trigger_resource)

    return created_trigger
