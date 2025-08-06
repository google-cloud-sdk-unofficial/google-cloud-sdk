#!/usr/bin/env python
"""The supported gcloud migration workflow commands in BQ CLI."""

from typing import List

from gcloud_wrapper import bq_to_gcloud_config_classes

FlagMapping = bq_to_gcloud_config_classes.FlagMapping
UnsupportedFlagMapping = bq_to_gcloud_config_classes.UnsupportedFlagMapping
CommandMapping = bq_to_gcloud_config_classes.CommandMapping


_MIGRATION_WORKFLOWS = 'migration_workflows'

SUPPORTED_COMMANDS_MIGRATION_WORKFLOW: List[CommandMapping] = [
    CommandMapping(
        resource=_MIGRATION_WORKFLOWS,
        bq_command='ls',
        gcloud_command=['bq', 'migration-workflows', 'list'],
        flag_mapping_list=[
            FlagMapping('location', 'location'),
            FlagMapping('max_results', 'limit'),
        ],
        table_projection='name,displayName,state,createTime,lastUpdateTime',
        csv_projection='name,displayName:label=display_name,state,createTime:label=create_time,lastUpdateTime:label=last_update_time',
    ),
]
