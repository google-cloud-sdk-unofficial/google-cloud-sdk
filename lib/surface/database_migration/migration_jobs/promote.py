# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command to promote migration jobs for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import migration_jobs
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration.migration_jobs import flags as mj_flags

DETAILED_HELP_ALPHA = {
    'DESCRIPTION': """
        Promote a Database Migration Service migration job.
        """,
    'EXAMPLES': """\
        To promote a migration job:

          $ {command} MIGRATION_JOB --region=us-central1
        """,
}

DETAILED_HELP_GA = {
    'DESCRIPTION': """
        Promote a Database Migration Service migration job.
        """,
    'EXAMPLES': """\
        To promote a migration job:

          $ {command} MIGRATION_JOB --region=us-central1
        """,
}


class _Promote(object):
  """Promote a Database Migration Service migration job."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddOnlyMigrationJobResourceArgs(parser, 'to promote')

  def Run(self, args):
    """Promote a Database Migration Service migration job.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the promote
      operation if the promote was successful.
    """
    migration_job_ref = args.CONCEPTS.migration_job.Parse()

    mj_client = migration_jobs.MigrationJobsClient(self.ReleaseTrack())
    return mj_client.Promote(
        migration_job_ref.RelativeName(),
        args,
    )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class PromoteGA(_Promote, base.Command):
  """Promote a Database Migration Service migration job."""

  detailed_help = DETAILED_HELP_GA

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    _Promote.Args(parser)
    mj_flags.AddMigrationJobObjectsConfigFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class PromoteAlpha(_Promote, base.Command):
  """Promote a Database Migration Service migration job."""

  detailed_help = DETAILED_HELP_ALPHA

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    _Promote.Args(parser)
