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

"""Submit a PySpark notebook batch job."""

from typing import Any

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc.batches import batch_submitter
from googlecloudsdk.command_lib.dataproc.batches import pyspark_notebook_batch_factory


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
@base.Hidden
class PySparkNotebook(base.Command):
  """Submit a PySpark notebook batch job."""
  detailed_help = {
      'EXAMPLES':
          """\
          To submit a PySpark notebook batch job called "my-batch" that runs "my-pyspark-notebook.ipynb", run:
          $ {command} my-pyspark-notebook.ipynb --batch=my-batch --deps-bucket=gs://my-bucket --region=us-central1 --param=input-path=gs://my-bucket/input --param=city=London --param=country=UK
          """
  }

  @staticmethod
  def Args(parser):
    pyspark_notebook_batch_factory.AddArguments(parser)

  def Run(self, args: Any) -> Any:
    dataproc = dp.Dataproc(self.ReleaseTrack())
    notebook_batch = pyspark_notebook_batch_factory.PySparkNotebookBatchFactory(
        dataproc).UploadLocalFilesAndGetMessage(args)

    return batch_submitter.Submit(notebook_batch, dataproc, args)
