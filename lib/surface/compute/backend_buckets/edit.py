# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for modifying backend buckets."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.backend_buckets import flags as backend_buckets_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EditAlpha(base_classes.BaseEdit):
  """Modify backend buckets."""

  @staticmethod
  def Args(parser):
    base_classes.BaseEdit.Args(parser)
    backend_buckets_flags.BACKEND_BUCKET_ARG.AddArgument(parser)

  @property
  def service(self):
    return self.compute.backendBuckets

  @property
  def resource_type(self):
    return 'backendBuckets'

  @property
  def example_resource(self):
    uri_prefix = ('https://www.googleapis.com/compute/alpha/projects/'
                  'my-project/')

    return self.messages.BackendBucket(
        bucketName='gcs-bucket-1',
        description='My backend bucket',
        name='backend-bucket',
        selfLink=uri_prefix + 'global/backendBuckets/backend-bucket',
    )

  def CreateReference(self, args):
    return backend_buckets_flags.BACKEND_BUCKET_ARG.ResolveAsResource(
        args, self.resources,
        default_scope=flags.ScopeEnum.GLOBAL)

  @property
  def reference_normalizers(self):
    return []

  def GetGetRequest(self, args):
    return (
        self.service,
        'Get',
        self.messages.ComputeBackendBucketsGetRequest(
            project=self.project,
            backendBucket=self.ref.Name()))

  def GetSetRequest(self, args, replacement, _):
    return (
        self.service,
        'Update',
        self.messages.ComputeBackendBucketsUpdateRequest(
            project=self.project,
            backendBucket=self.ref.Name(),
            backendBucketResource=replacement))


EditAlpha.detailed_help = {
    'brief': 'Modify backend buckets',
    'DESCRIPTION': """\
        *{command}* can be used to modify a backend bucket. The backend
        bucket resource is fetched from the server and presented in a text
        editor. After the file is saved and closed, this command will
        update the resource. Only fields that can be modified are
        displayed in the editor.

        The editor used to modify the resource is chosen by inspecting
        the ``EDITOR'' environment variable.
        """,
}
