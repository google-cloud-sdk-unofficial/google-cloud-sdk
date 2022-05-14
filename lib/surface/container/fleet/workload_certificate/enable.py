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
"""The command to enable Workload Certificate Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base


class Enable(base.EnableCommand):
  """Enable Workload Certificate Feature.

  Enable the Workload Certificate Feature in a Fleet, specify
  provision-google-ca to use Google provisioned CAS.

  ## Examples

  To enable Workload Certificate Feature, run:

    $ {command}

  To enable Workload Certificate Feature with Google provisioned CAS, run:

    $ {command} --provision-google-ca

  """

  feature_name = 'workloadcertificate'
  feature_display_name = 'Workload Certificate'
  feature_api = 'workloadcertificate.googleapis.com'

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--provision-google-ca',
        help='Use Google provisioned CAS.',
        action='store_true',
    )

  def Run(self, args):
    feature = self.messages.Feature()
    if args.provision_google_ca:
      feature.spec = self.messages.CommonFeatureSpec(
          workloadcertificate=self.messages.FeatureSpec(
              provisionGoogleCa=self.messages.FeatureSpec
              .ProvisionGoogleCaValueValuesEnum.ENABLED,),)
    else:
      feature.spec = self.messages.CommonFeatureSpec(
          workloadcertificate=self.messages.FeatureSpec(
              provisionGoogleCa=self.messages.FeatureSpec
              .ProvisionGoogleCaValueValuesEnum.DISABLED,),)
    self.Enable(feature)
