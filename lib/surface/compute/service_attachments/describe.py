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
"""Command for describing a service attachment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.service_attachments import flags


def _DetailedHelp():
  return {
      'EXAMPLES':
          """\
          To describe a service attachment, run:

              $ {command} SERVICE_ATTACHMENT_NAME --region=us-central1"""
  }


def _Run(args, holder, service_attachment_arg, support_show_nat_ips=False):
  """Issues requests necessary to describe a service attachment."""
  service_attachment_ref = service_attachment_arg.ResolveAsResource(
      args, holder.resources, default_scope=compute_scope.ScopeEnum.REGION
  )
  client = holder.client
  request = client.messages.ComputeServiceAttachmentsGetRequest(
      **service_attachment_ref.AsDict())
  if support_show_nat_ips and args.show_nat_ips is not None:
    request.showNatIps = args.show_nat_ips
  collection = client.apitools_client.serviceAttachments

  return client.MakeRequests([(collection, 'Get', request)])[0]


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Display details about a Google Compute Engine service attachment."""

  SERVICE_ATTACHMENT_ARG = None
  detailed_help = _DetailedHelp()
  _support_show_nat_ips = False

  @classmethod
  def Args(cls, parser):
    cls.SERVICE_ATTACHMENT_ARG = flags.ServiceAttachmentArgument()
    cls.SERVICE_ATTACHMENT_ARG.AddArgument(parser, operation_type='describe')
    if cls._support_show_nat_ips:
      flags.AddShowNatIpsFlag(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(
        args, holder, self.SERVICE_ATTACHMENT_ARG, self._support_show_nat_ips
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):
  """Display details about a Google Compute Engine service attachment."""

  _support_show_nat_ips = True
