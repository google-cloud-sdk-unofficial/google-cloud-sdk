# Copyright 2017 Google Inc. All Rights Reserved.
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

"""The meta cache completers list command."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import walker
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import pkg_resources


class CompleterModule(object):

  def __init__(self, module_path, collection, api_version):
    self.module_path = module_path
    self.collection = collection
    self.api_version = api_version
    self.attachments = []
    self._attachments_dict = {}


class CompleterAttachment(object):

  def __init__(self, command):
    self.command = command
    self.arguments = []


class CompleterModuleGenerator(walker.Walker):
  """Constructs a CLI command dict tree."""

  def __init__(self, cli):
    super(CompleterModuleGenerator, self).__init__(cli)
    self._modules_dict = {}

  def Visit(self, command, parent, is_group):
    """Visits each command in the CLI command tree to construct the module list.

    Args:
      command: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if command is a group, otherwise its is a command.

    Returns:
      The subtree module list.
    """
    args = command.ai
    for arg in sorted(args.flag_args + args.positional_args):
      try:
        completer_class = arg.completer
      except AttributeError:
        continue
      if isinstance(completer_class, type):
        module_path = pkg_resources.GetModulePath(completer_class)
        completer = completer_class()
        try:
          collection = completer.collection
        except AttributeError:
          collection = None
        try:
          api_version = completer.api_version
        except AttributeError:
          api_version = None
        if arg.option_strings:
          name = arg.option_strings[0]
        else:
          name = arg.dest.replace('_', '-')
        module = self._modules_dict.get(module_path)
        if not module:
          module = CompleterModule(
              collection=collection,
              api_version=api_version,
              module_path=module_path,
          )
          self._modules_dict[module_path] = module
        command_path = ' '.join(command.GetPath())
        # pylint: disable=protected-access
        attachment = module._attachments_dict.get(command_path)
        if not attachment:
          attachment = CompleterAttachment(command_path)
          module._attachments_dict[command_path] = attachment
          module.attachments.append(attachment)
        attachment.arguments.append(name)
    return self._modules_dict


class List(base.ListCommand):
  """List all Cloud SDK command argument completer objects.

  Cloud SDK command argument completers are objects that have a module path,
  collection name and API version.  The module path may be used as the
  _MODULE_PATH_ argument to the $ gcloud meta cache completers run command.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
       table[box](module_path,
                  collection,
                  api_version,
                  attachments:format="table[box](
                     command:sort=1,
                     arguments.list())")
    """)

  def Run(self, args):
    if not args.IsSpecified('sort_by'):
      args.sort_by = ['module_path', 'collection', 'api_version']
    with progress_tracker.ProgressTracker(
        'Collecting attached completers from all command flags and arguments'):
      return CompleterModuleGenerator(
          self._cli_power_users_only).Walk().values()
