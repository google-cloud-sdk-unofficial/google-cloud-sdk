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
"""Command for generating Terraform Import script for exported resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.declarative import flags
from googlecloudsdk.command_lib.util.declarative import terraform_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files


_DETAILED_HELP = {
    'EXAMPLES':
        """
    To generate an import script named `import.sh` based on exported files in `my-dir/`, run:

      $ {command} my-dir/ --output-file=import.sh

    To generate an import script with the default `terraform_import_YYYYMMDD-HH-MM-SS.cmd` name on Windows, based on exported files in `my-dir/`, run:

      $ {command} my-dir
   """
}


class GenerateImport(base.DeclarativeCommand):
  """Generate Terraform import script for exported resources."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddTerraformGenerateImportArgs(parser)

  def Run(self, args):
    input_path = args.INPUT_PATH
    output_file = args.output_file.strip() if args.output_file else None
    output_dir = (os.path.abspath(
        args.output_dir.strip()) if args.output_dir else None)
    destfile = None
    destdir = None

    if output_file:
      if os.path.isfile(output_file):
        overwrite_prompt = ('{} already exists.'.format(output_file))
        console_io.PromptContinue(
            overwrite_prompt,
            prompt_string='Do you want to overwrite?',
            default=True,
            cancel_string='Aborted script generation.',
            cancel_on_no=True)
      destfile = os.path.basename(output_file)
      destdir = os.path.dirname(output_file) or None

    if output_dir:
      if (os.path.isdir(output_dir) and
          not files.HasWriteAccessInDir(output_dir)):
        raise ValueError('Cannot write output to directory {}. '
                         'Please check permissions.'.format(output_dir))
      destfile = None
      destdir = output_dir

    with progress_tracker.ProgressTracker(
        message='Generating import script.',
        aborted_message='Aborted script generation.'):
      output, success, errors = terraform_utils.GenerateScriptFromTemplate(
          input_path, dest_file=destfile, dest_dir=destdir)

    if errors:
      log.warning(
          'Error generating imports for the following resource files: {}'
          .format('\n'.join(errors)))

    if not output:
      log.error('No Terraform importable data found in {path}.'.format(
          path=input_path))
      return None

    log.status.Print(
        'Successfully generated imports for {} resources.'.format(success))
    return output

