# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for operating on endpoints for different regions."""


import contextlib

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from six.moves.urllib import parse


def DeriveAiplatformRegionalEndpoint(endpoint, region, is_prediction=False):
  """Derives the regional or multi-regional (mREP) AI Platform endpoint.

  The `region` value may be either a GCP region (e.g. us-central1) or an mREP
  jurisdiction (see MREP_JURISDICTIONS, e.g. us). The universe domain is taken
  from the base `endpoint` and preserved. Given a base host of
  aiplatform.<domain>, an mREP jurisdiction is served on its dedicated REP host
  aiplatform.<geo>.rep.<domain>, while a GCP region uses the locational
  <region>-aiplatform.<domain> form.

  A host that is already an mREP host (contains '.rep.') is returned unchanged,
  so the derivation is idempotent. A non-prod base (e.g. a sandbox host that
  doesn't start with 'aiplatform') is also returned unchanged.

  Args:
    endpoint: str, the base AI Platform endpoint URL.
    region: str, a GCP region or an mREP jurisdiction.
    is_prediction: bool, whether this is a prediction endpoint.

  Returns:
    str, the derived regional or multi-regional endpoint URL.
  """
  scheme, netloc, path, params, query, fragment = parse.urlparse(endpoint)
  if netloc.startswith('aiplatform') and '.rep.' not in netloc:
    if region in constants.MREP_JURISDICTIONS and '.' in netloc:
      # aiplatform.<domain> -> aiplatform.<geo>.rep.<domain>.
      service, base_domain = netloc.split('.', 1)
      netloc = '{}.{}.rep.{}'.format(service, region, base_domain)
    elif is_prediction:
      netloc = '{}-prediction-{}'.format(region, netloc)
    else:
      netloc = '{}-{}'.format(region, netloc)
  return parse.urlunparse((scheme, netloc, path, params, query, fragment))


@contextlib.contextmanager
def AiplatformEndpointOverrides(
    version, region, is_prediction=False, use_info_log=False
):
  """Context manager to override the AI Platform endpoints for a while.

  Raises an error if
  region is not set.

  Args:
    version: str, implies the version that the endpoint will use.
    region: str, region of the AI Platform stack.
    is_prediction: bool, it's for prediction endpoint or not.
    use_info_log: bool, whether to use info log or print.

  Yields:
    None
  """
  used_endpoint = GetEffectiveEndpoint(version=version, region=region,
                                       is_prediction=is_prediction)
  if use_info_log:
    log.info('Using endpoint [%s]', used_endpoint)
  else:
    log.status.Print('Using endpoint [{}]'.format(used_endpoint))
  properties.VALUES.api_endpoint_overrides.aiplatform.Set(used_endpoint)
  yield


def GetEffectiveEndpoint(version, region, is_prediction=False):
  """Returns regional AI Platform endpoint, or raise an error if the region not set."""
  endpoint = apis.GetEffectiveApiEndpoint(
      constants.AI_PLATFORM_API_NAME,
      constants.AI_PLATFORM_API_VERSION[version])
  return DeriveAiplatformRegionalEndpoint(
      endpoint, region, is_prediction=is_prediction)
