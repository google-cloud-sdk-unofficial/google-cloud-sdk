# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command to enroll a new scope."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.audit_manager import enrollments
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.audit_manager import exception_utils
from googlecloudsdk.command_lib.audit_manager import flags

_DETAILED_HELP = {
    'DESCRIPTION': 'Enroll a new scope.',
    'EXAMPLES': """ \
        To enroll a project with ID 123 in the us-central1 region, run:

        $ {command} --project=123 --location=us-central1 --eligible-gcs-buckets "gs://my-bucket-1,gs://my-bucket-2"
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Add(base.CreateCommand):
  """Enroll a new scope."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddProjectOrFolderFlags(parser, 'to enroll')
    flags.AddLocationFlag(parser, 'to enroll')
    flags.AddEligibleDestinationsFlags(parser)

  def Run(self, args):
    """Run the generate command."""
    is_parent_folder = args.folder is not None

    scope = (
        'folders/{folder}'.format(folder=args.folder)
        if is_parent_folder
        else 'projects/{project}'.format(project=args.project)
    )

    scope += '/locations/{location}'.format(location=args.location)

    client = enrollments.EnrollmentsClient()
    try:
      return client.Add(
          scope,
          eligible_gcs_buckets=args.eligible_gcs_buckets,
          is_parent_folder=is_parent_folder,
      )

    except apitools_exceptions.HttpNotFoundError as e:
      details = exception_utils.ExtractErrorDetails(e)
      if (
          details['reason']
          == exception_utils.ERROR_REASON_NO_ORGANISATION_FOUND
      ):
        raise exceptions.HttpException(
            e,
            error_format=(
                'No corresponding oganization found for the given resource.'
            ),
        )
