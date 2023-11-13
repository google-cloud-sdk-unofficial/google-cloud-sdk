# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Implementation of list command for insights dataset config."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List returns all the insights dataset configs for given location."""

  detailed_help = {
      'DESCRIPTION': """
      List Cloud storage insights dataset configs.
      """,
      'EXAMPLES': """

      List all dataset configs for any locations:

          $ {command}

      List all dataset configs for location "us-central1":

          $ {command} --location=us-central1

      List all dataset configs with the page size of "20":

          $ {command} --location=us-central1 --page-size=20

      List all dataset configs with JSON formatting:

          $ {command} --location=us-central1 --format=json
      """,
  }

  @staticmethod
  def Args(parser):
    flags.add_dataset_config_location_flag(parser)

  def Run(self, args):
    # TODO(b/277754528): Add when API function available.
    raise NotImplementedError
