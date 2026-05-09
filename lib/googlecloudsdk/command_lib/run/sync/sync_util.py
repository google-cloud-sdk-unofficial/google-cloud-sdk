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
"""Library to SSH into a Cloud Run Deployment."""

import argparse
import contextlib
import os

from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.run.sync import polling_watcher
from googlecloudsdk.command_lib.run.sync import sync_rule_util
from googlecloudsdk.command_lib.run.sync import syncer as syncer_lib
from googlecloudsdk.core.console import progress_tracker


def NecessaryChangesForInstancesDevSync(
    args: argparse.Namespace,
) -> list[config_changes.ConfigChanger]:
  """Adds necessary changes for instances used by dev sync, if not specified by flags.

  1. Set SSH Enabled for the new Instance
  2. Set port to 8080
  3. Disable invoker IAM check - keep until IAP support is added for Instances
  4. Set ingress to allow all - to generate URL for instance

  TODO: b/498806046 - Remove this function once instances don't require hacks
    to work.

  Args:
    args: The command-line arguments.

  Returns:
    A list of Config Changes objects to apply to the Instances for Dev Sync.
    A list of Config Changes objects to apply to the Instances for Dev Sync.
  """
  changes = [
      config_changes.SetAnnotationChange(
          'run.googleapis.com/ssh-enabled', 'true'
      ),
  ]
  if getattr(args, 'port', None) is None:
    changes.append(config_changes.ContainerPortChange(port='8080'))
  if getattr(args, 'invoker_iam_check', None) is None:
    changes.append(config_changes.InvokerIamChange(invoker_iam_check=False))

  if getattr(args, 'ingress_settings', None) is None:
    changes.append(
        config_changes.SetAnnotationChange(
            service.INGRESS_ANNOTATION, service.INGRESS_ALL
        ),
    )

  return changes


class Sync:
  """Sync into an resource."""

  def __init__(
      self,
      args: argparse.Namespace,
      workload_type: run_ssh.Ssh.WorkloadType,
      source: str,
  ):
    """Initialize the Sync library."""
    self.args = args
    self.workload_type = workload_type
    self.abs_source_dir = os.path.abspath(source)

  def _GetTracker(self):
    """Get the progress tracker for the sync command."""
    stages_list = stages.SyncStages()
    return progress_tracker.StagedProgressTracker(
        'Starting Sync',
        stages_list,
        failure_message='Failed to start sync',
        suppress_output=False,
    )

  def Run(self):
    """Run the sync command."""

    with contextlib.ExitStack() as stack:
      with self._GetTracker() as tracker:
        sync_rules = sync_rule_util.GenerateRules(self.abs_source_dir)
        tracker.CompleteStage(stages.SYNC_RULES)

        is_buildpack = not os.path.exists(
            os.path.join(self.abs_source_dir, 'Dockerfile')
        )
        syncer_instance = syncer_lib.CloudRunSyncer(
            self.args,
            self.workload_type,
            is_buildpack,
            tracker,
        )
        stack.enter_context(syncer_instance)

        tracker.StartStage(stages.ESTABLISH_CONNECTION)
        syncer_instance.PrimeSshConnection()
        tracker.CompleteStage(stages.ESTABLISH_CONNECTION)

      polling_watcher.PollingWatcher(
          self.abs_source_dir,
          sync_rules,
          syncer_instance,
      ).Watch()
