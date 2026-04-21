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
from googlecloudsdk.command_lib.orchestration_pipelines import gcp_deployer
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import registry
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
        help="The target environment of the pipeline, as defined in"
        " deployment.yaml.",
    )
    parser.add_argument(
        "--pipeline-paths",
        metavar="PATH",
        type=arg_parsers.ArgList(),
        help="The list of relative pipeline YAML file paths to validate.",
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
    parser.add_argument(
        "--mode",
        choices=["syntax-only", "full"],
        default="full",
        help=(
            "The validation mode to use. 'syntax-only' checks the syntax"
            " and type correctness of the pipeline YAML files. 'full' performs"
            " 'syntax-only' validation and adds semantic checks for referenced"
            " resources such as Cloud project, Composer environment, and"
            " other resources in both deployment and pipeline YAML files."
            " Default mode is 'full'."
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

    # 2. Setup validation contexts based on provided arguments.
    # Each context contains an environment, combined variables, pipeline paths,
    # and resources specific to that context.
    validation_contexts = []
    error_environments = {}
    if args.environment:
      deployment_path = work_dir / DEPLOYMENT_FILE_NAME
      environment = yaml_processor.load_environment(
          deployment_path, args.environment, external_vars
      )
      yaml_processor.validate_environment(environment, args.environment)

      combined_variables = {
          "project": environment.project,
          "region": environment.region,
          **(environment.variables if environment.variables else {}),
      }
      pipeline_paths_in_deployment = (
          [p.source for p in environment.pipelines]
          if getattr(environment, "pipelines", None)
          else []
      )

      # Check if all the pipeline paths specified in the command are a
      # subset of the pipelines in the deployment environment. If not, raise
      # an error.
      if not args.pipeline_paths:
        pipeline_paths = pipeline_paths_in_deployment
      else:
        pipeline_paths = args.pipeline_paths
        for pipeline_path in pipeline_paths:
          if pipeline_path not in pipeline_paths_in_deployment:
            raise calliope_exceptions.BadArgumentException(
                "--pipeline-paths",
                f"Pipeline path '{pipeline_path}' not found in deployment "
                f"environment '{args.environment}'."
            )
      validation_contexts.append({
          "env": environment,
          "combined_vars": combined_variables,
          "pipeline_paths": pipeline_paths,
          "resources": environment.resources if environment else [],
          "name": args.environment,
      })
    elif args.pipeline_paths:
      # Validating pipelines without an explicit environment context.
      validation_contexts.append({
          "env": None,
          "combined_vars": external_vars,
          "pipeline_paths": args.pipeline_paths,
          "resources": [],
          "name": "provided pipelines",
      })
    else:
      all_environments_dict, error_environments = (
          yaml_processor.load_all_environments(
              work_dir / DEPLOYMENT_FILE_NAME,
              external_vars,
          )
      )
      if not all_environments_dict:
        print("No environments found in deployment.yaml.")
        return

      for env_name, env in all_environments_dict.items():
        yaml_processor.validate_environment(env, env_name)
        combined_variables = {
            "project": env.project,
            "region": env.region,
            **(env.variables if env.variables else {}),
        }
        pipeline_paths = (
            [p.source for p in env.pipelines]
            if getattr(env, "pipelines", None)
            else []
        )
        validation_contexts.append({
            "env": env,
            "combined_vars": combined_variables,
            "pipeline_paths": pipeline_paths,
            "resources": env.resources if env else [],
            "name": env_name,
        })

    if not validation_contexts:
      print("No pipelines or environments to validate.")
      return

    # 3. Perform L1 syntax validation for each context.
    for context in validation_contexts:
      env = context["env"]
      combined_vars = context["combined_vars"]
      pipeline_paths = context["pipeline_paths"]
      resources = context["resources"]
      env_name = context["name"]
      has_environment = env is not None

      if pipeline_paths:
        yaml_processor.validate_pipeline_l1(
            work_dir,
            pipeline_paths,
            combined_vars,
        )

      if has_environment:
        for resource in resources:
          if resource.type == "resourceProfile":
            continue
          handler = registry.GetHandler(resource, env)
          gcp_deployer.validate_gcp_resource_l1(handler)

      if has_environment:
        print(
            "Successfully finished syntax validation for pipelines and"
            f" resources in deployment environment '{env_name}'."
        )
      elif args.pipeline_paths:
        print(
            "Successfully finished syntax validation for all provided"
            " pipelines."
        )

    if error_environments:
      print("Errors found while parsing deployment file:")
      for env, e in error_environments.items():
        print(f"  Environment '{env}': {e}")

    if args.mode == "syntax-only":
      return

    # 4. Perform L2 semantic validation for each context.
    for context in validation_contexts:
      env = context["env"]
      combined_vars = context["combined_vars"]
      pipeline_paths = context["pipeline_paths"]
      resources = context["resources"]
      env_name = context["name"]
      has_environment = env is not None

      if pipeline_paths:
        yaml_processor.validate_pipeline_l2(
            work_dir,
            pipeline_paths,
            combined_vars,
            env,
        )

      if has_environment:
        for resource in resources:
          if resource.type == "resourceProfile":
            continue
          handler = registry.GetHandler(resource, env)
          gcp_deployer.validate_gcp_resource_l2(handler)

      if has_environment:
        print(
            "Successfully finished full validation for all pipelines and"
            f" resources in deployment environment '{env_name}'."
        )
      elif args.pipeline_paths:
        print(
            "Successfully finished full validation for all provided pipelines."
        )
