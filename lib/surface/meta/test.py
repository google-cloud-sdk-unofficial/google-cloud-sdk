# Copyright 2017 Google Inc. All Rights Reserved.
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
"""The `gcloud meta test` command."""

import os
import signal
import time

from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions


class Test(base.Command):
  """Run miscellaneous gcloud command and CLI test scenarios.

  This command sets up scenarios for testing the gcloud command and CLI.
  """

  @staticmethod
  def Args(parser):
    scenarios = parser.add_mutually_exclusive_group()
    scenarios.add_argument(
        '--interrupt',
        action='store_true',
        help='Kill the command with SIGINT.')
    scenarios.add_argument(
        '--sleep',
        metavar='SECONDS',
        type=float,
        default=0.0,
        help='Sleep for SECONDS seconds and exit.')

  def Run(self, args):
    if args.interrupt:
      try:
        # Windows hackery to simulate ^C and wait for it to register.
        # NOTICE: This only works if this command is run from the console.
        os.kill(os.getpid(), signal.CTRL_C_EVENT)
        time.sleep(1)
      except AttributeError:
        # Back to normal where ^C is SIGINT and it works immediately.
        os.kill(os.getpid(), signal.SIGINT)
      raise exceptions.Error('SIGINT delivery failed.')
    elif args.sleep:
      time.sleep(args.sleep)
    else:
      raise exceptions.Error(
          'Exactly one test scenario flag must be specified.')
