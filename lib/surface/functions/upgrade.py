# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Upgrade a 1st gen Cloud Function to the 2nd gen environment."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.functions import api_enablement
from googlecloudsdk.api_lib.functions.v2 import client as client_v2
from googlecloudsdk.api_lib.functions.v2 import exceptions
from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import types as trigger_types
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v2 import deploy_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

import six

UpgradeAction = collections.namedtuple(
    'UpgradeAction',
    [
        'target_state',
        'prompt_msg',
        'op_description',
        'success_msg',
    ],
)

# TODO(b/272771821): Standardize upgrade related strings.
_SETUP_CONFIG_ACTION = UpgradeAction(
    target_state='SETUP_FUNCTION_UPGRADE_CONFIG_SUCCESSFUL',
    prompt_msg=(
        'This will duplicate the code and configuration of 1st gen function'
        ' [{}] to the 2nd gen environment. This will not affect production'
        ' traffic. Billing and performance of the 2nd gen function may differ.'
        ' To learn more about the differences between 1st gen and 2nd'
        ' functions, visit:'
        ' https://cloud.google.com/functions/docs/concepts/version-comparison'
    ),
    op_description=(
        'Setting up the upgrade config and copying the function to the 2nd'
        ' gen environment'
    ),
    success_msg=(
        'Your 2nd gen function copy is now ready for testing. View the'
        ' function upgrade testing guide for ideas on how to test your'
        ' function before redirecting production traffic to it.'
        # TODO(b/265016036): Link to the user test guide for upgrade.
        '\n\nOnce you are ready to redirect production traffic, rerun this'
        ' command with the --redirect-traffic flag.'
    ),
)

_REDIRECT_TRAFFIC_ACTION = UpgradeAction(
    target_state='REDIRECT_FUNCTION_UPGRADE_TRAFFIC_SUCCESSFUL',
    prompt_msg=(
        'This will redirect all production traffic from 1st gen function [{}]'
        ' to its 2nd gen function copy. Please ensure you have tested the 2nd'
        ' gen function before proceeding.'
    ),
    op_description='Redirecting traffic to your 2nd gen function',
    success_msg=(
        'Your 2nd gen function is now serving all of your production traffic.'
        ' If you experience issues, rerun this command with the'
        ' --rollback-traffic flag. Otherwise, once you are ready to finalize'
        ' the upgrade, rerun this command with the --commit flag.'
    ),
)

_ROLLBACK_TRAFFIC_ACTION = UpgradeAction(
    target_state='SETUP_FUNCTION_UPGRADE_CONFIG_SUCCESSFUL',
    prompt_msg=(
        'This will rollback all production traffic from 2nd gen function [{}]'
        ' to the original 1st gen function copy. Your 2nd gen function copy'
        ' will still be available for manual testing.'
    ),
    op_description='Rolling back traffic to your 1st gen function',
    success_msg=(
        'Your 1st gen function is now serving all of your production traffic.'
        ' Once you are ready to redirect traffic to the 2nd gen function copy,'
        ' rerun this command with the --redirect-traffic flag.'
    ),
)

_ABORT_ACTION = UpgradeAction(
    target_state='ELIGIBLE_FOR_2ND_GEN_UPGRADE',
    prompt_msg=(
        'This will abort the generation upgrade process and delete the 2nd gen'
        ' function copy for 1st gen function [{}].'
    ),
    op_description='Aborting the function upgrade',
    success_msg=(
        'The 2nd gen function copy and configuration were successfully deleted.'
    ),
)

_COMMIT_ACTION = UpgradeAction(
    target_state=None,
    prompt_msg=(
        'This will finish the upgrade process for function [{}] and permanently'
        ' delete the original 1st gen function copy. This action cannot be'
        ' undone.'
    ),
    op_description=(
        'Committing the function upgrade and deleting the 1st gen function copy'
    ),
    success_msg=(
        'The 1st gen function copy and configuration were successfully deleted.'
    ),
)

# Source: http://cs/f:UpgradeStateMachine.java
_VALID_TRANSITION_ACTIONS = {
    'ELIGIBLE_FOR_2ND_GEN_UPGRADE': [_SETUP_CONFIG_ACTION],
    'UPGRADE_OPERATION_IN_PROGRESS': [],
    'SETUP_FUNCTION_UPGRADE_CONFIG_SUCCESSFUL': [
        _REDIRECT_TRAFFIC_ACTION,
        _ABORT_ACTION,
    ],
    'SETUP_FUNCTION_UPGRADE_CONFIG_ERROR': [
        _SETUP_CONFIG_ACTION,
        _ABORT_ACTION,
    ],
    'ABORT_FUNCTION_UPGRADE_ERROR': [_ABORT_ACTION],
    'REDIRECT_FUNCTION_UPGRADE_TRAFFIC_SUCCESSFUL': [
        _COMMIT_ACTION,
        _ROLLBACK_TRAFFIC_ACTION,
        _ABORT_ACTION,
    ],
    'REDIRECT_FUNCTION_UPGRADE_TRAFFIC_ERROR': [
        _REDIRECT_TRAFFIC_ACTION,
        _ABORT_ACTION,
    ],
    'ROLLBACK_FUNCTION_UPGRADE_TRAFFIC_ERROR': [
        _ROLLBACK_TRAFFIC_ACTION,
        _ABORT_ACTION,
    ],
    'COMMIT_FUNCTION_UPGRADE_SUCCESSFUL': [],
    'COMMIT_FUNCTION_UPGRADE_ERROR': [_COMMIT_ACTION, _ABORT_ACTION],
}  # type: dict[str, UpgradeAction]


def _ValidateStateTransition(upgrade_state, action):
  # type: (_,UpgradeAction) -> None
  """Validates whether the action is a valid action for the given upgrade state."""
  upgrade_state_str = six.text_type(upgrade_state)
  if upgrade_state_str == 'UPGRADE_OPERATION_IN_PROGRESS':
    raise exceptions.FunctionsError(
        'An upgrade operation is already in progress for this function.'
        ' Please try again later.'
    )

  if upgrade_state_str == action.target_state:
    raise exceptions.FunctionsError(
        'This function is already in the desired upgrade state: {}'.format(
            upgrade_state
        )
    )

  if action not in _VALID_TRANSITION_ACTIONS[upgrade_state_str]:
    raise exceptions.FunctionsError(
        'This function is not eligible for this operation. Its current upgrade'
        " state is '{}'.".format(upgrade_state)
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpgradeAlpha(base.Command):
  """Upgrade a 1st gen Cloud Function to the 2nd gen environment."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To start the upgrade process for a 1st gen function `foo` and create a 2nd gen function copy, run:

            $ {command} foo

          Once you are ready to redirect production traffic to the 2nd gen function copy, run:

            $ {command} foo --redirect-traffic

          If you find you need to do more local testing you can rollback
          production traffic to the 1st gen function copy:

            $ {command} foo --rollback-traffic

          Once you're ready to finish upgrading and delete the 1st gen function copy, run:

            $ {command} foo --commit

          You can abort the generation upgrade process at any time by running:

            $ {command} foo --abort
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddFunctionResourceArg(parser, 'to upgrade')
    flags.AddUpgradeFlags(parser)

  def Run(self, args):
    client = client_v2.FunctionsClient(self.ReleaseTrack())
    function_ref = args.CONCEPTS.name.Parse()
    function_name = function_ref.RelativeName()

    function = client.GetFunction(function_name)

    if not function:
      raise exceptions.FunctionsError(
          'Function [{}] does not exist.'.format(function_name)
      )

    if not function.upgradeInfo:
      # TODO(b/271030987): Provide additional info on why a function is not
      # eligible for an upgrade.
      raise exceptions.FunctionsError(
          'Function [{}] is not eligible for 2nd gen upgrade.'.format(
              function_name
          )
      )

    upgrade_state = function.upgradeInfo.upgradeState

    action = None
    action_fn = None
    if args.redirect_traffic:
      action = _REDIRECT_TRAFFIC_ACTION
      action_fn = client.RedirectFunctionUpgradeTraffic
    elif args.rollback_traffic:
      action = _ROLLBACK_TRAFFIC_ACTION
      action_fn = client.RollbackFunctionUpgradeTraffic
    elif args.commit:
      action = _COMMIT_ACTION
      action_fn = client.CommitFunctionUpgrade
    elif args.abort:
      action = _ABORT_ACTION
      action_fn = client.AbortFunctionUpgrade
    else:
      action = _SETUP_CONFIG_ACTION
      action_fn = client.SetupFunctionUpgradeConfig

    _ValidateStateTransition(upgrade_state, action)

    message = action.prompt_msg.format(function_name)
    if not console_io.PromptContinue(message, default=True):
      return

    if action == _SETUP_CONFIG_ACTION:
      # Preliminary checks to ensure APIs and permissions are set up in case
      # this is the user's first time deploying a 2nd gen function.
      api_enablement.PromptToEnableApiIfDisabled('cloudbuild.googleapis.com')
      api_enablement.PromptToEnableApiIfDisabled(
          'artifactregistry.googleapis.com'
      )
      trigger = function.eventTrigger
      if trigger and trigger_types.IsPubsubType(trigger.eventType):
        deploy_util.ensure_pubsub_sa_has_token_creator_role()
      if trigger and trigger_types.IsAuditLogType(trigger.eventType):
        deploy_util.ensure_data_access_logs_are_enabled(trigger.eventFilters)

    operation = action_fn(function_name)
    description = action.op_description
    api_util.WaitForOperation(
        client.client, client.messages, operation, description
    )

    log.status.Print()
    log.status.Print(action.success_msg)
    log.status.Print(
        'You can abort the upgrade process at any time by rerunning this'
        ' command with the --abort flag.'
    )
