# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Command for setting usage buckets."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions


# TODO(b/33690890): remove after deprecation
class BucketRequiredError(exceptions.Error):
  """One of the required bucket flags was not specified."""


class SetUsageBucket(base_classes.NoOutputAsyncMutator):
  """Set the usage reporting bucket for a project."""

  @staticmethod
  def Args(parser):
    # TODO(b/33690890): add required=True for this group
    bucket_group = parser.add_mutually_exclusive_group()
    bucket_group.add_argument(
        '--no-bucket', action='store_true',
        help='Unsets the bucket. This disables usage report storage.')
    bucket = bucket_group.add_argument(
        '--bucket',
        nargs='?',
        action=arg_parsers.HandleNoArgAction(
            'no_bucket',
            'Use of --bucket without an argument is deprecated and will stop '
            'working in the future. To unset the bucket, please use '
            '--no-bucket'),
        help=('The URI of a Google Cloud Storage bucket where the usage report '
              'object should be stored'))
    bucket.detailed_help = """\
        The URI of a Google Cloud Storage bucket where the usage
        report object should be stored. The Google Service Account for
        performing usage reporting is granted write access to this bucket.
        The user running this command must be an owner of the bucket.

        To clear the usage bucket, use --no-bucket.
        """

    prefix = parser.add_argument(
        '--prefix',
        help='An optional prefix for the name of the usage report object.')
    prefix.detailed_help = """\
        An optional prefix for the name of the usage report object stored in
        the bucket. If not supplied, then this defaults to ``usage''. The
        report is stored as a CSV file named PREFIX_gce_YYYYMMDD.csv where
        YYYYMMDD is the day of the usage according to Pacific Time. The prefix
        should conform to Google Cloud Storage object naming conventions.
        This flag must not be provided when clearing the usage bucket.
        """

  @property
  def service(self):
    return self.compute.projects

  @property
  def method(self):
    return 'SetUsageExportBucket'

  @property
  def resource_type(self):
    return 'projects'

  def CreateRequests(self, args):
    # TODO(b/33690890): remove this check after the deprecation
    if args.bucket is None and not args.no_bucket:
      # The user gave neither flag but one of them is required. Using
      # required=True for the group would be the prefered way to handle this
      # but it would prevent the deprecated case.
      raise BucketRequiredError('one of the arguments --no-bucket --bucket '
                                'is required')

    if not args.bucket and args.prefix:
      raise calliope_exceptions.ToolException(
          '[--prefix] cannot be specified when unsetting the usage bucket.')

    bucket_uri = utils.NormalizeGoogleStorageUri(args.bucket or None)

    request = self.messages.ComputeProjectsSetUsageExportBucketRequest(
        project=self.project,
        usageExportLocation=self.messages.UsageExportLocation(
            bucketName=bucket_uri,
            reportNamePrefix=args.prefix,
        )
    )

    return [request]


SetUsageBucket.detailed_help = {
    'brief': 'Set the usage reporting bucket for a project',
    'DESCRIPTION': """\
        *{command}* is used to configure usage reporting for projects.

        Setting usage reporting will cause a log of usage per resource to be
        written to a specified Google Cloud Storage bucket daily. For example,

          $ gcloud compute project-info set-usage-bucket --bucket gs://my-bucket

        will cause logs of the form usage_gce_YYYYMMDD.csv to be written daily
        to the bucket `my-bucket`. To disable this feature, issue the command:

          $ gcloud compute project-info set-usage-bucket --no-bucket
        """,
}
