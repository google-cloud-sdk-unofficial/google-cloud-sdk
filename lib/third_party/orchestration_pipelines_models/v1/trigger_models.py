# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from typing import Literal, Optional
from datetime import datetime
from attrs import define, field
from orchestration_pipelines_models.utils.time_utils import validate_cron_expression, validate_timezone


@define(kw_only=True)
class ScheduleTriggerModel:
    type: Literal['schedule']
    scheduleInterval: str = field(validator=validate_cron_expression)
    startTime: str
    endTime: str
    catchup: bool
    timezone: Optional[str] = field(default='UTC', validator=validate_timezone)

    def __attrs_post_init__(self):
        """
        Validates cross-field logic for start and end times.
        """
        parsed_start_time = datetime.fromisoformat(self.startTime)
        parsed_end_time = datetime.fromisoformat(self.endTime)

        if parsed_end_time < parsed_start_time:
            raise ValueError('endTime must be after startTime')
