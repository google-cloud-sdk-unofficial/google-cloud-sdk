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

"""A command that generates all DevSite and manpage documents."""

import os

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import walker_util
from googlecloudsdk.core.util import pkg_resources


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
  """Generate all DevSite and man page help docs.

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
              'be written. If not specified then manpage documents will not be '
              'generated.'))
    parser.add_argument(
        'restrict',
        metavar='COMMAND/GROUP',
        nargs='*',
        default=None,
        help=('Restrict document generation to these dotted command paths. '
              'For example: gcloud.alpha gcloud.beta.test'))

  def Run(self, args):
    if args.devsite_dir:
      walker_util.DevSiteGenerator(self.cli, args.devsite_dir).Walk(
          args.hidden, args.restrict)
    if args.html_dir:
      walker_util.HtmlGenerator(
          self.cli, args.html_dir).Walk(args.hidden, args.restrict)
      tree = walker_util.CommandTreeGenerator(
          self.cli).Walk(args.hidden, args.restrict)
      with open(os.path.join(args.html_dir, '_menu_.html'), 'w') as out:
        WriteHtmlMenu(tree, out)
      for file_name in _HELP_HTML_DATA_FILES:
        with open(os.path.join(args.html_dir, file_name), 'wb') as out:
          file_contents = pkg_resources.GetResource(
              'googlecloudsdk.api_lib.meta.help_html_data.', file_name)
          out.write(file_contents)
    if args.manpage_dir:
      walker_util.ManPageGenerator(
          self.cli, args.manpage_dir).Walk(args.hidden, args.restrict)
