# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command for spanner databases update."""


import textwrap

from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.spanner import resource_args


@base.UniverseCompatible
class Update(base.UpdateCommand):
  """Update a Cloud Spanner database."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
        To enable database deletion protection on a Cloud Spanner database
        'my-database', run:

          $ {command} my-database --enable-drop-protection

        To disable database deletion protection on a Cloud Spanner database
        'my-database', run:

          $ {command} my-database --no-enable-drop-protection

        To update KMS key references for a Cloud Spanner database
        'my-database', run:

          $ {command} my-database --kms-keys="KEY1,KEY2"

        To remove all KMS key references and revert a Cloud Spanner database
        'my-database' to Google-managed encryption, run:

          $ {command} my-database --clear-kms-keys
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddDatabaseResourceArg(parser, 'to update')
    mutex_group = parser.add_argument_group(mutex=True)
    flags.EnableDropProtection().AddToParser(mutex_group)
    flags.EnableUpdateKmsKeys().AddToParser(mutex_group)
    flags.ClearKmsKeys().AddToParser(mutex_group)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs the `database update` command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Database update response.
    """
    op = databases.Update(
        args.CONCEPTS.database.Parse(),
        enable_drop_protection=args.enable_drop_protection,
        kms_keys=args.kms_keys,
        clear_kms_keys=args.clear_kms_keys,
    )
    if args.async_:
      return op
    return database_operations.Await(op, 'Updating database.')
