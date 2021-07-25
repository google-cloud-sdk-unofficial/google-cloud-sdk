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
"""Command for deleting a service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun.core import events_constants
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import flags
from googlecloudsdk.command_lib.kuberun import connection_context
from googlecloudsdk.command_lib.kuberun import events_flags
from googlecloudsdk.command_lib.kuberun.core.events import init_shared
from googlecloudsdk.command_lib.kuberun.core.events import operator
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class Init(base.Command):
  """Initialize a cluster for eventing."""

  detailed_help = {
      'DESCRIPTION': """
          {description}
          Enables necessary services for the project, adds necessary IAM policy
          bindings to the provided service account, and creates a new key for
          the provided service account.
          """,
      'EXAMPLES': """
          To initialize a cluster:

              $ {command}
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    """Defines arguments common to all release tracks."""
    flags.AddControlPlaneServiceAccountFlag(parser)
    flags.AddBrokerServiceAccountFlag(parser)
    flags.AddSourcesServiceAccountFlag(parser)
    events_flags.AddAuthenticationFlag(parser)

  @staticmethod
  def Args(parser):
    Init.CommonArgs(parser)

  def Run(self, args):
    """Executes when the user runs the init command."""
    project = properties.VALUES.core.project.Get(required=True)
    conn_context = connection_context.EventsConnectionContext(args)

    with eventflow_operations.Connect(conn_context) as client:
      operator.install_eventing_via_operator(client, self.ReleaseTrack())

      # Eventing has been installed and enabled, but not initialized yet.
      product_type = init_shared.determine_product_type(client,
                                                        args.authentication)

      if client.IsClusterInitialized(product_type):
        console_io.PromptContinue(
            message='This cluster has already been initialized.',
            prompt_string='Would you like to re-run initialization?',
            cancel_on_no=True)

      _EnableMissingServices(project)

      if args.authentication == events_constants.AUTH_SECRETS:
        # Create secrets for each Google service account and adds to cluster.
        gsa_emails = init_shared.construct_service_accounts(args, product_type)
        init_shared.initialize_eventing_secrets(client, gsa_emails,
                                                product_type)

      elif args.authentication == events_constants.AUTH_WI_GSA:
        # Bind controller and broker GSA to KSA via workload identity.
        gsa_emails = init_shared.construct_service_accounts(args, product_type)
        init_shared.initialize_workload_identity_gsa(client, gsa_emails)
      else:
        log.status.Print('Skipped initializing cluster.')

    log.status.Print(
        _InitializedMessage(self.ReleaseTrack(), conn_context.cluster_name,
                            args.authentication))


def _EnableMissingServices(project):
  """Enables any required services for the project."""
  enabled_services = set(
      service.config.name for service in
      serviceusage.ListServices(project, True, 100, None))
  missing_services = list(
      sorted(
          set(init_shared.CONTROL_PLANE_REQUIRED_SERVICES) - enabled_services))
  if not missing_services:
    return

  formatted_services = '\n'.join(['- {}'.format(s) for s in missing_services])
  init_shared.prompt_if_can_prompt(
      '\nThis will enable the following services:\n'
      '{}'.format(formatted_services))
  if len(missing_services) == 1:
    op = serviceusage.EnableApiCall(project, missing_services[0])
  else:
    op = serviceusage.BatchEnableApiCall(project, missing_services)
  if not op.done:
    op = services_util.WaitOperation(op.name, serviceusage.GetOperation)
  log.status.Print('Services successfully enabled.')


def _InitializedMessage(release_track, cluster_name, authentication):
  """Returns a string containing recommended next initialization steps."""
  command_prefix = 'gcloud '
  if release_track != base.ReleaseTrack.GA:
    command_prefix += release_track.prefix + ' '
  ns_init_command = command_prefix + (
      'kuberun core events init-namespace --authentication={}'.format(
          authentication))
  if authentication == events_constants.AUTH_SECRETS:
    ns_init_command += ' --copy-default-secret'
  brokers_create_command = command_prefix + ('kuberun core brokers create '
                                             'default')
  setup_commands = '`{}` and `{}`'.format(ns_init_command,
                                          brokers_create_command)

  return ('Initialized cluster [{}] for KubeRun eventing. '
          'Next, initialize the namespace(s) you plan to use and '
          'create a broker via {}.'.format(cluster_name, setup_commands))
