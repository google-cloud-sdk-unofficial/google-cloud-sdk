# Copyright 2013 Google Inc. All Rights Reserved.
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

"""The gcloud datastore group."""
from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'brief': 'Manage your Cloud Datastore indexes.',
    'DESCRIPTION': """
This set of commands allows you to create and delete datastore indexes.
      """,
    'EXAMPLES': """\
          To create new indexes from a file, run:

            $ {command} create-indexes index.yaml

          To clean up unused indexes from a file, run:

            $ {command} cleanup-indexes index.yaml
          """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Datastore(base.Group):
  detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.PREVIEW)
@base.Deprecate(
    is_removed=False,
    warning='This is now available in GA and preview has been deprecated. '
            'Please use the `gcloud datastore` commands instead.')
class DatastorePreview(base.Group):
  detailed_help = DETAILED_HELP
