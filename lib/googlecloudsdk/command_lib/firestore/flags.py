# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the firestore related commands."""


import argparse
import json
import string
import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import arg_parsers_usage_text
from googlecloudsdk.calliope import base as calliope_base

# Keys used in index field configuration.
FIELD_CONFIG_FIELD_PATH = 'field-path'
FIELD_CONFIG_ORDER = 'order'
FIELD_CONFIG_ARRAY_CONFIG = 'array-config'
FIELD_CONFIG_VECTOR_CONFIG = 'vector-config'
FIELD_CONFIG_SEARCH_CONFIG = 'search-config'
FIELD_CONFIG_DIMENSION = 'dimension'
FIELD_CONFIG_FLAT = 'flat'
FIELD_CONFIG_TEXT_SPEC = 'text-spec'
FIELD_CONFIG_INDEX_SPECS = 'index-specs'
FIELD_CONFIG_INDEX_TYPE = 'index-type'
FIELD_CONFIG_MATCH_TYPE = 'match-type'
FIELD_CONFIG_GEO_SPEC = 'geo-spec'
FIELD_CONFIG_GEO_JSON_INDEXING_DISABLED = 'geo-json-indexing-disabled'

# Keys used in search index options.
SEARCH_INDEX_OPTIONS_TEXT_LANGUAGE = 'text-language'
SEARCH_INDEX_OPTIONS_TEXT_LANGUAGE_OVERRIDE_FIELD_PATH = (
    'text-language-override-field-path'
)


class FlattenedAppendAction(argparse.Action):
  """Custom argparse action that flattens parsed lists on append.

  This avoids producing nested list-of-lists (e.g., [[obj1], [obj2]]) when
  ArgObject.repeated=True is used in conjunction with parser action='append'.
  """

  def __call__(self, parser, namespace, values, option_string=None):
    items = getattr(namespace, self.dest, None) or []
    if isinstance(values, list):
      items.extend(values)
    else:
      items.append(values)
    setattr(namespace, self.dest, items)


def AddCollectionGroupIdsFlag(parser):
  """Adds flag for collection group ids to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--collection-ids',
      metavar='COLLECTION_GROUP_IDS',
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""\
          List specifying which collection groups will be included in the operation.
          When omitted, all collection groups are included.

          For example, to operate on only the `customers` and `orders`
          collections groups:

            $ {command} --collection-ids='customers','orders'
          """),
  )


def AddDatabaseIdFlag(parser, required=False, hidden=False):
  """Adds flag for database id to the given parser.

  Args:
    parser: The argparse parser.
    required: Whether the flag must be set for running the command, a bool.
    hidden: Whether the flag is hidden, a bool.
  """
  if not required:
    helper_text = textwrap.dedent("""\
        The database to operate on. The default value is `(default)`.

        For example, to operate on database `foo`:

          $ {command} --database='foo'
        """)
  else:
    helper_text = textwrap.dedent("""\
        The database to operate on.

        For example, to operate on database `foo`:

          $ {command} --database='foo'
        """)
  parser.add_argument(
      '--database',
      metavar='DATABASE',
      type=str,
      default='(default)' if not required else None,
      required=required,
      hidden=hidden,
      help=helper_text,
  )


def AddNamespaceIdsFlag(parser):
  """Adds flag for namespace ids to the given parser."""
  parser.add_argument(
      '--namespace-ids',
      metavar='NAMESPACE_IDS',
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""\
          List specifying which namespaces will be included in the operation.
          When omitted, all namespaces are included.

          This is only supported for Datastore Mode databases.

          For example, to operate on only the `customers` and `orders` namespaces:

            $ {command} --namespaces-ids='customers','orders'
          """),
  )


def AddSnapshotTimeFlag(parser):
  """Adds flag for snapshot time to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--snapshot-time',
      metavar='SNAPSHOT_TIME',
      type=str,
      default=None,
      required=False,
      help=textwrap.dedent("""\
          The version of the database to export.

          The timestamp must be in the past, rounded to the minute and not older
          than `earliestVersionTime`. If specified, then the exported documents will
          represent a consistent view of the database at the provided time.
          Otherwise, there are no guarantees about the consistency of the exported
          documents.

          For example, to operate on snapshot time `2023-05-26T10:20:00.00Z`:

            $ {command} --snapshot-time='2023-05-26T10:20:00.00Z'
          """),
  )


def AddLocationFlag(
    parser, required=False, hidden=False, suggestion_aliases=None
):
  """Adds flag for location to the given parser.

  Args:
    parser: The argparse parser.
    required: Whether the flag must be set for running the command, a bool.
    hidden: Whether the flag is hidden in document. a bool.
    suggestion_aliases: A list of flag name aliases. A list of string.
  """
  parser.add_argument(
      '--location',
      metavar='LOCATION',
      required=required,
      hidden=hidden,
      type=str,
      suggestion_aliases=suggestion_aliases,
      help=textwrap.dedent("""\
          The location to operate on. Available locations are listed at
          https://cloud.google.com/firestore/docs/locations.

          For example, to operate on location `us-east1`:

            $ {command} --location='us-east1'
          """),
  )


def AddBackupFlag(parser):
  """Adds flag for backup to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--backup',
      metavar='BACKUP',
      required=True,
      type=str,
      help=textwrap.dedent("""\
          The backup to operate on.

          For example, to operate on backup `cf9f748a-7980-4703-b1a1-d1ffff591db0`:

            $ {command} --backup='cf9f748a-7980-4703-b1a1-d1ffff591db0'
          """),
  )


def AddBackupScheduleFlag(parser):
  """Adds flag for backup schedule id to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--backup-schedule',
      metavar='BACKUP_SCHEDULE',
      required=True,
      type=str,
      help=textwrap.dedent("""\
          The backup schedule to operate on.

          For example, to operate on backup schedule `091a49a0-223f-4c98-8c69-a284abbdb26b`:

            $ {command} --backup-schedule='091a49a0-223f-4c98-8c69-a284abbdb26b'
          """),
  )


def AddRetentionFlag(parser, required=False):
  """Adds flag for retention to the given parser.

  Args:
    parser: The argparse parser.
    required: Whether the flag must be set for running the command, a bool.
  """
  parser.add_argument(
      '--retention',
      metavar='RETENTION',
      required=required,
      type=arg_parsers.Duration(),
      help=textwrap.dedent("""\
          The rention of the backup. At what relative time in the future,
          compared to the creation time of the backup should the backup be
          deleted, i.e. keep backups for 7 days.

          For example, to set retention as 7 days.

          $ {command} --retention=7d
          """),
  )


def AddRecurrenceFlag(parser):
  """Adds flag for recurrence to the given parser.

  Args:
    parser: The argparse parser.
  """
  group = parser.add_group(
      help=textwrap.dedent("""\
          Recurrence settings of a backup schedule.
          """),
      required=True,
  )
  help_text = textwrap.dedent("""\
      The recurrence settings of a backup schedule.

      Currently only daily and weekly backup schedules are supported.

      When a weekly backup schedule is created, day-of-week is needed.

      For example, to create a weekly backup schedule which creates backups on
      Monday.

        $ {command} --recurrence=weekly --day-of-week=MON
  """)
  group.add_argument('--recurrence', type=str, help=help_text, required=True)

  help_text = textwrap.dedent("""\
     The day of week (UTC time zone) of when backups are created.

      The available values are: `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`,`SUN`.
      Values are case insensitive.

      This is required when creating a weekly backup schedule.
  """)
  group.add_argument(
      '--day-of-week',
      choices=arg_parsers.DayOfWeek.DAYS,
      type=arg_parsers.DayOfWeek.Parse,
      help=help_text,
      required=False,
  )


def AddEncryptionConfigGroup(parser, source_type):
  """Adds flags for the database's encryption configuration to the given parser.

  Args:
    parser: The argparse parser.
    source_type: "backup" if a restore; "database" if a clone
  """
  encryption_config = parser.add_argument_group(
      required=False,
      help=textwrap.dedent(string.Template("""\
            The encryption configuration of the new database being created from the $source_type.
            If not specified, the same encryption settings as the $source_type will be used.

            To create a CMEK-enabled database:

              $$ {command} --encryption-type=customer-managed-encryption --kms-key-name=projects/PROJECT_ID/locations/LOCATION_ID/keyRings/KEY_RING_ID/cryptoKeys/CRYPTO_KEY_ID

            To create a Google-default-encrypted database:

              $$ {command} --encryption-type=google-default-encryption

            To create a database using the same encryption settings as the $source_type:

              $$ {command} --encryption-type=use-source-encryption
            """).substitute(source_type=source_type)),
  )
  encryption_config.add_argument(
      '--encryption-type',
      metavar='ENCRYPTION_TYPE',
      type=str,
      required=True,
      choices=[
          'use-source-encryption',
          'customer-managed-encryption',
          'google-default-encryption',
      ],
      help=textwrap.dedent("""\
          The encryption type of the destination database.
          """),
  )
  AddKmsKeyNameFlag(
      encryption_config,
      'This flag must only be specified when encryption-type is'
      ' `customer-managed-encryption`.',
  )


def AddConcurrencyModeFlag(parser):
  """Adds flag for concurrency mode to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--concurrency-mode',
      metavar='CONCURRENCY_MODE',
      type=str,
      choices=['optimistic', 'pessimistic'],
      help=textwrap.dedent("""\
          The concurrency control mode to use for this database.

          When not specified, Firestore will pick a default concurrency mode
          based on the database edition.
          """),
  )


def AddKmsKeyNameFlag(parser, additional_help_text=None):
  """Adds flag for KMS Key Name to the given parser.

  Args:
    parser: The argparse parser.
    additional_help_text: Additional help text to be added to the flag.
  """

  help_text = textwrap.dedent("""\
      The resource ID of a Cloud KMS key. If set, the database created will be a Customer-Managed Encryption Key (CMEK) database encrypted with this key.
      This feature is allowlist only in initial launch.

      Only a key in the same location as this database is allowed to be used for encryption.
      For Firestore's nam5 multi-region, this corresponds to Cloud KMS location us.
      For Firestore's eur3 multi-region, this corresponds to Cloud KMS location europe.
      See https://cloud.google.com/kms/docs/locations.

      This value should be the KMS key resource ID in the format of `projects/{project_id}/locations/{kms_location}/keyRings/{key_ring}/cryptoKeys/{crypto_key}`.
      How to retrieve this resource ID is listed at https://cloud.google.com/kms/docs/getting-resource-ids#getting_the_id_for_a_key_and_version.
    """)
  if additional_help_text:
    help_text = help_text + '\n\n' + additional_help_text

  parser.add_argument(
      '--kms-key-name',
      metavar='KMS_KEY_NAME',
      type=str,
      required=False,
      default=None,
      help=help_text,
  )


def AddDestinationDatabase(parser, action_name, source_type):
  parser.add_argument(
      '--destination-database',
      metavar='DESTINATION_DATABASE',
      type=str,
      required=True,
      help=textwrap.dedent(f"""\
          Destination database to {action_name} to. Destination database will be created in the same location as the source {source_type}.

          This value should be 4-63 characters. Valid characters are /[a-z][0-9]-/
          with first character a letter and the last a letter or a number. Must
          not be UUID-like /[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/.

          Using "(default)" database ID is also allowed.

          For example, to {action_name} to database `testdb`:

          $ {{command}} --destination-database=testdb
          """),
  )


def AddTags(parser, resource_type):
  """Adds the --tags flag to the given parser.

  Args:
    parser: The parser to add the flag to.
    resource_type: The resource type to use in the help text (e.g. 'database').
  """
  parser.add_argument(
      '--tags',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      default=None,
      help=textwrap.dedent(f"""\
          Tags to attach to the destination {resource_type}. Example: --tags=key1=value1,key2=value2

          For example, to attach tags to a {resource_type}:

          $ --tags=key1=value1,key2=value2
          """),
  )


def AddUserCredsIdArg(parser):
  """Adds positional arg for user creds id to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      'user_creds',
      metavar='USER_CREDS',
      type=str,
      help="""
      The user creds to operate on.

      For example, to operate on user creds `creds-name-1`:

        $ {command} creds-name-1
      """,
  )


def _ChoiceType(choices):
  """Adapts calliope_base.ChoiceArgument behavior for use with nested arg_parse.ArgObject.

  Args:
    choices: [str], A list of valid flag values.

  Returns:
    A callable that sanitizes and validates a user provided flag value against
    those choices. This callable matches ChoiceArgument behavior.
  """
  # Validate the choice list with calliope_base.
  _ = calliope_base.ChoiceArgument('unused', choices=choices)

  def Parse(val):
    val_sanitized = calliope_base.SanitizeChoices([val])[0]
    if val_sanitized not in choices:
      raise arg_parsers.ArgumentTypeError(
          f'Invalid choice: {val}. Valid choices are: [{", ".join(choices)}].'
      )
    return val_sanitized

  return Parse


_FIELD_PATH_SPEC = arg_parsers.ArgObject(
    value_type=str,
    help_text='specifies the field path (e.g. address.city).',
)

_ARRAY_CONFIG_SPEC = arg_parsers.ArgObject(
    value_type=_ChoiceType(['contains']),
    help_text=(
        'Specifies the configuration for an array field. The only '
        "valid option is 'contains'. Exactly one of 'order', "
        "'array-config', or 'vector-config' must be specified."
    ),
)

_ORDER_SPEC = arg_parsers.ArgObject(
    value_type=_ChoiceType(['ascending', 'descending', 'order-unspecified']),
    help_text=(
        "Specifies the order. Valid options are 'ascending', "
        "'descending'. Exactly one of 'order', 'array-config', or "
        "'vector-config' must be specified."
    ),
)

_VECTOR_CONFIG_SPEC = arg_parsers.ArgObject(
    help_text=(
        'Specifies the configuration for a vector field. Exactly one of '
        "'order', 'array-config', or 'vector-config' must be specified."
    ),
    spec={
        FIELD_CONFIG_DIMENSION: arg_parsers.ArgObject(
            value_type=int,
        ),
        FIELD_CONFIG_FLAT: arg_parsers.ArgObject(
            spec={},
        ),
    },
    required_keys=(FIELD_CONFIG_DIMENSION,),
)

_SEARCH_CONFIG_SPEC = arg_parsers.ArgObject(
    help_text=textwrap.dedent("""\
        Specifies the configuration for a search field. An index definition
        must contain either only 'search-config' fields or only non
        'search-config' fields.

        The following shorthand aliases are supported instead of a full 'search-config':
          * `TEXT_TOKENIZED_MATCH_GLOBALLY`: Tokenized text search with global matching.
          * `GEO_POINT`: Geo search.

        Examples:

        With alias:

            --field-config=field-path=title,search-config=TEXT_TOKENIZED_MATCH_GLOBALLY

        Text search:

            --field-config=field-path=title,search-config='{"text-spec": {"index-specs": [{"index-type": "tokenized", "match-type": "match-globally"}]}}'

        Geo search:

            --field-config=field-path=location,search-config='{"geo-spec": {"geo-json-indexing-disabled": true}}'

        With file:

            --field-config=field-path=text,search-config='/path/to/configs/search-config.json'

        For complex configurations, it is recommended to use a file.
        """),
    spec={
        FIELD_CONFIG_TEXT_SPEC: arg_parsers.ArgObject(
            help_text=(
                'Optional. The specification for building a text search '
                'index for a field.'
            ),
            spec={
                FIELD_CONFIG_INDEX_SPECS: arg_parsers.ArgObject(
                    help_text=(
                        'Optional. Array of specifications for how the '
                        'field should be indexed.'
                    ),
                    repeated=True,
                    spec={
                        FIELD_CONFIG_INDEX_TYPE: arg_parsers.ArgObject(
                            value_type=_ChoiceType(['tokenized']),
                            help_text=textwrap.dedent("""\
                                Required. How to index the text field value. Valid options are:
                                  * `tokenized`: Field values are tokenized.
                                """),
                        ),
                        FIELD_CONFIG_MATCH_TYPE: arg_parsers.ArgObject(
                            value_type=_ChoiceType(['match-globally']),
                            help_text=textwrap.dedent("""\
                                Required. How to match the text field value. Valid options are:
                                  * `match-globally`: Match on any indexed field.
                                """),
                        ),
                    },
                ),
            },
        ),
        FIELD_CONFIG_GEO_SPEC: arg_parsers.ArgObject(
            help_text=(
                'Optional. The specification for building a geo search '
                'index for a field.'
            ),
            spec={
                FIELD_CONFIG_GEO_JSON_INDEXING_DISABLED: arg_parsers.ArgObject(
                    value_type=bool,
                    help_text=(
                        'Optional. Disables geoJSON indexing for the '
                        'field. By default, geoJSON points are indexed.'
                    ),
                ),
            },
        ),
    },
)


_SEARCH_CONFIG_ALIASES = {
    'TEXT_TOKENIZED_MATCH_GLOBALLY': json.dumps({
        'text-spec': {
            'index-specs': [{
                'index-type': 'tokenized',
                'match-type': 'match-globally',
            }]
        }
    }),
    'GEO_POINT': json.dumps({'geo-spec': {}}),
}


# Inheriting from DefaultArgTypeWrapper allows us to support aliases without
# sacrificing the generated help text.
class _SearchConfigTypeWrapper(arg_parsers_usage_text.DefaultArgTypeWrapper):
  """Parses search config, expanding aliases if present."""

  def __init__(self):
    # Pass the search config spec to the parent class so it gets saved to
    # self.arg_type. This allows Calliope to extract the usage help text.
    super().__init__(_SEARCH_CONFIG_SPEC)

  def __call__(self, val):
    if isinstance(val, str):
      val_upper = val.upper()
      if val_upper in _SEARCH_CONFIG_ALIASES:
        val = _SEARCH_CONFIG_ALIASES[val_upper]

    return self.arg_type(val)


def AddFieldConfigFlag(parser, is_search_released):
  """Adds the repeated --field-config flag to the given parser.

  Args:
    parser: The argparse parser.
    is_search_released: Whether search is released in gcloud.
  """
  field_config_spec = {
      FIELD_CONFIG_FIELD_PATH: _FIELD_PATH_SPEC,
      FIELD_CONFIG_ARRAY_CONFIG: _ARRAY_CONFIG_SPEC,
      FIELD_CONFIG_ORDER: _ORDER_SPEC,
      FIELD_CONFIG_VECTOR_CONFIG: _VECTOR_CONFIG_SPEC,
  } | (
      {FIELD_CONFIG_SEARCH_CONFIG: _SearchConfigTypeWrapper()}
      if is_search_released
      else {}
  )

  help_text = 'Configuration for an index field.'

  parser.add_argument(
      '--field-config',
      type=arg_parsers.ArgObject(
          help_text=help_text,
          spec=field_config_spec,
          required_keys=(FIELD_CONFIG_FIELD_PATH,),
          enable_shorthand=True,
          disable_key_description=False,
          repeated=True,
      ),
      required=True,
      action=FlattenedAppendAction,
      help=help_text,
  )


def AddQueryScopeFlag(parser):
  """Adds the --query-scope flag to the given parser.

  Args:
    parser: The argparse parser.
  """
  calliope_base.ChoiceArgument(
      '--query-scope',
      choices=['collection', 'collection-group', 'collection-recursive'],
      default='collection',
      help_str='Query scope the index applies to.',
  ).AddToParser(parser)


def AddApiScopeFlag(parser):
  """Adds the --api-scope flag to the given parser.

  Args:
    parser: The argparse parser.
  """
  calliope_base.ChoiceArgument(
      '--api-scope',
      choices=['any-api', 'datastore-mode-api', 'mongodb-compatible-api'],
      default='any-api',
      help_str='Api scope the index applies to.',
  ).AddToParser(parser)


def AddDensityFlag(parser):
  """Adds the --density flag to the given parser.

  Args:
    parser: The argparse parser.
  """
  calliope_base.ChoiceArgument(
      '--density',
      choices=['dense', 'density-unspecified', 'sparse-all', 'sparse-any'],
      default=None,
      help_str='Density of the index.',
  ).AddToParser(parser)


def AddMultikeyFlag(parser):
  """Adds the --multikey flag to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--multikey',
      action='store_true',
      help=textwrap.dedent("""\
          Optional. Whether the index is multikey. By default, the index
          is not multikey. For non-multikey indexes, none of the paths in the
          index definition reach or traverse an array, except via an explicit
          array index. For multikey indexes, at most one of the paths in the index
          definition reach or traverse an array, except via an explicit array
          index. Violations will result in errors. Note this field only applies to
          index with 'mongodb-compatible-api' ApiScope.
      """),
  )


def AddUniqueFlag(parser):
  """Adds the --unique flag to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--unique',
      action='store_true',
      help=textwrap.dedent("""\
          Optional. Whether it is an unique index. Unique index ensures all values for
          the indexed field(s) are unique across documents.
      """),
  )


_SEARCH_INDEX_OPTIONS_SPEC = arg_parsers.ArgObject(
    help_text='Optional. Configuration options for search indexes.',
    spec={
        SEARCH_INDEX_OPTIONS_TEXT_LANGUAGE: arg_parsers.ArgObject(
            value_type=str,
            help_text=(
                'Optional. The language to use for text search '
                'indexes. Used as the default language if not '
                'overridden at the document level by specifying the '
                "'text-language-override-field-path'. The language is "
                'specified as a BCP 47 language code. For indexes '
                "with 'mongodb-compatible-api' ApiScope: If "
                'unspecified, the default language is English. For '
                "indexes with 'any-api' ApiScope: If unspecified, "
                'the default behavior is autodetect.'
            ),
        ),
        SEARCH_INDEX_OPTIONS_TEXT_LANGUAGE_OVERRIDE_FIELD_PATH: arg_parsers.ArgObject(
            value_type=str,
            help_text=(
                'Optional. The field in the document that specifies'
                ' which language to use for that specific document. If'
                ' unspecified, the language is taken from the'
                " 'language' document field if it exists or from"
                " 'text-language' if it does not."
            ),
        ),
    },
    disable_key_description=False,
)


def AddSearchIndexOptionsFlag(parser, is_search_released):
  """Adds the --search-index-options flag to the given parser.

  Args:
    parser: The argparse parser.
    is_search_released: Whether search is released in gcloud.
  """
  if is_search_released:
    search_index_help = 'Optional. Configuration options for search indexes.'
    parser.add_argument(
        '--search-index-options',
        type=_SEARCH_INDEX_OPTIONS_SPEC,
        required=False,
        help=search_index_help,
    )
