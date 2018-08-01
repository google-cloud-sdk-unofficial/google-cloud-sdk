# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Creates a Cloud Filestore instance."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.api_lib.filestore import filestore_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.filestore import flags
from googlecloudsdk.command_lib.filestore.instances import flags as instances_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log

import six


class Create(base.CreateCommand):
  """Create a Cloud Filestore instance.

  ## EXAMPLES

  The following command creates a Cloud Filestore instance named NAME with a
  single volume.

    $ {command} NAME --description=DESCRIPTION --tier=TIER
        --fileshare=name=VOLUME_NAME,capacity=CAPACITY
        --network=name=NETWORK_NAME,reserved-ip-range=RESERVED-IP-RANGE
  """

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([flags.GetInstancePresentationSpec(
        'The instance to create.')]).AddToParser(parser)
    instances_flags.AddDescriptionArg(parser)
    messages = filestore_util.GetMessages()
    instances_flags.GetTierArg(messages).choice_arg.AddToParser(parser)
    instances_flags.AddAsyncFlag(parser, 'create')
    instances_flags.AddFileshareArg(parser)
    instances_flags.AddNetworkArg(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    """Create a Cloud Filestore instance in the current project."""
    instance_ref = args.CONCEPTS.instance.Parse()
    messages = filestore_util.GetMessages()
    tier = instances_flags.GetTierArg(messages).GetEnumForChoice(args.tier)
    labels = labels_util.ParseCreateArgs(args,
                                         messages.Instance.LabelsValue)
    instance = filestore_util.ParseFilestoreConfig(
        tier=tier, description=args.description,
        file_share=args.file_share, network=args.network,
        labels=labels)
    client = filestore_client.FilestoreClient()
    try:
      client.ValidateFileshares(instance)
    except filestore_client.InvalidCapacityError as e:
      raise exceptions.InvalidArgumentException('--file-share',
                                                six.text_type(e))
    result = client.CreateInstance(instance_ref, args.async, instance)
    if args.async:
      log.status.Print(
          '\nCheck the status of the new instance by listing all instances:\n  '
          '$ gcloud alpha filestore instances list')
    return result
