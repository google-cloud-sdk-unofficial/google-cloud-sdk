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
"""Command for setting the default service account on a GCE project."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetDefaultServiceAccount(base_classes.NoOutputAsyncMutator):
  """Set the default service account on the project."""

  @staticmethod
  def Args(parser):
    accounts_group = parser.add_mutually_exclusive_group()
    service_account = accounts_group.add_argument(
        '--service-account',
        help='The service account email address to set as default.')
    service_account.detailed_help = """\
        The email address of the service account that will be set as the default
        service account for all newly created instances in the project.

        To set the default service account to
        example@project.iam.gserviceaccount.com:

          $ {command} --service-account example@project.iam.gserviceaccount.com
        """
    no_service_account = accounts_group.add_argument(
        '--no-service-account',
        action='store_true',
        help='Sets the default service account as no service account from the '
             'project.')
    no_service_account.detailed_help = """\
        Sets the default service account on the project as no service account.
        This causes newly created instances to not run as a service account
        by default.

        To set the default service account as no service account, specify this
        flag:

          $ {command} --no-service-account
        """

  @property
  def service(self):
    return self.compute.projects

  @property
  def method(self):
    return 'SetDefaultServiceAccount'

  @property
  def resource_type(self):
    return 'projects'

  def CreateRequests(self, args):
    self.validateFlags(args)

    if args.no_service_account:
      return [self.messages.ComputeProjectsSetDefaultServiceAccountRequest(
          project=self.project,
          projectsSetDefaultServiceAccountRequest=
          self.messages.ProjectsSetDefaultServiceAccountRequest())]
    else:
      return [self.messages.ComputeProjectsSetDefaultServiceAccountRequest(
          project=self.project,
          projectsSetDefaultServiceAccountRequest=
          self.messages.ProjectsSetDefaultServiceAccountRequest(
              email=args.service_account
          )
      )]

  def validateFlags(self, args):
    if not args.no_service_account and not args.service_account:
      raise exceptions.RequiredArgumentException(
          '--service-account', 'must be specified with a service account. To '
          'clear the default service account use [--no-service-account].')


SetDefaultServiceAccount.detailed_help = {
    'DESCRIPTION': """\
        *{command}* is used to configure the default service account on project.

        The project's default service account is used when a new instance is
        created unless a custom service account is set via --scopes or
        --no-scopes. Existing existances are not effected.

        For example,

          $ {command} --email=example@developers.gserviceaccount.com
          $ gcloud compute instances create instance-name

        will set the project's default service account as
        example@developers.gserviceaccount.com. The instance created will have
        example@developers.gserviceaccount.com as the service account associated
        with because no service account email was specified in the
        "instances create" command.

        To remove the default service account from the project, issue the command:

          $ gcloud compute project-info set-default-service-account --no-service-account
        """,
}
