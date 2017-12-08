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
"""Command for removing project-wide metadata."""

from googlecloudsdk.api_lib.compute import base_classes


class RemoveMetadata(base_classes.ProjectMetadataMutatorMixin,
                     base_classes.BaseMetadataRemover):
  """Remove project-wide metadata entries."""

  @staticmethod
  def Args(parser):
    base_classes.BaseMetadataRemover.Args(parser)


RemoveMetadata.detailed_help = {
    'brief': 'Remove project-wide metadata entries',
    'DESCRIPTION': """\
        *{command}* can be used to remove project-wide metadata entries.
        """,
}
