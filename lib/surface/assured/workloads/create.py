# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to create a new Assured Workloads environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import create_workload
from googlecloudsdk.command_lib.assured import flags


@base.ReleaseTracks(ReleaseTrack.GA)
class GaCreate(create_workload.CreateWorkload):
  """Create a new Assured Workloads environment."""

  detailed_help = {
      'DESCRIPTION':
          'Create a new Assured Workloads environment',
      'EXAMPLES':
          """ \
      The following example command creates a new Assured Workloads environment with these properties:

      * belonging to an organization with ID 123
      * located in the `us-central1` region
      * display name `Test-Workload`
      * compliance regime `FEDRAMP_MODERATE`
      * billing account `billingAccounts/456`
      * first key rotation set for 10:15am on the December 30, 2020
      * key rotation interval set for every 48 hours
      * with the label: key = 'LabelKey1', value = 'LabelValue1'
      * with the label: key = 'LabelKey2', value = 'LabelValue2'
      * provisioned resources parent 'folders/789'

        $ {command} --organization=123 --location=us-central1 --display-name=Test-Workload --compliance-regime=FEDRAMP_MODERATE --billing-account=billingAccounts/456 --next-rotation-time=2020-12-30T10:15:00.00Z --rotation-period=172800s --labels=LabelKey1=LabelValue1,LabelKey2=LabelValue2 --provisioned-resources-parent=folders/789

      """,
  }

  @staticmethod
  def Args(parser):
    flags.AddCreateWorkloadFlags(parser, ReleaseTrack.GA)


@base.ReleaseTracks(ReleaseTrack.BETA)
class BetaCreate(create_workload.CreateWorkload):
  """Create a new Assured Workloads environment."""

  @staticmethod
  def Args(parser):
    flags.AddCreateWorkloadFlags(parser, ReleaseTrack.BETA)


@base.ReleaseTracks(ReleaseTrack.ALPHA)
class AlphaCreate(create_workload.CreateWorkload):
  """Create a new Assured Workloads environment."""

  @staticmethod
  def Args(parser):
    flags.AddCreateWorkloadFlags(parser, ReleaseTrack.ALPHA)
