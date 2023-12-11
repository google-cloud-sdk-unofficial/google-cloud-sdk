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
"""Set the IAM policy for an application."""
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
    'EXAMPLES': """ \
        To set the application IAM policy using a json file 'my_policy.json' for
        the Application `my-app` in location `us-east1`, run:

          $ {command} my-app --location=us-east1 /path/to/my_policy.json

        To set the application IAM policy using a yaml file 'my_policy.yaml` for
        the Application `my-app` in location `us-east1`, run:

          $ {command} my-app --location=us-east1 /path/to/my_policy.yaml
        """,
}


class SetIamPolicy(base.Command):
  """Set the IAM policy for an Apphub application as defined in a JSON/YAML file.

     See https://cloud.google.com/iam/docs/managing-policies for details of
        the policy file format and contents.
  """
  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddSetIamPolicyFlags(parser)
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    client = apis.ApplicationsClient()
    app_ref = args.CONCEPTS.application.Parse()
    if not app_ref.Name():
      raise exceptions.InvalidArgumentException(
          'application', 'application id must be non-empty.'
      )
    return client.SetIamPolicy(
        app_id=app_ref.RelativeName(), policy_file=args.policy_file
    )
