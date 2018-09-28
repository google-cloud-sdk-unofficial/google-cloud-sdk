# -*- coding: utf-8 -*- #
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

"""A command that generates and/or updates help document directoriess."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import walker_util
from googlecloudsdk.command_lib.meta import help_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import pkg_resources


class HelpOutOfDateError(exceptions.Error):
  """Help documents out of date for --test."""


_HELP_HTML_DATA_FILES = [
    'favicon.ico',
    'index.html',
    '_menu_.css',
    '_menu_.js',
    '_title_.html',
]


def WriteHtmlMenu(command, out):
  """Writes the command menu tree HTML on out.

  Args:
    command: dict, The tree (nested dict) of command/group names.
    out: stream, The output stream.
  """

  def ConvertPathToIdentifier(path):
    return '_'.join(path)

  def WalkCommandTree(command, prefix):
    """Visit each command and group in the CLI command tree.

    Args:
      command: dict, The tree (nested dict) of command/group names.
      prefix: [str], The subcommand arg prefix.
    """
    level = len(prefix)
    visibility = 'visible' if level <= 1 else 'hidden'
    indent = level * 2 + 2
    name = command.get('_name_')
    args = prefix + [name]
    out.write('{indent}<li class="{visibility}" id="{item}" '
              'onclick="select(event, this.id)">{name}'.format(
                  indent=' ' * indent, visibility=visibility, name=name,
                  item=ConvertPathToIdentifier(args)))
    commands = command.get('commands', []) + command.get('groups', [])
    if commands:
      out.write('<ul>\n')
      for c in sorted(commands, key=lambda x: x['_name_']):
        WalkCommandTree(c, args)
      out.write('{indent}</ul>\n'.format(indent=' ' * (indent + 1)))
      out.write('{indent}</li>\n'.format(indent=' ' * indent))
    else:
      out.write('</li>\n'.format(indent=' ' * (indent + 1)))

  out.write("""\
<html>
<head>
<meta name="description" content="man page tree navigation">
<meta name="generator" content="gcloud meta generate-help-docs --html-dir=.">
<title> man page tree navigation </title>
<base href="." target="_blank">
<link rel="stylesheet" type="text/css" href="_menu_.css">
<script type="text/javascript" src="_menu_.js"></script>
</head>
<body>

<div class="menu">
 <ul>
""")
  WalkCommandTree(command, [])
  out.write("""\
 </ul>
</div>

</body>
</html>
""")


class GenerateHelpDocs(base.Command):
  """Generate and/or update help document directories.

  The DevSite docs are generated in the --devsite-dir directory with pathnames
  in the reference directory hierarchy. The manpage docs are generated in the
  --manpage-dir directory with pathnames in the manN/ directory hierarchy.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--hidden',
        action='store_true',
        default=None,
        help=('Include documents for hidden commands and groups.'))
    parser.add_argument(
        '--devsite-dir',
        metavar='DIRECTORY',
        help=('The directory where the generated DevSite reference document '
              'subtree will be written. If not specified then DevSite '
              'documents will not be generated.'))
    parser.add_argument(
        '--help-text-dir',
        metavar='DIRECTORY',
        help=('The directory where the generated help text reference document '
              'subtree will be written. If not specified then help text '
              'documents will not be generated.'))
    parser.add_argument(
        '--html-dir',
        metavar='DIRECTORY',
        help=('The directory where the standalone manpage HTML files will be '
              'generated. index.html contains manpage tree navigation in the '
              'left pane. The active command branch and its immediate children '
              'are visible and clickable. Hover to navigate the tree. Run '
              '`python -m SimpleHTTPServer 8888 &` in DIRECTORY and point '
              'your browser at [](http://localhost:8888) to view the manpage '
              'tree. If not specified then the HTML manpage site will not be '
              'generated.'))
    parser.add_argument(
        '--manpage-dir',
        metavar='DIRECTORY',
        help=('The directory where the generated manpage document subtree will '
              'be written. The manpage hierarchy is flat with all command '
              'documents in the manN/ subdirectory. If not specified then '
              'manpage documents will not be generated.'))
    parser.add_argument(
        '--test',
        action='store_true',
        help=('Show but do not apply --update actions. Exit with non-zero exit '
              'status if any help document file must be updated.'))
    parser.add_argument(
        '--update',
        action='store_true',
        help=('Update destination directories to match the current CLI. '
              'Documents for commands not present in the current CLI will be '
              'deleted. Use this flag to update the help text golden files '
              'after the help_text_test test fails.'))
    parser.add_argument(
        '--update-help-text-dir',
        hidden=True,
        metavar='DIRECTORY',
        help='Deprecated. Use --update --help-text-dir=DIRECTORY instead.')
    parser.add_argument(
        'restrict',
        metavar='COMMAND/GROUP',
        nargs='*',
        default=None,
        help=('Restrict document generation to these dotted command paths. '
              'For example: gcloud.alpha gcloud.beta.test'))

  def Run(self, args):
    out_of_date = set()

    def Generate(kind, generator, directory, encoding='utf8'):
      """Runs generator and optionally updates help docs in directory."""
      console_attr.ResetConsoleAttr(encoding)
      if not args.update:
        generator(self._cli_power_users_only, directory).Walk(
            args.hidden, args.restrict)
      elif help_util.HelpUpdater(
          self._cli_power_users_only, directory, generator,
          test=args.test).Update(args.restrict):
        out_of_date.add(kind)

    def GenerateHtmlNav(directory):
      """Generates html nav files in directory."""
      tree = walker_util.CommandTreeGenerator(
          self._cli_power_users_only).Walk(args.hidden, args.restrict)
      with files.FileWriter(os.path.join(directory, '_menu_.html')) as out:
        WriteHtmlMenu(tree, out)
      for file_name in _HELP_HTML_DATA_FILES:
        file_contents = pkg_resources.GetResource(
            'googlecloudsdk.api_lib.meta.help_html_data.', file_name)
        files.WriteBinaryFileContents(os.path.join(directory, file_name),
                                      file_contents)

    # Handle deprecated flags -- probably burned in a bunch of eng scripts.

    if args.update_help_text_dir:
      log.warning('[--update-help-text-dir={directory}] is deprecated. Use '
                  'this instead: --update --help-text-dir={directory}.'.format(
                      directory=args.update_help_text_dir))
      args.help_text_dir = args.update_help_text_dir
      args.update = True

    # Generate/update the destination document directories.

    if args.devsite_dir:
      Generate('DevSite', walker_util.DevSiteGenerator, args.devsite_dir)
    if args.help_text_dir:
      Generate('help text', walker_util.HelpTextGenerator, args.help_text_dir,
               'ascii')
    if args.html_dir:
      Generate('html', walker_util.HtmlGenerator, args.html_dir)
      GenerateHtmlNav(args.html_dir)
    if args.manpage_dir:
      Generate('man page', walker_util.ManPageGenerator, args.manpage_dir)

    # Test update fails with an exception if documents are out of date.

    if out_of_date and args.test:
      names = sorted(out_of_date)
      if len(names) > 1:
        kinds = ' and '.join([', '.join(names[:-1]), names[-1]])
      else:
        kinds = names[0]
      raise HelpOutOfDateError(
          '{} document files must be updated.'.format(kinds))
