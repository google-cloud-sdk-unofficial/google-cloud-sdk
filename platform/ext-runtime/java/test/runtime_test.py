#!/usr/bin/python
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

"""Tests of the java runtime."""

import logging
import mock
import os
import re
import sys
import shutil
import tempfile
import textwrap
import unittest

from gae_ext_runtime import testutil
from gae_ext_runtime import ext_runtime

# Augment the path with our library directory.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(os.path.join(ROOT_DIR, 'lib'))

import constants

#from googlecloudsdk.third_party.appengine.api import appinfo
#from googlecloudsdk.core import log
#from googlecloudsdk.api_lib.app import ext_runtime
#from googlecloudsdk.api_lib.app.runtimes import fingerprinter
#from googlecloudsdk.api_lib.app.ext_runtimes import fingerprinting

RUNTIME_DEF_ROOT = os.path.dirname(os.path.dirname(__file__))


class RuntimeTests(testutil.TestBase):

    def setUp(self):
        self.runtime_def_root = RUNTIME_DEF_ROOT
        super(RuntimeTests, self).setUp()

    def assert_no_file(self, *path):
        self.assertFalse(os.path.exists(self.full_path(*path)))

    def make_app_yaml(self, runtime):
        return self.read_runtime_def_file('data', 'app.yaml.template').format(
            runtime=runtime)

    def test_java_all_defaults(self):
        self.write_file('foo.jar', '')

        self.generate_configs()

        self.assert_file_exists_with_contents('app.yaml',
                                              self.make_app_yaml('java'))
        self.assert_no_file('Dockerfile')
        self.assert_no_file('.dockerignore')

        cleaner = self.generate_configs(deploy=True)

        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))
        dockerfile_contents = [
            constants.DOCKERFILE_JAVA8_PREAMBLE,
            constants.DOCKERFILE_INSTALL_APP.format('foo.jar'),
            constants.DOCKERFILE_JAVA8_ENTRYPOINT.format('foo.jar'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                              ''.join(dockerfile_contents))

        # Verify cleanup. TODO(ludo): refactor this and do it for all tests.
        cleaner()
        self.assertEqual(
            sorted(os.listdir(self.temp_path)), ['app.yaml', 'foo.jar'])

    def test_java_custom(self):
        self.write_file('foo.jar', '')
        self.generate_configs(deploy=False, custom=True)

        self.assert_file_exists_with_contents('app.yaml',
                                              self.make_app_yaml('custom'))

        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))
        dockerfile_contents = [
            constants.DOCKERFILE_JAVA8_PREAMBLE,
            constants.DOCKERFILE_INSTALL_APP.format('foo.jar'),
            constants.DOCKERFILE_JAVA8_ENTRYPOINT.format('foo.jar'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                              ''.join(dockerfile_contents))

    def test_java_files_no_java(self):
        self.write_file('foo.nojava', '')
        self.assertIsNone(self.generate_configs())

    def test_java_files_with_war(self):
        self.write_file('foo.war', '')

        self.generate_configs()
        self.assert_file_exists_with_contents('app.yaml',
                                              self.make_app_yaml('java'))
        self.assert_no_file('Dockerfile')
        self.assert_no_file('.dockerignore')

        self.generate_configs(deploy=True)
        dockerfile_contents = [
            constants.DOCKERFILE_JETTY9_PREAMBLE,
            constants.DOCKERFILE_INSTALL_WAR.format('foo.war'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                            ''.join(dockerfile_contents))
        self.assert_file_exists_with_contents(
            '.dockerignore', self.read_runtime_def_file('data', 'dockerignore'))

    def test_java_files_with_jar(self):
        self.write_file('foo.jar', '')

        self.generate_configs()
        self.assert_file_exists_with_contents('app.yaml',
                                              self.make_app_yaml('java'))
        self.assert_no_file('Dockerfile')
        self.assert_no_file('.dockerignore')

        self.generate_configs(deploy=True)
        dockerfile_contents = [
            constants.DOCKERFILE_JAVA8_PREAMBLE,
            constants.DOCKERFILE_INSTALL_APP.format('foo.jar'),
            constants.DOCKERFILE_JAVA8_ENTRYPOINT.format('foo.jar'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                              ''.join(dockerfile_contents))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))

    def testJavaFilesWithWebInf(self):
        self.write_file('WEB-INF', '')

        self.generate_configs()
        self.assert_file_exists_with_contents('app.yaml',
                                              self.make_app_yaml('java'))
        self.assert_no_file('Dockerfile')
        self.assert_no_file('.dockerignore')

        self.generate_configs(deploy=True)
        dockerfile_contents = [
            constants.DOCKERFILE_LEGACY_PREAMBLE,
            constants.DOCKERFILE_INSTALL_APP.format('.'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                              ''.join(dockerfile_contents))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))

    def test_java_files_with_too_many_artifacts(self):
        self.write_file('WEB-INF', '')
        self.write_file('foo.jar', '')

        errors = []

        def ErrorFake(message):
          errors.append(message)

        with mock.patch.dict(ext_runtime._LOG_FUNCS, {'error': ErrorFake}):
            self.assertEqual(self.generate_configs(), None)

        self.assertEqual(errors,
                         ['Too many java artifacts to deploy (.jar, .war, or '
                          'Java Web App).'])

    # TODO(ludo) cover the case were the app.yaml might not be called app.yaml.
    # For example: "gen-config --config=foo.yaml <path>" will use foo.yaml
    def test_java_files_with_war_and_yaml(self):
        self.write_file('foo.war', '')
        appinfo = testutil.AppInfoFake(
            runtime='java',
            env='2',
            runtime_config=dict(
                jdk='openjdk8',
                server='jetty9'))
        self.generate_configs(appinfo=appinfo, deploy=True)
        dockerfile_contents = [
            constants.DOCKERFILE_JETTY9_PREAMBLE,
            constants.DOCKERFILE_INSTALL_WAR.format('foo.war'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                              ''.join(dockerfile_contents))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))

    def test_java_files_with_web_inf_and_yaml_and_env2(self):
        self.write_file('WEB-INF', '')
        config = testutil.AppInfoFake(
            runtime='java',
            env='2',
            runtime_config=dict(
              jdk='openjdk8',
              server='jetty9'))
        self.generate_configs(appinfo=config, deploy=True)
        dockerfile_contents = [
            constants.DOCKERFILE_COMPAT_PREAMBLE,
            constants.DOCKERFILE_INSTALL_APP.format('.'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                              ''.join(dockerfile_contents))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))

    def test_java_files_with_web_inf_and_yaml_and_no_env2(self):
        self.write_file('WEB-INF', '')
        config = testutil.AppInfoFake(
            runtime='java',
            vm=True,
            runtime_config=dict(server='jetty9'))
        self.generate_configs(appinfo=config, deploy=True)
        dockerfile_contents = [
            constants.DOCKERFILE_LEGACY_PREAMBLE,
            constants.DOCKERFILE_INSTALL_APP.format('.'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                              ''.join(dockerfile_contents))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))

    def test_java_files_with_web_inf_and_yaml_and_open_jdk8_no_env2(self):
        self.write_file('WEB-INF', '')
        config = testutil.AppInfoFake(
            runtime='java',
            vm=True,
            runtime_config=dict(
                jdk='openjdk8',
                server='jetty9'))
        self.generate_configs(appinfo=config, deploy=True)
        dockerfile_contents = [
            constants.DOCKERFILE_COMPAT_PREAMBLE,
            constants.DOCKERFILE_INSTALL_APP.format('.'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                              ''.join(dockerfile_contents))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))

    def test_java_files_with_config_error(self):
        self.write_file('foo.war', '')

        errors = []

        def ErrorFake(message):
          errors.append(message)

        config = testutil.AppInfoFake(
            runtime='java',
            env='2',
            runtime_config=dict(
                jdk='openjdk9'))
        with mock.patch.dict(ext_runtime._LOG_FUNCS, {'error': ErrorFake}):
            self.assertIsNone(
                self.generate_configs(appinfo=config, deploy=True))
        self.assertEqual(errors, ['Unknown JDK : openjdk9.'])

    def test_java_custom_runtime_field(self):
        self.write_file('foo.jar', '')
        config = testutil.AppInfoFake(
            runtime='java',
            env='2')
        self.assertTrue(self.generate_configs(appinfo=config))

    def test_java7_runtime(self):
        self.write_file('WEB-INF', '')
        config = testutil.AppInfoFake(
            runtime='java7',
            vm=True)
        self.generate_configs(appinfo=config, deploy=True)
        dockerfile_contents = [
            constants.DOCKERFILE_LEGACY_PREAMBLE,
            constants.DOCKERFILE_INSTALL_APP.format('.'),
        ]
        self.assert_file_exists_with_contents('Dockerfile',
                                              ''.join(dockerfile_contents))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))


if __name__ == '__main__':
  unittest.main()


