# Copyright 2015 Google Inc. All Rights Reserved.
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
"""The super-group for the compute CLI."""
import argparse
import sys

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.third_party.apis.iam.v1 import iam_v1_client
from googlecloudsdk.third_party.apis.iam.v1 import iam_v1_messages


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Iam(base.Group):

  def Filter(self, context, args):
    context['iam-client'] = iam_v1_client.IamV1(
        get_credentials=False,
        http=self.Http(),
        url=properties.VALUES.api_endpoint_overrides.iam.Get())
    context['iam-messages'] = iam_v1_messages
    context['iam-resources'] = resources
