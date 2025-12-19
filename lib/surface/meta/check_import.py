# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""The `gcloud meta check-import` command."""


from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import module_util


@base.UniverseCompatible
@base.Hidden
class CheckImport(base.Command):
  """Check if modules are importable."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'modules',
        metavar='MODULES',
        nargs='*',
        help='The list of modules to check, separated with spaces',
    )

  def Run(self, args):
    if not args.modules:
      raise exceptions.Error('No modules to check.')
    errors = []
    for module in args.modules:
      try:
        module_util.ImportModule(module)
        log.status.Print(f'Module [{module}] imported successfully.')
      except Exception as e:  # pylint: disable=broad-except
        errors.append(f'Error importing [{module}]: {e}')
    if errors:
      raise exceptions.MultiError(errors)
