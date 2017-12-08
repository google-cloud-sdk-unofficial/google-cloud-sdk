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
  """Manage IAM policies for services."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To describe the IAM policy for a service, run:

            $ {command} describe SERVICE_NAME

          To check a member's permissions for a service, run:

            $ {command} check SERVICE_NAME --member MEMBER

          To add a user to a service's access policy, run:

            $ {command} add SERVICE_NAME --member user:USER_EMAIL

          To add a group to a service's access policy, run:

            $ {command} add SERVICE_NAME --member group:GROUP_EMAIL

          To remove a user from a service's access policy, run:

            $ {command} remove SERVICE_NAME --member user:USER_EMAIL

          See https://cloud.google.com/iam/docs/managing-policies for details
          of policy role and member types.
          """,
  }

