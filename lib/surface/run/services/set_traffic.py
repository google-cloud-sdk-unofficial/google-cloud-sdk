# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for updating env vars and other configuration info."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.console import progress_tracker


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AdjustTraffic(base.Command):
  """Adjust the trafic assignments for a Cloud Run service."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To adjust the traffic assignments for myservice

              $ {command} myservice --to-revision=revis-name-1=10,revis-name-2=34 --to-latest=23`

         Sets 10% on revis-name1, 34% on revis-name-2, and 23% on the latest revision
         """,
  }

  @staticmethod
  def Args(parser):
    # Flags specific to CRoGKE
    gke_group = flags.GetGkeArgGroup(parser)
    concept_parsers.ConceptParser([resource_args.CLUSTER_PRESENTATION
                                  ]).AddToParser(gke_group)

    # Flags not specific to any platform
    service_presentation = presentation_specs.ResourcePresentationSpec(
        'SERVICE',
        resource_args.GetServiceResourceSpec(prompt=True),
        'Service to update the configuration of.',
        required=True,
        prefixes=False)
    flags.AddAsyncFlag(parser)
    flags.AddSetTrafficFlags(parser)
    concept_parsers.ConceptParser([service_presentation]).AddToParser(parser)
    flags.AddPlatformArg(parser)

  def Run(self, args):
    """Update the traffic split for the service.

    Args:
      args: Args!
    """
    conn_context = connection_context.GetConnectionContext(args)
    service_ref = flags.GetService(args)

    if conn_context.supports_one_platform:
      flags.VerifyOnePlatformFlags(args)
    else:
      flags.VerifyGKEFlags(args)

    changes = flags.GetConfigurationChanges(args)
    if not changes:
      raise exceptions.NoConfigurationChangeError(
          'No traffic configuration change requested.')

    with serverless_operations.Connect(conn_context) as client:
      deployment_stages = stages.SetTrafficStages()
      with progress_tracker.StagedProgressTracker(
          'Setting traffic...',
          deployment_stages,
          failure_message='Setting traffic failed',
          suppress_output=args.async) as tracker:
        client.SetTraffic(
            service_ref, changes, tracker, args.async, flags.IsManaged(args))
        if args.async:
          pretty_print.Success('Setting traffic asynchronously.')
        else:
          serv = client.GetService(service_ref)
          splits = ['{{bold}}{rev}{{reset}}={percent}'.format(
              rev='latest' if target.latestRevision else target.revisionName,
              percent=target.percent) for target in serv.spec.traffic]
          msg = 'Traffic set to %s.' % ', '.join(splits)

      pretty_print.Success(msg)
