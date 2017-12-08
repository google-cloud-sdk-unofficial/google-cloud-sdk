# Copyright 2017 Google Inc. All Rights Reserved.
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
"""ml jobs describe command."""
from googlecloudsdk.api_lib.ml import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.core import resources


class Describe(base.DescribeCommand):
  """Describe a Cloud ML operation."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.OPERATION_NAME.AddToParser(parser)

  def Run(self, args):
    operation_ref = resources.REGISTRY.Parse(
        args.operation, collection='ml.projects.operations')
    return operations.OperationsClient().Get(operation_ref)
