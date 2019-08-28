# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""The super-group for the Policy Troubleshoot CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class PolicyTroubleshoot(base.Group):
  """Troubleshoot Google Cloud Platform Policies.

     Policy Troubleshooter troubleshoots cloud
     policies running on Google Cloud Platform. Policy Troubleshooter works by
     evaluating the current access a user has on a cloud resource.

     More information on Policy Troubleshooter can be found here:
     https://cloud.google.com/iam
  """

  category = base.IDENTITY_AND_SECURITY_CATEGORY
