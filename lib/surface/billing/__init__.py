# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Commands for managing billing accounts and associate them with projects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Billing(base.Group):
  # TODO(b/190388783): Once gcloud billing is fully GA, replace "gcloud beta
  # billing" with "{command}" in the examples below.
  #
  # Currently we hardcode "gcloud beta billing" because the example commands are
  # only in beta. They are not yet available as GA commands, so if we wrote
  # "{command}" right now, we would generate documentation with invalid sample
  # commands in the GA environment.
  #
  # Note that we don't want to suppress this billing group documentation
  # entirely from the GA environment, since other billing commands (namely the
  # budget commands) are GA, so the GA billing landing page should remain as an
  # entry point to reach the documentation for those commands.
  r"""Manage billing accounts and associate them with projects.

  Manage billing accounts and associate them with projects.

  ## EXAMPLES

  To list billing accounts associated with the current user, run:

    $ gcloud beta billing accounts list

  To link one of the billing accounts `0X0X0X-0X0X0X-0X0X0X` with a project
  `my-project`, run:

    $ gcloud beta billing projects link my-project \
        --billing-account 0X0X0X-0X0X0X-0X0X0X
  """

  category = base.BILLING_CATEGORY

  def Filter(self, context, args):
    del context, args
    base.DisableUserProjectQuota()
