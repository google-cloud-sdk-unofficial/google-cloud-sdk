#!/usr/bin/python

import os
import re
import sys
import shutil
import tempfile
import textwrap
import unittest

from gae_ext_runtime import testutil

RUNTIME_DEF_ROOT = os.path.dirname(os.path.dirname(__file__))


class RuntimeTests(testutil.TestBase):

    def setUp(self):
        self.runtime_def_root = RUNTIME_DEF_ROOT
        super(RuntimeTests, self).setUp()

    def read_dist_file(self, *args):
        """Read the entire contents of the file.

        Returns the entire contents of the file identified by a set of
        arguments forming a path relative to the root of the runtime
        definition.

        TODO: Move this down into the SDK.

        Args:
            *args: A set of path components (see full_path()).  Note that
                these are relative to the runtime definition root, not the
                temporary directory.
        """
        with open(os.path.join(self.runtime_def_root, *args)) as fp:
            return fp.read()

    def test_node_js_server_js_only(self):
        self.write_file('server.js', 'fake contents')
        cleaner = self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        cleaner = self.generate_configs(deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.read_dist_file('data', 'Dockerfile') + textwrap.dedent("""\
                COPY . /app/
                CMD node server.js
                """))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(cleaner.GetFiles(),
                        [self.full_path('Dockerfile'),
                         self.full_path('.dockerignore')])

    def test_node_js_package_json(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        cleaner = self.generate_configs(deploy=True)

        base_dockerfile = self.read_dist_file('data', 'Dockerfile')
        self.assert_file_exists_with_contents(
            'Dockerfile',
            base_dockerfile + 'COPY . /app/\n' +
            self.read_dist_file('data', 'package-json-install') +
            'CMD npm start\n')
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(cleaner.GetFiles(),
                         [self.full_path('Dockerfile'),
                          self.full_path('.dockerignore')])

    def test_node_js_with_engines(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json',
                        '{"scripts": {"start": "foo.js"},'
                        '"engines": {"node": "0.12.3"}}')
        self.generate_configs(deploy=True)
        dockerfile_path = self.full_path('Dockerfile')
        self.assertTrue(os.path.exists(dockerfile_path))

        # This just verifies that the crazy node install line is generated, it
        # says nothing about whether or not it works.
        rx = re.compile(r'RUN npm install')
        for line in open(dockerfile_path):
            if rx.match(line):
                break
        else:
            self.fail('node install line not generated')

    def test_node_js_custom_runtime(self):
        self.write_file('server.js', 'fake contents')
        cleaner = self.generate_configs(custom=True)
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='custom'))
        self.assertEqual(sorted(cleaner.GetFiles()),
                         [os.path.join(self.temp_path, '.dockerignore'),
                          os.path.join(self.temp_path, 'Dockerfile')])
        cleaner()
        self.assertEqual(sorted(os.listdir(self.temp_path)),
                         ['app.yaml', 'server.js'])

    def test_node_js_runtime_field(self):
        self.write_file('server.js', 'fake contents')
        config = testutil.AppInfoFake(runtime='nodejs')
        self.assertTrue(self.generate_configs(appinfo=config))

    def test_node_js_custom_runtime_field(self):
        self.write_file('server.js', 'fake contents')
        config = testutil.AppInfoFake(runtime='custom')
        self.assertTrue(self.generate_configs(appinfo=config))

    def test_invalid_package_json(self):
        self.write_file('package.json', '')
        self.write_file('server.js', '')
        self.generate_configs()
        self.assertFalse(self.generate_configs())


if __name__ == '__main__':
  unittest.main()


