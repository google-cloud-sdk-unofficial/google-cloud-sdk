# -*- coding: utf-8 -*- #
# Copyright 2024 Google Inc. All Rights Reserved.
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
"""Command to add-iam-policy-binding to a secret resource."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.secrets import args as secrets_args


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class AddIamPolicyBinding(base.Command):
  """Add IAM policy binding to a secret.

  Add an IAM policy binding to the IAM policy of a secret. One binding
  consists of a member and a role.
  """

  detailed_help = {
      'EXAMPLES': """\
          To add an IAM policy binding for the role of 'roles/secretmanager.secretAccessor'
          for the user 'test-user@gmail.com' on my-secret, run:

            $ {command} my-secret --member='user:test-user@gmail.com' --role='roles/secretmanager.secretAccessor'

          See https://cloud.google.com/iam/docs/managing-policies for details of
          policy role and member types.
          """,
  }

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser,
        purpose='',
        positional=True,
        required=True,
        help_text='Name of the secret for which to add the IAM policy binding.',
    )
    secrets_args.AddLocation(parser, purpose='to add iam policy', hidden=False)

    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args):
    api_version = secrets_api.GetApiFromTrack(self.ReleaseTrack())
    multi_ref = args.CONCEPTS.secret.Parse()
    condition = iam_util.ValidateAndExtractConditionMutexRole(args)
    result = secrets_api.Secrets(api_version=api_version).AddIamPolicyBinding(
        multi_ref,
        args.member,
        args.role,
        condition=condition,
        secret_location=args.location,
    )
    iam_util.LogSetIamPolicy(multi_ref.Name(), 'secret')
    return result


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AddIamPolicyBindingBeta(AddIamPolicyBinding):
  """Add IAM policy binding to a secret resource."""

  detailed_help = {
      'EXAMPLES': """\
          To add an IAM policy binding for the role of 'roles/secretmanager.secretAccessor'
          for the user 'test-user@gmail.com' on my-secret, run:

            $ {command} my-secret --member='user:test-user@gmail.com' --role='roles/secretmanager.secretAccessor'

          See https://cloud.google.com/iam/docs/managing-policies for details of
          policy role and member types.
          """,
  }
