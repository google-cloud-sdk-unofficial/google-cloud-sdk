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

"""Base template using which the apis_map.py is generated."""


class APIDef(object):
  """Struct for info required to instantiate clients/messages for API versions.

  Attributes:
    client_classpath: str, Path to the client class for an API version.
    messages_modulepath: str, Path to the messages module for an API version.
    default_version: bool, Whether this API version is the default version for
    the API.
  """

  def __init__(self,
               client_classpath,
               messages_modulepath,
               default_version=False):
    self.client_classpath = client_classpath
    self.messages_modulepath = messages_modulepath
    self.default_version = default_version

  def __eq__(self, other):
    return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

  def __ne__(self, other):
    return not self.__eq__(other)

  def get_init_source(self):
    src_fmt = 'APIDef("{0}", "{1}", {2})'
    return src_fmt.format(self.client_classpath, self.messages_modulepath,
                          self.default_version)

  def __repr__(self):
    return self.get_init_source()
