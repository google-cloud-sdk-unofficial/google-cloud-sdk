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

"""Service Registry endpoints sub-group."""

from googlecloudsdk.calliope import base


class Endpoints(base.Group):
  # pylint: disable=line-too-long
  """Commands for Service Registry endpoints.

  Commands to create, update, delete, and examine Service Registry entries.

  Service Registry is currently released as v1alpha. In order to use it,
  please request access through this form:
  [](https://docs.google.com/forms/d/11SfJGB3LUGgT_aSMlVzWoJ0ec2fHKwk0J4e-zTNw0Bs)
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To print out a list of endpoints with some summary information about each

            $ {command} list

          To display information about an endpoint

            $ {command} describe ENDPOINT_NAME

          To create a new endpoint

            $ {command} my_endpoint --target my_service.my_domain:8080
                --networks NETWORK_URL

          More commands and options can be found with

            $ {command} --help
          """,
  }
