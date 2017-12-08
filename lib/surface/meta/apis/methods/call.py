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

"""A command that describes a registered gcloud API."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Call(base.Command):
  """Calls an API method with specific parameters."""

  @staticmethod
  def Args(parser):
    # TODO(b/38000796): Add a placeholder arg for the dynamic args that get
    # added.
    apis.API_VERSION_FLAG.AddToParser(parser)
    apis.COLLECTION_FLAG.AddToParser(parser)

    parser.AddDynamicPositional(
        'method',
        action=apis.MethodDynamicPositionalAction,
        help='The name of the API method to invoke.')

  def Run(self, args):
    properties.VALUES.core.enable_gri.Set(True)

    method = apis.GetMethod(args.collection, args.method,
                            api_version=args.api_version, no_http=False)
    request_class = method.GetRequestType()

    # TODO(b/38000796): Move all this into an argparse Action.
    # Parse the resource based on the positional arg and the flags for its
    # flat_path parameters.
    # Start by adding in all the applicable default parameters.
    params = method.GetDefaultParams()
    # Add in any resource fields explicitly provided by flags.
    resource_flags = {f: getattr(args, f) for f in method.ResourceFieldNames()}
    params.update({f: v for f, v in resource_flags.iteritems()
                   if v is not None})
    # TODO(b/38000796): Make sure everything has a collection or have a mode
    # where a collection is not required.
    ref = resources.REGISTRY.Parse(
        args.resource,
        collection=method.RequestCollection().full_name,
        params=params)

    # Add all the message fields specified by flags.
    kwargs = {f: getattr(args, f) for f in method.RequestFieldNames()}
    # For each actual method path field, add the attribute to the request.
    kwargs.update({f: getattr(ref, f) for f in method.params})

    # TODO(b/38000796): Should have special handling for list requests to do
    # paging automatically.
    response = method.Call(request_class(**kwargs))
    return response
