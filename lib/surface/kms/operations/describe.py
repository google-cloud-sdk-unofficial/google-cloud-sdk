# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Describe operation command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args


@base.DefaultUniverseOnly
class Describe(base.Command):
  """View the details of an operation.

  View the details of an operation.

  ## EXAMPLES

  To view the details of an operation, run:

    $ {command} operation_id
        --location=us-central1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsOperationResourceArgForKMS(parser, True, 'operation')

  def Run(self, args):
    """View the details of an operation."""
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    operation_ref = args.CONCEPTS.operation.Parse()
    get_request = messages.CloudkmsProjectsLocationsOperationsGetRequest(
        name=operation_ref.RelativeName()
    )
    operation = client.projects_locations_operations.Get(get_request)
    return operation
