# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Workflow to set up gcloud environment."""

import argparse
import os
import sys
import types

from googlecloudsdk.api_lib.projects import projects_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import platforms


class Init(base.Command):
  """Initialize or reinitialize gcloud."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          {command} launches an interactive Getting Started workflow for gcloud.
          It replaces `gcloud auth login` as the recommended command to execute
          after you install the Cloud SDK. {command} performs the following
          setup steps:

            - Authorizes gcloud and other SDK tools to access Google Cloud
              Platform using your user account credentials, or lets you select
              from accounts whose credentials are already available. {command}
              uses the same browser-based authorization flow as
              `gcloud auth login`.
            - Sets properties in a gcloud configuration, including the current
              project and the default Google Compute Engine region and zone.

          Most users run {command} to get started with gcloud. You can use
          subsequent {command} invocations to create new gcloud configurations
          or to reinitialize existing configurations.  See `gcloud topic
          configurations` for additional information.

          Properties set by `gcloud init` are local and persistent. They are
          not affected by remote changes to your project. For instance, the
          default Compute Engine zone in your configuration remains stable,
          even if you or another user changes the project-level default zone in
          the Cloud Platform Console.  You can resync your configuration at any
          time by rerunning `gcloud init`.

          (Available since version 0.9.79. Run $ gcloud --version to see which
          version you are running.)
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'obsolete_project_arg',
        nargs='?',
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--console-only',
        action='store_true',
        help=('Prevent the command from launching a browser for '
              'authorization.'))

  def Run(self, args):
    """Allows user to select configuration, and initialize it."""

    if args.obsolete_project_arg:
      raise c_exc.InvalidArgumentException(
          args.obsolete_project_arg,
          '`gcloud init` has changed and no longer takes a PROJECT argument. '
          'Please use `gcloud source repos clone` to clone this '
          'project\'s source repositories.')

    log.status.write('Welcome! This command will take you through '
                     'the configuration of gcloud.\n\n')

    if properties.VALUES.core.disable_prompts.GetBool():
      raise c_exc.InvalidArgumentException(
          'disable_prompts/--quiet',
          'gcloud init command cannot run with disabled prompts.')

    configuration_name = self._PickConfiguration()
    if not configuration_name:
      return
    log.status.write('Your current configuration has been set to: [{0}]\n\n'
                     .format(configuration_name))

    if not self._PickAccount(args.console_only):
      return

    project_id = self._PickProject()
    if not project_id:
      return

    self._PickDefaultRegionAndZone()

    self._CreateBotoConfig()

    self._Summarize()

  def _PickAccount(self, console_only):
    """Checks if current credentials are valid, if not runs auth login.

    Args:
      console_only: bool, True if the auth flow shouldn't use the browser

    Returns:
      bool, True if valid credentials are setup.
    """

    auth_info = self._RunCmd(['auth', 'list'])
    if auth_info and auth_info.accounts:
      idx = console_io.PromptChoice(
          auth_info.accounts + ['Log in with new credentials'],
          message='Pick credentials to use:',
          prompt_string=None)
      if idx is None:
        return None
      new_credentials = idx == len(auth_info.accounts)
    else:
      answer = console_io.PromptContinue(
          prompt_string='To continue, you must log in. Would you like to log '
                        'in')
      if not answer:
        return False
      new_credentials = True
    if new_credentials:
      # gcloud auth login may have user interaction, do not suppress it.
      browser_args = ['--no-launch-browser'] if console_only else []
      if not self._RunCmd(['auth', 'login'],
                          ['--force', '--brief'] + browser_args,
                          disable_user_output=False):
        return None
    else:
      account = auth_info.accounts[idx]
      self._RunCmd(['config', 'set'], ['account', account])

    log.status.write('You are now logged in as: [{0}]\n\n'
                     .format(properties.VALUES.core.account.Get()))
    return True

  def _PickConfiguration(self):
    """Allows user to re-initialize, create or pick new configuration.

    Returns:
      Configuration name or None.
    """

    configs = self._RunCmd(['config', 'configurations', 'list'])
    if not configs:
      new_config_name = 'default'
      if self._RunCmd(['config', 'configurations', 'create'],
                      [new_config_name]):
        self._RunCmd(['config', 'configurations', 'activate'],
                     [new_config_name])
        properties.PropertiesFile.Invalidate()
      return new_config_name

    config_names = [cfg['name'] for cfg in configs]
    active_configs = [cfg['name'] for cfg in configs
                      if cfg.get('is_active', False)]
    if not active_configs:
      return None
    choices = []
    active_config = active_configs[0]
    log.status.write('Settings from your current configuration [{0}] are:\n'
                     .format(active_config))
    log.status.flush()
    # Not using self._RunCmd to get command actual output.
    self.cli.Execute(['config', 'list'])
    log.out.flush()
    log.status.write('\n')
    log.status.flush()
    choices.append(
        'Re-initialize this configuration [{0}] with new settings '.format(
            active_config))
    choices.append('Create a new configuration')
    config_choices = [name for name in config_names if name != active_config]
    choices.extend('Switch to and re-initialize '
                   'existing configuration: [{0}]'.format(name)
                   for name in config_choices)
    idx = console_io.PromptChoice(choices, message='Pick configuration to use:')
    if idx is None:
      return None
    if idx == 0:  # If reinitialize was selected.
      self._CleanCurrentConfiguration()
      return active_config
    if idx == 1:  # Second option is to create new configuration.
      return self._CreateConfiguration()
    config_name = config_choices[idx - 2]
    self._RunCmd(['config', 'configurations', 'activate'], [config_name])
    return config_name

  def _PickProject(self):
    """Allows user to select a project.

    Returns:
      str, project_id or None if was not selected.
    """
    try:
      projects = list(projects_api.List())
    except Exception:  # pylint: disable=broad-except
      log.debug('Failed to execute projects list: %s, %s, %s', *sys.exc_info())
      projects = None

    if projects is None:  # Failed to get the list.
      project_id = console_io.PromptResponse(
          'Enter project id you would like to use:  ')
      if not project_id:
        return None
    else:
      projects = sorted(projects, key=lambda prj: prj.projectId)
      choices = ['[{0}]'.format(project.projectId) for project in projects]
      if not choices:
        log.status.write('\nThis account has no projects. Please create one in '
                         'developers console '
                         '(https://console.developers.google.com/project) '
                         'before running this command.\n')
        return None
      if len(choices) == 1:
        project_id = projects[0].projectId
      else:
        idx = console_io.PromptChoice(
            choices,
            message='Pick cloud project to use: ',
            prompt_string=None)
        if idx is None:
          return
        project_id = projects[idx].projectId

    self._RunCmd(['config', 'set'], ['project', project_id])
    log.status.write('Your current project has been set to: [{0}].\n\n'
                     .format(project_id))
    return project_id

  def _PickDefaultRegionAndZone(self):
    """Pulls metadata properties for region and zone and sets them in gcloud."""
    try:
      project_info = self._RunCmd(['compute', 'project-info', 'describe'])
    except c_exc.FailedSubCommand:
      log.status.write("""\
Not setting default zone/region (this feature makes it easier to use
[gcloud compute] by setting an appropriate default value for the
--zone and --region flag).
See https://cloud.google.com/compute/docs/gcloud-compute section on how to set
default compute region and zone manually. If you would like [gcloud init] to be
able to do this for you the next time you run it, make sure the
Compute Engine API is enabled for your project on the
https://console.developers.google.com/apis page.

""")
      return None

    default_zone = None
    default_region = None
    if project_info is not None:
      metadata = project_info.get('commonInstanceMetadata', {})
      for item in metadata.get('items', []):
        if item['key'] == 'google-compute-default-zone':
          default_zone = item['value']
        elif item['key'] == 'google-compute-default-region':
          default_region = item['value']

    # Same logic applies to region and zone properties.
    def SetProperty(name, default_value, list_command):
      """Set named compute property to default_value or get via list command."""
      if not default_value:
        values = self._RunCmd(list_command)
        if values is None:
          return
        values = list(values)
        idx = console_io.PromptChoice(
            ['[{0}]'.format(value['name']) for value in values]
            + ['Do not set default {0}'.format(name)],
            message=('Which compute {0} would you like '
                     'to use as project default?'.format(name)),
            prompt_string=None)
        if idx is None or idx == len(values):
          return
        default_value = values[idx]
      self._RunCmd(['config', 'set'],
                   ['compute/{0}'.format(name), default_value['name']])
      log.status.write('Your project default compute {0} has been set to '
                       '[{1}].\nYou can change it by running '
                       '[gcloud config set compute/{0} NAME].\n\n'
                       .format(name, default_value['name']))
      return default_value

    if default_zone:
      default_zone = self._RunCmd(['compute', 'zones', 'describe'],
                                  [default_zone])
    zone = SetProperty('zone', default_zone, ['compute', 'zones', 'list'])
    if zone and not default_region:
      default_region = zone['region']
    if default_region:
      default_region = self._RunCmd(['compute', 'regions', 'describe'],
                                    [default_region])
    SetProperty('region', default_region, ['compute', 'regions', 'list'])

  def _Summarize(self):
    log.status.Print('Your Google Cloud SDK is configured and ready to use!\n')

    log.status.Print(
        '* Commands that require authentication will use {0} by default'
        .format(properties.VALUES.core.account.Get()))
    project = properties.VALUES.core.project.Get()
    if project:
      log.status.Print(
          '* Commands will reference project `{0}` by default'
          .format(project))
    region = properties.VALUES.compute.region.Get()
    if region:
      log.status.Print(
          '* Compute Engine commands will use region `{0}` by default'
          .format(region))
    zone = properties.VALUES.compute.zone.Get()
    if zone:
      log.status.Print(
          '* Compute Engine commands will use zone `{0}` by default\n'
          .format(zone))

    log.status.Print(
        'Run `gcloud help config` to learn how to change individual settings\n')

    log.status.Print(
        'This gcloud configuration is called [default]. You can create '
        'additional configurations if you work with multiple accounts and/or '
        'projects.')
    log.status.Print('Run `gcloud topic configurations` to learn more.\n')

    log.status.Print('Some things to try next:\n')

    log.status.Print(
        '* Run `gcloud --help` to see the Cloud Platform services you can '
        'interact with. And run `gcloud help COMMAND` to get help on any '
        'gcloud command.')
    log.status.Print(
        '* Run `gcloud topic -h` to learn about advanced features of the SDK '
        'like arg files and output formatting')
    log.status.Print(
        '* Clone your Google Source Repository to a local directory by running '
        'the command `gcloud source repos clone default /local/path`')

  def _CreateConfiguration(self):
    configuration_name = console_io.PromptResponse(
        'Enter configuration name:  ')
    new_config_name = self._RunCmd(['config', 'configurations', 'create'],
                                   [configuration_name])
    if new_config_name:
      self._RunCmd(['config', 'configurations', 'activate'],
                   [configuration_name])
      properties.PropertiesFile.Invalidate()
    return new_config_name

  def _CreateBotoConfig(self):
    gsutil_path = _FindGsutil()
    if not gsutil_path:
      log.debug('Unable to find [gsutil]. Not configuring default .boto '
                'file')
      return

    boto_path = platforms.ExpandHomePath(os.path.join('~', '.boto'))
    if os.path.exists(boto_path):
      log.debug('Not configuring default .boto file. File already '
                'exists at [{boto_path}].'.format(boto_path=boto_path))
      return

    # 'gsutil config -n' creates a default .boto file that the user can read and
    # modify.
    command_args = ['config', '-n', '-o', boto_path]
    if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
      gsutil_args = execution_utils.ArgsForCMDTool(gsutil_path,
                                                   *command_args)
    else:
      gsutil_args = execution_utils.ArgsForShellTool(gsutil_path, *command_args)

    return_code = execution_utils.Exec(gsutil_args, no_exit=True,
                                       pipe_output_through_logger=True,
                                       file_only_logger=True)
    if return_code == 0:
      log.status.write("""\
Created a default .boto configuration file at [{boto_path}]. See this file and
[https://cloud.google.com/storage/docs/gsutil/commands/config] for more
information about configuring Google Cloud Storage.
""".format(boto_path=boto_path))

    else:
      log.status.write('Error creating a default .boto configuration file. '
                       'Please run [gsutil config -n] if you would like to '
                       'create this file.\n')

  def _CleanCurrentConfiguration(self):
    self._RunCmd(['config', 'unset'], ['account'])
    self._RunCmd(['config', 'unset'], ['project'])
    self._RunCmd(['config', 'unset'], ['compute/zone'])
    self._RunCmd(['config', 'unset'], ['compute/region'])

  def _RunCmd(self, cmd, params=None, disable_user_output=True):
    if not self.cli.IsValidCommand(cmd):
      log.info('Command %s does not exist.', cmd)
      return None
    if params is None:
      params = []
    args = cmd + params
    log.info('Executing: [gcloud %s]', ' '.join(args))
    try:
      # Disable output from individual commands, so that we get
      # command run results, and don't clutter output of init.
      if disable_user_output:
        args.append('--no-user-output-enabled')

      if (properties.VALUES.core.verbosity.Get() is None and
          disable_user_output):
        # Unless user explicitly set verbosity, suppress from subcommands.
        args.append('--verbosity=none')

      result = self.cli.Execute(args)
      # Best effort to force result of Execute eagerly.  Don't just check
      # that result is iterable to avoid category errors (e.g., accidently
      # converting a string or dict to a list).
      if isinstance(result, types.GeneratorType):
        return list(result)
      return result

    except SystemExit as exc:
      log.info('[%s] has failed\n', ' '.join(cmd + params))
      raise c_exc.FailedSubCommand(cmd + params, exc.code)
    except BaseException:
      log.info('Failed to run [%s]\n', ' '.join(cmd + params))
      raise


def _FindGsutil():
  """Finds the bundled gsutil wrapper.

  Returns:
    The path to gsutil.
  """
  sdk_bin_path = config.Paths().sdk_bin_path
  if not sdk_bin_path:
    return

  if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
    gsutil = 'gsutil.cmd'
  else:
    gsutil = 'gsutil'
  return os.path.join(sdk_bin_path, gsutil)
