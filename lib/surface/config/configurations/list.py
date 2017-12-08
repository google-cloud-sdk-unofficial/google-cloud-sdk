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

"""Command to list named configuration."""

from googlecloudsdk.calliope import base
from googlecloudsdk.core import named_configs
from googlecloudsdk.core.console import console_io


class List(base.Command):
  """Lists existing named configurations."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          Run `$ gcloud topic configurations` for an overview of named
          configurations.
          """,
      'EXAMPLES': """\
          To list all available configurations, run:

            $ {command}
          """,
  }

  def Run(self, args):
    configs = named_configs.ListNamedConfigs(log_warnings=True)
    return configs

  def Display(self, _, resources):
    # Custom selector to format configs as a table
    selectors = (('NAME', lambda x: x.name),
                 ('IS_ACTIVE', lambda x: x.is_active))
    console_io.PrintExtendedList(resources, selectors)
