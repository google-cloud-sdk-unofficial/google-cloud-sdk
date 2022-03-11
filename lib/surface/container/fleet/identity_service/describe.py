# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""The command to describe the status of the Identity Service Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as gcloud_base
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import log


class Describe(base.FeatureCommand, gcloud_base.ListCommand):
  """Prints the status of all clusters with Identity Service installed.

  Prints the status of the Identity Service Feature resource in a fleet.

  ## EXAMPLES

  To describe the status of the Identity Service configuration, run:

    $ {command}

  """

  feature_name = 'identityservice'

  @classmethod
  def Args(cls, parser):
    pass

  def Run(self, args):
    # Get fleet memberships (cluster registered with fleet) from GCP Project.
    memberships = base.ListMemberships()
    response = self.GetFeature()
    if not memberships:
      log.status.Print('No Memberships available in the fleet.')
      return {}

    return {'Identity Service Feature': response}
