# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Import workflow template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files

SCHEMA_PATH = 'v1beta2/WorkflowTemplate.yaml'


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Import(base.UpdateCommand):
  """Import a workflow template.

  If the specified template resource already exists, it will be overwritten.
  Otherwise, a new template will be created.
  To edit an existing template, you can export the template to a file, edit its
  configuration, and then import the new configuration.
  """

  @staticmethod
  def Args(parser):
    flags.AddTemplateResourceArg(parser, 'import')
    flags.AddTemplateSourceFlag(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    msgs = dataproc.messages

    template_ref = args.CONCEPTS.template.Parse()
    # TODO(b/109837200) make the dataproc discovery doc parameters consistent
    # Parent() fails for the collection because of projectId/projectsId and
    # regionId/regionsId inconsistencies.
    # parent = template_ref.Parent().RelativePath()
    parent = '/'.join(template_ref.RelativeName().split('/')[0:4])

    if args.source:
      with files.FileReader(args.source) as stream:
        template = util.ReadYaml(
            message_type=msgs.WorkflowTemplate,
            stream=stream,
            schema_path=SCHEMA_PATH)
    else:
      template = util.ReadYaml(
          message_type=msgs.WorkflowTemplate,
          stream=sys.stdin,
          schema_path=SCHEMA_PATH)

    # Populate id field.
    template.id = template_ref.Name()

    try:
      old_template = dataproc.GetRegionsWorkflowTemplate(template_ref)
    except apitools_exceptions.HttpError as error:
      if error.status_code != 404:
        raise error
      # Template does not exist. Create a new one.
      request = msgs.DataprocProjectsRegionsWorkflowTemplatesCreateRequest(
          parent=parent, workflowTemplate=template)
      return dataproc.client.projects_regions_workflowTemplates.Create(request)
    # Update the existing template.
    console_io.PromptContinue(
        message=('Workflow template [{0}] will be overwritten.').format(
            template.id),
        cancel_on_no=True)
    # Populate version field and name field.
    template.version = old_template.version
    template.name = template_ref.RelativeName()
    return dataproc.client.projects_regions_workflowTemplates.Update(template)
