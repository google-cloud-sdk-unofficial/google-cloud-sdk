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
"""Implements command to generate data validation configuration."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq.migration import validation_client
from googlecloudsdk.command_lib.bq.migration import validation_flags


@base.RegionalEndpointsSupported
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Configure(base.Command):
  """Generate the configuration for validating migrated data."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Generate the configuration files that `{parent_command} run` uses to
          validate data migrated to BigQuery against its source. The
          configuration covers the source tables described by a metadata
          archive produced by `gcloud alpha bq migration metadata extract`
          (`--metadata`) and/or by the `tables.yaml` mapping files produced by
          BigQuery Migration Service SQL translation (`--tables-yaml`).

          The output directory contains one YAML file per table under
          `databases/`, `index.yaml` listing the configured tables,
          `connections.yaml` with templates for the source and target
          connection profiles, and `settings.yaml` with the Cloud Storage
          location where source samples are staged and the results settings.
          Complete `connections.yaml` and `settings.yaml` before running the
          validation.

          The configuration is generated on this machine by the BigQuery
          Migration Validation Client, which requires Java 11 or later on your
          `PATH`; the `bqms` component of the gcloud CLI, which contains the
          client, is installed on first use if it is missing. To pass
          additional options to the Java virtual machine, set the `JAVA_OPTS`
          environment variable, for example `export JAVA_OPTS=-Xmx8G` (Linux
          and macOS) or `set JAVA_OPTS=-Xmx8G` (Windows Command Prompt).

          Arguments after `--` are forwarded to the validation client
          unchanged. With `--quiet`, the client resolves ambiguities with
          defaults instead of prompting.
          """
      ),
      'EXAMPLES': (
          """\
          To generate configuration files under `./validation_config` for the
          tables in the Teradata metadata archive
          `dwh-migration-teradata-metadata.zip`, migrated to the BigQuery
          dataset `my_dataset`, run:

            $ {command} --metadata=dwh-migration-teradata-metadata.zip \\
                --target-dataset=my_dataset --output=validation_config

          To generate configuration files for the tables of the `sales` schema
          from the `tables.yaml` mapping files under `./translation_output`,
          overwriting any existing files under `./validation_config`, run:

            $ {command} --tables-yaml=translation_output --schemas=sales \\
                --output=validation_config --force
          """
      ),
  }

  @staticmethod
  def Args(parser):
    validation_flags.AddConfigureFlags(parser)

  def Run(self, args):
    validation_client.Run(
        validation_client.GENERATE_CONFIG_SUBCOMMAND,
        validation_flags.GetConfigureClientArgs(args),
    )
