# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Add IAM policy binding to an application."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.apphub.applications import client as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.apphub import flags
from googlecloudsdk.command_lib.iam import iam_util


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """\
        To add an IAM policy binding for the role of `roles/apphub.viewer`
        for the user `test-user@gmail.com` to Application `my-app` in location
        `us-east1`, run:

          $ {command} my-app --location=us-east1 --role=roles/apphub.viewer --member=user:test-user@gmail.com
        """,
}


class AddIamPolicyBinding(base.Command):
  """Add IAM policy binding to an Apphub application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddAddIamPolicyBindingFlags(parser)
    iam_util.AddArgsForAddIamPolicyBinding(parser)

  def Run(self, args):
    client = apis.ApplicationsClient()
    app_ref = args.CONCEPTS.application.Parse()
    if not app_ref.Name():
      raise exceptions.InvalidArgumentException(
          'application', 'application id must be non-empty.'
      )
    return client.AddIamPolicyBinding(
        app_id=app_ref.RelativeName(), member=args.member, role=args.role
    )
