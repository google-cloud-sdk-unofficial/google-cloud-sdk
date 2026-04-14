# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Utilities for interacting with the Composer DAG API."""

import json
import pathlib
from googlecloudsdk.api_lib.composer import dags_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


DEPLOYMENT_FILE = 'deployment.yaml'


def _build_triggers(dag):
  """Creates a list of triggers for a DAG.

  Args:
    dag: The DAG object from Composer API.

  Returns:
    A list containing a trigger dictionary for the DAG.
  """
  return [{
      'schedule': (
          dag.cronSchedule if dag.cronSchedule else dag.durationSchedule
      ),
      'start_time': dag.startDate,
      'end_time': dag.endDate,
      'catchup': dag.catchup,
  }]


def build_resource_name(environment=None, runner=None):
  """Builds a resource name.

  The resource name is in the format of
  projects/{project}/locations/{location}/environments/{environment}.

  Args:
    environment: Optional; The name of the environment configuration to use from
      deployment.yaml. Used if 'runner' is not provided.
    runner: Optional; The full resource name to use. For now it supports only
      Composer environment full resource name. If provided, this argument takes
      precedence over 'environment'.

  Returns:
    The resource name string.
  """
  if runner:
    prefix = '//composer.{}/'.format(
        properties.VALUES.core.universe_domain.Get()
    )
    if not runner.startswith(prefix):
      raise calliope_exceptions.InvalidArgumentException(
          '--runner',
          'Runner must be a full resource name. Example: '
          '"{}projects/PROJECT_ID/locations/LOCATION/environments/ENVIRONMENT_NAME"'
          .format(prefix),
      )
    return runner[len(prefix) :]
  else:
    work_dir = pathlib.Path.cwd()
    bundle_dir = work_dir
    deployment_path = bundle_dir / DEPLOYMENT_FILE
    environment_config = yaml_processor.load_environment(
        deployment_path, environment
    )
    project = environment_config.project
    location = environment_config.region
    environment = environment_config.composer_environment
    return f'projects/{project}/locations/{location}/environments/{environment}'


def build_dags_filter_tags(
    bundle=None,
    pipeline=None,
    is_current=False,
    version=None,
    owner=None,
    is_paused=False,
):
  """Builds a filter string for listing Composer DAGs based on tags.

  Args:
    bundle: Optional; The bundle ID to filter by.
    pipeline: Optional; The pipeline ID to filter by.
    is_current: Optional; If True, filters for DAGs with the 'op:is_current'
      tag.
    version: Optional; The version to filter by. Requires 'bundle' to be set.
    owner: Optional; The owner to filter by.
    is_paused: Optional; If True, filters for DAGs with the 'op:is_paused' tag.

  Returns:
    A filter string for use with Composer API list DAGs requests.
  """

  tags = ['op:orchestration_pipeline']
  if is_current:
    tags.append('op:is_current')
  if bundle:
    tags.append('op:bundle:' + bundle)
    if version:
      tags.append('op:version:' + version)
  if pipeline:
    tags.append('op:pipeline:' + pipeline)
  if owner:
    tags.append('op:owner:' + owner)
  if is_paused:
    tags.append('op:is_paused')
  return ' AND '.join(['tags="' + tag + '"' for tag in tags])


def build_dag_runs_filter_dag_id(bundle, pipeline, version=None):
  """Builds a filter string regex for listing Composer DAG runs based on DAG ID.

  The DAG ID format for orchestration pipelines is bundle__v__version__pipeline.

  Args:
    bundle: The bundle ID to filter by.
    pipeline: The pipeline ID to filter by.
    version: Optional; The version to filter by.

  Returns:
    A regex string for filtering DAG runs by DAG ID.
  """
  bundle_id = bundle or '*'
  version_id = version or '*'
  pipeline_id = pipeline or '*'
  return f'dag_id="{bundle_id}__v__{version_id}__{pipeline_id}"'


def list_pipelines_with_filter(list_filter, environment, runner, api_version):
  """Lists pipelines with the given filter.

  Args:
    list_filter: The filter to apply when listing pipelines.
    environment: The name of the environment configuration to use from
      deployment.yaml.
    runner: The full resource name to use.
    api_version: The API version to use for the Composer API.

  Returns:
    A list of DAGs matching the filter.
  """
  environment_resource_name = build_resource_name(
      environment, runner
  )
  environment_ref = resources.REGISTRY.ParseRelativeName(
      environment_resource_name,
      collection='composer.projects.locations.environments',
      api_version=api_version,
  )
  dags_list = dags_util.ListDags(
      environment_ref,
      list_filter=list_filter,
  )
  return dags_list


def parse_metadata_json(metadata_json):
  """Parses the metadata JSON string.

  Args:
    metadata_json: The metadata JSON string.

  Returns:
    A dictionary representing the metadata JSON string, or an empty dictionary
    if the metadata JSON string is not valid JSON.
  """

  try:
    return json.loads(metadata_json)
  except (json.JSONDecodeError, TypeError) as e:
    log.warning('Could not parse metadata for resource: %s', e)
    return {}


def get_pipeline_paused_status(dag):
  """Returns True if pipeline is paused.

  Pipeline is considered paused if it has 'op_is_paused' field in its doc_md and
  has no active schedule.

  Args:
    dag: The DAG object from Composer API.

  Returns:
    True if pipeline is paused, False otherwise.
  """
  doc_md = parse_metadata_json(dag.docMd)
  return doc_md.get('op_is_paused', False) and (
      dag.cronSchedule is None and dag.durationSchedule is None
  )


def convert_dags_to_pipelines(dags):
  """Converts a list of DAGs to a list of pipeline dicts.

  Args:
    dags: A list of DAG objects from Composer API.

  Returns:
    A list of pipelines.
  """
  pipelines = []
  for dag in dags:
    doc_md = parse_metadata_json(dag.docMd)
    is_paused = get_pipeline_paused_status(dag) or dag.state.name == 'PAUSED'
    metadata = {
        'airflow_dag_id': dag.dagId,
        'origination': doc_md.get('op_origination'),
    }
    if doc_md.get('op_origination') == 'GIT_CI_CD':
      metadata.update({
          'source': {
              'repository': (
                  doc_md.get('op_deployment_details').get('op_repository')
              ),
              'branch': doc_md.get('op_deployment_details').get('op_branch'),
              'commit_sha': (
                  doc_md.get('op_deployment_details').get('op_commit_sha')
              ),
          },
      })
    pipelines.append({
        'pipeline_id': doc_md.get('op_pipeline'),
        'bundle_id': doc_md.get('op_bundle'),
        'version': doc_md.get('op_version'),
        'description': dag.description,
        'owner': doc_md.get('op_owner'),
        'status': 'UNHEALTHY' if dag.dagId.startswith('ERROR__') else 'HEALTHY',
        'is_paused': is_paused,
        'tags': dag.tags,
        'metadata': metadata,
    })

    if dag.dagId.startswith('ERROR__'):
      pipelines[-1].update({
          'error': {
              'message': doc_md.get('op_error'),
          }
      })

    # Only add triggers for active pipelines.
    if not is_paused:
      pipelines[-1].update({'triggers': _build_triggers(dag)})
    else:
      pipelines[-1].update({'schedule': doc_md.get('op_schedule')})
  return pipelines


def convert_tasks_to_actions(tasks):
  """Converts a list of Tasks to a list of action dicts.

  Tasks are aggregated based on `action_name`.

  Args:
    tasks: A list of Task objects from Composer DAG API.

  Returns:
    A list of dictionaries, each representing an action.
  """
  task_id_to_action_name = {}
  action_tasks = {}
  for task in tasks:
    doc_md = parse_metadata_json(task.docMd)
    action_name = doc_md.get('op_action_name')
    task_id_to_action_name[task.id] = action_name
    action_tasks.setdefault(action_name, []).append(task)

  actions_dict = {}
  for action_name, tasks_in_action in action_tasks.items():
    upstream_actions = set()
    downstream_actions = set()

    for task in tasks_in_action:
      for upstream_task_id in task.upstreamTasks:
        upstream_action_name = task_id_to_action_name.get(upstream_task_id)
        if upstream_action_name and upstream_action_name != action_name:
          upstream_actions.add(upstream_action_name)

      for downstream_task_id in task.downstreamTasks:
        downstream_action_name = task_id_to_action_name.get(downstream_task_id)
        if downstream_action_name and downstream_action_name != action_name:
          downstream_actions.add(downstream_action_name)

    first_task = tasks_in_action[0]
    actions_dict[action_name] = {
        'name': action_name,
        'upstream_actions': sorted(list(upstream_actions)),
        'downstream_actions': sorted(list(downstream_actions)),
        'execution_timeout': first_task.executionTimeout,
        'retries': first_task.retries,
        'metadata': {'airflow_dag_id': first_task.dagId},
    }
  return sorted(actions_dict.values(), key=lambda x: x['name'])


def convert_dag_runs_to_pipeline_runs(dag_runs):
  """Converts a list of DAG runs to a list of pipeline run dicts.

  Args:
    dag_runs: A list of DAG run objects from Composer API.

  Returns:
    A list of dictionaries, each representing a pipeline run.
  """

  pipeline_runs = []
  for dag_run in dag_runs:
    note = parse_metadata_json(dag_run.note)
    metadata = {
        'airflow_dag_id': dag_run.dagId,
    }

    pipeline_runs.append({
        'pipeline_run_id': dag_run.dagRunId,
        'bundle_id': note.get('op_bundle'),
        'version': note.get('op_version'),
        'pipeline_id': note.get('op_pipeline'),
        'state': dag_run.state,
        'type': dag_run.type,
        'execution_date': dag_run.executionDate,
        'start_date': dag_run.startDate,
        'end_date': dag_run.endDate,
        'metadata': metadata,
    })
  return pipeline_runs


def aggregate_task_instances_to_actions(task_instances):
  """Converts a list of Task Instances to a list of actions dict.

  Task Instances are aggregated based on `action_name`.

  Args:
    task_instances: A list of Task Instances objects from Composer DAG API.

  Returns:
    A list of dictionaries, each representing an action.
  """
  task_instance_id_to_action_name = {}
  action_task_instances = {}
  for task_instance in task_instances:
    note = parse_metadata_json(task_instance.note)
    action_name = note.get('op_action_name')
    task_instance_id_to_action_name[task_instance.id] = action_name
    action_task_instances.setdefault(action_name, []).append(task_instance)

  actions_dict = {}
  for action_name, task_instances_in_action in action_task_instances.items():

    start_dates = [
        ti.startDate for ti in task_instances_in_action if ti.startDate
    ]
    end_dates = [ti.endDate for ti in task_instances_in_action if ti.endDate]
    states = {ti.state.name for ti in task_instances_in_action if ti.state}

    if not states:
      combined_state = 'STATE_UNSPECIFIED'
    elif 'FAILED' in states or 'UPSTREAM_FAILED' in states:
      combined_state = 'FAILED'
    elif any(
        s in states
        for s in [
            'RUNNING',
            'QUEUED',
            'SCHEDULED',
            'DEFERRED',
            'SENSING',
            'UP_FOR_RETRY',
            'UP_FOR_RESCHEDULE',
        ]
    ):
      combined_state = 'RUNNING'
    elif 'SKIPPED' in states or 'REMOVED' in states:
      combined_state = 'SKIPPED'
    elif states == {'SUCCEEDED'}:
      combined_state = 'SUCCEEDED'
    else:
      combined_state = 'STATE_UNSPECIFIED'

    try_numbers = [
        ti.tryNumber for ti in task_instances_in_action if ti.tryNumber
    ]

    ti = task_instances_in_action[0]
    actions_dict[action_name] = {
        'name': action_name,
        'state': combined_state,
        'start_date': (
            min(start_dates)
            if len(start_dates) == len(task_instances_in_action)
            else None
        ),
        'end_date': (
            max(end_dates)
            if len(end_dates) == len(task_instances_in_action)
            else None
        ),
        'execution_date': ti.executionDate,
        'try_number': max(try_numbers) if try_numbers else None,
        'max_retries': ti.maxTries,
        'metadata': {
            'airflow_dag_id': ti.dagId,
            'airflow_task_instances': [
                build_task_instance_metadata(ti)
                for ti in task_instances_in_action
            ],
        },
    }
  return sorted(actions_dict.values(), key=lambda x: x['name'])


def build_task_instance_metadata(task_instance):
  """Builds task instance metadata from a Task Instance object.

  Args:
    task_instance: A Task Instance object from Composer DAG API.

  Returns:
    A dictionary containing metadata for the task instance.
  """

  return {
      'name': task_instance.taskId,
      'state': task_instance.state,
      'start_date': task_instance.startDate,
      'end_date': task_instance.endDate,
      'execution_date': task_instance.executionDate,
      'try_number': task_instance.tryNumber,
      'max_retries': task_instance.maxTries,
  }
