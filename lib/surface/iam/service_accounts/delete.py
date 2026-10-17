# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command for deleting service accounts."""


import textwrap

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.UniverseCompatible
class Delete(base.DeleteCommand):
  """Delete a service account from a project.

  If the service account does not exist, this command returns a
  `PERMISSION_DENIED` error.
  """

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""
          To delete an service account from your project, run:

            $ {command} my-iam-account@my-project.iam.gserviceaccount.com
          """),
  }

  @classmethod
  def Args(cls, parser):
    iam_util.AddServiceAccountNameArg(
        parser, action='to delete')
    if cls.ReleaseTrack() != base.ReleaseTrack.GA:
      # No-op, kept so existing invocations keep working.
      iam_util.AddServiceAccountRecommendArg(parser)

  def Run(self, args):
    prompt_message = 'You are about to delete service account [{0}]'.format(
        args.service_account
    )
    client, messages = util.GetClientAndMessages()
    sa_resource_name = iam_util.EmailToAccountResourceName(args.service_account)
    console_io.PromptContinue(message=prompt_message, cancel_on_no=True)
    client.projects_serviceAccounts.Delete(
        messages.IamProjectsServiceAccountsDeleteRequest(name=sa_resource_name)
    )

    log.status.Print('deleted service account [{0}]'.format(
        args.service_account))
