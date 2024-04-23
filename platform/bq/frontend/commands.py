#!/usr/bin/env python
"""All the BigQuery CLI commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import json
import os
import sys
import textwrap
import time
from typing import List, Optional, Tuple


from absl import app
from absl import flags

import termcolor

import bigquery_client
import bq_flags
import bq_utils
from clients import bigquery_client as bigquery_client_core
from clients import client_dataset
from clients import utils as bq_client_utils
from frontend import bigquery_command
from frontend import bq_cached_client
from frontend import utils as frontend_utils
from utils import bq_error
from utils import bq_id_utils
from utils import bq_logging
from utils import bq_processor_utils
from pyglib import stringutil

FLAGS = flags.FLAGS

# These aren't relevant for user-facing docstrings:
# pylint: disable=g-doc-return-or-yield
# pylint: disable=g-doc-args


class MakeExternalTableDefinition(bigquery_command.BigqueryCmd):
  usage = """mkdef <source_uri> [<schema>]"""

  def __init__(self, name, fv):
    super(MakeExternalTableDefinition, self).__init__(name, fv)

    flags.DEFINE_boolean(
        'autodetect',
        None,
        'Should schema and format options be autodetected.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'ignore_unknown_values',
        None,
        'Ignore any values in a row that are not present in the schema.',
        short_name='i',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'hive_partitioning_mode',
        None,
        'Enables hive partitioning.  AUTO indicates to perform '
        'automatic type inference.  STRINGS indicates to treat all hive '
        'partition keys as STRING typed.  No other values are accepted',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'hive_partitioning_source_uri_prefix',
        None,
        'Prefix after which hive partition '
        'encoding begins.  For URIs like gs://bucket/path/key1=value/file, '
        'the value should be gs://bucket/path.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'require_hive_partition_filter',
        None,
        'Whether queries against a table are required to '
        'include a hive partition key in a query predicate.',
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'source_format',
        'CSV',
        [
            'CSV',
            'GOOGLE_SHEETS',
            'NEWLINE_DELIMITED_JSON',
            'DATASTORE_BACKUP',
            'DELTA_LAKE',
            'ORC',
            'PARQUET',
            'AVRO',
            'ICEBERG',
        ],
        'Format of source data. Options include:'
        '\n CSV'
        '\n GOOGLE_SHEETS'
        '\n NEWLINE_DELIMITED_JSON'
        '\n DATASTORE_BACKUP'
        '\n DELTA_LAKE'
        '\n ORC'
        '\n PARQUET'
        '\n ICEBERG'
        '\n AVRO',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'connection_id',
        None,
        'The connection specifying the credentials to be used to read external '
        'storage, such as Azure Blob, Cloud Storage, or S3. The connection_id '
        'can have the form "<project_id>.<location_id>.<connection_id>" or '
        '"projects/<project_id>/locations/<location_id>/connections/'
        '<connection_id>".',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'use_avro_logical_types',
        True,
        'If sourceFormat is set to "AVRO", indicates whether to enable '
        'interpreting logical types into their corresponding types '
        '(ie. TIMESTAMP), instead of only using their raw types (ie. INTEGER).',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'parquet_enum_as_string',
        False,
        'Infer Parquet ENUM logical type as STRING '
        '(instead of BYTES by default).',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'parquet_enable_list_inference',
        False,
        frontend_utils.PARQUET_LIST_INFERENCE_DESCRIPTION,
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'metadata_cache_mode',
        None,
        ['AUTOMATIC', 'MANUAL'],
        'Enables metadata cache for an external table with a connection. '
        'Specify AUTOMATIC to automatically refresh the cached metadata. '
        'Specify MANUAL to stop the automatic refresh.',
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'object_metadata',
        None,
        ['DIRECTORY', 'SIMPLE'],
        'Object Metadata Type. Options include:\n SIMPLE.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'preserve_ascii_control_characters',
        False,
        'Whether to preserve embedded Ascii Control characters in CSV External '
        'table ',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'reference_file_schema_uri',
        None,
        'provide a referencing file with the expected table schema, currently '
        'enabled for the formats: AVRO, PARQUET, ORC.',
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'encoding',
        None,
        ['UTF-8', 'ISO-8859-1', 'UTF-16BE', 'UTF-16LE', 'UTF-32BE', 'UTF-32LE'],
        'The character encoding used by the input file.  Options include:'
        '\n ISO-8859-1 (also known as Latin-1)'
        '\n UTF-8'
        '\n UTF-16BE (UTF-16 BigEndian)'
        '\n UTF-16LE (UTF-16 LittleEndian)'
        '\n UTF-32BE (UTF-32 BigEndian)'
        '\n UTF-32LE (UTF-16 LittleEndian)',
        short_name='E',
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'file_set_spec_type',
        None,
        ['FILE_SYSTEM_MATCH', 'NEW_LINE_DELIMITED_MANIFEST'],
        '[Experimental] Specifies how to discover files given source URIs. '
        'Options include: '
        '\n FILE_SYSTEM_MATCH: expand source URIs by listing files from the '
        'underlying object store. This is the default behavior.'
        '\n NEW_LINE_DELIMITED_MANIFEST: indicate the source URIs provided are '
        'new line delimited manifest files, where each line contains a URI '
        'with no wild-card.',
        flag_values=fv,
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, source_uris, schema=None):
    """Emits a definition in JSON for an external table, such as GCS.

    The output of this command can be redirected to a file and used for the
    external_table_definition flag with the "bq query" and "bq mk" commands.
    It produces a definition with the most commonly used values for options.
    You can modify the output to override option values.

    The <source_uris> argument is a comma-separated list of URIs indicating
    the data referenced by this external table.

    The <schema> argument should be either the name of a JSON file or a text
    schema.

    In the case that the schema is provided in text form, it should be a
    comma-separated list of entries of the form name[:type], where type will
    default to string if not specified.

    In the case that <schema> is a filename, it should be a JSON file
    containing a single array, each entry of which should be an object with
    properties 'name', 'type', and (optionally) 'mode'. For more detail:
    https://cloud.google.com/bigquery/docs/schemas#specifying_a_json_schema_file

    Note: the case of a single-entry schema with no type specified is
    ambiguous; one can use name:string to force interpretation as a
    text schema.

    Usage:
      mkdef <source_uris> [<schema>]

    Examples:
      bq mkdef 'gs://bucket/file.csv' field1:integer,field2:string

    Arguments:
      source_uris: Comma-separated list of URIs.
      schema: Either a text schema or JSON file, as above.
    """
    # pylint: disable=line-too-long
    json.dump(
        frontend_utils.CreateExternalTableDefinition(
            source_format=self.source_format,
            source_uris=source_uris,
            schema=schema,
            autodetect=self.autodetect,
            connection_id=self.connection_id,
            ignore_unknown_values=self.ignore_unknown_values,
            hive_partitioning_mode=self.hive_partitioning_mode,
            hive_partitioning_source_uri_prefix=self.hive_partitioning_source_uri_prefix,
            require_hive_partition_filter=self.require_hive_partition_filter,
            use_avro_logical_types=self.use_avro_logical_types,
            parquet_enum_as_string=self.parquet_enum_as_string,
            parquet_enable_list_inference=self.parquet_enable_list_inference,
            metadata_cache_mode=self.metadata_cache_mode,
            object_metadata=self.object_metadata,
            preserve_ascii_control_characters=self.preserve_ascii_control_characters,
            reference_file_schema_uri=self.reference_file_schema_uri,
            encoding=self.encoding,
            file_set_spec_type=self.file_set_spec_type,
        ),
        sys.stdout,
        sort_keys=True,
        indent=2,
    )
    # pylint: enable=line-too-long


class Extract(bigquery_command.BigqueryCmd):
  usage = """extract <source_table> <destination_uris>"""

  def __init__(self, name, fv):
    super(Extract, self).__init__(name, fv)
    flags.DEFINE_string(
        'field_delimiter',
        None,
        'The character that indicates the boundary between columns in the '
        'output file. "\\t" and "tab" are accepted names for tab. '
        'Not applicable when extracting models.',
        short_name='F',
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'destination_format',
        None,
        [
            'CSV',
            'NEWLINE_DELIMITED_JSON',
            'AVRO',
            'PARQUET',
            'ML_TF_SAVED_MODEL',
            'ML_XGBOOST_BOOSTER',
        ],
        'The extracted file format. Format CSV, NEWLINE_DELIMITED_JSON, '
        'PARQUET and AVRO are applicable for extracting tables. '
        'Formats ML_TF_SAVED_MODEL and ML_XGBOOST_BOOSTER are applicable for '
        'extracting models. The default value for tables is CSV. Tables with '
        'nested or repeated fields cannot be exported as CSV. The default '
        'value for models is ML_TF_SAVED_MODEL.',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'trial_id',
        None,
        '1-based ID of the trial to be exported from a hyperparameter tuning '
        'model. The default_trial_id will be exported if not specified. This '
        'does not apply for models not trained with hyperparameter tuning.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'add_serving_default_signature',
        None,
        'Whether to add serving_default signature for export BigQuery ML '
        'trained tf based models.',
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'compression',
        'NONE',
        ['GZIP', 'DEFLATE', 'SNAPPY', 'ZSTD', 'NONE'],
        'The compression type to use for exported files. Possible values '
        'include GZIP, DEFLATE, SNAPPY, ZSTD, and NONE. The default value is '
        'None. Not applicable when extracting models.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'print_header',
        None,
        'Whether to print header rows for formats that '
        'have headers. Prints headers by default.'
        'Not applicable when extracting models.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'use_avro_logical_types',
        None,
        'If destinationFormat is set to "AVRO", this flag indicates whether to '
        'enable extracting applicable column types (such as TIMESTAMP) to '
        'their corresponding AVRO logical types (timestamp-micros), instead of '
        'only using their raw types (avro-long). '
        'Not applicable when extracting models.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'model',
        False,
        'Extract model with this model ID.',
        short_name='m',
        flag_values=fv,
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier, destination_uris):
    """Perform an extract operation of source into destination_uris.

    Usage:
      extract <source_table> <destination_uris>

    Use -m option to extract a source_model.

    Examples:
      bq extract ds.table gs://mybucket/table.csv
      bq extract -m ds.model gs://mybucket/model

    Arguments:
      source_table: Source table to extract.
      source_model: Source model to extract.
      destination_uris: One or more Google Cloud Storage URIs, separated by
        commas.
    """
    client = bq_cached_client.Client.Get()
    kwds = {
        'job_id': frontend_utils.GetJobIdFromFlags(),
    }
    if FLAGS.location:
      kwds['location'] = FLAGS.location

    if self.m:
      reference = client.GetModelReference(identifier)
    else:
      reference = client.GetTableReference(identifier)
    job = client.Extract(
        reference,
        destination_uris,
        print_header=self.print_header,
        field_delimiter=frontend_utils.NormalizeFieldDelimiter(
            self.field_delimiter
        ),
        destination_format=self.destination_format,
        trial_id=self.trial_id,
        add_serving_default_signature=self.add_serving_default_signature,
        compression=self.compression,
        use_avro_logical_types=self.use_avro_logical_types,
        **kwds,
    )
    if FLAGS.sync:
      # If we are here, the job succeeded, but print warnings if any.
      frontend_utils.PrintJobMessages(bq_client_utils.FormatJobInfo(job))
    else:
      self.PrintJobStartInfo(job)


class Partition(bigquery_command.BigqueryCmd):  # pylint: disable=missing-docstring
  usage = """partition source_prefix destination_table"""

  def __init__(self, name, fv):
    super(Partition, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'no_clobber',
        False,
        'Do not overwrite an existing partition.',
        short_name='n',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'time_partitioning_type',
        'DAY',
        'Enables time based partitioning on the table and set the type. The '
        'default value is DAY, which will generate one partition per day. '
        'Other supported values are HOUR, MONTH, and YEAR.',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'time_partitioning_expiration',
        None,
        'Enables time based partitioning on the table and sets the number of '
        'seconds for which to keep the storage for the partitions in the table.'
        ' The storage in a partition will have an expiration time of its '
        'partition time plus this value.',
        flag_values=fv,
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, source_prefix, destination_table):
    """Copies source tables into partitioned tables.

    Usage:
    bq partition <source_table_prefix> <destination_partitioned_table>

    Copies tables of the format <source_table_prefix><time_unit_suffix> to a
    destination partitioned table, with the <time_unit_suffix> of the source
    tables becoming the partition ID of the destination table partitions. The
    suffix is <YYYYmmdd> by default, <YYYY> if the time_partitioning_type flag
    is set to YEAR, <YYYYmm> if set to MONTH, and <YYYYmmddHH> if set to HOUR.

    If the destination table does not exist, one will be created with
    a schema and that matches the last table that matches the supplied
    prefix.

    Examples:
      bq partition dataset1.sharded_ dataset2.partitioned_table
    """

    client = bq_cached_client.Client.Get()
    formatter = frontend_utils.GetFormatterFromFlags()

    source_table_prefix = client.GetReference(source_prefix)
    bq_id_utils.typecheck(
        source_table_prefix,
        bq_id_utils.ApiClientHelper.TableReference,
        'Cannot determine table associated with "%s"' % (source_prefix,),
        is_usage_error=True,
    )
    destination_table = client.GetReference(destination_table)
    bq_id_utils.typecheck(
        destination_table,
        bq_id_utils.ApiClientHelper.TableReference,
        'Cannot determine table associated with "%s"' % (destination_table,),
        is_usage_error=True,
    )

    source_dataset = source_table_prefix.GetDatasetReference()
    source_id_prefix = stringutil.ensure_str(source_table_prefix.tableId)
    source_id_len = len(source_id_prefix)

    job_id_prefix = frontend_utils.GetJobIdFromFlags()
    if isinstance(job_id_prefix, bq_client_utils.JobIdGenerator):
      job_id_prefix = job_id_prefix.Generate(
          [source_table_prefix, destination_table]
      )

    destination_dataset = destination_table.GetDatasetReference()

    bq_client_utils.ConfigureFormatter(
        formatter, bq_id_utils.ApiClientHelper.TableReference
    )
    results = map(
        client.FormatTableInfo,
        client.ListTables(source_dataset, max_results=1000 * 1000),
    )

    partition_ids = []
    representative_table = None

    time_format = '%Y%m%d'  # default to format for DAY
    if self.time_partitioning_type == 'HOUR':
      time_format = '%Y%m%d%H'
    elif self.time_partitioning_type == 'MONTH':
      time_format = '%Y%m'
    elif self.time_partitioning_type == 'YEAR':
      time_format = '%Y'

    for result in results:
      table_id = stringutil.ensure_str(result['tableId'])
      if table_id.startswith(source_id_prefix):
        suffix = table_id[source_id_len:]
        try:
          partition_id = datetime.datetime.strptime(suffix, time_format)
          partition_ids.append(partition_id.strftime(time_format))
          representative_table = result
        except ValueError:
          pass

    if not representative_table:
      print('No matching source tables found')
      return

    print(
        'Copying %d source partitions to %s'
        % (len(partition_ids), destination_table)
    )

    # Check to see if we need to create the destination table.
    if not client.TableExists(destination_table):
      source_table_id = representative_table['tableId']
      source_table_ref = source_dataset.GetTableReference(source_table_id)
      source_table_schema = client.GetTableSchema(source_table_ref)
      # Get fields in the schema.
      if source_table_schema:
        source_table_schema = source_table_schema['fields']

      time_partitioning = frontend_utils.ParseTimePartitioning(
          self.time_partitioning_type, self.time_partitioning_expiration
      )

      print(
          'Creating table: %s with schema from %s and partition spec %s'
          % (destination_table, source_table_ref, time_partitioning)
      )

      client.CreateTable(
          destination_table,
          schema=source_table_schema,
          time_partitioning=time_partitioning,
      )
      print('%s successfully created.' % (destination_table,))

    for partition_id in partition_ids:
      destination_table_id = '%s$%s' % (destination_table.tableId, partition_id)
      source_table_id = '%s%s' % (source_id_prefix, partition_id)
      current_job_id = '%s%s' % (job_id_prefix, partition_id)

      source_table = source_dataset.GetTableReference(source_table_id)
      destination_partition = destination_dataset.GetTableReference(
          destination_table_id
      )

      avoid_copy = False
      if self.no_clobber:
        maybe_destination_partition = client.TableExists(destination_partition)
        avoid_copy = (
            maybe_destination_partition
            and int(maybe_destination_partition['numBytes']) > 0
        )

      if avoid_copy:
        print("Table '%s' already exists, skipping" % (destination_partition,))
      else:
        print('Copying %s to %s' % (source_table, destination_partition))
        kwds = {
            'write_disposition': 'WRITE_TRUNCATE',
            'job_id': current_job_id,
        }
        if FLAGS.location:
          kwds['location'] = FLAGS.location
        job = client.CopyTable([source_table], destination_partition, **kwds)
        if not FLAGS.sync:
          self.PrintJobStartInfo(job)
        else:
          print(
              'Successfully copied %s to %s'
              % (source_table, destination_partition)
          )


class ListCmd(bigquery_command.BigqueryCmd):  # pylint: disable=missing-docstring
  usage = """ls [(-j|-p|-d)] [-a] [-n <number>] [<identifier>]"""

  def __init__(self, name, fv):
    super(ListCmd, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'all',
        None,
        'Show all results. For jobs, will show jobs from all users. For '
        'datasets, will list hidden datasets.'
        'For transfer configs and runs, '
        'this flag is redundant and not necessary.'
        '',
        short_name='a',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'all_jobs', None, 'DEPRECATED. Use --all instead', flag_values=fv
    )
    flags.DEFINE_boolean(
        'jobs',
        False,
        'Show jobs described by this identifier.',
        short_name='j',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'max_results',
        None,
        'Maximum number to list.',
        short_name='n',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'min_creation_time',
        None,
        'Timestamp in milliseconds. Return jobs created after this timestamp.',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'max_creation_time',
        None,
        'Timestamp in milliseconds. Return jobs created before this timestamp.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'projects', False, 'Show all projects.', short_name='p', flag_values=fv
    )
    flags.DEFINE_boolean(
        'datasets',
        False,
        'Show datasets described by this identifier.',
        short_name='d',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'models', False, 'Show all models.', short_name='m', flag_values=fv
    )
    flags.DEFINE_boolean(
        'routines', False, 'Show all routines.', flag_values=fv
    )
    flags.DEFINE_boolean(
        'row_access_policies',
        False,
        'Show all row access policies.',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'transfer_location',
        None,
        'Location for list transfer config (e.g., "eu" or "us").',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'transfer_config',
        False,
        'Show transfer configurations described by this identifier. '
        'This requires setting --transfer_location.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'transfer_run', False, 'List the transfer runs.', flag_values=fv
    )
    flags.DEFINE_string(
        'run_attempt',
        'LATEST',
        'For transfer run, respresents which runs should be '
        'pulled. See https://cloud.google.com/bigquery/docs/reference/'
        'datatransfer/rest/v1/projects.transferConfigs.runs/list#RunAttempt '
        'for details',
        flag_values=fv,
    )
    flags.DEFINE_bool(
        'transfer_log',
        False,
        'List messages under the run specified',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'message_type',
        None,
        'usage:- messageTypes:INFO '
        'For transferlog, represents which messages should '
        'be listed. See '
        'https://cloud.google.com/bigquery/docs/reference'
        '/datatransfer/rest/v1/projects.transferConfigs'
        '.runs.transferLogs#MessageSeverity '
        'for details.',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'page_token',
        None,
        'Start listing from this page token.',
        short_name='k',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'print_last_token',
        False,
        'If true, also print the next page token for the jobs list.',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'filter',
        None,
        'Filters resources based on the filter expression.'
        '\nFor datasets, use a space-separated list of label keys and values '
        'in the form "labels.key:value". Datasets must match '
        'all provided filter expressions. See '
        'https://cloud.google.com/bigquery/docs/filtering-labels'
        '#filtering_datasets_using_labels '
        'for details'
        '\nFor transfer configurations, the filter expression, '
        'in the form "dataSourceIds:value(s)", will show '
        'transfer configurations with '
        ' the specified dataSourceId. '
        '\nFor transfer runs, the filter expression, '
        'in the form "states:VALUE(s)", will show '
        'transfer runs with the specified states. See '
        'https://cloud.google.com/bigquery/docs/reference/datatransfer/rest/v1/'
        'TransferState '
        'for details.'
        '\nFor jobs, filtering is currently not supported.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'reservation',
        None,
        'List all reservations for the given project and location.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'capacity_commitment',
        None,
        'Lists all capacity commitments (e.g. slots) for the given project and '
        'location.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'reservation_assignment',
        None,
        'List all reservation assignments for given project/location',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'parent_job_id',
        None,
        'Only show jobs which are children of this parent job; if omitted, '
        'shows all jobs which have no parent.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'connection',
        None,
        'List all connections for given project/location',
        flag_values=fv,
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier=''):
    """List the objects contained in the named collection.

    List the objects in the named project or dataset. A trailing : or
    . can be used to signify a project or dataset.
     * With -j, show the jobs in the named project.
     * With -p, show all projects.

    Examples:
      bq ls
      bq ls -j proj
      bq ls -p -n 1000
      bq ls mydataset
      bq ls -a
      bq ls -m mydataset
      bq ls --routines mydataset
      bq ls --row_access_policies mytable (requires whitelisting)
      bq ls --filter labels.color:red
      bq ls --filter 'labels.color:red labels.size:*'
      bq ls --transfer_config --transfer_location='us'
          --filter='dataSourceIds:play,adwords'
      bq ls --transfer_run --filter='states:SUCCESSED,PENDING'
          --run_attempt='LATEST' projects/p/locations/l/transferConfigs/c
      bq ls --transfer_log --message_type='messageTypes:INFO,ERROR'
          projects/p/locations/l/transferConfigs/c/runs/r
      bq ls --capacity_commitment --project_id=proj --location='us'
      bq ls --reservation --project_id=proj --location='us'
      bq ls --reservation_assignment --project_id=proj --location='us'
      bq ls --reservation_assignment --project_id=proj --location='us'
          <reservation_id>
      bq ls --connection --project_id=proj --location=us
    """

    # pylint: disable=g-doc-exception
    if frontend_utils.ValidateAtMostOneSelected(self.j, self.p, self.d):
      raise app.UsageError('Cannot specify more than one of -j, -p, or -d.')
    if self.p and identifier:
      raise app.UsageError('Cannot specify an identifier with -p')

    # Copy deprecated flag specifying 'all' to current one.
    if self.all_jobs is not None:
      self.a = self.all_jobs

    client = bq_cached_client.Client.Get()
    if identifier:
      reference = client.GetReference(identifier)
    else:
      try:
        reference = client.GetReference(identifier)
      except bq_error.BigqueryError:
        # We want to let through the case of no identifier, which
        # will fall through to the second case below.
        reference = None

    if self.row_access_policies:
      bq_id_utils.typecheck(
          reference,
          bq_id_utils.ApiClientHelper.TableReference,
          (
              'Invalid identifier "%s" for ls, cannot list row access '
              'policies on object of type %s'
          )
          % (identifier, type(reference).__name__),
          is_usage_error=True,
      )
    else:
      # If we got a TableReference, we might be able to make sense
      # of it as a DatasetReference, as in 'ls foo' with dataset_id
      # set.
      if isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
        try:
          reference = client.GetDatasetReference(identifier)
        except bq_error.BigqueryError:
          pass
      bq_id_utils.typecheck(
          reference,
          (
              type(None),
              bq_id_utils.ApiClientHelper.ProjectReference,
              bq_id_utils.ApiClientHelper.DatasetReference,
          ),
          (
              'Invalid identifier "%s" for ls, cannot call list on object '
              'of type %s'
          )
          % (identifier, type(reference).__name__),
          is_usage_error=True,
      )

    if self.d and isinstance(
        reference, bq_id_utils.ApiClientHelper.DatasetReference
    ):
      reference = reference.GetProjectReference()

    page_token = self.k
    results = None
    object_type = None
    if self.j:
      object_type = bq_id_utils.ApiClientHelper.JobReference
      reference = client.GetProjectReference(identifier)
      bq_id_utils.typecheck(
          reference,
          bq_id_utils.ApiClientHelper.ProjectReference,
          'Cannot determine job(s) associated with "%s"' % (identifier,),
          is_usage_error=True,
      )
      if self.print_last_token:
        results = client.ListJobsAndToken(
            reference=reference,
            max_results=self.max_results,
            all_users=self.a,
            min_creation_time=self.min_creation_time,
            max_creation_time=self.max_creation_time,
            page_token=page_token,
            parent_job_id=self.parent_job_id,
        )
        assert object_type is not None
        frontend_utils.PrintObjectsArrayWithToken(results, object_type)
        return
      results = client.ListJobs(
          reference=reference,
          max_results=self.max_results,
          all_users=self.a,
          min_creation_time=self.min_creation_time,
          max_creation_time=self.max_creation_time,
          page_token=page_token,
          parent_job_id=self.parent_job_id,
      )
    elif self.m:
      object_type = bq_id_utils.ApiClientHelper.ModelReference
      reference = client.GetDatasetReference(identifier)
      response = client.ListModels(
          reference=reference,
          max_results=self.max_results,
          page_token=page_token,
      )
      if 'models' in response:
        results = response['models']
      if 'nextPageToken' in response:
        frontend_utils.PrintPageToken(response)
    elif self.routines:
      object_type = bq_id_utils.ApiClientHelper.RoutineReference
      reference = client.GetDatasetReference(identifier)
      response = client.ListRoutines(
          reference=reference,
          max_results=self.max_results,
          page_token=page_token,
          filter_expression=self.filter,
      )
      if 'routines' in response:
        results = response['routines']
      if 'nextPageToken' in response:
        frontend_utils.PrintPageToken(response)
    elif self.reservation_assignment:
      try:
        if FLAGS.api_version == 'v1beta1':
          object_type = (
              bq_id_utils.ApiClientHelper.BetaReservationAssignmentReference
          )
        else:
          object_type = (
              bq_id_utils.ApiClientHelper.ReservationAssignmentReference
          )
        reference = client.GetReservationReference(
            identifier=identifier if identifier else '-',
            default_location=FLAGS.location,
            default_reservation_id=' ',
        )
        response = client.ListReservationAssignments(
            reference, self.max_results, self.page_token
        )
        if 'assignments' in response:
          results = response['assignments']
        else:
          print('No reservation assignments found.')
        if 'nextPageToken' in response:
          frontend_utils.PrintPageToken(response)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list reservation assignments '%s': %s" % (identifier, e)
        )
    elif self.capacity_commitment:
      try:
        object_type = bq_id_utils.ApiClientHelper.CapacityCommitmentReference
        reference = client.GetCapacityCommitmentReference(
            identifier=identifier,
            default_location=FLAGS.location,
            default_capacity_commitment_id=' ',
        )
        response = client.ListCapacityCommitments(
            reference, self.max_results, self.page_token
        )
        if 'capacityCommitments' in response:
          results = response['capacityCommitments']
        else:
          print('No capacity commitments found.')
        if 'nextPageToken' in response:
          frontend_utils.PrintPageToken(response)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list capacity commitments '%s': %s" % (identifier, e)
        )
    elif self.reservation:
      response = None
      if FLAGS.api_version == 'v1beta1':
        object_type = bq_id_utils.ApiClientHelper.BetaReservationReference
      else:
        object_type = bq_id_utils.ApiClientHelper.ReservationReference
      reference = client.GetReservationReference(
          identifier=identifier,
          default_location=FLAGS.location,
          default_reservation_id=' ',
      )
      try:
        if True:
          response = client.ListBiReservations(reference)
          results = [response]
        if response and 'size' in response:
          size_in_bytes = int(response['size'])
          size_in_gbytes = size_in_bytes / (1024 * 1024 * 1024)
          print('BI Engine reservation: %sGB' % size_in_gbytes)
      except bq_error.BigqueryNotFoundError:
        pass
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list BI reservations '%s': %s" % (identifier, e)
        )

      try:
        if True:
          response = client.ListReservations(
              reference=reference,
              page_size=self.max_results,
              page_token=self.page_token,
          )
          results = (
              response['reservations'] if 'reservations' in response else []
          )
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list reservations '%s': %s" % (identifier, e)
        )
      if not results:
        print('No reservations found.')
      if response and 'nextPageToken' in response:
        frontend_utils.PrintPageToken(response)
    elif self.transfer_config:
      object_type = bq_id_utils.ApiClientHelper.TransferConfigReference
      reference = client.GetProjectReference(
          bq_id_utils.FormatProjectIdentifier(client, identifier)
      )
      bq_id_utils.typecheck(
          reference,
          bq_id_utils.ApiClientHelper.ProjectReference,
          'Cannot determine transfer configuration(s) associated with "%s"'
          % (identifier,),
          is_usage_error=True,
      )

      if self.transfer_location is None:
        raise app.UsageError(
            'Need to specify transfer_location for list transfer configs.'
        )

      # transfer_configs tuple contains transfer configs at index 0 and
      # next page token at index 1 if there is one.
      transfer_configs = client.ListTransferConfigs(
          reference=reference,
          location=self.transfer_location,
          page_size=self.max_results,
          page_token=page_token,
          data_source_ids=self.filter,
      )
      # If the max_results flag is set and the length of transfer_configs is 2
      # then it also contains the next_page_token.
      if self.max_results and len(transfer_configs) == 2:
        page_token = dict(nextPageToken=transfer_configs[1])
        frontend_utils.PrintPageToken(page_token)
      results = transfer_configs[0]
    elif self.transfer_run:
      object_type = bq_id_utils.ApiClientHelper.TransferRunReference
      run_attempt = self.run_attempt
      formatted_identifier = bq_id_utils.FormatDataTransferIdentifiers(
          client, identifier
      )
      reference = bq_id_utils.ApiClientHelper.TransferRunReference(
          transferRunName=formatted_identifier
      )
      # list_transfer_runs_result tuple contains transfer runs at index 0 and
      # next page token at index 1 if there is next page token.
      list_transfer_runs_result = client.ListTransferRuns(
          reference,
          run_attempt,
          max_results=self.max_results,
          page_token=self.page_token,
          states=self.filter,
      )
      # If the max_results flag is set and the length of response is 2
      # then it also contains the next_page_token.
      if self.max_results and len(list_transfer_runs_result) == 2:
        page_token = dict(nextPageToken=list_transfer_runs_result[1])
        frontend_utils.PrintPageToken(page_token)
      results = list_transfer_runs_result[0]
    elif self.transfer_log:
      object_type = bq_id_utils.ApiClientHelper.TransferLogReference
      formatted_identifier = bq_id_utils.FormatDataTransferIdentifiers(
          client, identifier
      )
      reference = bq_id_utils.ApiClientHelper.TransferLogReference(
          transferRunName=formatted_identifier
      )
      # list_transfer_log_result tuple contains transfer logs at index 0 and
      # next page token at index 1 if there is one.
      list_transfer_log_result = client.ListTransferLogs(
          reference,
          message_type=self.message_type,
          max_results=self.max_results,
          page_token=self.page_token,
      )
      if self.max_results and len(list_transfer_log_result) == 2:
        page_token = dict(nextPageToken=list_transfer_log_result[1])
        frontend_utils.PrintPageToken(page_token)
      results = list_transfer_log_result[0]
    elif self.connection:
      object_type = bq_id_utils.ApiClientHelper.ConnectionReference
      list_connections_results = client.ListConnections(
          FLAGS.project_id,
          FLAGS.location,
          max_results=self.max_results,
          page_token=self.page_token,
      )
      if 'connections' in list_connections_results:
        results = list_connections_results['connections']
      else:
        print('No connections found.')
      if 'nextPageToken' in list_connections_results:
        frontend_utils.PrintPageToken(list_connections_results)
    elif self.row_access_policies:
      object_type = bq_id_utils.ApiClientHelper.RowAccessPolicyReference
      response = client.ListRowAccessPoliciesWithGrantees(
          reference,
          self.max_results,
          self.page_token,
      )
      if 'rowAccessPolicies' in response:
        results = response['rowAccessPolicies']
      else:
        print('No row access policies found.')
      if 'nextPageToken' in response:
        frontend_utils.PrintPageToken(response)
    elif self.d:
      reference = client.GetProjectReference(identifier)
      object_type = bq_id_utils.ApiClientHelper.DatasetReference
      results = client.ListDatasets(
          reference,
          max_results=self.max_results,
          list_all=self.a,
          page_token=page_token,
          filter_expression=self.filter,
      )
    elif self.p or reference is None:
      object_type = bq_id_utils.ApiClientHelper.ProjectReference
      results = client.ListProjects(
          max_results=self.max_results, page_token=page_token
      )
    elif isinstance(reference, bq_id_utils.ApiClientHelper.ProjectReference):
      object_type = bq_id_utils.ApiClientHelper.DatasetReference
      results = client.ListDatasets(
          reference,
          max_results=self.max_results,
          list_all=self.a,
          page_token=page_token,
          filter_expression=self.filter,
      )
    else:  # isinstance(reference, DatasetReference):
      object_type = bq_id_utils.ApiClientHelper.TableReference
      results = client.ListTables(
          reference, max_results=self.max_results, page_token=page_token
      )
    if results:
      assert object_type is not None
      frontend_utils.PrintObjectsArray(results, object_type)


class Delete(bigquery_command.BigqueryCmd):
  usage = """rm [-f] [-r] [(-d|-t)] <identifier>"""

  def __init__(self, name, fv):
    super(Delete, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'dataset',
        False,
        'Remove dataset described by this identifier.',
        short_name='d',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'table',
        False,
        'Remove table described by this identifier.',
        short_name='t',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'job',
        False,
        'Remove job described by this identifier.',
        short_name='j',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'transfer_config',
        False,
        'Remove transfer configuration described by this identifier.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'force',
        None,
        "Ignore existing tables and datasets, don't prompt.",
        short_name='f',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'recursive',
        False,
        'Remove dataset and any tables it may contain.',
        short_name='r',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'reservation',
        False,
        'Deletes the reservation described by this identifier.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'capacity_commitment',
        False,
        'Deletes the capacity commitment described by this identifier.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'reservation_assignment',
        False,
        'Delete a reservation assignment.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'model',
        False,
        'Remove model with this model ID.',
        short_name='m',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'routine', False, 'Remove routine with this routine ID.', flag_values=fv
    )
    flags.DEFINE_boolean(
        'connection', False, 'Delete a connection.', flag_values=fv
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier):
    """Delete the resource described by the identifier.

    Always requires an identifier, unlike the show and ls commands.
    By default, also requires confirmation before deleting. Supports
    the -d -t flags to signify that the identifier is a dataset
    or table.
     * With -f, don't ask for confirmation before deleting.
     * With -r, remove all tables in the named dataset.

    Examples:
      bq rm ds.table
      bq rm -m ds.model
      bq rm --routine ds.routine
      bq rm -r -f old_dataset
      bq rm --transfer_config=projects/p/locations/l/transferConfigs/c
      bq rm --connection --project_id=proj --location=us con
      bq rm --capacity_commitment proj:US.capacity_commitment_id
      bq rm --reservation --project_id=proj --location=us reservation_name
      bq rm --reservation_assignment --project_id=proj --location=us
          assignment_name
    """

    client = bq_cached_client.Client.Get()

    # pylint: disable=g-doc-exception
    if (
        self.d
        + self.t
        + self.j
        + self.routine
        + self.transfer_config
        + self.reservation
        + self.reservation_assignment
        + self.capacity_commitment
        + self.connection
    ) > 1:
      raise app.UsageError('Cannot specify more than one resource type.')
    if not identifier:
      raise app.UsageError('Must provide an identifier for rm.')

    if self.t:
      reference = client.GetTableReference(identifier)
    elif self.m:
      reference = client.GetModelReference(identifier)
    elif self.routine:
      reference = client.GetRoutineReference(identifier)
    elif self.d:
      reference = client.GetDatasetReference(identifier)
    elif self.j:
      reference = client.GetJobReference(
          identifier, default_location=FLAGS.location
      )
    elif self.transfer_config:
      formatted_identifier = bq_id_utils.FormatDataTransferIdentifiers(
          client, identifier
      )
      reference = bq_id_utils.ApiClientHelper.TransferConfigReference(
          transferConfigName=formatted_identifier
      )
    elif self.reservation:
      try:
        reference = client.GetReservationReference(
            identifier=identifier, default_location=FLAGS.location
        )
        client.DeleteReservation(
            reference
        )
        print("Reservation '%s' successfully deleted." % identifier)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to delete reservation '%s': %s" % (identifier, e)
        )
    elif self.reservation_assignment:
      try:
        reference = client.GetReservationAssignmentReference(
            identifier=identifier, default_location=FLAGS.location
        )
        client.DeleteReservationAssignment(reference)
        print("Reservation assignment '%s' successfully deleted." % identifier)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to delete reservation assignment '%s': %s" % (identifier, e)
        )
    elif self.capacity_commitment:
      try:
        reference = client.GetCapacityCommitmentReference(
            identifier=identifier, default_location=FLAGS.location
        )
        client.DeleteCapacityCommitment(reference, self.force)
        print("Capacity commitment '%s' successfully deleted." % identifier)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to delete capacity commitment '%s': %s" % (identifier, e)
        )
    elif self.connection:
      reference = client.GetConnectionReference(
          identifier=identifier, default_location=FLAGS.location
      )
      client.DeleteConnection(reference)
    else:
      reference = client.GetReference(identifier)
      bq_id_utils.typecheck(
          reference,
          (
              bq_id_utils.ApiClientHelper.DatasetReference,
              bq_id_utils.ApiClientHelper.TableReference,
          ),
          'Invalid identifier "%s" for rm.' % (identifier,),
          is_usage_error=True,
      )

    if (
        isinstance(reference, bq_id_utils.ApiClientHelper.TableReference)
        and self.r
    ):
      raise app.UsageError('Cannot specify -r with %r' % (reference,))

    if (
        isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference)
        and self.r
    ):
      raise app.UsageError('Cannot specify -r with %r' % (reference,))

    if (
        isinstance(reference, bq_id_utils.ApiClientHelper.RoutineReference)
        and self.r
    ):
      raise app.UsageError('Cannot specify -r with %r' % (reference,))

    if not self.force:
      if (
          (
              isinstance(
                  reference, bq_id_utils.ApiClientHelper.DatasetReference
              )
              and client.DatasetExists(reference)
          )
          or (
              isinstance(reference, bq_id_utils.ApiClientHelper.TableReference)
              and client.TableExists(reference)
          )
          or (
              isinstance(reference, bq_id_utils.ApiClientHelper.JobReference)
              and client.JobExists(reference)
          )
          or (
              isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference)
              and client.ModelExists(reference)
          )
          or (
              isinstance(
                  reference, bq_id_utils.ApiClientHelper.RoutineReference
              )
              and client.RoutineExists(reference)
          )
          or (
              isinstance(
                  reference, bq_id_utils.ApiClientHelper.TransferConfigReference
              )
              and client.TransferExists(reference)
          )
      ):
        if 'y' != frontend_utils.PromptYN(
            'rm: remove %r? (y/N) ' % (reference,)
        ):
          print('NOT deleting %r, exiting.' % (reference,))
          return 0

    if isinstance(reference, bq_id_utils.ApiClientHelper.DatasetReference):
      client_dataset.DeleteDataset(
          client.apiclient,
          reference,
          ignore_not_found=self.force,
          delete_contents=self.recursive,
      )
    elif isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
      client.DeleteTable(reference, ignore_not_found=self.force)
    elif isinstance(reference, bq_id_utils.ApiClientHelper.JobReference):
      client.DeleteJob(reference, ignore_not_found=self.force)
    elif isinstance(reference, bq_id_utils.ApiClientHelper.ModelReference):
      client.DeleteModel(reference, ignore_not_found=self.force)
    elif isinstance(reference, bq_id_utils.ApiClientHelper.RoutineReference):
      client.DeleteRoutine(reference, ignore_not_found=self.force)
    elif isinstance(
        reference, bq_id_utils.ApiClientHelper.TransferConfigReference
    ):
      client.DeleteTransferConfig(reference, ignore_not_found=self.force)


class Copy(bigquery_command.BigqueryCmd):
  usage = """cp [-n] <source_table>[,<source_table>]* <dest_table>"""

  _NOTE = '**** NOTE! **** '
  _DATASET_NOT_FOUND = (
      'Dataset %s not found. Please enter a valid dataset name.'
  )
  _CROSS_REGION_WARNING = (
      'Warning: This operation is a cross-region copy operation. This may incur'
      ' additional charges.'
  )
  _SYNC_FLAG_ENABLED_WARNING = (
      'Warning: This operation is a cross-region copy operation. This may incur'
      ' additional charges and take a long time to complete.\nThis command is'
      ' running in sync mode. It is recommended to use async mode (-sync=false)'
      ' for cross-region copy operation.'
  )
  _CONFIRM_CROSS_REGION = 'cp: Proceed with cross-region copy of %s? [y/N]: '
  _CONFIRM_OVERWRITE = 'cp: Table %s already exists. Replace the table? [y/N]: '
  _NOT_COPYING = ' %s, exiting.'

  def __init__(self, name, fv):
    super(Copy, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'no_clobber',
        False,
        'Do not overwrite an existing table.',
        short_name='n',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'force',
        False,
        "Ignore existing destination tables, don't prompt.",
        short_name='f',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'append_table',
        False,
        'Append to an existing table.',
        short_name='a',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'destination_kms_key',
        None,
        'Cloud KMS key for encryption of the destination table data.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'snapshot',
        False,
        'Create a table snapshot of source table.',
        short_name='s',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'restore',
        False,
        'Restore table snapshot to a live table. Deprecated, please use clone '
        ' instead.',
        short_name='r',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'expiration',
        None,
        'Expiration time, in seconds from now, of the destination table.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'clone', False, 'Create a clone of source table.', flag_values=fv
    )
    self._ProcessCommandRc(fv)

  def _CheckAllSourceDatasetsInSameRegionAndGetFirstSourceRegion(
      self,
      client: bigquery_client_core.BigqueryClient,
      source_references: List[bq_id_utils.ApiClientHelper.TableReference],
  ) -> Tuple[bool, Optional[str]]:
    """Checks whether all source datasets are from same region.

    Args:
      client: Bigquery client
      source_references: Source reference

    Returns:
      true  - all source datasets are from the same region. Includes the
              scenario in which there is only one source dataset
      false - all source datasets are not from the same region.
    Raises:
      bq_error.BigqueryNotFoundError: If unable to compute the dataset
        region
    """
    all_source_datasets_in_same_region = True
    first_source_region = None
    for _, val in enumerate(source_references):
      source_dataset = val.GetDatasetReference()
      source_region = client_dataset.GetDatasetRegion(
          apiclient=client.apiclient,
          reference=source_dataset,
      )
      if source_region is None:
        raise bq_error.BigqueryNotFoundError(
            self._DATASET_NOT_FOUND % (str(source_dataset),),
            {'reason': 'notFound'},
            [],
        )
      if first_source_region is None:
        first_source_region = source_region
      elif first_source_region != source_region:
        all_source_datasets_in_same_region = False
        break
    return all_source_datasets_in_same_region, first_source_region

  def shouldContinueAfterCrossRegionCheck(
      self,
      client,
      source_references,
      source_references_str,
      dest_reference,
      destination_region,
  ):
    """Checks if it is a Cross Region Copy operation and obtains confirmation.

    Args:
      client: Bigquery client
      source_references: Source reference
      source_references_str: Source reference string
      dest_reference: Destination dataset reference
      destination_region: Destination dataset region

    Returns:
      true  - it is not a cross-region operation, or user has used force option,
              or cross-region operation is verified confirmed with user, or
              Insufficient permissions to query datasets for validation
      false - if user did not allow cross-region operation, or
              Dataset does not exist hence operation can't be performed.
    Raises:
      bq_error.BigqueryNotFoundError: If unable to compute the dataset
        region
    """
    destination_dataset = dest_reference.GetDatasetReference()

    try:
      all_source_datasets_in_same_region, first_source_region = (
          self._CheckAllSourceDatasetsInSameRegionAndGetFirstSourceRegion(
              client, source_references
          )
      )
      if destination_region is None:
        destination_region = client.GetDatasetRegion(destination_dataset)
    except bq_error.BigqueryAccessDeniedError as err:
      print(
          'Unable to determine source or destination dataset location, skipping'
          ' cross-region validation: '
          + str(err)
      )
      return True
    if destination_region is None:
      raise bq_error.BigqueryNotFoundError(
          self._DATASET_NOT_FOUND % (str(destination_dataset),),
          {'reason': 'notFound'},
          [],
      )
    if all_source_datasets_in_same_region and (
        destination_region == first_source_region
    ):
      return True
    print(
        self._NOTE,
        '\n' + self._SYNC_FLAG_ENABLED_WARNING
        if FLAGS.sync
        else '\n' + self._CROSS_REGION_WARNING,
    )
    if self.force:
      return True
    if 'y' != frontend_utils.PromptYN(
        self._CONFIRM_CROSS_REGION % (source_references_str,)
    ):
      print(self._NOT_COPYING % (source_references_str,))
      return False
    return True

  def RunWithArgs(self, source_tables, dest_table):
    """Copies one table to another.

    Examples:
      bq cp dataset.old_table dataset2.new_table
      bq cp --destination_kms_key=kms_key dataset.old_table dataset2.new_table
    """
    client = bq_cached_client.Client.Get()
    source_references = [
        client.GetTableReference(src) for src in source_tables.split(',')
    ]
    source_references_str = ', '.join(str(src) for src in source_references)
    dest_reference = client.GetTableReference(dest_table)

    if self.append_table:
      write_disposition = 'WRITE_APPEND'
      ignore_already_exists = True
    elif self.no_clobber:
      write_disposition = 'WRITE_EMPTY'
      ignore_already_exists = True
    else:
      write_disposition = 'WRITE_TRUNCATE'
      ignore_already_exists = False

    # Check if destination table exists, confirm overwrite
    destination_region = None
    if not ignore_already_exists and not self.force:
      destination_region = client.GetTableRegion(dest_reference)
      if destination_region and 'y' != frontend_utils.PromptYN(
          self._CONFIRM_OVERWRITE % (dest_reference)
      ):
        print(self._NOT_COPYING % (source_references_str,))
        return 0

    if not self.shouldContinueAfterCrossRegionCheck(
        client,
        source_references,
        source_references_str,
        dest_reference,
        destination_region,
    ):
      return 0

    operation = 'copied'
    if self.snapshot:
      operation_type = 'SNAPSHOT'
      operation = 'snapshotted'
    elif self.restore:
      operation_type = 'RESTORE'
      operation = 'restored'
    elif self.clone:
      operation_type = 'CLONE'
      operation = 'cloned'
    else:
      operation_type = 'COPY'
    kwds = {
        'write_disposition': write_disposition,
        'ignore_already_exists': ignore_already_exists,
        'job_id': frontend_utils.GetJobIdFromFlags(),
        'operation_type': operation_type,
    }
    if FLAGS.location:
      kwds['location'] = FLAGS.location

    if self.destination_kms_key:
      kwds['encryption_configuration'] = {
          'kmsKeyName': self.destination_kms_key
      }
    if self.expiration:
      datetime_utc = datetime.datetime.utcfromtimestamp(
          int(self.expiration + time.time())
      )
      kwds['destination_expiration_time'] = frontend_utils.FormatRfc3339(
          datetime_utc
      )
    job = client.CopyTable(source_references, dest_reference, **kwds)
    if job is None:
      print("Table '%s' already exists, skipping" % (dest_reference,))
    elif not FLAGS.sync:
      self.PrintJobStartInfo(job)
    else:
      plurality = 's' if len(source_references) > 1 else ''
      print(
          "Table%s '%s' successfully %s to '%s'"
          % (plurality, source_references_str, operation, dest_reference)
      )
      # If we are here, the job succeeded, but print warnings if any.
      frontend_utils.PrintJobMessages(bq_client_utils.FormatJobInfo(job))






class Truncate(bigquery_command.BigqueryCmd):  # pylint: disable=missing-docstring
  usage = """bq truncate project_id:dataset[.table] [--timestamp] [--dry_run] [--overwrite] [--skip_fully_replicated_tables]
"""

  def __init__(self, name, fv):
    super(Truncate, self).__init__(name, fv)
    flags.DEFINE_integer(
        'timestamp',
        None,
        'Optional timestamp to which table(s) will be truncated. Specified as '
        'milliseconds since epoch.',
        short_name='t',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'dry_run',
        None,
        'No-op that simply prints out information and the recommended '
        'timestamp without modifying tables or datasets.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'overwrite',
        False,
        'Overwrite existing tables. Otherwise timestamp will be appended to '
        'all output table names.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'skip_fully_replicated_tables',
        True,
        'Skip tables that are fully replicated (synced) and do not need to be '
        'truncated back to a point in time. This could result in datasets that '
        'have tables synchronized to different points in time, but will '
        'require less data to be re-loaded',
        short_name='s',
        flag_values=fv,
    )

    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier=''):
    # pylint: disable=g-doc-exception
    """Truncates table/dataset/project to a particular timestamp.

    Examples:
      bq truncate project_id:dataset
      bq truncate --overwrite project_id:dataset --timestamp 123456789
      bq truncate --skip_fully_replicated_tables=false project_id:dataset
    """
    client = bq_cached_client.Client.Get()

    if identifier:
      reference = client.GetReference(identifier.strip())
    else:
      raise app.UsageError('Must specify one of project, dataset or table')

    self.truncated_table_count = 0
    self.skipped_table_count = 0
    self.failed_table_count = 0
    status = []
    if self.timestamp and not self.dry_run:
      print(
          'Truncating to user specified timestamp %s.(Not skipping fully'
          ' replicated tables.)'
          % self.timestamp
      )
      if isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
        all_tables = [reference]
      else:
        if isinstance(reference, bq_id_utils.ApiClientHelper.DatasetReference):
          all_tables = list(
              map(
                  lambda x: client.GetReference(x['id']),
                  client.ListTables(reference, max_results=1000 * 1000),
              )
          )
      for a_table in all_tables:
        try:
          status.append(
              self._TruncateTable(a_table, str(self.timestamp), False)
          )
        except bq_error.BigqueryError as e:
          print(e)
          status.append((self._formatOutputString(a_table, 'Failed')))
          self.failed_table_count += 1
    else:
      if isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
        all_table_infos = self._GetTableInfo(reference)
      else:
        if isinstance(reference, bq_id_utils.ApiClientHelper.DatasetReference):
          all_table_infos = self._GetTableInfosFromDataset(reference)
      try:
        recovery_timestamp = min(
            list(map(self._GetRecoveryTimestamp, all_table_infos))
        )
      except (ValueError, TypeError):
        recovery_timestamp = None
      # Error out if we can't figure out a recovery timestamp
      # This can happen in following cases:
      # 1. No multi_site_info present for a table because no commit has been
      #  made to the table.
      # 2. No secondary site is present.
      if not recovery_timestamp:
        raise app.UsageError(
            'Unable to figure out a recovery timestamp for %s. Exiting.'
            % reference
        )
      print('Recommended timestamp to truncate to is %s' % recovery_timestamp)

      for a_table in all_table_infos:
        try:
          table_reference = bq_id_utils.ApiClientHelper.TableReference.Create(
              projectId=reference.projectId,
              datasetId=reference.datasetId,
              tableId=a_table['name'],
          )
          status.append(
              self._TruncateTable(
                  table_reference,
                  str(recovery_timestamp),
                  a_table['fully_replicated'],
              )
          )
        except bq_error.BigqueryError as e:
          print(e)
          status.append((self._formatOutputString(table_reference, 'Failed')))
          self.failed_table_count += 1
    print(
        '%s tables truncated, %s tables failed to truncate, %s tables skipped'
        % (
            self.truncated_table_count,
            self.failed_table_count,
            self.skipped_table_count,
        )
    )
    print(*status, sep='\n')

  def _GetTableInfosFromDataset(self, dataset_reference):

    # Find minimum of second maximum(latest_replicated_time) for all tables in
    # the dataset and if they are fully replicated.
    recovery_timestamp_for_dataset_query = ("""SELECT
  TABLE_NAME,
  UNIX_MILLIS(replicated_time_at_remote_site),
  CASE
    WHEN last_update_time <= min_latest_replicated_time THEN TRUE
  ELSE
  FALSE
END
  AS fully_replicated
FROM (
  SELECT
    TABLE_NAME,
    multi_site_info.last_update_time,
    ARRAY_AGG(site_info.latest_replicated_time
    ORDER BY
      latest_replicated_time DESC)[safe_OFFSET(1)] AS replicated_time_at_remote_site,
    ARRAY_AGG(site_info.latest_replicated_time
    ORDER BY
      latest_replicated_time ASC)[safe_OFFSET(0)] AS min_latest_replicated_time
  FROM
    %s.INFORMATION_SCHEMA.TABLES t,
    t.multi_site_info.site_info
  GROUP BY
    1,
    2)""") % dataset_reference.datasetId
    return self._ReadTableInfo(
        recovery_timestamp_for_dataset_query, 1000 * 1000
    )

  def _GetTableInfo(self, table_reference):

    # Find second maximum of latest_replicated_time across all sites for this
    # table and if the table is fully replicated
    recovery_timestamp_for_table_query = ("""SELECT
  TABLE_NAME,
  UNIX_MILLIS(replicated_time_at_remote_site),
  CASE
    WHEN last_update_time <= min_latest_replicated_time THEN TRUE
  ELSE
  FALSE
END
  AS fully_replicated
FROM (
  SELECT
    TABLE_NAME,
    multi_site_info.last_update_time,
    ARRAY_AGG(site_info.latest_replicated_time
    ORDER BY
      latest_replicated_time DESC)[safe_OFFSET(1)] AS replicated_time_at_remote_site,
    ARRAY_AGG(site_info.latest_replicated_time
    ORDER BY
      latest_replicated_time ASC)[safe_OFFSET(0)] AS min_latest_replicated_time
  FROM
    %s.INFORMATION_SCHEMA.TABLES t,
    t.multi_site_info.site_info
  WHERE
    TABLE_NAME = '%s'
  GROUP BY
    1,
    2 )""") % (table_reference.datasetId, table_reference.tableId)
    return self._ReadTableInfo(recovery_timestamp_for_table_query, row_count=1)

  def _GetRecoveryTimestamp(self, table_info):
    return (
        int(table_info['recovery_timestamp'])
        if table_info['recovery_timestamp']
        else None
    )

  def _ReadTableInfo(self, query, row_count):
    client = bq_cached_client.Client.Get()
    try:
      job = client.Query(query, use_legacy_sql=False)
    except bq_error.BigqueryError as e:
      # TODO(b/324243535): Correct this typing.
      # pytype: disable=attribute-error
      if 'Name multi_site_info not found' in e.error['message']:
        # pytype: enable=attribute-error
        raise app.UsageError(
            'This functionality is not enabled for the current project.'
        )
      else:
        raise e
    all_table_infos = []
    if not bq_client_utils.IsFailedJob(job):
      _, rows = client.ReadSchemaAndJobRows(
          job['jobReference'], start_row=0, max_rows=row_count
      )
      for i in range(len(rows)):
        table_info = {}
        table_info['name'] = rows[i][0]
        table_info['recovery_timestamp'] = rows[i][1]
        table_info['fully_replicated'] = rows[i][2] == 'true'
        all_table_infos.append(table_info)
      return all_table_infos

  def _formatOutputString(self, table_reference, status):
    return '%s %200s' % (table_reference, status)

  def _TruncateTable(
      self, table_reference, recovery_timestamp, is_fully_replicated
  ):
    client = bq_cached_client.Client.Get()
    kwds = {}
    if not self.overwrite:
      dest = bq_id_utils.ApiClientHelper.TableReference.Create(
          projectId=table_reference.projectId,
          datasetId=table_reference.datasetId,
          tableId='_'.join(
              [table_reference.tableId, 'TRUNCATED_AT', recovery_timestamp]
          ),
      )
    else:
      dest = table_reference

    if self.skip_fully_replicated_tables and is_fully_replicated:
      self.skipped_table_count += 1
      return self._formatOutputString(
          table_reference, 'Fully replicated...Skipped'
      )
    if self.dry_run:
      return self._formatOutputString(
          dest, 'will be Truncated@%s' % recovery_timestamp
      )
    kwds = {
        'write_disposition': 'WRITE_TRUNCATE',
        'ignore_already_exists': 'False',
        'operation_type': 'COPY',
    }
    if FLAGS.location:
      kwds['location'] = FLAGS.location
    source_table = client.GetTableReference(
        '%s@%s' % (table_reference, recovery_timestamp)
    )
    job_ref = ' '
    try:
      job = client.CopyTable([source_table], dest, **kwds)
      if job is None:
        self.failed_table_count += 1
        return self._formatOutputString(dest, 'Failed')
      job_ref = bq_processor_utils.ConstructObjectReference(job)
      self.truncated_table_count += 1
      return self._formatOutputString(dest, 'Successful %s ' % job_ref)
    except bq_error.BigqueryError as e:
      print(e)
      self.failed_table_count += 1
      return self._formatOutputString(dest, 'Failed %s ' % job_ref)


class Cancel(bigquery_command.BigqueryCmd):
  """Attempt to cancel the specified job if it is running."""

  usage = """cancel [--nosync] [<job_id>]"""

  def __init__(self, name, fv):
    super(Cancel, self).__init__(name, fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, job_id=''):
    # pylint: disable=g-doc-exception
    """Request a cancel and waits for the job to be cancelled.

    Requests a cancel and then either:
    a) waits until the job is done if the sync flag is set [default], or
    b) returns immediately if the sync flag is not set.
    Not all job types support a cancel, an error is returned if it cannot be
    cancelled. Even for jobs that support a cancel, success is not guaranteed,
    the job may have completed by the time the cancel request is noticed, or
    the job may be in a stage where it cannot be cancelled.

    Examples:
      bq cancel job_id  # Requests a cancel and waits until the job is done.
      bq --nosync cancel job_id  # Requests a cancel and returns immediately.

    Arguments:
      job_id: Job ID to cancel.
    """
    client = bq_cached_client.Client.Get()
    job_reference_dict = dict(client.GetJobReference(job_id, FLAGS.location))
    job = client.CancelJob(
        job_id=job_reference_dict['jobId'],
        location=job_reference_dict['location'],
    )
    frontend_utils.PrintObjectInfo(
        job,
        bq_id_utils.ApiClientHelper.JobReference.Create(**job['jobReference']),
        custom_format='show',
    )
    status = job['status']
    if status['state'] == 'DONE':
      if (
          'errorResult' in status
          and 'reason' in status['errorResult']
          and status['errorResult']['reason'] == 'stopped'
      ):
        print('Job has been cancelled successfully.')
      else:
        print('Job completed before it could be cancelled.')
    else:
      print('Job cancel has been requested.')
    return 0


class Head(bigquery_command.BigqueryCmd):
  usage = """head [-n <max rows>] [-j] [-t] <identifier>"""

  def __init__(self, name, fv):
    super(Head, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'job',
        False,
        'Reads the results of a query job.',
        short_name='j',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'table',
        False,
        'Reads rows from a table.',
        short_name='t',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'start_row',
        0,
        'The number of rows to skip before showing table data.',
        short_name='s',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'max_rows',
        100,
        'The number of rows to print when showing table data.',
        short_name='n',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'selected_fields',
        None,
        'A subset of fields (including nested fields) to return when showing '
        'table data. If not specified, full row will be retrieved. '
        'For example, "-c:a,b".',
        short_name='c',
        flag_values=fv,
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier=''):
    # pylint: disable=g-doc-exception
    """Displays rows in a table.

    Examples:
      bq head dataset.table
      bq head -j job
      bq head -n 10 dataset.table
      bq head -s 5 -n 10 dataset.table
    """
    client = bq_cached_client.Client.Get()
    if self.j and self.t:
      raise app.UsageError('Cannot specify both -j and -t.')

    if self.j:
      reference = client.GetJobReference(identifier, FLAGS.location)
    else:
      reference = client.GetTableReference(identifier)

    if isinstance(reference, bq_id_utils.ApiClientHelper.JobReference):
      fields, rows = client.ReadSchemaAndJobRows(
          dict(reference), start_row=self.s, max_rows=self.n
      )
    elif isinstance(reference, bq_id_utils.ApiClientHelper.TableReference):
      fields, rows = client.ReadSchemaAndRows(
          dict(reference),
          start_row=self.s,
          max_rows=self.n,
          selected_fields=self.c,
      )
    else:
      raise app.UsageError("Invalid identifier '%s' for head." % (identifier,))

    bq_cached_client.Factory.ClientTablePrinter.GetTablePrinter().PrintTable(
        fields, rows
    )


class Insert(bigquery_command.BigqueryCmd):
  usage = """insert [-s] [-i] [-x=<suffix>] <table identifier> [file]"""

  def __init__(self, name, fv):
    super(Insert, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'skip_invalid_rows',
        None,
        'Attempt to insert any valid rows, even if invalid rows are present.',
        short_name='s',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'ignore_unknown_values',
        None,
        'Ignore any values in a row that are not present in the schema.',
        short_name='i',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'template_suffix',
        None,
        'If specified, treats the destination table as a base template, and '
        'inserts the rows into an instance table named '
        '"{destination}{templateSuffix}". BigQuery will manage creation of the '
        'instance table, using the schema of the base template table.',
        short_name='x',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'insert_id',
        None,
        'Used to ensure repeat executions do not add unintended data. '
        'A present insert_id value will be appended to the row number of '
        'each row to be inserted and used as the insertId field for the row. '
        'Internally the insertId field is used for deduping of inserted rows.',
        flag_values=fv,
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier='', filename=None):
    """Inserts rows in a table.

    Inserts the records formatted as newline delimited JSON from file
    into the specified table. If file is not specified, reads from stdin.
    If there were any insert errors it prints the errors to stdout.

    Examples:
      bq insert dataset.table /tmp/mydata.json
      echo '{"a":1, "b":2}' | bq insert dataset.table

    Template table examples:
    Insert to dataset.table_suffix table using dataset.table table as its
    template.
      bq insert -x=_suffix dataset.table /tmp/mydata.json
    """
    if filename:
      with open(filename, 'r') as json_file:
        return self._DoInsert(
            identifier,
            json_file,
            skip_invalid_rows=self.skip_invalid_rows,
            ignore_unknown_values=self.ignore_unknown_values,
            template_suffix=self.template_suffix,
            insert_id=self.insert_id,
        )
    else:
      return self._DoInsert(
          identifier,
          sys.stdin,
          skip_invalid_rows=self.skip_invalid_rows,
          ignore_unknown_values=self.ignore_unknown_values,
          template_suffix=self.template_suffix,
          insert_id=self.insert_id,
      )

  def _DoInsert(
      self,
      identifier,
      json_file,
      skip_invalid_rows=None,
      ignore_unknown_values=None,
      template_suffix=None,
      insert_id=None,
  ):
    """Insert the contents of the file into a table."""
    client = bq_cached_client.Client.Get()
    reference = client.GetReference(identifier)
    bq_id_utils.typecheck(
        reference,
        (bq_id_utils.ApiClientHelper.TableReference,),
        'Must provide a table identifier for insert.',
        is_usage_error=True,
    )
    reference = dict(reference)
    batch = []

    def Flush():
      result = client.InsertTableRows(
          reference,
          batch,
          skip_invalid_rows=skip_invalid_rows,
          ignore_unknown_values=ignore_unknown_values,
          template_suffix=template_suffix,
      )
      del batch[:]
      return result, result.get('insertErrors', None)

    result = {}
    errors = None
    lineno = 1
    for line in json_file:
      try:
        unique_insert_id = None
        if insert_id is not None:
          unique_insert_id = insert_id + '_' + str(lineno)
        batch.append(
            bq_processor_utils.JsonToInsertEntry(unique_insert_id, line)
        )
        lineno += 1
      except bq_error.BigqueryClientError as e:
        raise app.UsageError('Line %d: %s' % (lineno, str(e)))
      if (
          FLAGS.max_rows_per_request
          and len(batch) == FLAGS.max_rows_per_request
      ):
        result, errors = Flush()
      if errors:
        break
    if batch and not errors:
      result, errors = Flush()

    if FLAGS.format in ['prettyjson', 'json']:
      bq_utils.PrintFormattedJsonObject(result)
    elif FLAGS.format in [None, 'sparse', 'pretty']:
      if errors:
        for entry in result['insertErrors']:
          entry_errors = entry['errors']
          sys.stdout.write('record %d errors: ' % (entry['index'],))
          for error in entry_errors:
            print(
                '\t%s: %s'
                % (
                    stringutil.ensure_str(error['reason']),
                    stringutil.ensure_str(error.get('message')),
                )
            )
    return 1 if errors else 0


class Wait(bigquery_command.BigqueryCmd):  # pylint: disable=missing-docstring
  usage = """wait [<job_id>] [<secs>]"""

  def __init__(self, name, fv):
    super(Wait, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'fail_on_error',
        True,
        'When done waiting for the job, exit the process with an error '
        'if the job is still running, or ended with a failure.',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'wait_for_status',
        'DONE',
        'Wait for the job to have a certain status. Default is DONE.',
        flag_values=fv,
    )
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, job_id='', secs=sys.maxsize):
    # pylint: disable=g-doc-exception
    """Wait some number of seconds for a job to finish.

    Poll job_id until either (1) the job is DONE or (2) the
    specified number of seconds have elapsed. Waits forever
    if unspecified. If no job_id is specified, and there is
    only one running job, we poll that job.

    Examples:
      bq wait # Waits forever for the currently running job.
      bq wait job_id  # Waits forever
      bq wait job_id 100  # Waits 100 seconds
      bq wait job_id 0  # Polls if a job is done, then returns immediately.
      # These may exit with a non-zero status code to indicate "failure":
      bq wait --fail_on_error job_id  # Succeeds if job succeeds.
      bq wait --fail_on_error job_id 100  # Succeeds if job succeeds in 100 sec.

    Arguments:
      job_id: Job ID to wait on.
      secs: Number of seconds to wait (must be >= 0).
    """
    try:
      secs = bq_client_utils.NormalizeWait(secs)
    except ValueError:
      raise app.UsageError('Invalid wait time: %s' % (secs,))

    client = bq_cached_client.Client.Get()
    if not job_id:
      running_jobs = client.ListJobRefs(state_filter=['PENDING', 'RUNNING'])
      if len(running_jobs) != 1:
        raise bq_error.BigqueryError(
            'No job_id provided, found %d running jobs' % (len(running_jobs),)
        )
      job_reference = running_jobs.pop()
    else:
      job_reference = client.GetJobReference(job_id, FLAGS.location)
    try:
      job = client.WaitJob(
          job_reference=job_reference, wait=secs, status=self.wait_for_status
      )
      frontend_utils.PrintObjectInfo(
          job,
          bq_id_utils.ApiClientHelper.JobReference.Create(
              **job['jobReference']
          ),
          custom_format='show',
      )
      return 1 if self.fail_on_error and bq_client_utils.IsFailedJob(job) else 0
    except StopIteration as e:
      print()
      print(e)
    # If we reach this point, we have not seen the job succeed.
    return 1 if self.fail_on_error else 0


class Init(bigquery_command.BigqueryCmd):
  """Create a .bigqueryrc file and set up OAuth credentials."""

  def __init__(self, name, fv):
    super(Init, self).__init__(name, fv)
    self.surface_in_shell = False
    flags.DEFINE_boolean(
        'delete_credentials',
        False,
        'If specified, the credentials file associated with this .bigqueryrc '
        'file is deleted.',
        flag_values=fv,
    )

  def _NeedsInit(self):
    """Init never needs to call itself before running."""
    return False

  def DeleteCredentials(self):
    """Deletes this user's credential file."""
    bq_utils.ProcessBigqueryrc()
    filename = FLAGS.service_account_credential_file or FLAGS.credential_file
    if not os.path.exists(filename):
      print('Credential file %s does not exist.' % (filename,))
      return 0
    try:
      if 'y' != frontend_utils.PromptYN(
          'Delete credential file %s? (y/N) ' % (filename,)
      ):
        print('NOT deleting %s, exiting.' % (filename,))
        return 0
      os.remove(filename)
    except OSError as e:
      print('Error removing %s: %s' % (filename, e))
      return 1

  def RunWithArgs(self):
    """Authenticate and create a default .bigqueryrc file."""
    message = (
        'BQ CLI will soon require all users to log in using'
        ' `gcloud auth login`. `bq init` will no longer handle'
        ' authentication after January 1, 2024.\n'
    )
    termcolor.cprint(
        '\n'.join(textwrap.wrap(message, width=80)),
        color='red',
        attrs=['bold'],
        file=sys.stdout,
    )

    # Capture project_id before loading defaults from ~/.bigqueryrc so that we
    # get the true value of the flag as specified on the command line.
    project_id_flag = FLAGS.project_id
    bq_utils.ProcessBigqueryrc()
    bq_logging.ConfigureLogging(bq_flags.APILOG.value)
    if self.delete_credentials:
      return self.DeleteCredentials()
    bigqueryrc = bq_utils.GetBigqueryRcFilename()
    # Delete the old one, if it exists.
    print()
    print('Welcome to BigQuery! This script will walk you through the ')
    print('process of initializing your .bigqueryrc configuration file.')
    print()
    if os.path.exists(bigqueryrc):
      print(' **** NOTE! ****')
      print('An existing .bigqueryrc file was found at %s.' % (bigqueryrc,))
      print('Are you sure you want to continue and overwrite your existing ')
      print('configuration?')
      print()

      if 'y' != frontend_utils.PromptYN('Overwrite %s? (y/N) ' % (bigqueryrc,)):
        print('NOT overwriting %s, exiting.' % (bigqueryrc,))
        return 0
      print()
      try:
        os.remove(bigqueryrc)
      except OSError as e:
        print('Error removing %s: %s' % (bigqueryrc, e))
        return 1

    print('First, we need to set up your credentials if they do not ')
    print('already exist.')
    print()
    # NOTE: even if the client is not used below (when --project_id is
    # specified), getting the client will start the authorization workflow if
    # credentials do not already exist and so it is important this is done
    # unconditionally.
    client = bq_cached_client.Client.Get()

    entries = {'credential_file': FLAGS.credential_file}
    if project_id_flag:
      print('Setting project_id %s as the default.' % project_id_flag)
      print()
      entries['project_id'] = project_id_flag
    else:
      projects = client.ListProjects(max_results=1000)
      print(
          'Credential creation complete. Now we will select a default project.'
      )
      print()
      if not projects:
        print('No projects found for this user. Please go to ')
        print('  https://console.cloud.google.com/')
        print('and create a project.')
        print()
      else:
        print('List of projects:')
        formatter = frontend_utils.GetFormatterFromFlags()
        formatter.AddColumn('#')
        bq_client_utils.ConfigureFormatter(
            formatter, bq_id_utils.ApiClientHelper.ProjectReference
        )
        for index, project in enumerate(projects):
          result = bq_client_utils.FormatProjectInfo(project)
          result.update({'#': index + 1})
          formatter.AddDict(result)
        formatter.Print()

        if len(projects) == 1:
          project_reference = bq_processor_utils.ConstructObjectReference(
              projects[0]
          )
          print(
              'Found only one project, setting %s as the default.'
              % (project_reference,)
          )
          print()
          entries['project_id'] = project_reference.projectId
        else:
          print('Found multiple projects. Please enter a selection for ')
          print('which should be the default, or leave blank to not ')
          print('set a default.')
          print()

          response = None
          while not isinstance(response, int):
            response = frontend_utils.PromptWithDefault(
                'Enter a selection (1 - %s): ' % (len(projects),)
            )
            try:
              if not response or 1 <= int(response) <= len(projects):
                response = int(response or 0)
            except ValueError:
              pass
          print()
          if response:
            project_reference = bq_processor_utils.ConstructObjectReference(
                projects[response - 1]
            )
            entries['project_id'] = project_reference.projectId

    try:
      with open(bigqueryrc, 'w') as rcfile:
        for flag, value in entries.items():
          print('%s = %s' % (flag, value), file=rcfile)
    except IOError as e:
      print('Error writing %s: %s' % (bigqueryrc, e))
      return 1

    print('BigQuery configuration complete! Type "bq" to get started.')
    print()
    bq_utils.ProcessBigqueryrc()
    # Destroy the client we created, so that any new client will
    # pick up new flag values.
    bq_cached_client.Client.Delete()
    return 0


class Version(bigquery_command.BigqueryCmd):
  usage = """version"""

  def _NeedsInit(self):
    """If just printing the version, don't run `init` first."""
    return False

  def RunWithArgs(self):
    """Return the version of bq."""
    print('This is BigQuery CLI %s' % (bq_utils.VERSION_NUMBER,))
