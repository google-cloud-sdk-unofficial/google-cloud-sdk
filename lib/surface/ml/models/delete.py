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
"""ml models delete command."""
from googlecloudsdk.api_lib.ml import models
from googlecloudsdk.api_lib.ml import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags


class DeleteBeta(base.DeleteCommand):
  """Delete an existing Cloud ML model."""

  def Collection(self):
    return 'ml.models'

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.GetModelName().AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    client = models.ModelsClient()
    op = client.Delete(args.model)

    return operations.OperationsClient().WaitForOperation(
        op, message='Deleting model [{}]'.format(args.model)).response
