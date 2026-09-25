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

"""Common utilities for remotebuildexecution workerpool commands."""

DEFAULT_BACKUP_VM_DISK_TYPE = 'pd-standard'
DEFAULT_BACKUP_VM_DISK_SIZE_GB = 200


def SetDefaultBackupVmInstanceSpecs(worker_config):
  """Sets default values for diskType and diskSizeGb in backup_vm_instance_specs."""
  if worker_config and worker_config.backupVmInstanceSpecs:
    for spec in worker_config.backupVmInstanceSpecs:
      if not spec.diskType:
        spec.diskType = DEFAULT_BACKUP_VM_DISK_TYPE
      if not spec.diskSizeGb:
        spec.diskSizeGb = DEFAULT_BACKUP_VM_DISK_SIZE_GB
