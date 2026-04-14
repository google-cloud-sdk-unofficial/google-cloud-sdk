# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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

"""Factory class for PySparkNotebookBatch message."""

from typing import Any

from apitools.base.py import encoding
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc import local_file_uploader


class PySparkNotebookBatchFactory(object):
  """Factory class for PySparkNotebookBatch message."""

  def __init__(self, dataproc):
    """Initialize the factory.

    Args:
      dataproc: A Dataproc instance.
    """
    self.dataproc = dataproc

  def UploadLocalFilesAndGetMessage(self, args: Any) -> Any:
    """upload user local files and create a PySparkNotebookBatch message.

    Upload user local files and point URIs to the local files to the uploaded
    URIs.
    Creates a PySparkNotebookBatch message from parsed arguments.

    Args:
      args: Parsed arguments.

    Returns:
      PySparkNotebookBatch: A PySparkNotebookBatch message.

    Raises:
      AttributeError: Bucket is required to upload local files, but not
      specified.
    """
    kwargs = {}

    # Merge repeated --param k=v flags into a single map for the proto.
    params = {}
    if args.param:
      for param_dict in args.param:
        params.update(param_dict)
    if params:
      kwargs['params'] = encoding.DictToAdditionalPropertyMessage(
          params, self.dataproc.messages.PySparkNotebookBatch.ParamsValue,
          sort_items=True)

    # Stage local files to Cloud Storage.
    dependencies = {}
    dependencies['notebookFileUri'] = [args.NOTEBOOK_FILE]

    if args.py_files:
      dependencies['pythonFileUris'] = args.py_files
    if args.jars:
      dependencies['jarFileUris'] = args.jars
    if args.files:
      dependencies['fileUris'] = args.files
    if args.archives:
      dependencies['archiveUris'] = args.archives

    if local_file_uploader.HasLocalFiles(dependencies):
      if not args.deps_bucket:
        raise AttributeError('--deps-bucket was not specified.')
      dependencies = local_file_uploader.Upload(args.deps_bucket, dependencies)

    # Build the final message with resolved Cloud Storage URIs.
    kwargs['notebookFileUri'] = dependencies.pop('notebookFileUri')[0]

    # Merges pythonFileUris, jarFileUris, etc. if they exist.
    # Old python versions don't support multi unpacking of dictionaries.
    kwargs.update(dependencies)

    return self.dataproc.messages.PySparkNotebookBatch(**kwargs)


def AddArguments(parser: Any) -> None:
  """Adds notebook-specific arguments to the parser.

  Args:
    parser: A parser to add arguments to.
  """
  parser.add_argument(
      'NOTEBOOK_FILE',
      help='The HCFS URI of the notebook file to execute.')
  parser.add_argument(
      '--param',
      type=arg_parsers.ArgDict(),
      action='append',
      metavar='PARAM=VALUE',
      help='Parameters to pass to the notebook for parameterization '
           '(papermill). This flag can be repeated.')
  flags.AddPythonFiles(parser)
  flags.AddJarFiles(parser)
  flags.AddOtherFiles(parser)
  flags.AddArchives(parser)
  # Cloud Storage bucket to upload workload dependencies.
  # It is required until we figure out a place to upload user files.
  parser.add_argument(
      '--deps-bucket',
      help='A Cloud Storage bucket to upload workload dependencies.')

