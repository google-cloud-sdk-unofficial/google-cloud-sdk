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
"""Packages a dbt project and its generated `profiles.yml` into one `.tar.gz`."""

from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import pipeline_loader
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration.packagers import models

ARCHIVE_NAME = "dbt_{action}.tar.gz"


def GenerateProfilesYaml(action: pipeline_loader.DbtAction, target: str) -> str:
  """Renders the `profiles.yml` for one dbt action and target.

  Args:
    action: The dbt action whose `profile_config` is rendered.
    target: The dbt target name (the deployment environment).

  Returns:
    The `profiles.yml` document as a string.

  Raises:
    errors.PackagingError: If `profile_config` is invalid.
  """
  # TODO(b/567520802): Build a `type: bigquery`, `method: oauth` profile from
  # the allow-listed keys of `action.profile_config` (DBT design doc).
  del action, target
  raise errors.NotImplementedYetError(
      "GenerateProfilesYaml is not implemented yet."
  )


class DbtPackager:
  """Packages a dbt project directory into a single deterministic archive."""

  def Package(
      self,
      action: pipeline_loader.DbtAction,
      context: models.PackagingContext,
  ) -> models.PackagedArtifact:
    """Bundles the allow-listed project files and `profiles.yml` into a tar.gz.

    Args:
      action: The dbt action to package.
      context: The per-deployment packaging context.

    Returns:
      The packaged artifact containing the single `.tar.gz` staged under
      `context.staging_dir`.

    Raises:
      errors.PackagingError: If the project is invalid or cannot be archived.
    """
    # TODO(b/567520802): Validate the project, collect the allow-listed files
    # (DBT design doc), generate `profiles.yml`, and write a single
    # reproducible `dbt_<action>.tar.gz`.
    del action, context
    raise errors.NotImplementedYetError(
        "DbtPackager.Package is not implemented yet."
    )
