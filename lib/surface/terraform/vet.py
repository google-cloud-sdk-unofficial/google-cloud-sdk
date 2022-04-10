# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.credentials.store import GetFreshAccessToken
from googlecloudsdk.core.util import files

MISSING_BINARY = ('Could not locate terraform-tools executable [{binary}]. '
                  'Please ensure gcloud terraform-tools component is '
                  'properly installed. '
                  'See https://cloud.google.com/sdk/docs/components for '
                  'more details.')


class TerraformToolsTfplanToCaiOperation(
    binary_operations.StreamingBinaryBackedOperation):
  """Streaming operation for Terraform Tools tfplan-to-cai command."""
  custom_errors = {}

  def __init__(self, **kwargs):
    custom_errors = {
        'MISSING_EXEC': MISSING_BINARY.format(binary='terraform-tools'),
    }
    super(TerraformToolsTfplanToCaiOperation, self).__init__(
        binary='terraform-tools',
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


class TerraformToolsValidateOperation(binary_operations.BinaryBackedOperation):
  """operation for Terraform Tools validate-cai command."""
  custom_errors = {}

  def __init__(self, **kwargs):
    custom_errors = {
        'MISSING_EXEC': MISSING_BINARY.format(binary='terraform-tools'),
    }
    super(TerraformToolsValidateOperation, self).__init__(
        binary='terraform-tools',
        check_hidden=True,
        # Install will be handled by the conversion operation
        install_if_missing=False,
        custom_errors=custom_errors,
        **kwargs)

  def _ParseArgsForCommand(self, command, input_file, policy_library, verbosity,
                           **kwargs):
    args = [
        command,
        input_file,
        '--verbosity',
        verbosity,
        '--policy-library',
        os.path.expanduser(policy_library),
    ]
    return args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Vet(base.Command):
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
    tfplan_to_cai_operation = TerraformToolsTfplanToCaiOperation()
    validate_cai_operation = TerraformToolsValidateOperation()
    validate_tfplan_operation = TerraformToolsValidateOperation()

    env_vars = {
        'GOOGLE_OAUTH_ACCESS_TOKEN':
            GetFreshAccessToken(account=properties.VALUES.core.account.Get()),
        'USE_STRUCTURED_LOGGING':
            'true',
        'GOOGLE_TERRAFORM_VALIDATOR_USERAGENT_EXTENSION':
            metrics.GetUserAgent(),
    }

    with files.TemporaryDirectory() as tempdir:
      cai_assets = os.path.join(tempdir, 'cai_assets.json')

      response = tfplan_to_cai_operation(
          command='tfplan-to-cai',
          project=args.project or properties.VALUES.core.project.Get(),
          terraform_plan_json=args.terraform_plan_json,
          verbosity=args.verbosity,
          output_path=cai_assets,
          env=env_vars)
      self.exit_code = response.exit_code
      if self.exit_code > 0:
        # The streaming binary backed operation handles its own writing to
        # stdout and stderr, so there's nothing left to do here.
        return None

      with progress_tracker.ProgressTracker(
          message='Validating resources',
          aborted_message='Aborted validation.'):
        cai_response = validate_cai_operation(
            command='validate-cai',
            policy_library=args.policy_library,
            input_file=cai_assets,
            verbosity=args.verbosity,
            env=env_vars)
        tfplan_response = validate_tfplan_operation(
            command='validate-tfplan',
            policy_library=args.policy_library,
            input_file=args.terraform_plan_json,
            verbosity=args.verbosity,
            env=env_vars)

    # exit code 2 from a validate_* command indicates violations; we need to
    # pass that through to users so they can detect this case. However, if
    # either command errors out (exit code 1) return that instead.
    if cai_response.exit_code == 1 or tfplan_response.exit_code == 1:
      self.exit_code = 1
    elif cai_response.exit_code == 2 or tfplan_response.exit_code == 2:
      self.exit_code = 2

    # Output from validate commands uses "structured output", same as the
    # streaming output from conversion. The final output should be a combined
    # list of violations.
    violations = []

    for policy_type, response in (('CAI', cai_response), ('Terraform',
                                                          tfplan_response)):
      if response.stdout:
        try:
          msg = binary_operations.ReadStructuredOutput(
              response.stdout, as_json=True)
        except binary_operations.StructuredOutputError:
          log.warning('Could not parse {} policy validation output.'.format(
              policy_type))
        else:
          violations += msg.resource_body
      if response.stderr:
        handler = binary_operations.DefaultStreamStructuredErrHandler(None)
        for line in response.stderr.split('\n'):
          handler(line)

    return violations
