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
"""ml-engine models describe command."""
from googlecloudsdk.api_lib.ml import models
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags


_COLLECTION = 'ml.models'


def _AddDescribeArgs(parser):
  flags.GetModelName().AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class DescribeBeta(base.DescribeCommand):
  """Describe an existing Cloud ML Engine model."""

  def Collection(self):
    return _COLLECTION

  @staticmethod
  def Args(parser):
    _AddDescribeArgs(parser)

  def Run(self, args):
    return models.ModelsClient('v1beta1').Get(args.model)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeGa(base.DescribeCommand):
  """Describe an existing Cloud ML Engine model."""

  def Collection(self):
    return _COLLECTION

  @staticmethod
  def Args(parser):
    _AddDescribeArgs(parser)

  def Run(self, args):
    return models.ModelsClient('v1').Get(args.model)
