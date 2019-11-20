# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for running a local development environment."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import signal
import subprocess
import sys
import tempfile

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.local import flags
from googlecloudsdk.command_lib.local import local_files
from googlecloudsdk.command_lib.local import minikube
import six

CLUSTER_NAME = 'gcloud-local-dev'


def _EmptyHandler(unused_signum, unused_stack):
  """Do nothing signal handler."""
  pass


class _SigInterruptedHandler(object):
  """Context manager to capture CTRL-C and send it to a handler."""

  def __init__(self, handler):
    self._orig_handler = None
    self._handler = handler

  def __enter__(self):
    self._orig_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, self._handler)

  def __exit__(self, exc_type, exc_value, tb):
    signal.signal(signal.SIGINT, self._orig_handler)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Dev(base.Command):
  """Run a service in a development environemnt."""

  @classmethod
  def Args(cls, parser):
    flags.CommonFlags(parser)

  def Run(self, args):
    local_file_generator = local_files.LocalRuntimeFiles.FromArgs(args)

    with tempfile.NamedTemporaryFile(mode='w+t') as kubernetes_config, \
         tempfile.NamedTemporaryFile(mode='w+t') as skaffold_config:
      kubernetes_config.write(six.u(local_file_generator.KubernetesConfig()))
      kubernetes_config.flush()
      skaffold_config.write(
          six.u(local_file_generator.SkaffoldConfig(kubernetes_config.name)))
      skaffold_config.flush()

      with minikube.Minikube(CLUSTER_NAME):
        self._RunSkaffold(skaffold_config.name)

  def _RunSkaffold(self, skaffold_config):
    # TODO(b/143302920): Point to the skaffold installed by gcloud when that
    # is ready.
    cmd = [
        'skaffold', 'dev', '-f', skaffold_config, '--port-forward',
        '--kube-context', CLUSTER_NAME
    ]

    # Supress the current Ctrl-C handler and pass the signal to the child
    # process.
    with _SigInterruptedHandler(_EmptyHandler):
      try:
        p = subprocess.Popen(cmd)
        p.wait()
      except KeyboardInterrupt:
        p.terminate()
        p.wait()

    sys.stdout.flush()
    sys.stderr.flush()
