# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Update workflow template command."""

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc import workflow_templates


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  """Update a workflow template."""

  @staticmethod
  def Args(parser):
    flags.AddTemplateFlag(parser, 'update')
    workflow_templates.AddConfigFileArgs(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    messages = dataproc.messages

    template = util.ParseWorkflowTemplates(args.template, dataproc)

    workflow_template = dataproc.GetRegionsWorkflowTemplate(
        template, args.version)

    # load workflow template from YAML or JSON file
    local_workflow_yaml = workflow_templates.ParseYamlOrJsonToWorkflowTemplate(
        args.config_file, messages.WorkflowTemplate)

    if local_workflow_yaml.id != workflow_template.id:
      raise exceptions.WorkflowTemplateError(
          'Workflow template ID [{0}] in YAML or JSON file does not match the '
          'workflow template ID [{1}] in Dataproc.'.format(
              local_workflow_yaml.id, workflow_template.id))

    if local_workflow_yaml.name != workflow_template.name:
      raise exceptions.WorkflowTemplateError(
          'Workflow template name [{0}] in YAML or JSON file does not match '
          'the workflow template name [{1}] in Dataproc.'.format(
              local_workflow_yaml.name, workflow_template.name))

    # update version fields in local yaml workflow template
    local_workflow_yaml.version = workflow_template.version

    response = dataproc.client.projects_regions_workflowTemplates.Update(
        local_workflow_yaml)
    return response
