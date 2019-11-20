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
"""Delete command for the Label Manager - Label Bindings CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.labelmanager import service as labelmanager
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.labelmanager import arguments
from googlecloudsdk.command_lib.labelmanager import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Deletes a LabelBinding.

    Deletes a LabelBinding given the LabelValue and the resource that the
    LabelValue should be bound to. For Organization,
    Folder, and Project resources, it should be in the form "type/id", e.g.
    "organizations/123". For other resource types, full resource name must be
    used. See:
    https://cloud.google.com/apis/design/resource_names#full_resource_name.
    The LabelValue can be represented with it's numeric id or with it's display
    name along with details on the parent LabelKey. The LabelKey's details
    can be passed as a numeric id or the display name along with the
    label-parent.
  """

  detailed_help = {
      'EXAMPLES':
          """
          To delete a binding between 'labelValue/123' and Project with name
          '//cloudresourcemanager.googleapis.com/projects/1234' run:

            $ {command} labelValue/123 --resource='//cloudresourcemanager.googleapis.com/projects/1234'

          To create a binding between LabelValue 'test' under 'labelKeys/456'
          and Project '//cloudresourcemanager.googleapis.com/projects/1234' run:

            $ {command} test --label-key='labelKeys/456' --resource='//cloudresourcemanager.googleapis.com/projects/1234'

          To delete a binding between LabelValue test under LabelKey 'env' that
          lives under 'organizations/789' and Project '//cloudresourcemanager.googleapis.com/projects/1234' run:

            $ {command} test --label-key='env' --label-parent='organizations/789' --resource='//cloudresourcemanager.googleapis.com/projects/1234'
          """
  }

  @staticmethod
  def Args(parser):
    group = parser.add_argument_group('LabelValue.', required=True)
    arguments.AddLabelValueIdArgToParser(group)
    arguments.AddLabelKeyArgToParser(
        group,
        required=False,
        message=(' --label-key is required when using display name instead '
                 'of numeric id for LABEL_VALUE_ID.'))
    arguments.AddLabelParentArgToParser(
        group,
        required=False,
        message=(' --label-parent is required when using display name instead '
                 'of numeric id for the --label-key.'))
    arguments.AddResourceArgToParser(
        parser,
        required=True,
        message=('Fully qualified name of the resource that the LabelValue is '
                 'bound to.')
    )

  def Run(self, args):
    labelbindings_service = labelmanager.LabelBindingsService()
    labelmanager_messages = labelmanager.LabelManagerMessages()

    label_value = utils.GetLabelValueIfArgsAreValid(args)
    label_value_id = utils.GetIdFromResourceName(label_value)

    request = labelmanager_messages.LabelmanagerLabelValuesLabelBindingsDeleteRequest(
        labelBinding_labelValue=label_value,
        labelBinding_resource=args.resource,
        labelValuesId=label_value_id,
        labelBindingsId=args.resource)

    return labelbindings_service.Delete(request)
