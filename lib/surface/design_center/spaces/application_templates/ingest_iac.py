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
"""Command to ingest IaC into an Application Template."""


from __future__ import annotations

import argparse

from googlecloudsdk.api_lib.design_center import application_templates as apis
from googlecloudsdk.api_lib.design_center import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags
from googlecloudsdk.core import log


_DETAILED_HELP = {
    'DESCRIPTION': """\
        Ingest Infrastructure as Code (IaC) for a Design Center application
        template from a Cloud Storage bucket, a local IaC module file, a
        Developer Connect repository, or a public Git repository.
        """,
    'EXAMPLES': """ \
        To ingest IaC from a Cloud Storage URI into the application template `my-template` in space `my-space` and location `us-central1`, run:

          $ {command} my-template --space=my-space --location=us-central1 --gcs-uri=gs://my-bucket/iac

        To ingest IaC from a local YAML file named `iac_module.yaml` as raw Terraform, run:

          $ {command} my-template --space=my-space --location=us-central1 --iac-module-from-file=iac_module.yaml --raw-terraform-import-enabled

        To ingest IaC from the `main` branch of a Developer Connect repository, run:

          $ {command} my-template --space=my-space --location=us-central1 --developer-connect-repo-uri=projects/my-project/locations/us-central1/connections/my-connection/gitRepositoryLinks/my-repo --developer-connect-dir=infra --developer-connect-branch=main

        To return immediately without waiting for the operation to complete, run:

          $ {command} my-template --space=my-space --location=us-central1 --gcs-uri=gs://my-bucket/iac --async
        """,
}

_MAX_WAIT_SEC = 600


def _Run(command, args: argparse.Namespace) -> object:
  """Runs the ingest-iac command for the given release track."""
  release_track = command.ReleaseTrack()
  client = apis.ApplicationTemplatesClient(release_track)
  messages = client.messages
  app_template_ref = args.CONCEPTS.application_template.Parse()

  iac_module_msg = None
  if args.iac_module_from_file:
    iac_module_data = flags.ParseIacModuleFile(args.iac_module_from_file)
    try:
      iac_module_msg = utils.ParseIaCModuleData(client, iac_module_data)
    except ValueError as e:
      raise flags.arg_parsers.ArgumentTypeError(
          'Invalid format for --iac-module-from-file: {}'.format(e))

  developer_connect_source_config = None
  if args.developer_connect_repo_uri:
    developer_connect_source_config = messages.DeveloperConnectSourceConfig(
        developerConnectRepoUri=args.developer_connect_repo_uri,
        dir=args.developer_connect_dir,
        reference=messages.GitReference(
            branch=args.developer_connect_branch,
            refTag=args.developer_connect_ref_tag,
            commitSha=args.developer_connect_commit_sha))

  git_source = None
  if args.git_source_repo:
    git_source = messages.GitSource(
        repo=args.git_source_repo,
        refTag=args.git_source_ref_tag,
        dir=args.git_source_dir)

  operation = client.IngestIac(
      name=app_template_ref.RelativeName(),
      gcs_uri=args.gcs_uri,
      iac_module=iac_module_msg,
      developer_connect_source_config=developer_connect_source_config,
      git_source=git_source,
      raw_terraform_import_enabled=args.raw_terraform_import_enabled,
      validate_catalog_compatibility=args.validate_catalog_compatibility)

  if args.async_:
    log.status.Print(f'Check operation [{operation.name}] for status.')
    return operation

  return utils.WaitForOperationWithEmbeddedResult(
      client.client,
      operation,
      message='Waiting for IaC ingestion to complete',
      release_track=release_track,
      max_wait_sec=_MAX_WAIT_SEC)


def _Args(parser):
  flags.AddApplicationTemplateResourceArg(parser, verb='into which to ingest')
  flags.AddIngestIacFlags(parser)
  base.ASYNC_FLAG.AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
@base.UniverseCompatible
class IngestIacGA(base.Command):
  """Ingest Infrastructure as Code (IaC) for an application template."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args: argparse.Namespace) -> object:
    """Run the ingest-iac command."""
    return _Run(self, args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class IngestIacAlpha(base.Command):
  """Ingest Infrastructure as Code (IaC) for an application template."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args: argparse.Namespace) -> object:
    """Run the ingest-iac command."""
    return _Run(self, args)
