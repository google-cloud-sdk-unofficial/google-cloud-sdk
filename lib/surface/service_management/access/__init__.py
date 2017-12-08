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

"""Package for the service-management/access CLI subcommands."""

from googlecloudsdk.calliope import base


class Access(base.Group):
  """Manage access policies for services and their visibility labels."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To describe the access policy for a service, run:

            $ {command} describe SERVICE_NAME

          To check a user or group's permissions for a service, run:

            $ {command} check EMAIL --service SERVICE_NAME

          To add a user to a service's access policy, run:

            $ {command} add user EMAIL --service SERVICE_NAME

          To add a group to a service's access policy, run:

            $ {command} add group GROUP_EMAIL --service SERVICE_NAME

          To add a user to a service under a visibility label, run:

            $ {command} add user EMAIL --service SERVICE_NAME --label LABEL_NAME

          To remove a user from a service's access policy, run:

            $ {command} remove user EMAIL --service SERVICE_NAME

          To remove a user from a service's visibility label, run:

            $ {command} remove user EMAIL --service SERVICE_NAME --label LABEL_NAME
          """,
  }

