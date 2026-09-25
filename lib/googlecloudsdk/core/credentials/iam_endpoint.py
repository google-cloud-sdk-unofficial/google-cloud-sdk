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
"""Utilities for IAM endpoints."""

from googlecloudsdk.core import properties

IAM_ENDPOINT_GDU = 'https://iamcredentials.googleapis.com/'


def GetEffectiveIamEndpoint() -> str:
  """Returns the effective IAM endpoint.

  (1) If the [api_endpoint_overrides/iamcredentials] property is explicitly set,
  return the property value.
  (2) Otherwise if [core/universe_domain] value is not default, return
  "https://iamcredentials.{universe_domain_value}/".
  (3) Otherwise return "https://iamcredentials.googleapis.com/"

  Returns:
    str: The effective IAM endpoint.
  """
  if properties.VALUES.api_endpoint_overrides.iamcredentials.IsExplicitlySet():
    return properties.VALUES.api_endpoint_overrides.iamcredentials.Get()

  universe_domain_property = properties.VALUES.core.universe_domain
  if universe_domain_property.Get() != universe_domain_property.default:
    return IAM_ENDPOINT_GDU.replace(
        'googleapis.com', universe_domain_property.Get()
    )
  return IAM_ENDPOINT_GDU
