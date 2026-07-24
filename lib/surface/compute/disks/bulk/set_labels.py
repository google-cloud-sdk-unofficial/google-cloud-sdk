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
"""Command for setting labels on multiple disks at once."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks.bulk import util as bulk_util
from googlecloudsdk.core import properties

_DETAILED_HELP = {
    'brief': 'Add or remove labels on multiple Compute Engine disks.',
    'DESCRIPTION': (
        """\
        *{command}* allows you to add or remove labels on multiple Compute
        Engine disks in a single zone. Labels are key-value pairs that help you
        organize your Google Cloud resources.

        You can specify the disks and their labels in two ways:

        1.  By providing a JSON file using the `--source` flag. Each request in
            the JSON list must specify the disk `name` and `labels`, and may
            optionally include `label_fingerprint` for optimistic concurrency
            control.

        2.  By providing a list of disk names using the `--disks` flag and the
            labels to apply using the `--labels` flag.
        """
    ),
    'EXAMPLES': (
        """\
        To set the labels `env=production` and `team=sre` on `disk-1` and
        `disk-2` in zone `us-central1-a`, run:

        $ {command} \\
            --zone=us-central1-a \\
            --disks=disk-1,disk-2 \\
            --labels=env=production,team=sre

        To clear all labels on `disk-3` and `disk-4` in zone `europe-west1-b`
        provide an empty value to --labels, run:

        $ {command} \\
            --zone=europe-west1-b \\
            --disks=disk-3,disk-4 \\
            --labels=''

        To set labels based on a JSON file named `disk_labels.json`, run:

        Example `disk_labels.json` content:
        ```json
        [
          {
            "name": "disk-1",
            "labels": { "env": "production", "team": "sre" },
            "label_fingerprint": "42WmSpB8rSM="
          },
          {
            "name": "disk-2",
            "labels": { "env": "production", "team": "sre" }
          }
        ]
        ```

        $ {command} \\
            --zone=us-central1-a \\
            --source=disk_labels.json
        ```

        To clear all labels on `disk-3` and `disk-4` in zone `europe-west1-b`
        provide an empty labels value in the JSON file, run:

        Example `disk_labels.json` content:
        ```json
        [
          {
            "name": "disk-3",
            "labels": {}
          },
          {
            "name": "disk-4",
            "labels": {}
          }
        ]
        ```

        $ {command} \\
            --zone=europe-west1-b \\
            --source=disk_labels.json
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
    base.ReleaseTrack.PREVIEW,
)
class SetLabels(base.Command):
  """Sets the labels on many disks at once."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddZoneFlag(
        parser, resource_type='disk', operation_type='update labels'
    )

    mutex_group = parser.add_mutually_exclusive_group(required=True)
    mutex_group.add_argument(
        '--source',
        help=(
            'Path to a JSON file containing a list of disk label update'
            ' requests. Each request object must specify "name" and "labels",'
            ' and may optionally include "label_fingerprint".'
        ),
    )

    flag_group = mutex_group.add_group(required=False)
    flag_group.add_argument(
        '--disks',
        type=arg_parsers.ArgList(),
        metavar='DISK_NAME',
        help='Comma-separated list of disk names to update.',
        required=True,
    )
    flag_group.add_argument(
        '--labels',
        type=arg_parsers.ArgDict(),
        metavar='KEY=VALUE',
        help='List of label KEY=VALUE pairs to set on all specified disks.',
        required=True,
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    project = properties.VALUES.core.project.GetOrFail()
    zone = (
        args.zone
        if args.IsSpecified('zone')
        else properties.VALUES.compute.zone.GetOrFail()
    )

    if args.source:
      requests_data = bulk_util.ReadDataFromFile(args.source)

      bulk_util.ValidateSourceDataOuter(requests_data)
      bulk_util.ValidateSourceDataInner(requests_data)
    else:
      requests_data = []

      for disk in args.disks:
        requests_data.append({'name': disk, 'labels': args.labels or {}})

    requests = bulk_util.FormRequests(messages, requests_data)

    request = (
        client.apitools_client.disks,
        'BulkSetLabels',
        messages.ComputeDisksBulkSetLabelsRequest(
            project=project,
            zone=zone,
            bulkZoneSetLabelsRequest=messages.BulkZoneSetLabelsRequest(
                requests=requests
            ),
        ),
    )

    return bulk_util.FromResponse(
        requests=requests,
        responses=client.MakeRequests([request], no_followup=True),
    )
