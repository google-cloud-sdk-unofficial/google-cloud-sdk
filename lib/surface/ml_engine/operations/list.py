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
"""ml-engine operations list command."""
from googlecloudsdk.api_lib.ml import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import operations_util


_COLLECTION = 'ml.operations'
_LIST_FORMAT = """\
    table(
        name.basename(),
        metadata.operationType,
        done
    )
"""


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListBeta(base.ListCommand):
  """List existing Cloud ML Engine jobs."""

  def Collection(self):
    return _COLLECTION

  def Format(self, args):
    del args  # Unused in Format
    return _LIST_FORMAT

  def Run(self, args):
    return operations_util.List(operations.OperationsClient('v1beta1'))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGa(base.ListCommand):
  """List existing Cloud ML Engine jobs."""

  def Collection(self):
    return _COLLECTION

  def Format(self, args):
    del args  # Unused in Format
    return _LIST_FORMAT

  def Run(self, args):
    return operations_util.List(operations.OperationsClient('v1'))
