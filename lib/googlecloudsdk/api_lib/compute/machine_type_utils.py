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
"""Utilities for parsing custom machine type names."""

import re


def GetCpuRamVmFamilyFromCustomName(name):
  """Gets the CPU and memory specs from the custom machine type name.

  Args:
    name: the custom machine type name for the 'instance create' call

  Returns:
    A three-tuple with the vm family, number of cpu and amount of memory for the
    custom machine type.
    custom_family, the name of the VM family
    custom_cpu, the number of cpu desired for the custom machine type instance
    custom_memory_mib, the amount of ram desired in MiB for the custom machine
      type instance
    None for both variables otherwise
  """
  check_custom = re.search('([a-zA-Z0-9]+)-custom-([0-9]+)-([0-9]+)', name)
  if check_custom:
    custom_family = check_custom.group(1)
    custom_cpu = check_custom.group(2)
    custom_memory_mib = check_custom.group(3)
    return custom_family, custom_cpu, custom_memory_mib
  return None, None, None
