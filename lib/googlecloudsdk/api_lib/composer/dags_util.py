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
    release_track=base.ReleaseTrack.BETA,
):
  """Calls the Composer DAG API ListDags method."""
  return GetDagsService(release_track=release_track).List(
      api_util.GetMessagesModule(
          release_track=release_track
      ).ComposerProjectsLocationsEnvironmentsDagsListRequest(
          parent=environment_ref.RelativeName(),
          filter=list_filter,
          pageSize=page_size,
      )
  )


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
    release_track=base.ReleaseTrack.BETA,
):
  """Calls the Composer DAG API ListTasks method."""
  return GetTasksService(release_track=release_track).List(
      api_util.GetMessagesModule(
          release_track=release_track
      ).ComposerProjectsLocationsEnvironmentsDagsTasksListRequest(
          parent=dag_ref.RelativeName(),
          pageSize=page_size,
      )
  )


def ListDagRuns(
    dag_ref,
    list_filter=None,
    page_size=_DEFAULT_PAGE_SIZE,
    release_track=base.ReleaseTrack.BETA,
):
  """Calls the Composer DAG API ListDagRuns method."""
  return GetDagRunsService(release_track=release_track).List(
      api_util.GetMessagesModule(
          release_track=release_track
      ).ComposerProjectsLocationsEnvironmentsDagsDagRunsListRequest(
          parent=dag_ref.RelativeName(),
          filter=list_filter,
          pageSize=page_size,
      )
  )


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
    release_track=base.ReleaseTrack.BETA,
):
  """Calls the Composer DAG API ListTaskInstances method."""
  return GetTaskInstancesService(release_track=release_track).List(
      api_util.GetMessagesModule(
          release_track=release_track
      ).ComposerProjectsLocationsEnvironmentsDagsDagRunsTaskInstancesListRequest(
          parent=dag_run_ref.RelativeName(),
      )
  )
