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
"""Universe domain property helpers."""

from googlecloudsdk.core.properties.values import VALUES


def IsDefaultUniverse():
  universe_domain_property = VALUES.core.universe_domain
  return universe_domain_property.Get() == universe_domain_property.default


def GetUniverseDomain():
  """Get the universe domain."""

  return VALUES.core.universe_domain.Get()

