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
"""The super-group for the IAM CLI."""
import argparse
import sys

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Iam(base.Group):
  """Manage IAM service accounts and keys."""
  detailed_help = {
      'brief': 'Manage IAM service accounts and keys.',
  }

  def Filter(self, context, args):
    context['iam-client'] = apis.GetClientInstance('iam', 'v1')
    context['iam-messages'] = apis.GetMessagesModule('iam', 'v1')
    context['iam-resources'] = resources
