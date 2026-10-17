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

from __future__ import annotations

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


def OverrideIamIdTokenEndpoint(
    effective_iam_endpoint: str | None = None,
) -> None:
  """Overrides the IAM generateIdToken endpoint on google.auth.iam if needed.

  Args:
    effective_iam_endpoint: Optional precomputed effective IAM endpoint URL. If
      not provided, GetEffectiveIamEndpoint() is used.
  """
  # pylint: disable=g-import-not-at-top
  from google.auth import iam as google_auth_iam
  # pylint: enable=g-import-not-at-top

  if effective_iam_endpoint is None:
    effective_iam_endpoint = GetEffectiveIamEndpoint()
  google_auth_iam._IAM_IDTOKEN_ENDPOINT = (  # pylint: disable=protected-access
      google_auth_iam._IAM_IDTOKEN_ENDPOINT.replace(  # pylint: disable=protected-access
          IAM_ENDPOINT_GDU,
          effective_iam_endpoint,
      )
  )


def PerformIamEndpointsOverride() -> None:
  """Perform IAM endpoint override if needed.

  We will override IAM generateAccessToken, signBlob, and generateIdToken
  endpoint under the following conditions.
  (1) If the [api_endpoint_overrides/iamcredentials] property is explicitly
  set, we replace "https://iamcredentials.googleapis.com/" with the given
  property value in these endpoints.
  (2) If the property above is not set, and the [core/universe_domain] value
  is not default, we replace "googleapis.com" with the [core/universe_domain]
  property value in these endpoints.
  """
  # pylint: disable=g-import-not-at-top
  from google.auth import iam as google_auth_iam
  # pylint: enable=g-import-not-at-top

  effective_iam_endpoint = GetEffectiveIamEndpoint()
  google_auth_iam._IAM_ENDPOINT = (  # pylint: disable=protected-access
      google_auth_iam._IAM_ENDPOINT.replace(  # pylint: disable=protected-access
          IAM_ENDPOINT_GDU,
          effective_iam_endpoint,
      )
  )
  google_auth_iam._IAM_SIGN_ENDPOINT = (  # pylint: disable=protected-access
      google_auth_iam._IAM_SIGN_ENDPOINT.replace(  # pylint: disable=protected-access
          IAM_ENDPOINT_GDU,
          effective_iam_endpoint,
      )
  )
  OverrideIamIdTokenEndpoint(effective_iam_endpoint)
