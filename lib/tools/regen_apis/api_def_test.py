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

"""Unit tests for template.py."""

from tests.lib import test_case
from tools.regen_apis import api_def


class ApisMapTemplateTest(test_case.Base):

  def testAPIDefRepr(self):
    api_definition = api_def.APIDef(
        'fruits.orange.v1.orange_v1_client.OrangeV1',
        'fruits.orange.v1.orange_v1_messages', True)

    expected_repr = ('APIDef("fruits.orange.v1.orange_v1_client.OrangeV1", '
                     '"fruits.orange.v1.orange_v1_messages", True)')

    self.assertEquals(expected_repr, str(api_definition))


if __name__ == '__main__':
  test_case.main()
