# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Python installers for gcloud."""

import os
import sys

from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms


PYTHON_VERSION = '3.13'
PYTHON_VERSION_INFO = (3, 13)
MACOS_PYTHON = 'python-3.13.7-macos11.tar.gz'

HOMEBREW_BIN = '/opt/homebrew/bin'
MACOS_PYTHON_INSTALL_PATH = (
    f'/Library/Frameworks/Python.framework/Versions/{PYTHON_VERSION}/')
MACOS_PYTHON_URL = (
    'https://dl.google.com/dl/cloudsdk/channels/rapid/' + MACOS_PYTHON
)


def _VirtualEnvPath():
  env_dir = config.Paths().virtualenv_dir
  if os.path.isdir(env_dir):
    return env_dir
  else:
    return None


def _CreateVirtualEnv(cli, python_to_use):
  cli.Execute(['config', 'virtualenv', 'create', '--python-to-use',
               python_to_use])


def _RecreateVirtualEnv(cli, python_to_use, existing_env_dir):
  print(f'Virtual env already exists at {existing_env_dir}. '
        'Deleting so we can create new one.')
  cli.Execute(['config', 'virtualenv', 'delete'])
  _CreateVirtualEnv(cli, python_to_use)


def _UpdateVirtualEnv(cli):
  cli.Execute(['config', 'virtualenv', 'update'])


def _EnableVirtualEnv(cli):
  cli.Execute(['config', 'virtualenv', 'enable'])


def UpdatePythonDependencies(python_to_use):
  """Enables virtual environment with new python version and dependencies."""
  try:
    from googlecloudsdk import gcloud_main  # pylint: disable=g-import-not-at-top
    cli = gcloud_main.CreateCLI([])

    # Assume we are executing in a virtual environment if env_dir exists
    env_dir = _VirtualEnvPath()
    if env_dir and sys.version_info[:2] != PYTHON_VERSION_INFO:
      _RecreateVirtualEnv(cli, python_to_use, env_dir)
    elif env_dir:
      _UpdateVirtualEnv(cli)
    else:
      _CreateVirtualEnv(cli, python_to_use)

    _EnableVirtualEnv(cli)
  except ImportError:
    print('Failed to enable virtual environment')


def _IsHomebrewInstalled():
  return os.path.isdir(HOMEBREW_BIN) and 'homebrew' in config.GcloudPath()


def _PrintPythonInstallError(error):
  print(
      f'Failed to install the required Python. Error: {error}. \n'
      'Please install the required Python and modules manually by running:\n'
      '   $ gcloud components update-macos-python'
  )


def _BrewInstallPython():
  """Make sure python version is correct for user using gcloud with homebrew."""
  python_to_use = f'{HOMEBREW_BIN}/python{PYTHON_VERSION}'
  if os.path.isfile(python_to_use):
    print(f'Python {PYTHON_VERSION} is already installed via homebrew.')
    return python_to_use

  brew_install = f'{HOMEBREW_BIN}/brew install python@{PYTHON_VERSION}'
  print(f'Running "{brew_install}".')

  exit_code = execution_utils.Exec(brew_install.split(' '), no_exit=True)
  if exit_code != 0:
    _PrintPythonInstallError(
        f'"{brew_install}" failed. Please brew install '
        f'python@{PYTHON_VERSION} manually.')
    return None
  return python_to_use


def _MacInstallPython():
  """Optionally install Python on Mac machines."""

  python_to_use = f'{MACOS_PYTHON_INSTALL_PATH}bin/python3'
  if os.path.isfile(python_to_use):
    print(f'Python {PYTHON_VERSION} is already installed.')
    return python_to_use

  print(f'Running Python {PYTHON_VERSION} installer, you may be prompted for '
        'sudo password...')

  # Xcode Command Line Tools is required to install Python.
  install_error = InstallXcodeCommandLineTools()
  if install_error:
    return install_error

  with files.TemporaryDirectory() as tempdir:
    with files.ChDir(tempdir):
      curl_args = ['curl', '--silent', '-O', MACOS_PYTHON_URL]
      exit_code = execution_utils.Exec(curl_args, no_exit=True)
      if exit_code != 0:
        _PrintPythonInstallError('Failed to download Python installer')
        return None

      exit_code = execution_utils.Exec(
          ['tar', '-xf', MACOS_PYTHON], no_exit=True)
      if exit_code != 0:
        _PrintPythonInstallError('Failed to extract Python installer')
        return None

      exit_code = execution_utils.Exec([
          'sudo', 'installer', '-target', '/', '-pkg',
          './python-3.13.7-macos11.pkg'
      ], no_exit=True)
      if exit_code != 0:
        _PrintPythonInstallError('Installer failed.')
        return None

  return python_to_use


def _GcloudRequiredPythonToUse():
  """Determine python install path."""
  homebrew_installed = _IsHomebrewInstalled()
  homebrew_python = f'{HOMEBREW_BIN}/python{PYTHON_VERSION}'
  gcloud_python = f'{MACOS_PYTHON_INSTALL_PATH}bin/python3'
  user_specified_python = encoding.GetEncodedValue(
      os.environ, 'CLOUDSDK_PYTHON')

  if homebrew_installed and os.path.isfile(homebrew_python):
    return homebrew_python
  elif os.path.isfile(gcloud_python):
    return gcloud_python
  elif user_specified_python and sys.version_info[:2] == PYTHON_VERSION_INFO:
    # If the user specified python is the same version as the gcloud required
    # python, then we should use it.
    print(f'Using CLOUDSDK_PYTHON Python: {user_specified_python}')
    return sys.executable
  else:
    return None


def InstallPythonAndDependenciesOnMac():
  """Install Python and dependencies on Mac machines."""
  if platforms.OperatingSystem.Current() != platforms.OperatingSystem.MACOSX:
    return

  print(
      f'\nGoogle Cloud CLI works best with Python {PYTHON_VERSION} '
      'and certain modules.\n')

  # Get which Python to use to create virtualenv and install dependencies.
  python_to_use = _GcloudRequiredPythonToUse()

  # If gcloud required Python version is not installed, install it.
  if not python_to_use:
    # Determine python install path
    homebrew_installed = _IsHomebrewInstalled()
    if homebrew_installed:
      python_to_use = _BrewInstallPython()
    else:
      python_to_use = _MacInstallPython()

  # Update python dependencies
  if python_to_use:
    os.environ['CLOUDSDK_PYTHON'] = python_to_use
    print('Setting up virtual environment')
    UpdatePythonDependencies(python_to_use)


def CheckXcodeCommandLineToolsInstalled():
  """Checks if Xcode Command Line Tools is installed."""
  exit_code = execution_utils.Exec(['xcode-select', '-p'], no_exit=True)
  return exit_code == 0


def InstallXcodeCommandLineTools():
  """Optionally install Xcode Command Line Tools on Mac machines."""
  if platforms.OperatingSystem.Current() != platforms.OperatingSystem.MACOSX:
    return None

  if CheckXcodeCommandLineToolsInstalled():
    print('Xcode Command Line Tools is already installed.')
    return None

  print('Installing Xcode Command Line Tools, which is '
        'required to install Python...')
  xcode_command = ['xcode-select', '--install']
  exit_code = execution_utils.Exec(xcode_command, no_exit=True)
  if exit_code != 0:
    print('Failed to install Xcode Command Line Tools. '
          'Please run `xcode-select --install` manually to install '
          'Xcode Command Line Tools.')
    return 'Failed to install Xcode Command Line Tools.'
  else:
    print('Xcode Command Line Tools is installed.')

  return None
