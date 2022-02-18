# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Validate that a terraform plan complies with policies."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os.path

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.credentials.store import GetFreshAccessToken
from googlecloudsdk.core.util import files

MISSING_BINARY = ('Could not locate terraform-validator executable [{binary}]. '
                  'Please ensure gcloud terraform-validator component is '
                  'properly installed. '
                  'See https://cloud.google.com/sdk/docs/components for '
                  'more details.')


class TerraformValidatorConvertOperation(
    binary_operations.StreamingBinaryBackedOperation):
  """Streaming operation for Terraform Validator convert binary."""
  custom_errors = {}

  def __init__(self, **kwargs):
    custom_errors = {
        'MISSING_EXEC': MISSING_BINARY.format(binary='terraform-validator'),
    }
    super(TerraformValidatorConvertOperation, self).__init__(
        binary='terraform-validator',
        check_hidden=True,
        install_if_missing=True,
        custom_errors=custom_errors,
        structured_output=True,
        **kwargs)

  def _ParseArgsForCommand(self, command, terraform_plan_json, project,
                           verbosity, output_path, **kwargs):
    args = [
        command,
        terraform_plan_json,
        '--output-path',
        output_path,
        '--verbosity',
        verbosity,
    ]
    if project:
      args += ['--project', project]
    return args


class TerraformValidatorValidateOperation(
    binary_operations.BinaryBackedOperation):
  """operation for Terraform Validator validate binary."""
  custom_errors = {}

  def __init__(self, **kwargs):
    custom_errors = {
        'MISSING_EXEC': MISSING_BINARY.format(binary='terraform-validator'),
    }
    super(TerraformValidatorValidateOperation, self).__init__(
        binary='terraform-validator',
        check_hidden=True,
        install_if_missing=True,
        custom_errors=custom_errors,
        **kwargs)

  def _ParseArgsForCommand(self, command, terraform_plan_json, policy_library,
                           project, verbosity, **kwargs):
    args = [
        command,
        terraform_plan_json,
        '--verbosity',
        verbosity,
        '--policy-path',
        os.path.expanduser(policy_library),
    ]
    if project:
      args += ['--project', project]
    return args


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Terraform(base.BinaryBackedCommand):
  """Validate that a terraform plan complies with policies."""

  detailed_help = {
      'EXAMPLES':
          """
        To validate that a terraform plan complies with a policy library
        at `/my/policy/library`:

        $ {command} tfplan.json --policy-library=/my/policy/library
        """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'terraform_plan_json',
        help=(
            'File which contains a JSON export of a terraform plan. This file '
            'will be validated against the given policy library.'),
    )
    parser.add_argument(
        '--policy-library',
        required=True,
        help='Directory which contains a policy library',
    )

  def Run(self, args):
    convert_operation = TerraformValidatorConvertOperation()
    validate_operation = TerraformValidatorValidateOperation()

    env_vars = {
        'GOOGLE_OAUTH_ACCESS_TOKEN':
            GetFreshAccessToken(account=properties.VALUES.core.account.Get()),
        'USE_STRUCTURED_LOGGING':
            'true',
        'GOOGLE_TERRAFORM_VALIDATOR_USERAGENT_EXTENSION':
            metrics.GetUserAgent(),
    }

    with files.TemporaryDirectory() as tempdir:
      filename = os.path.join(tempdir, 'converted.json')

      response = convert_operation(
          command='convert',
          project=args.project or properties.VALUES.core.project.Get(),
          terraform_plan_json=args.terraform_plan_json,
          verbosity=args.verbosity,
          output_path=filename,
          env=env_vars)
      self.exit_code = response.exit_code
      ret = self._DefaultOperationResponseHandler(response)
      if self.exit_code > 0:
        return ret

      with progress_tracker.ProgressTracker(
          message='Validating resources',
          aborted_message='Aborted validation.'):
        response = validate_operation(
            command='validate',
            policy_library=args.policy_library,
            project=args.project or properties.VALUES.core.project.Get(),
            terraform_plan_json=filename,
            verbosity=args.verbosity,
            env=env_vars)
        self.exit_code = response.exit_code
        return self._DefaultOperationResponseHandler(response)
