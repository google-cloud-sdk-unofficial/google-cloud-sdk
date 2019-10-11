# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Implements command to execute an OS patch on the specified VM instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.resource import resource_projector
import six


def _AddTopLevelArguments(parser):
  """Add top-level argument flags."""
  parser.add_argument(
      '--instance-filter',
      required=True,
      type=str,
      help="""\
      Filter for selecting the instances to patch. Patching supports the same
      filter mechanisms as `gcloud compute instances list`, allowing one to
      patch specific instances by name, zone, label, or other criteria.""",
  )
  base.ASYNC_FLAG.AddToParser(parser)
  parser.add_argument(
      '--description', type=str, help='Textual description of the patch job.')
  parser.add_argument(
      '--dry-run',
      action='store_true',
      help="""\
      Whether to execute this patch job as a dry run. If this patch job is a dry
      run, instances are contacted, but the patch is not run.""",
  )
  parser.add_argument(
      '--duration',
      type=arg_parsers.Duration(),
      help="""\
      Total duration in which the patch job must complete. If the patch does not
      complete in this time, the process times out. While some instances might
      still be running the patch, they will not continue to work after
      completing the current step. See $ gcloud topic datetimes for information
      on specifying absolute time durations.

      If unspecified, the job stays active until all instances complete the
      patch.""",
  )
  base.ChoiceArgument(
      '--reboot-config',
      help_str='Post-patch reboot settings.',
      choices={
          'default':
              """\
          The agent decides if a reboot is necessary by checking signals such as
          registry keys or '/var/run/reboot-required'.""",
          'always':
              """Always reboot the machine after the update completes.""",
          'never':
              """Never reboot the machine after the update completes.""",
      },
  ).AddToParser(parser)
  parser.add_argument(
      '--retry',
      action='store_true',
      help="""\
      Specifies whether to attempt to retry, within the duration window, if
      patching initially fails. If omitted, the agent uses its default retry
      strategy.""",
  )


def _AddAptGroupArguments(parser):
  """Add Apt setting flags."""
  apt_group = parser.add_group(help='Settings for machines running Apt:')
  apt_group.add_argument(
      '--apt-dist',
      action='store_true',
      help="""\
      If specified, machines running Apt use the `apt-get dist-upgrade` command;
      otherwise the `apt-get upgrade` command is used.""",
  )


def _AddWinGroupArguments(parser):
  """Add Windows setting flags."""
  win_group = parser.add_group(help='Settings for machines running Windows:')
  win_group.add_argument(
      '--windows-classifications',
      metavar='WINDOWS_CLASSIFICATIONS',
      type=arg_parsers.ArgList(choices=[
          'critical', 'security', 'definition', 'driver', 'feature-pack',
          'service-pack', 'tool', 'update-rollup', 'update'
      ]),
      help="""\
      List of classifications to use to restrict the Windows update. Only
      patches of the given classifications are applied. If omitted, a default
      Windows update is performed. For more information on classifications,
      see: https://support.microsoft.com/en-us/help/824684""",
  )
  win_group.add_argument(
      '--windows-excludes',
      metavar='WINDOWS_EXCLUDES',
      type=arg_parsers.ArgList(),
      help="""Optional list of KBs to exclude from the update operation.""",
  )


def _AddYumGroupArguments(parser):
  """Add Yum setting flags."""
  yum_group = parser.add_group(help='Settings for machines running Yum:')
  yum_group.add_argument(
      '--yum-security',
      action='store_true',
      help="""\
      If specified, machines running Yum append the `--security` flag to the
      patch command.""",
  )
  yum_group.add_argument(
      '--yum-minimal',
      action='store_true',
      help="""\
      If specified, machines running Yum use the command `yum update-minimal`;
      otherwise the patch uses `yum-update`.""",
  )
  yum_group.add_argument(
      '--yum-excludes',
      metavar='YUM_EXCLUDES',
      type=arg_parsers.ArgList(),
      help="""\
      Optional list of packages to exclude from updating. If this argument is
      specified, machines running Yum exclude the given list of packages using
      the Yum `--exclude` flag.""",
  )


def _AddZypperGroupArguments(parser):
  """Add Zypper setting flags."""
  zypper_group = parser.add_group(help='Settings for machines running Zypper:')
  zypper_group.add_argument(
      '--zypper-categories',
      metavar='ZYPPER_CATEGORIES',
      type=arg_parsers.ArgList(),
      help="""\
      If specified, machines running Zypper install only patches with the
      specified categories. Categories include security, recommended, and
      feature.""",
  )
  zypper_group.add_argument(
      '--zypper-severities',
      metavar='ZYPPER_SEVERITIES',
      type=arg_parsers.ArgList(),
      help="""\
      If specified, machines running Zypper install only patch with the
      specified severities. Severities include critical, important, moderate,
      and low.""",
  )
  zypper_group.add_argument(
      '--zypper-with-optional',
      action='store_true',
      help="""\
      If specified, machines running Zypper add the `--with-optional` flag to
      `zypper patch`.""",
  )
  zypper_group.add_argument(
      '--zypper-with-update',
      action='store_true',
      help="""\
      If specified, machines running Zypper add the `--with-update` flag to
      `zypper patch`.""",
  )


def _AddPrePostStepArguments(parser):
  """Add pre-/post-patch setting flags."""
  pre_patch_linux_group = parser.add_group(
      help='Pre-patch step settings for Linux machines:')
  pre_patch_linux_group.add_argument(
      '--pre-patch-linux-executable',
      help="""\
      A set of commands to run on a Linux machine before an OS patch begins.
      Commands must be supplied in a file. If the file contains a shell script,
      include the shebang line.

      The path to the file must be supplied in one of the following formats:

      An absolute path of the file on the local filesystem.

      A URI for a Google Cloud Storage object with a generation number.
      """,
  )
  pre_patch_linux_group.add_argument(
      '--pre-patch-linux-success-codes',
      type=arg_parsers.ArgList(element_type=int),
      metavar='PRE_PATCH_LINUX_SUCCESS_CODES',
      help="""\
      Additional exit codes that the executable can return to indicate a
      successful run. The default exit code for success is 0.""",
  )
  post_patch_linux_group = parser.add_group(
      help='Post-patch step settings for Linux machines:')
  post_patch_linux_group.add_argument(
      '--post-patch-linux-executable',
      help="""\
      A set of commands to run on a Linux machine after an OS patch completes.
      Commands must be supplied in a file. If the file contains a shell script,
      include the shebang line.

      The path to the file must be supplied in one of the following formats:

      An absolute path of the file on the local filesystem.

      A URI for a Google Cloud Storage object with a generation number.
      """,
  )
  post_patch_linux_group.add_argument(
      '--post-patch-linux-success-codes',
      type=arg_parsers.ArgList(element_type=int),
      metavar='POST_PATCH_LINUX_SUCCESS_CODES',
      help="""\
      Additional exit codes that the executable can return to indicate a
      successful run. The default exit code for success is 0.""",
  )

  pre_patch_windows_group = parser.add_group(
      help='Pre-patch step settings for Windows machines:')
  pre_patch_windows_group.add_argument(
      '--pre-patch-windows-executable',
      help="""\
      A set of commands to run on a Windows machine before an OS patch begins.
      Commands must be supplied in a file. If the file contains a PowerShell
      script, include the .ps1 file extension.

      The path to the file must be supplied in one of the following formats:

      An absolute path of the file on the local filesystem.

      A URI for a Google Cloud Storage object with a generation number.
      """,
  )
  pre_patch_windows_group.add_argument(
      '--pre-patch-windows-success-codes',
      type=arg_parsers.ArgList(element_type=int),
      metavar='PRE_PATCH_WINDOWS_SUCCESS_CODES',
      help="""\
      Additional exit codes that the executable can return to indicate a
      successful run. The default exit code for success is 0.""",
  )

  post_patch_windows_group = parser.add_group(
      help='Post-patch step settings for Windows machines:')
  post_patch_windows_group.add_argument(
      '--post-patch-windows-executable',
      help="""\
      A set of commands to run on a Windows machine after an OS patch completes.
      Commands must be supplied in a file. If the file contains a PowerShell
      script, include the .ps1 file extension.

      The path to the file must be supplied in one of the following formats:

      An absolute path of the file on the local filesystem.

      A URI for a Google Cloud Storage object with a generation number.
      """,
  )
  post_patch_windows_group.add_argument(
      '--post-patch-windows-success-codes',
      type=arg_parsers.ArgList(element_type=int),
      metavar='POST_PATCH_WINDOWS_SUCCESS_CODES',
      help="""\
      Additional exit codes that the executable can return to indicate a
      successful run. The default exit code for success is 0.""",
  )


def _GetWindowsUpdateSettings(args, messages):
  """Create WindowsUpdateSettings from input arguments."""
  if args.windows_classifications or args.windows_excludes:
    enums = messages.WindowsUpdateSettings.ClassificationsValueListEntryValuesEnum
    classifications = [
        arg_utils.ChoiceToEnum(c, enums) for c in args.windows_classifications
    ] if args.windows_classifications else []
    return messages.WindowsUpdateSettings(
        classifications=classifications,
        excludes=args.windows_excludes if args.windows_excludes else [],
    )
  else:
    return None


def _GetYumSettings(args, messages):
  if args.yum_excludes or args.yum_minimal or args.yum_security:
    return messages.YumSettings(
        excludes=args.yum_excludes if args.yum_excludes else [],
        minimal=args.yum_minimal,
        security=args.yum_security,
    )
  else:
    return None


def _GetZypperSettings(args, messages):
  """Create ZypperSettings from input arguments."""
  for arg in [
      args.zypper_categories, args.zypper_severities, args.zypper_with_optional,
      args.zypper_with_update
  ]:
    if arg:
      return messages.ZypperSettings(
          categories=args.zypper_categories if args.zypper_categories else [],
          severities=args.zypper_severities if args.zypper_severities else [],
          withOptional=args.zypper_with_optional,
          withUpdate=args.zypper_with_update,
      )
  return None


def _GetWindowsExecStepConfigInterpreter(messages, path):
  if path.endswith('.ps1'):
    return messages.ExecStepConfig.InterpreterValueValuesEnum.POWERSHELL
  else:
    return messages.ExecStepConfig.InterpreterValueValuesEnum.SHELL


def _GetExecStepConfig(messages, arg_name, path, allowed_success_codes,
                       is_windows):
  """Create ExecStepConfig from input arguments."""
  interpreter = messages.ExecStepConfig.InterpreterValueValuesEnum.INTERPRETER_UNSPECIFIED
  gcs_params = osconfig_command_utils.GetGcsParams(arg_name, path)
  if gcs_params:
    if is_windows:
      interpreter = _GetWindowsExecStepConfigInterpreter(
          messages, gcs_params['object'])
    return messages.ExecStepConfig(
        gcsObject=messages.GcsObject(
            bucket=gcs_params['bucket'],
            object=gcs_params['object'],
            generationNumber=gcs_params['generationNumber'],
        ),
        allowedSuccessCodes=allowed_success_codes
        if allowed_success_codes else [],
        interpreter=interpreter,
    )
  else:
    if is_windows:
      interpreter = _GetWindowsExecStepConfigInterpreter(messages, path)
    return messages.ExecStepConfig(
        localPath=path,
        allowedSuccessCodes=allowed_success_codes
        if allowed_success_codes else [],
        interpreter=interpreter,
    )


def _ValidatePrePostPatchStepArgs(executable_arg_name, executable_arg,
                                  success_codes_arg_name, success_codes_arg):
  if success_codes_arg and not executable_arg:
    raise exceptions.InvalidArgumentException(
        success_codes_arg_name,
        '[{}] must also be specified.'.format(executable_arg_name))


def _GetPrePostPatchStepSettings(args, messages, is_pre_patch_step):
  """Create ExecStep from input arguments."""
  if is_pre_patch_step:
    if not any([
        args.pre_patch_linux_executable, args.pre_patch_linux_success_codes,
        args.pre_patch_windows_executable, args.pre_patch_windows_success_codes
    ]):
      return None

    _ValidatePrePostPatchStepArgs('pre-patch-linux-executable',
                                  args.pre_patch_linux_executable,
                                  'pre-patch-linux-success-codes',
                                  args.pre_patch_linux_success_codes)
    _ValidatePrePostPatchStepArgs('pre-patch-windows-executable',
                                  args.pre_patch_windows_executable,
                                  'pre-patch-windows-success-codes',
                                  args.pre_patch_windows_success_codes)

    pre_patch_linux_step_config = pre_patch_windows_step_config = None
    if args.pre_patch_linux_executable:
      pre_patch_linux_step_config = _GetExecStepConfig(
          messages,
          'pre-patch-linux-executable',
          args.pre_patch_linux_executable,
          args.pre_patch_linux_success_codes,
          is_windows=False)
    if args.pre_patch_windows_executable:
      pre_patch_windows_step_config = _GetExecStepConfig(
          messages,
          'pre-patch-windows-executable',
          args.pre_patch_windows_executable,
          args.pre_patch_windows_success_codes,
          is_windows=True)
    return messages.ExecStep(
        linuxExecStepConfig=pre_patch_linux_step_config,
        windowsExecStepConfig=pre_patch_windows_step_config,
    )
  else:
    if not any([
        args.post_patch_linux_executable, args.post_patch_linux_success_codes,
        args.post_patch_windows_executable,
        args.post_patch_windows_success_codes
    ]):
      return None

    _ValidatePrePostPatchStepArgs('post-patch-linux-executable',
                                  args.post_patch_linux_executable,
                                  'post-patch-linux-success-codes',
                                  args.post_patch_linux_success_codes)
    _ValidatePrePostPatchStepArgs('post-patch-windows-executable',
                                  args.post_patch_windows_executable,
                                  'post-patch-windows-success-codes',
                                  args.post_patch_windows_success_codes)

    post_patch_linux_step_config = post_patch_windows_step_config = None
    if args.post_patch_linux_executable:
      post_patch_linux_step_config = _GetExecStepConfig(
          messages,
          'post-patch-linux-executable',
          args.post_patch_linux_executable,
          args.post_patch_linux_success_codes,
          is_windows=False)
    if args.post_patch_windows_executable:
      post_patch_windows_step_config = _GetExecStepConfig(
          messages,
          'post-patch-windows-executable',
          args.post_patch_windows_executable,
          args.post_patch_windows_success_codes,
          is_windows=True)
    return messages.ExecStep(
        linuxExecStepConfig=post_patch_linux_step_config,
        windowsExecStepConfig=post_patch_windows_step_config,
    )


def _GetProgressTracker(patch_job_name):
  stages = [
      progress_tracker.Stage(
          'Generating instance details...', key='pre-summary'),
      progress_tracker.Stage(
          'Reporting instance details...', key='with-summary')
  ]
  return progress_tracker.StagedProgressTracker(
      message='Executing patch job [{0}]'.format(patch_job_name), stages=stages)


def _GetExecutionUpdateMessage(percent_complete, instance_details_json):
  """Construct a message to be displayed during synchronous execute."""
  instance_states = {
      state: 0 for state in osconfig_command_utils.InstanceDetailsStates
  }

  for key, state in osconfig_command_utils.INSTANCE_DETAILS_KEY_MAP.items():
    num_instances = int(
        instance_details_json[key]) if key in instance_details_json else 0
    instance_states[state] = instance_states[state] + num_instances

  instance_details_str = ', '.join([
      '{} {}'.format(num, state.name.lower())
      for state, num in instance_states.items()
  ])
  return '{:.1f}% complete with {}'.format(percent_complete,
                                           instance_details_str)


def _UpdateProgressTracker(tracker, patch_job, unused_status):
  """Update the progress tracker on screen based on patch job details.

  Args:
    tracker: Progress tracker to be updated.
    patch_job: Patch job being executed.
  """
  details_json = resource_projector.MakeSerializable(
      patch_job.instanceDetailsSummary)
  if not details_json or details_json == '{}':
    if not tracker.IsRunning('pre-summary'):
      tracker.StartStage('pre-summary')
    else:
      tracker.UpdateStage('pre-summary', 'Please wait...')
  else:
    details_str = _GetExecutionUpdateMessage(patch_job.percentComplete,
                                             details_json)
    if tracker.IsRunning('pre-summary'):
      tracker.CompleteStage('pre-summary', 'Done!')
      tracker.StartStage('with-summary')
      tracker.UpdateStage('with-summary', details_str)
    else:
      tracker.UpdateStage('with-summary', details_str)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Execute(base.Command):
  r"""Execute an OS patch on the specified VM instances.

  ## EXAMPLES

  To patch all instances in the current project, use --instance-filter="" (or
  equivalently, --instance-filter="id=*"):

        $ {command} --instance-filter=""

  To patch the instances named 'my-instance1' and 'my-instance2', run:

        $ {command} --instance-filter="name=my-instance-1 OR name=my-instance-2"

  To patch all instances in the 'us-central1-b' and 'europe-west1-d' zones, run:

        $ {command} --instance-filter="zone:(us-central1-b europe-west1-d)"

  To patch all instances where their 'env' label is 'test', run:

        $ {command} --instance-filter="labels.env=test"

  To apply security and critical patches to a Windows instance named
  'my-instance', run:

        $ {command} --instance-filter="name=my-instance" \
        --windows-classifications=SECURITY,CRITICAL

  To patch all instances in the current project and specify scripts to run
  pre-patch and post-patch, run:

        $ {command} --instance-filter="" \
        --pre-patch-linux-executable="/bin/my-script" \
        --pre-patch-linux-success-codes=0,200 \
        --pre-patch-windows-executable="C:\\Users\\user\\test-script.ps1" \
        --post-patch-linux-executable="gs://my-bucket/my-linux-script#12345" \
        --post-patch-windows-executable="gs://my-bucket/my-windows-script#67890"
  """

  _command_prefix = 'gcloud alpha compute os-config patch-jobs'

  @staticmethod
  def Args(parser):
    _AddTopLevelArguments(parser)
    _AddAptGroupArguments(parser)
    _AddYumGroupArguments(parser)
    _AddWinGroupArguments(parser)
    _AddZypperGroupArguments(parser)
    _AddPrePostStepArguments(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()

    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    duration = six.text_type(args.duration) + 's' if args.duration else None
    filter_arg = 'id=*' if not args.instance_filter else args.instance_filter
    apt_settings = messages.AptSettings(
        type=messages.AptSettings.TypeValueValuesEnum.DIST
    ) if args.apt_dist else None
    reboot_config = getattr(
        messages.PatchConfig.RebootConfigValueValuesEnum,
        args.reboot_config.upper()) if args.reboot_config else None
    retry_strategy = messages.RetryStrategy(
        enabled=True) if args.retry else None
    patch_config = messages.PatchConfig(
        apt=apt_settings,
        rebootConfig=reboot_config,
        retryStrategy=retry_strategy,
        windowsUpdate=_GetWindowsUpdateSettings(args, messages),
        yum=_GetYumSettings(args, messages),
        zypper=_GetZypperSettings(args, messages),
        preStep=_GetPrePostPatchStepSettings(
            args, messages, is_pre_patch_step=True),
        postStep=_GetPrePostPatchStepSettings(
            args, messages, is_pre_patch_step=False),
    )

    request = messages.OsconfigProjectsPatchJobsExecuteRequest(
        executePatchJobRequest=messages.ExecutePatchJobRequest(
            description=args.description,
            dryRun=args.dry_run,
            duration=duration,
            filter=filter_arg,
            patchConfig=patch_config,
        ),
        parent=osconfig_command_utils.GetProjectUriPath(project))
    async_response = client.projects_patchJobs.Execute(request)

    patch_job_name = osconfig_command_utils.GetPatchJobName(async_response.name)

    if args.async_:
      log.status.Print(
          'Execution in progress for patch job [{}]'.format(patch_job_name))
      log.status.Print(
          'Run the [{} describe] command to check the status of this execution.'
          .format(self._command_prefix))
      return async_response

    # Execute the patch job synchronously.
    patch_job_poller = osconfig_api_utils.Poller(client, messages)
    get_request = messages.OsconfigProjectsPatchJobsGetRequest(
        name=async_response.name)
    sync_response = waiter.WaitFor(
        patch_job_poller,
        get_request,
        custom_tracker=_GetProgressTracker(patch_job_name),
        tracker_update_func=_UpdateProgressTracker,
        pre_start_sleep_ms=5000,
        exponential_sleep_multiplier=1,  # Constant poll rate of 5s.
        sleep_ms=5000,
    )
    log.status.Print(
        'Execution for patch job [{}] has completed with status [{}].'.format(
            patch_job_name, sync_response.state))
    log.status.Print('Run the [{} list-instance-details] command to view any '
                     'instance failure reasons.'.format(self._command_prefix))
    return sync_response
