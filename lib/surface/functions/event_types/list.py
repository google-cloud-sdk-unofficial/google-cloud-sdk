# Copyright 2016 Google Inc. All Rights Reserved.
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
"""The event-types command subgroup for Google Cloud Functions.

'functions event-types list' command.
"""
import itertools

from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """Describes the allowed values and meanings of --trigger-* flags.

  Prints the table with list of all ways to deploy an event trigger. When using
  `gcloud functions deploy` Event Providers are specified as
  --trigger-provider and Event Types are specified as --trigger-event.
  The table includes the type of resource expected in
  --trigger-resource and which parameters --trigger-params takes and whether
  they are optional, required, or not-allowed. For EVENT_TYPE and RESOURCE_TYPE
  look at the column at right side to see if flag can be omitted.
  """

  def Format(self, args):
    return '''\
        table(provider.label:label="EVENT_PROVIDER":sort=1,
              label:label="EVENT_TYPE":sort=2,
              event_is_optional.yesno('Yes'):label="EVENT_TYPE_OPTIONAL",
              resource_type.value.name:label="RESOURCE_TYPE",
              resource_is_optional.yesno('Yes'):label="RESOURCE_OPTIONAL",
              args_spec_view.list():label="ARGS_SPEC"
        )'''

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Function call results (error or result with execution id)
    """
    return itertools.chain.from_iterable(
        p.events for p in util.trigger_provider_registry.providers)
