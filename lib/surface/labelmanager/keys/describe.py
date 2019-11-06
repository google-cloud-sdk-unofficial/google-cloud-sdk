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
"""Describe command for the Label Manager - Label Keys CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.Command):
  """Describes a label key resource under the specified label parent.

  ## EXAMPLES

  To describe a label key with the name env under the organization/123 run:

        $ gcloud alpha labelmanager keys describe env
        --label_parent='organizations/123'
  """

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group('label key', required=True)
    arguments.AddLabelParentArgToParser(group)
    arguments.AddDisplayNameArgToParser(group)

  def Run(self, args):
    labelkeys_service = labelmanager.LabelKeysService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    display_name = args.DISPLAY_NAME
    label_parent = args.label_parent

    label_key = utils.GetLabelKeyDisplayName(display_name, label_parent)

    get_request = labelmanager_messages.LabelmanagerLabelKeysGetRequest(
        name=label_key)
    return labelkeys_service.Get(get_request)
