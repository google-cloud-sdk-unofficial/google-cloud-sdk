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
"""The command to disable the Cloud Build Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.fleet.build import utils
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core.console import console_io


@gbase.Hidden
class Disable(base.DisableCommand):
  """Disable the Cloud Build hybrid pools feature.

  Disables the Cloud Build hybrid pools feature in the fleet.

  ## EXAMPLES

  To disable the Cloud Build hybrid pools feature, run:

    $ {command}
  """

  feature_name = 'cloudbuild'

  def Run(self, args):
    feature = self.GetFeature(v1alpha1=True)

    cloudbuild_members = utils.GetFeatureSpecMemberships(
        feature, self.v1alpha1_messages)
    if cloudbuild_members:
      console_io.PromptContinue(
          'The following members still have Cloud Build hybrid worker pools installed:\n\n{}'
          '\n\nIf you continue, Cloud Build hybrid worker pools will be uninstalled from these members.'
          .format('\n'.join(list(cloudbuild_members))),
          'Do you want to continue?',
          throw_if_unattended=True,
          cancel_on_no=True)

    self.Disable(args.force)
