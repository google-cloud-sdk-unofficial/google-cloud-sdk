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

"""The `app instances list` command."""

from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.calliope import base


# pylint: disable=invalid-name
AppEngineInstance = instances_util.AppEngineInstance


class List(base.ListCommand):
  """List the instances affiliated with the current App Engine project."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To list all App Engine instances, run:

              $ {command}

          To list all App Engine instances for a given service, run:

              $ {command} -s myservice

          To list all App Engine instances for a given version, run:

              $ {command} -v v1
          """,
  }

  def Collection(self):
    return 'app.instances'

  @staticmethod
  def Args(parser):
    parser.add_argument('--service', '-s',
                        help=('If specified, only list instances belonging to '
                              'the given service.'))
    parser.add_argument('--version', '-v',
                        help=('If specified, only list instances belonging to '
                              'the given version.'))

  def Run(self, args):
    # `--user-output-enabled=false` needed to prevent Display method from
    # consuming returned generator, and also to prevent this command from
    # causing confusing output
    all_instances = self.cli.Execute(['compute', 'instances', 'list',
                                      '--user-output-enabled', 'false'])
    app_engine_instances = []
    for instance in all_instances:
      if AppEngineInstance.IsInstance(instance):
        gae_instance = AppEngineInstance.FromComputeEngineInstance(instance)
        app_engine_instances.append(gae_instance)
    return instances_util.FilterInstances(app_engine_instances, args.service,
                                          args.version)
