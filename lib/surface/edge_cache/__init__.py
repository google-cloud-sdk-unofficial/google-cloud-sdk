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
"""Command group for Network Services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
@base.Hidden
class EdgeCache(base.Group):
  """Manage Edge Cache resources."""
  category = base.NETWORKING_CATEGORY

  detailed_help = {
      "DESCRIPTION": "Manage Cloud Media Edge resources.",
      "EXAMPLES":
          """
          To list Services in the active Cloud Platform project, run:

            $ {command} services list

          To create an Origin that points to a Cloud Storage bucket, run:

            $ {command} origins create my-origin --origin-address="gs://bucket"

          To import a Service configuration from a YAML definition, run:

            $ {command} services import my-service --source=config.yaml

          To describe a Keyset, run:

            $ {command} keysets describe my-keyset
          """
  }

  def Filter(self, context, args):
    # TODO(b/190537939):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
