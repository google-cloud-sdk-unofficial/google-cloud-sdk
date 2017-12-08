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

"""Command for removing a path matcher from a URL map."""

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.url_maps import flags


class RemovePathMatcher(base_classes.ReadWriteCommand):
  """Remove a path matcher from a URL map."""

  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

    parser.add_argument(
        '--path-matcher-name',
        required=True,
        help='The name of the path matcher to remove.')

  @property
  def service(self):
    return self.compute.urlMaps

  @property
  def resource_type(self):
    return 'urlMaps'

  def CreateReference(self, args):
    return self.URL_MAP_ARG.ResolveAsResource(args, self.resources)

  def GetGetRequest(self, args):
    """Returns the request for the existing URL map resource."""
    return (self.service,
            'Get',
            self.messages.ComputeUrlMapsGetRequest(
                urlMap=self.ref.Name(),
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    return (self.service,
            'Update',
            self.messages.ComputeUrlMapsUpdateRequest(
                urlMap=self.ref.Name(),
                urlMapResource=replacement,
                project=self.project))

  def Modify(self, args, existing):
    """Returns a modified URL map message."""
    replacement = copy.deepcopy(existing)

    # Removes the path matcher.
    new_path_matchers = []
    path_matcher_found = False
    for path_matcher in existing.pathMatchers:
      if path_matcher.name == args.path_matcher_name:
        path_matcher_found = True
      else:
        new_path_matchers.append(path_matcher)

    if not path_matcher_found:
      raise exceptions.ToolException(
          'No path matcher with the name [{0}] was found.'.format(
              args.path_matcher_name))

    replacement.pathMatchers = new_path_matchers

    # Removes all host rules that refer to the path matcher.
    new_host_rules = []
    for host_rule in existing.hostRules:
      if host_rule.pathMatcher != args.path_matcher_name:
        new_host_rules.append(host_rule)
    replacement.hostRules = new_host_rules

    return replacement


RemovePathMatcher.detailed_help = {
    'DESCRIPTION': """\
        *{command}* is used to remove a path matcher from a URL
         map. When a path matcher is removed, all host rules that
         refer to the path matcher are also removed.
        """,
    'EXAMPLES': """\
        To remove the path matcher named ``MY-MATCHER'' from the URL map named
        ``MY-URL-MAP'', you can use this command:

          $ {command} MY-URL-MAP --path-matcher MY-MATCHER
        """,
}
