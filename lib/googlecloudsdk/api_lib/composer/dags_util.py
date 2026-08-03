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
"""Utilities for calling the Composer DAG API."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base

_DEFAULT_PAGE_SIZE = 1000


def GetDagsService(release_track=base.ReleaseTrack.BETA):
  return api_util.GetClientInstance(
      release_track
  ).projects_locations_environments_dags


def GetTasksService(release_track=base.ReleaseTrack.BETA):
  return api_util.GetClientInstance(
      release_track
  ).projects_locations_environments_dags_tasks


def GetDagRunsService(release_track=base.ReleaseTrack.BETA):
  return api_util.GetClientInstance(
      release_track
  ).projects_locations_environments_dags_dagRuns


def GetTaskInstancesService(release_track=base.ReleaseTrack.BETA):
  return api_util.GetClientInstance(
      release_track
  ).projects_locations_environments_dags_dagRuns_taskInstances


def ListDags(
    environment_ref,
    list_filter=None,
    page_size=_DEFAULT_PAGE_SIZE,
    limit=None,
    release_track=base.ReleaseTrack.BETA,
):
  """List DAGs in the given environment by using the Composer DAG API."""
  service = GetDagsService(release_track=release_track)
  request = api_util.GetMessagesModule(
      release_track=release_track
  ).ComposerProjectsLocationsEnvironmentsDagsListRequest(
      parent=environment_ref.RelativeName(),
      filter=list_filter,
  )
  results = list_pager.YieldFromList(
      service,
      request,
      limit=limit,
      batch_size=page_size,
      field='dags',
      batch_size_attribute='pageSize',
  )
  return list(results)


def TriggerDag(
    dag_ref,
    release_track=base.ReleaseTrack.BETA,
):
  """Calls the Composer DAG API TriggerDag method."""
  return GetDagsService(release_track=release_track).Trigger(
      api_util.GetMessagesModule(
          release_track=release_track
      ).ComposerProjectsLocationsEnvironmentsDagsTriggerRequest(
          dag=dag_ref.RelativeName()
      )
  )


def PauseDag(
    dag_ref,
    release_track=base.ReleaseTrack.BETA,
):
  """Calls the Composer DAG API PauseDag method."""
  return GetDagsService(release_track=release_track).Pause(
      api_util.GetMessagesModule(
          release_track=release_track
      ).ComposerProjectsLocationsEnvironmentsDagsPauseRequest(
          name=dag_ref.RelativeName()
      )
  )


def ActivateDag(
    dag_ref,
    release_track=base.ReleaseTrack.BETA,
):
  """Calls the Composer DAG API ActivateDag method."""

  return GetDagsService(release_track=release_track).Activate(
      api_util.GetMessagesModule(
          release_track=release_track
      ).ComposerProjectsLocationsEnvironmentsDagsActivateRequest(
          name=dag_ref.RelativeName()
      )
  )


def ListTasks(
    dag_ref,
    page_size=_DEFAULT_PAGE_SIZE,
    limit=None,
    release_track=base.ReleaseTrack.BETA,
):
  """Lists tasks in the given DAG by using the Composer DAG API."""
  service = GetTasksService(release_track=release_track)
  request = api_util.GetMessagesModule(
      release_track=release_track
  ).ComposerProjectsLocationsEnvironmentsDagsTasksListRequest(
      parent=dag_ref.RelativeName(),
  )
  results = list_pager.YieldFromList(
      service,
      request,
      limit=limit,
      batch_size=page_size,
      field='tasks',
      batch_size_attribute='pageSize',
  )
  return list(results)


def ListDagRuns(
    dag_ref,
    list_filter=None,
    page_size=_DEFAULT_PAGE_SIZE,
    limit=None,
    release_track=base.ReleaseTrack.BETA,
):
  """Lists DAG runs in the given DAG by using the Composer DAG API."""
  service = GetDagRunsService(release_track=release_track)
  request = api_util.GetMessagesModule(
      release_track=release_track
  ).ComposerProjectsLocationsEnvironmentsDagsDagRunsListRequest(
      parent=dag_ref.RelativeName(),
      filter=list_filter,
  )
  results = list_pager.YieldFromList(
      service,
      request,
      limit=limit,
      batch_size=page_size,
      field='dagRuns',
      batch_size_attribute='pageSize',
  )
  return list(results)


def GetDagRun(
    dag_run_ref,
    release_track=base.ReleaseTrack.BETA,
):
  """Calls the Composer DAG API GetDagRun method."""
  return GetDagRunsService(release_track=release_track).Get(
      api_util.GetMessagesModule(
          release_track=release_track
      ).ComposerProjectsLocationsEnvironmentsDagsDagRunsGetRequest(
          name=dag_run_ref.RelativeName(),
      )
  )


def ListTaskInstances(
    dag_run_ref,
    list_filter=None,
    page_size=_DEFAULT_PAGE_SIZE,
    limit=None,
    release_track=base.ReleaseTrack.BETA,
):
  """Lists task instances in the given DAG run by using the Composer DAG API."""
  service = GetTaskInstancesService(release_track=release_track)
  request = api_util.GetMessagesModule(
      release_track=release_track
  ).ComposerProjectsLocationsEnvironmentsDagsDagRunsTaskInstancesListRequest(
      parent=dag_run_ref.RelativeName(),
      filter=list_filter,
  )
  results = list_pager.YieldFromList(
      service,
      request,
      limit=limit,
      batch_size=page_size,
      field='taskInstances',
      batch_size_attribute='pageSize',
  )
  return list(results)
