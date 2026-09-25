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

"""Utilities for remotebuildexecution workerpool create command."""

from googlecloudsdk.command_lib.remote_build_execution import workerpool_util


def RemoveDiskTypeForMacOS(ref, args, request):
  del ref, args
  if (
      request.workerPool
      and request.workerPool.hostOs is not None
      and request.workerPool.hostOs.startswith('macos-')
  ):
    if request.workerPool.workerConfig:
      request.workerPool.workerConfig.diskType = None
  return request


def SetBackupVmInstanceSpecDefaults(ref, args, request):
  """Sets default values for diskType and diskSizeGb in backup_vm_instance_specs."""
  del ref, args
  if request.workerPool:
    workerpool_util.SetDefaultBackupVmInstanceSpecs(
        request.workerPool.workerConfig
    )
  return request


