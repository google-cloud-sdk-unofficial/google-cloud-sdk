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
"""Command for adding project-wide metadata."""

from googlecloudsdk.api_lib.compute import base_classes


class AddMetadata(base_classes.ProjectMetadataMutatorMixin,
                  base_classes.BaseMetadataAdder):
  """Add or update project-wide metadata."""

  @staticmethod
  def Args(parser):
    base_classes.BaseMetadataAdder.Args(parser)


AddMetadata.detailed_help = {
    'brief': 'Add or update project-wide metadata',
    'DESCRIPTION': """\
        *{command}* can be used to add or update project-wide
        metadata. Every instance has access to a metadata server that
        can be used to query metadata that has been set through this
        tool. Project-wide metadata entries are visible to all
        instances. To set metadata for individual instances, use
        `gcloud compute instances add-metadata`. For information on
        metadata, see
        [](https://cloud.google.com/compute/docs/metadata)

        Only metadata keys that are provided are mutated. Existing
        metadata entries will remain unaffected.
        """,
}
