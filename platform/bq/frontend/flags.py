#!/usr/bin/env python
"""Flags shared across multiple commands."""

from typing import Optional

from absl import flags


def define_null_marker(
    flag_values: flags.FlagValues,
) -> flags.FlagHolder[Optional[str]]:
  return flags.DEFINE_string(
      'null_marker',
      None,
      'An optional custom string that will represent a NULL value'
      'in CSV External table data.',
      flag_values=flag_values,
  )


def define_parquet_map_target_type(
    flag_values: flags.FlagValues,
) -> flags.FlagHolder[Optional[str]]:
  return flags.DEFINE_enum(
      'parquet_map_target_type',
      None,
      ['ARRAY_OF_STRUCT'],
      'Specifies the parquet map type. If it is equal to ARRAY_OF_STRUCT,'
      ' then a map_field will be represented with a repeated struct (that has'
      ' key and value fields).',
      flag_values=flag_values,
  )


def define_workload_id(
    flag_values: flags.FlagValues,
) -> flags.FlagHolder[Optional[str]]:
  return flags.DEFINE_string(
      'workload_id',
      None,
      'Whether to execute the job using the provided workload_id.',
      flag_values=flag_values,
  )
