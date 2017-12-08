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

"""The command to perform any necessary post installation steps."""

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.cache import exceptions as cache_exceptions
from googlecloudsdk.core.cache import resource_cache
from googlecloudsdk.core.updater import local_state


@base.Hidden
class PostProcess(base.SilentCommand):
  """Performs any necessary post installation steps."""

  @staticmethod
  def Args(parser):
    parser.add_argument('data', nargs='*', default='')

  def Run(self, args):
    # Delete the deprecated completion cache.
    resource_cache.DeleteDeprecatedCache()

    # Delete the completion cache.
    try:
      resource_cache.ResourceCache(create=False).Delete()
    except cache_exceptions.CacheNotFound:
      pass
    except cache_exceptions.Error as e:
      log.info('Unexpected resource cache error ignored: [%s].', e)

    # Re-compile python files.
    state = local_state.InstallationState.ForCurrent()
    state.CompilePythonFiles()
