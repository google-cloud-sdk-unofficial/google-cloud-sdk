# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Get or provision a Starter Tier project for onboarding."""

from googlecloudsdk.api_lib.onboarding import session_orchestration
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.onboarding import exceptions as onboarding_exceptions
from googlecloudsdk.command_lib.onboarding import user_inputs
from googlecloudsdk.core import log

# Experience ID for getting or provisioning a starter-tier project.
_STARTER_TIER_XP_ID = 'de8dd731-c5da-4669-87e2-318c6142e112'


def _GetProject(session):
  """Extracts the project resource name from a session object."""
  if not session or not session.project:
    return None
  project = session.project
  name = project if isinstance(project, str) else getattr(project, 'name', None)
  if not name:
    return None
  if not name.startswith('projects/'):
    return f'projects/{name}'
  return name


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class GetProject(base.Command):
  """Get or provision a Starter Tier project for onboarding.

  This command starts an interactive session to onboard the user to Google
  Cloud Platform Starter Tier by guiding them through required setup steps.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('none')
    valid_tos = ', '.join(user_inputs.VALID_TOS_IDS)
    parser.add_argument(
        '--auto-accept-tos-ids',
        type=arg_parsers.ArgList(),
        metavar='TOS_ID',
        help=(
            'List of Terms of Service IDs to automatically accept without'
            f' prompting. Valid values are: {valid_tos}.'
        ),
    )

  def Run(self, args):
    with base.WithLegacyQuota():
      client = apis.GetClientInstance('useronboarding', 'v1alpha')
      messages = apis.GetMessagesModule('useronboarding', 'v1alpha')

      intent = messages.OnboardingIntent(
          xpId=_STARTER_TIER_XP_ID,
      )

      session = session_orchestration.ResolveAndOrchestrateSession(
          intent=intent,
          client=client,
          messages=messages,
          auto_accept_tos_ids=args.auto_accept_tos_ids,
      )
      project_id = _GetProject(session)
      if not project_id:
        raise onboarding_exceptions.SessionProtocolError(
            'Session completed successfully, but no project was returned.'
        )
      log.status.Print(f'Project ready: [{project_id}].')
      return project_id
