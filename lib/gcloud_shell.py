# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Gcloud Interactive Shell."""
from __future__ import unicode_literals

import os
import subprocess
import sys

_GCLOUD_PY_DIR = os.path.dirname(__file__)
_THIRD_PARTY_DIR = os.path.join(_GCLOUD_PY_DIR, 'third_party')

if os.path.isdir(_THIRD_PARTY_DIR):
  sys.path.insert(0, _THIRD_PARTY_DIR)

# pylint: disable=g-import-not-at-top
from googlecloudsdk.command_lib import gcloud_shell_util as util


def main():
  """Runs the CLI."""
  interactive_shell_cli = util.CreateCli(_GCLOUD_PY_DIR)
  while True:
    try:
      document = interactive_shell_cli.run(reset_current_buffer=True)
      subprocess.call(document.text, shell=True)
    except EOFError:
      break
    except KeyboardInterrupt:
      # Ignore ctrl-c
      pass


if __name__ == '__main__':
  main()
