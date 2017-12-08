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
"""ml-engine models delete command."""
from googlecloudsdk.api_lib.ml import models
from googlecloudsdk.api_lib.ml import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.command_lib.ml import models_util


def _AddDeleteArgs(parser):
  flags.GetModelName().AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DeleteGa(base.DeleteCommand):
  """Delete an existing Cloud ML Engine model."""

  def Collection(self):
    return 'ml.models'

  @staticmethod
  def Args(parser):
    _AddDeleteArgs(parser)

  def Run(self, args):
    models_client = models.ModelsClient('v1')
    operations_client = operations.OperationsClient('v1')
    return models_util.Delete(models_client, operations_client, args.model)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DeleteBeta(base.DeleteCommand):
  """Delete an existing Cloud ML Engine model."""

  def Collection(self):
    return 'ml.models'

  @staticmethod
  def Args(parser):
    _AddDeleteArgs(parser)

  def Run(self, args):
    models_client = models.ModelsClient('v1beta1')
    operations_client = operations.OperationsClient('v1beta1')
    return models_util.Delete(models_client, operations_client, args.model)
