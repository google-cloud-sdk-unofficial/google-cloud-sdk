#!/usr/bin/python

import mock
import os
import re
import sys
import shutil
import tempfile
import textwrap
import unittest

from gae_ext_runtime import ext_runtime
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

    # Tests that verify that the generated files match verbatim output.
    # These will need to be maintained whenever the code generation changes,
    # but this ensures that any diffs we introduce in the generate files will
    # be reviewed.

    def test_node_js_with_engines_retroactive(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json',
                        '{"scripts": {"start": "foo.js"},'
                        '"engines": {"node": "0.12.3"}}')
        self.generate_configs(deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            textwrap.dedent("""\
                # Dockerfile extending the generic Node image with application files for a
                # single application.
                FROM gcr.io/google_appengine/nodejs
                # Check to see if the the version included in the base runtime satisfies
                # 0.12.3, if not then do an npm install of the latest available
                # version that satisfies it.
                RUN /usr/local/bin/install_node 0.12.3
                COPY . /app/
                # You have to specify "--unsafe-perm" with npm install
                # when running as root.  Failing to do this can cause
                # install to appear to succeed even if a preinstall
                # script fails, and may have other adverse consequences
                # as well.
                # This command will also cat the npm-debug.log file after the
                # build, if it exists.
                RUN npm install --unsafe-perm || \\
                  ((if [ -f npm-debug.log ]; then \\
                      cat npm-debug.log; \\
                    fi) && false)
                CMD npm start
                """))


class FailureLoggingTests(testutil.TestBase):

    def setUp(self):
        self.runtime_def_root = RUNTIME_DEF_ROOT
        super(FailureLoggingTests, self).setUp()

        self.errors = []
        self.debug = []

    def error_fake(self, message):
        self.errors.append(message)

    def debug_fake(self, message):
        self.debug.append(message)

    def test_invalid_package_json(self):
        self.write_file('package.json', '')
        self.write_file('server.js', '')
        with mock.patch.dict(ext_runtime._LOG_FUNCS,
                             {'debug': self.debug_fake}):
            self.generate_configs()
        self.assertTrue(self.debug[0].startswith(
            'node.js checker: error accesssing package.json'))

        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs'),
        ]
        for appinfo, runtime in variations:
            self.errors = []
            with mock.patch.dict(ext_runtime._LOG_FUNCS,
                                 {'error': self.error_fake}):
                self.generate_configs(appinfo=appinfo, runtime=runtime)

            self.assertTrue(self.errors[0].startswith(
                'node.js checker: error accesssing package.json'))

    def test_no_startup_script(self):
        with mock.patch.dict(ext_runtime._LOG_FUNCS,
                             {'debug': self.debug_fake}):
            self.generate_configs()
        print self.debug
        self.assertTrue(self.debug[1].startswith(
            'node.js checker: No npm start and no server.js'))

        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs'),
        ]
        for appinfo, runtime in variations:
            self.errors = []
            with mock.patch.dict(ext_runtime._LOG_FUNCS,
                                 {'error': self.error_fake}):
                self.generate_configs(appinfo=appinfo, runtime=runtime)
            self.assertTrue(self.errors[0].startswith(
                'node.js checker: No npm start and no server.js'))


if __name__ == '__main__':
  unittest.main()


