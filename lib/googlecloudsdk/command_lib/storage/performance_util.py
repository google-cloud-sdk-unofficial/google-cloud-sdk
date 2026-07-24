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
"""Performance utilities for gcloud storage."""

import os

from googlecloudsdk.core import log


def apply_nic_isolation():
  """Pins worker processes to specific CPUs to isolate them from NIC interrupts.

  This is currently only for Linux; Mac does not support it, and it will be
  extended to Windows.

  This function sets the CPU affinity of the current process (the calling
  worker). When the worker process dies, the affinity goes away, so no manual
  unset is needed. Isolating from NIC cores reduces CPU contention and context
  switching, improving high-throughput workloads.
  """
  # TODO(b/529297608): Use first_task.is_bidi_download to restrict this to Bidi
  # downloads. This can be passed in from the executor in a future iteration.
  try:
    if hasattr(os, 'sched_setaffinity') and hasattr(os, 'sched_getaffinity'):
      available_cores = sorted(list(os.sched_getaffinity(0)))
      if len(available_cores) > 16:
        reserved_cores = max(1, int(len(available_cores) * 0.1))
        target_cores = set(available_cores[reserved_cores:])
        os.sched_setaffinity(0, target_cores)
      else:
        log.warning(
            'NIC isolation requested but the system has 16 or fewer cores '
            'available.'
        )
    else:
      log.warning(
          'NIC isolation requested but the current OS does not support '
          'setting CPU affinity.'
      )
  except Exception as e:  # pylint: disable=broad-except
    log.warning('Failed to set CPU affinity for NIC isolation: %r', e)
