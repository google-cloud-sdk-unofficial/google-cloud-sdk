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
"""Shared resource flags for Cloud Build commands."""


from googlecloudsdk.api_lib.cloudbuild import pipeline_config
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def RegionAttributeConfig():
  fallthroughs = [
      deps.PropertyFallthrough(properties.VALUES.builds.region)
  ]
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      fallthroughs=fallthroughs,
      help_text='The Cloud location for the {resource}.')


def GetTriggerResourceSpec():
  return concepts.ResourceSpec(
      'cloudbuild.projects.locations.triggers',
      api_version='v1',
      resource_name='trigger',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      triggersId=TriggerAttributeConfig())


def TriggerAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='trigger',
      help_text='Build Trigger ID')


def GetWorkflowResourceSpec():
  return concepts.ResourceSpec(
      'cloudbuild.projects.locations.workflows',
      api_version='v2',
      resource_name='workflow',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      workflowsId=WorkflowAttributeConfig())


def WorkflowAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='workflow', help_text='Workflow ID')


def GetGitLabConfigResourceSpec():
  return concepts.ResourceSpec(
      'cloudbuild.projects.locations.gitLabConfigs',
      api_version='v1',
      resource_name='gitLabConfig',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      gitLabConfigsId=GitLabConfigAttributeConfig())


def GitLabConfigAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='config', help_text='Config Name')


class PipelineIdFromFileFallthrough(deps.ArgFallthrough):
  """Resolves the pipeline ID from the pipeline definition file.

  A declarative definition already names itself in `metadata.name`, so
  demanding the ID on the command line as well would defeat the purpose of
  applying a file. This reads the ID back out of the file named by the given
  flag whenever the user supplies no ID of their own.
  """

  def __init__(self, arg_name='--file'):
    super(PipelineIdFromFileFallthrough, self).__init__(arg_name)
    self._hint = (
        'set `metadata.name` in the pipeline definition file given by `{}`'
        .format(arg_name)
    )

  def _Call(self, parsed_args):
    path = super(PipelineIdFromFileFallthrough, self)._Call(parsed_args)
    if not path:
      return None
    return pipeline_config.ExtractPipelineId(path)


def PipelineAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='pipeline',
      fallthroughs=[PipelineIdFromFileFallthrough()],
      help_text=(
          'The ID of the {resource}. If omitted, it is read from '
          '`metadata.name` in the pipeline definition file.'
      ))


def GetPipelineResourceSpec():
  return concepts.ResourceSpec(
      'cloudbuild.projects.locations.pipelines',
      api_version='v1',
      resource_name='pipeline',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      pipelinesId=PipelineAttributeConfig(),
      disable_auto_completers=False)


def AddPipelineResourceArg(parser, verb, positional=True, required=True):
  """Adds a pipeline resource argument to the parser.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    verb: str, a phrase describing what the command does with the pipeline,
      such as 'to apply'.
    positional: bool, whether the anchor is a positional argument.
    required: bool, whether the resource must resolve. The anchor is still
      accepted as an optional positional, because it has a fallthrough.
  """
  concept_parsers.ConceptParser.ForResource(
      'pipeline' if positional else '--pipeline',
      GetPipelineResourceSpec(),
      'The Cloud Build pipeline {}.'.format(verb),
      required=required).AddToParser(parser)
