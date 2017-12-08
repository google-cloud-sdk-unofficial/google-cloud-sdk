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

"""Tests for the generator.py script."""

import os
import textwrap

from googlecloudsdk.core import apis as core_apis
from googlecloudsdk.core.util import files
from tests.lib import test_case
from googlecloudsdk.third_party.apis import apis_map
from tools.regen_apis import api_def
from tools.regen_apis import regen
import yaml


class ApiMapGeneratorTest(test_case.Base):

  def testGetAPIsMap(self):
    config = yaml.loads(textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
            default: True
          v2:
            discovery: organge_v2.json
        banana:
          v2beta:
            discovery: banana_v2beta.json
          v2_staging:
            version: v2
            discovery: banana_v2_staging.json
            default: True
        pear:
          v7_test:
            discovery: pear_v7_test.json
    """))
    expected_map = {
        'orange': {
            'v1': api_def.APIDef(
                'fruits.orange.v1.orange_v1_client.OrangeV1',
                'fruits.orange.v1.orange_v1_messages', True),
            'v2': api_def.APIDef(
                'fruits.orange.v2.orange_v2_client.OrangeV2',
                'fruits.orange.v2.orange_v2_messages')
        },
        'banana': {
            'v2beta': api_def.APIDef(
                'fruits.banana.v2beta.banana_v2beta_client.BananaV2beta',
                'fruits.banana.v2beta.banana_v2beta_messages'),
            'v2_staging': api_def.APIDef(
                'fruits.banana.v2_staging.banana_v2_client.BananaV2',
                'fruits.banana.v2_staging.banana_v2_messages', True)
        },
        'pear': {
            'v7_test': api_def.APIDef(
                'fruits.pear.v7_test.pear_v7_test_client.PearV7Test',
                'fruits.pear.v7_test.pear_v7_test_messages', True)
        }
    }
    actual_map = regen._MakeApiMap('fruits', config)
    self.assertEquals(expected_map, actual_map)

  def testGetAPIsMapMultipleDefaultsClientsForAPI(self):
    config = yaml.loads(textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
            default: True
          v2:
            discovery: organge_v2.json
            default: True
    """))

    with self.assertRaises(Exception) as ctx:
      regen._MakeApiMap('fruits', config)

    msg = str(ctx.exception)
    self.assertEquals(msg, 'Multiple default client versions found for [pear]!')

  def testGetAPIsMapNoDefaultsClientsForAPIs(self):
    config = yaml.loads(textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
          v2:
            discovery: organge_v2.json
    """))

    with self.assertRaises(Exception) as ctx:
      regen._MakeApiMap('fruits', config)

    msg = str(ctx.exception)
    self.assertEquals(msg, 'No default client versions found for [fig, lime]!')

  def testCreateAPIsMapFile(self):
    config = yaml.loads(textwrap.dedent("""\
        orange:
          v1:
            discovery: organge_v1.json
            default: True
          v2:
            discovery: organge_v2.json
        banana:
          v2beta:
            discovery: banana_v2beta.json
          v2_staging:
            version: v2
            discovery: banana_v2_staging.json
            default: True
        pear:
          v7_test:
            discovery: pear_v7_test.json
    """))

    with files.TemporaryDirectory() as tmp_dir:
      regen.GenerateApiMap(tmp_dir, 'fruits', config)
      content = self.GetFileContent(os.path.join(tmp_dir, 'api_map.py'))

    self.assertEquals(
        self.GetFileContent(os.path.join(os.path.dirname(__file__),
                                         'testdata', 'api_map_sample.txt')),
        content)

  def testSanityOfGeneratedApisMap(self):
    for api_name, ver_map in apis_map.MAP.iteritems():
      for ver, api_definition in ver_map.iteritems():
        self.assertEquals(api_definition, core_apis._GetApiDef(api_name, ver))


if __name__ == '__main__':
  test_case.main()
