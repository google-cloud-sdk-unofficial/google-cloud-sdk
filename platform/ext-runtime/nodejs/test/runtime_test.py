#!/usr/bin/python

import mock
import os
import re
import sys
import stat
import shutil
import tempfile
import textwrap
import unittest

from gae_ext_runtime import ext_runtime
from gae_ext_runtime import testutil

RUNTIME_DEF_ROOT = os.path.dirname(os.path.dirname(__file__))


class InjectExecutable(object):
    """A decorator whose constructor has a 'name' and a 'content' argument.

    The decorator is used to decorate a method used for testing where it:
    1. Updates the path so that executing a command with name 'name'
       invokes a Python script with the give Python code specified by
       the 'content' specified when constructing the decorator.
    2. Invoke the method used for testing.
    3. Restore the path to its original state and clean up any temporary
       files created.
    """

    def __init__(self, name, content):
        self.name = name
        self.content = content

    def __call__(self, func):
        def which(name):
            ext = '.exe' if sys.platform.lower() == 'win32' else ''
            for d in os.environ['PATH'].split(os.pathsep):
                fullpath = os.path.join(d, name + ext)
                if os.access(fullpath, os.X_OK):
                    return fullpath

            return None

        def modified_func(*args, **kwargs):
            python_path = which('python') or sys.executable

            base_dir = tempfile.mkdtemp()
            try:
                old_path = os.environ['PATH']
                os.environ['PATH'] = (base_dir + os.pathsep +
                                      os.path.dirname(python_path))

                is_windows = sys.platform.lower() == 'win32'

                runner_name = self.name + '.bat' if is_windows else self.name
                runner_path = os.path.join(base_dir, runner_name)

                exec_name = '_{0}.py'.format(runner_name)
                exec_path = os.path.join(base_dir, exec_name)

                runner_content = ('{0} {1} %*' if is_windows else
                                  '#!/bin/sh\n{0} {1} "$@"').format(
                                      python_path, exec_path)

                try:
                    with open(runner_path, 'w') as f:
                        f.write(runner_content)

                    os.chmod(runner_path,
                             stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)

                    content = textwrap.dedent(self.content).lstrip()

                    with open(exec_path, 'w') as f:
                        f.write(content)

                    func(*args, **kwargs)
                finally:
                    if os.path.exists(runner_path):
                        os.remove(runner_path)

                    if os.path.exists(exec_path):
                        os.remove(exec_path)

                    os.environ['PATH'] = old_path
            finally:
                if os.path.exists(base_dir):
                    shutil.rmtree(base_dir)

        return modified_func


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
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        self.generate_configs(deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.read_dist_file('data', 'Dockerfile') + textwrap.dedent("""\
                COPY . /app/
                CMD node server.js
                """))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'Dockerfile', '.dockerignore', 'app.yaml',
                          'server.js'})

    def test_node_js_server_js_only_no_write(self):
        """Test generate_config_data with only .js files.

        After running generate_configs(), app.yaml exists; after
        generate_config_data(), only app.yaml should exist on disk --
        Dockerfile and .dockerignore should be returned by the method."""
        self.write_file('server.js', 'fake contents')
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        cfg_files = self.generate_config_data(deploy=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.read_dist_file('data', 'Dockerfile') + textwrap.dedent("""\
                COPY . /app/
                CMD node server.js
                """))
        self.assert_genfile_exists_with_contents(
            cfg_files,
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'app.yaml', 'server.js'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_node_js_package_json_npm(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        self.generate_configs(deploy=True)

        base_dockerfile = self.read_dist_file('data', 'Dockerfile')
        self.assert_file_exists_with_contents(
            'Dockerfile',
            base_dockerfile + 'COPY . /app/\n' +
            self.read_dist_file('data', 'npm-package-json-install') +
            'CMD npm start\n')
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'Dockerfile', '.dockerignore', 'app.yaml',
                          'foo.js', 'package.json'})

    @InjectExecutable(name='yarn',
                      content='''
                          import sys
                          sys.exit(0)
                      ''')
    def test_node_js_package_json_yarn(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('yarn.lock', 'yarn overridden')

        self.generate_configs(deploy=True)

        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        base_dockerfile = self.read_dist_file('data', 'Dockerfile')
        install_yarn = self.read_dist_file('data', 'install-yarn')
        self.assert_file_exists_with_contents(
            'Dockerfile',
            base_dockerfile + install_yarn + 'COPY . /app/\n' +
            self.read_dist_file('data', 'yarn-package-json-install') +
            'CMD yarn start\n')
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'Dockerfile', '.dockerignore', 'app.yaml',
                          'foo.js', 'package.json', 'yarn.lock'})

    def test_node_js_package_json_no_write(self):
        """Test generate_config_data with a nodejs file and package.json."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        cfg_files = self.generate_config_data(deploy=True)

        base_dockerfile = self.read_dist_file('data', 'Dockerfile')
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            base_dockerfile + 'COPY . /app/\n' +
            self.read_dist_file('data', 'npm-package-json-install') +
            'CMD npm start\n')
        self.assert_genfile_exists_with_contents(
            cfg_files,
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'app.yaml', 'foo.js', 'package.json'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_detect_basic(self):
        """Ensure that appinfo will be generated in detect method."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        configurator = self.detect()
        self.assertEqual(configurator.generated_appinfo,
                         {u'runtime': 'nodejs',
                          u'env': 'flex'})

    def test_detect_custom(self):
        """Ensure that appinfo is correct with custom=True."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        configurator = self.detect(custom=True)
        self.assertEqual(configurator.generated_appinfo,
                         {'runtime': 'custom',
                          'env': 'flex'})

    def test_detect_no_start_no_server(self):
        """Ensure that detect fails if no scripts.start field, no server.js."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"not-start": "foo.js"}}')
        configurator = self.detect()
        self.assertEqual(configurator, None)

    def test_detect_no_start_with_server(self):
        """Ensure appinfo generated if no scripts.start, server.js exists."""
        self.write_file('server.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        configurator = self.detect()
        self.assertEqual(configurator.generated_appinfo,
                         {'runtime': 'nodejs',
                          'env': 'flex'})

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

    def test_node_js_with_engines_no_write(self):
        """Test generate_config_data with 'engines' in package.json."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json',
                        '{"scripts": {"start": "foo.js"},'
                        '"engines": {"node": "0.12.3"}}')
        cfg_files = self.generate_config_data(deploy=True)
        self.assertIn('Dockerfile', [f.filename for f in cfg_files])

        # This just verifies that the crazy node install line is generated, it
        # says nothing about whether or not it works.
        rx = re.compile(r'RUN npm install')
        line_generated = False
        for cfg_file in cfg_files:
            if cfg_file.filename == 'Dockerfile':
                for line in cfg_file.contents.split('\n'):
                    if rx.match(line):
                        line_generated = True
        if not line_generated:
            self.fail('node install line not generated')

    def test_node_js_custom_runtime(self):
        self.write_file('server.js', 'fake contents')
        self.generate_configs(custom=True)
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='custom'))
        self.assertEqual(sorted(os.listdir(self.temp_path)),
                         ['.dockerignore', 'Dockerfile', 'app.yaml',
                          'server.js'])

    def test_node_js_custom_runtime_no_write(self):
        """Test generate_config_data with custom runtime.

        Should generate an app.yaml on disk, the Dockerfile and
        .dockerignore in memory."""
        self.write_file('server.js', 'fake contents')
        cfg_files = self.generate_config_data(custom=True)
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='custom'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'app.yaml', 'server.js'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_node_js_runtime_field(self):
        self.write_file('server.js', 'fake contents')
        config = testutil.AppInfoFake(runtime='nodejs')
        self.generate_configs(appinfo=config, deploy=True)
        self.assertTrue(os.path.exists(self.full_path('Dockerfile')))

    def test_node_js_custom_runtime_field(self):
        self.write_file('server.js', 'fake contents')
        config = testutil.AppInfoFake(runtime='custom')
        self.assertTrue(self.generate_configs(appinfo=config, deploy=True))

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
        self.warnings = []

    def error_fake(self, message):
        self.errors.append(message)

    def debug_fake(self, message):
        self.debug.append(message)

    def warn_fake(self, message):
        self.warnings.append(message)

    def test_invalid_package_json(self):
        self.write_file('package.json', '')
        self.write_file('server.js', '')
        with mock.patch.dict(ext_runtime._LOG_FUNCS,
                             {'warn': self.warn_fake}):
            self.generate_configs()
        self.assertTrue(self.warnings[0].startswith(
            'node.js checker: error accessing package.json'))

        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs'),
        ]
        for appinfo, runtime in variations:
            self.warnings = []
            with mock.patch.dict(ext_runtime._LOG_FUNCS,
                                 {'warn': self.warn_fake}):
                self.generate_configs(appinfo=appinfo, runtime=runtime)

            self.assertTrue(self.warnings[0].startswith(
                'node.js checker: error accessing package.json'))

    def test_no_startup_script(self):
        with mock.patch.dict(ext_runtime._LOG_FUNCS,
                             {'debug': self.debug_fake}):
            self.generate_configs()
        print self.debug
        self.assertTrue(self.debug[1].startswith(
            'node.js checker: Neither "start" in the "scripts" section '
            'of "package.json" nor the "server.js" file were found.'))

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
                'node.js checker: Neither "start" in the "scripts" section '
                'of "package.json" nor the "server.js" file were found.'))

    @InjectExecutable(name='yarn',
                      content='''
                          import sys
                          sys.exit(0)
                      ''')
    def test_yarn_lock_not_readable(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('yarn.lock', 'yarn overridden')

        # ensure the yarn.lock file is not readable
        os.chmod(self.full_path('yarn.lock'), ~stat.S_IREAD)

        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs'),
        ]
        for appinfo, runtime in variations:
            self.errors = []
            with mock.patch.dict(ext_runtime._LOG_FUNCS,
                                 {'error': self.error_fake}):
                self.generate_configs(appinfo=appinfo, runtime=runtime)

            self.assertTrue(
                self.errors[0].startswith(
                    'Yarn checker: "yarn.lock" exists, indicating Yarn '
                    'should be used, but Yarn cannot run since "yarn.lock" '
                    'is not readable.'))

    @InjectExecutable(name='yarn',
                      content='''
                          import sys
                          sys.exit(1)
                      ''')
    def test_no_yarn(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('yarn.lock', 'yarn overridden')

        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs'),
        ]
        for appinfo, runtime in variations:
            self.errors = []
            with mock.patch.dict(ext_runtime._LOG_FUNCS,
                                 {'error': self.error_fake}):
                self.generate_configs(appinfo=appinfo, runtime=runtime)

            self.assertTrue(
                self.errors[0].startswith(
                    'Yarn checker: "yarn.lock" was found indicating Yarn '
                    'is being used, but "yarn" could not be run.'))

    @InjectExecutable(name='yarn',
                      content='''
                          import sys
                          if sys.argv[1] == '--version':
                              sys.exit(1)
                          else:
                              sys.exit(0)
                      ''')
    def test_yarn_identification_fails(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('yarn.lock', 'yarn overridden')

        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs'),
        ]
        for appinfo, runtime in variations:
            self.errors = []
            with mock.patch.dict(ext_runtime._LOG_FUNCS,
                                 {'error': self.error_fake}):
                self.generate_configs(appinfo=appinfo, runtime=runtime)
            self.assertTrue(
                self.errors[0].startswith(
                    'Yarn checker: "yarn.lock" was found indicating Yarn '
                    'is being used, but "yarn" could not be run.'))

    @InjectExecutable(name='yarn',
                      content='''
                          import os

                          # Remove the yarn script so that the first
                          # invocation of 'yarn' with arguments '--version'
                          # succeeds, but the second invocation with arguments
                          # 'check' will fail.
                          os.remove(__file__)
                      ''')
    def _impl_test_yarn_check_invalid_yarn_lock(self, appinfo, runtime):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('yarn.lock', 'yarn overridden')

        self.errors = []
        with mock.patch.dict(ext_runtime._LOG_FUNCS,
                             {'error': self.error_fake}):
            self.generate_configs(appinfo=appinfo, runtime=runtime)
        self.assertTrue(
            self.errors[0].startswith(
                'Yarn checker: "yarn.lock" was found indicating Yarn '
                'is being used, but "yarn check" indicates '
                '"yarn.lock" is invalid.'))

    def test_yarn_check_invalid_yarn_lock(self):
        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs'),
        ]
        for appinfo, runtime in variations:
            self._impl_test_yarn_check_invalid_yarn_lock(appinfo, runtime)

if __name__ == '__main__':
  unittest.main()
