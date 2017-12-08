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

"""The targets command group for the gcloud debug command."""

from googlecloudsdk.calliope import base


@base.Hidden
class Logpoints(base.Group):
  """Commands for interacting with Cloud Debugger logpoints.

  Logpoints allow you to inject logging into running services without
  restarting or interfering with the normal function of the service. Log output
  will be sent to the appropriate log for the target's environment.
  On App Engine, for example, output will go to the request log.
  """

  detailed_help = {
      # TODO(user) Add some examples
      # 'EXAMPLES': ''
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--target', metavar='(ID|DESCRIPTION_REGEXP)',
        help="""\
            The debug target. It may be a target ID obtained from
            'debug targets list', or it may be a regular expression uniquely
            specifying a target based on its description. For App Engine
            projects, if not specified, the default target is
            the most recent deployment of the default module and version.
        """)
