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


def define_reservation_id_for_a_job(
    flag_values: flags.FlagValues,
) -> flags.FlagHolder[Optional[str]]:
  return flags.DEFINE_string(
      'reservation_id',
      None,
      'Reservation ID used when executing the job. Reservation should be in the'
      'format of project_id:reservation_id, project_id:location.reservation_id,'
      'or reservation_id',
      flag_values=flag_values,
  )


def define_event_driven_schedule(
    flag_values: flags.FlagValues,
) -> flags.FlagHolder[Optional[str]]:
  return flags.DEFINE_string(
      'event_driven_schedule',
      None,
      'Event driven schedule in json format. Example:'
      ' --event_driven_schedule=\'{"pubsub_subscription":'
      ' "projects/project-id/subscriptions/subscription-id"}\'. This flag'
      ' should not be used with --schedule, --no_auto_scheduling,'
      ' --schedule_start_time or --schedule_end_time.',
      flag_values=flag_values,
  )
