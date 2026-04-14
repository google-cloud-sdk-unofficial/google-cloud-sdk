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
"""Command to validate orchestration pipeline configurations."""

import pathlib
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import yaml

DEPLOYMENT_FILE_NAME = "deployment.yaml"


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Validate(calliope_base.Command):
  """Validate orchestration pipeline configurations against schemas."""

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        "--environment",
        required=True,
        help="The target environment of the pipeline, as defined in"
        " deployment.yaml.",
    )
    parser.add_argument(
        "--substitutions",
        metavar="KEY=VALUE",
        type=arg_parsers.ArgDict(),
        help="Variables to substitute in the pipeline configuration.",
    )
    parser.add_argument(
        "--substitutions-file",
        help=(
            "Path to a YAML file containing variable substitutions for the "
            "pipeline configuration."
        ),
    )

  def Run(self, args):
    work_dir = pathlib.Path.cwd()

    # 1. Collect all variables from substitutions file and environment
    # variables
    substitutions_file_vars = {}
    if getattr(args, "substitutions_file", None):
      try:
        substitutions_file_vars = yaml.load_path(args.substitutions_file)
        if not isinstance(substitutions_file_vars, dict):
          raise calliope_exceptions.BadFileException(
              f"Substitutions file {args.substitutions_file} "
              "must contain a dictionary."
          )
      except yaml.Error as e:
        raise calliope_exceptions.BadFileException(
            f"Error parsing substitutions file {args.substitutions_file}: {e}"
        ) from e

    env_vars = yaml_processor.collect_environment_variables()

    external_vars = {}
    external_vars.update(env_vars)
    external_vars.update(substitutions_file_vars)
    if getattr(args, "substitutions", None):
      external_vars.update(args.substitutions)

    # 2. Load and validate deployment file.
    deployment_path = work_dir / DEPLOYMENT_FILE_NAME
    try:
      environment = yaml_processor.load_environment(
          deployment_path, args.environment, external_vars
      )
      yaml_processor.validate_environment(environment, args.environment)
    except (
        yaml.FileLoadError,
        yaml.YAMLParseError,
        yaml_processor.BadFileError,
    ) as e:
      raise calliope_exceptions.BadFileException(
          "Deployment file not found or failed to parse:"
          f" {deployment_path.name}"
      ) from e

    combined_variables = {
        "project": environment.project,
        "region": environment.region,
        **(environment.variables if environment.variables else {}),
    }

    # 3. Perform L1 validation for pipelines defined in the deployment
    # environment.
    yaml_processor.validate_pipeline_l1(
        work_dir,
        environment,
        combined_variables,
    )
