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
"""Utilities for Cloud Run domain mapping."""

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import platforms


def VerifyDomain(domain_mapping_ref):
  """Verify that the provided domain has already been verified.

  Args:
    domain_mapping_ref: Resource, domainmapping resource.

  Raises:
    DomainMappingCreationError: if the domain is not verified.
  """
  if platforms.GetPlatform() == platforms.PLATFORM_MANAGED:
    client = global_methods.GetServerlessClientInstance()
    all_domains = global_methods.ListVerifiedDomains(client)
    # If not already verified, explain and error out
    if all(d.id not in domain_mapping_ref.Name() for d in all_domains):
      if not all_domains:
        domains_text = 'You currently have no verified domains.'
      else:
        domains = ['* {}'.format(d.id) for d in all_domains]
        domains_text = 'Currently verified domains:\n{}'.format(
            '\n'.join(domains)
        )
      raise exceptions.DomainMappingCreationError(
          'The provided domain does not appear to be verified for the current '
          'account. To verify it, run:\n\n'
          '  $ gcloud domains verify {domain}\n\n'
          'Once verified, try this command again.\n{domains}'.format(
              domain=domain_mapping_ref.Name(),
              domains=domains_text,
          )
      )


def GetDomainMapping(client, domain_mapping_ref):
  """Get a domain mapping.

  Args:
    client: ServerlessOperations, the serverless client.
    domain_mapping_ref: Resource, domainmapping resource.

  Returns:
    A domain_mapping.DomainMapping object or None if not found.
  """
  try:
    return client.GetDomainMapping(domain_mapping_ref)
  except api_lib_exceptions.apitools_exceptions.HttpNotFoundError:
    return None
