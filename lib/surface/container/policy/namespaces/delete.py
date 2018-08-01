# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""`cloud container policy namespaces delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.policy.namespaces import policy_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.policy.namespaces import command_lib
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a Kubernetes Managed Namespace."""

  @staticmethod
  def Args(parser):
    command_lib.AddNamespaceResourceArg(parser, 'to delete')

  def Run(self, args):
    namespace_ref = args.CONCEPTS.namespace.Parse()
    namespace_name = namespace_ref.RelativeName()

    console_io.PromptContinue(
        message='Namespace {name} will be deleted'.format(name=namespace_name),
        cancel_on_no=True)

    namespace = policy_api.Delete(namespace_name)
    log.DeletedResource(namespace_name)
    return namespace
