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

"""The 'gcloud test android' sub-group."""

from googlecloudsdk.calliope import base


class Android(base.Group):
  """Command group for Android application testing."""

  detailed_help = {
      'DESCRIPTION': """\
          Explore physical and virtual Android models, along with their
          supported OS versions.
          """,

      'EXAMPLES': """\
          (DEPRECATED) To see a list of available Android devices, their form
          factors, and supported Android OS versions, run:

            $ {command} devices list

          Note: the *devices list* command has been replaced with
          *firebase models list*.
      """
  }

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags common to this sub-group.

    Args:
      parser: An argparse parser used to add arguments that immediately follow
          this group in the CLI. Positional arguments are allowed.
    """
