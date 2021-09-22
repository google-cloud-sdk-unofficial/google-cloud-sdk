# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Enable a personal auth session on a cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import hashlib
import json
import os
import subprocess
import tempfile
import time

# TODO(b/173821917): Once the Cloud SDK supports pytype, uncomment the
# following lines and then replace all of the un-annotated method signatures
# with their corresponding typed signatures that are commented out above them.
#
# import argparse
# from typing import Any, IO, List

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import retry

import six


# def _inject_encrypted_credentials(dataproc: dp.Dataproc, project: str,
#                                   region: str, cluster_name: str,
#                                   cluster_uuid: str,
#                                   credentials_ciphertext: str) -> Any:
def _inject_encrypted_credentials(dataproc, project, region, cluster_name,
                                  cluster_uuid, credentials_ciphertext):
  """Inject credentials into the given cluster.

  The credentials must have already been encrypted before calling this method.

  Args:
    dataproc: The API client for calling into the Dataproc API.
    project: The project containing the cluster.
    region: The region where the cluster is located.
    cluster_name: The name of the cluster.
    cluster_uuid: The cluster UUID assigned by the Dataproc control plane.
    credentials_ciphertext: The (already encrypted) credentials to inject.

  Returns:
    An operation resource for the credential injection.
  """
  inject_credentials_request = dataproc.messages.InjectCredentialsRequest(
      clusterUuid=cluster_uuid, credentialsCiphertext=credentials_ciphertext)
  request = dataproc.messages.DataprocProjectsRegionsClustersInjectCredentialsRequest(
      project='projects/' + project,
      region='regions/' + region,
      cluster='clusters/' + cluster_name,
      injectCredentialsRequest=inject_credentials_request)
  return dataproc.client.projects_regions_clusters.InjectCredentials(request)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class EnablePersonalAuthSession(base.Command):
  """Enable a personal auth session on a cluster."""

  detailed_help = {
      'EXAMPLES':
          """
          To enable a personal auth session, run:

            $ {command} my_cluster --region=us-central1
          """,
  }

  # def Args(cls, parser: argparse.ArgumentParser):
  @classmethod
  def Args(cls, parser):
    """Method called by Calliope to register flags for this command.

    Args:
      parser: An argparser parser used to register flags.
    """
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddClusterResourceArg(parser, 'enable a personal auth session on',
                                dataproc.api_version)
    flags.AddPersonalAuthSessionArgs(parser)

  # def run_openssl_command(cls, openssl_executable: str, args: List[str],
  #                         stdin: IO[Any] = None) -> bytes:
  @classmethod
  def run_openssl_command(cls, openssl_executable, args, stdin=None):
    """Run the specified command, capturing and returning output as appropriate.

    Args:
      openssl_executable: The path to the openssl executable.
      args: The arguments to the openssl command to run.
      stdin: The input to the command.

    Returns:
      The output of the command.

    Raises:
      PersonalAuthError: If the call to openssl fails
    """
    command = [openssl_executable]
    command.extend(args)
    stderr = None
    try:
      if getattr(subprocess, 'run', None):
        proc = subprocess.run(
            command,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False)
        stderr = proc.stderr.decode('utf-8').strip()
        # N.B. It would be better if we could simply call `subprocess.run` with
        # the `check` keyword arg set to true rather than manually calling
        # `check_returncode`. However, we want to capture the stderr when the
        # command fails, and the CalledProcessError type did not have a field
        # for the stderr until Python version 3.5.
        #
        # As such, we need to manually call `check_returncode` as long as we
        # are supporting Python versions prior to 3.5.
        proc.check_returncode()
        return proc.stdout
      else:
        p = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, _ = p.communicate(input=stdin)
        return stdout
    except Exception as ex:
      if stderr:
        log.error('OpenSSL command "%s" failed with error message "%s"',
                  ' '.join(command), stderr)
      raise exceptions.PersonalAuthError('Failure running openssl command: "' +
                                         ' '.join(command) + '": ' +
                                         six.text_type(ex))

  def compute_hmac(self, key, data, openssl_executable):
    cmd_output = self.run_openssl_command(
        openssl_executable, ['dgst', '-hmac', key], stdin=data).decode('utf-8')
    # Drop the "(stdin)= " prefix that openssl appends to output.
    stripped_output = cmd_output[9:]
    return stripped_output.encode('utf-8')

  def derive_hkdf_key(self, prk, info, openssl_executable):
    base16_prk = base64.b16encode(prk).decode('utf-8')
    t0 = self.compute_hmac(base16_prk, b'', openssl_executable)
    t1data = bytearray(t0)
    t1data.extend(info)
    t1data.extend(b'\x01')
    return self.compute_hmac(base16_prk, t1data, openssl_executable)

  # It is possible (although very rare) for the random pad generated by
  # openssl to not be usable by openssl for encrypting the secret. When
  # that happens the call to openssl will raise a CalledProcessError with
  # the message "Error reading password from BIO\nError getting password".
  #
  # To account for this we retry on that error, but this is so rare that
  # a single retry should be sufficient.
  #
  # def encode_token_using_openssl(self, cluster_public_key: str,
  #                                secret: str, openssl_executable: str) -> str:
  @retry.RetryOnException(max_retrials=1)
  def encode_token_using_openssl(self, cluster_public_key, secret,
                                 openssl_executable):
    cluster_key_hash = hashlib.sha256(
        (cluster_public_key + '\n').encode('utf-8')).hexdigest()
    iv_bytes = base64.b16encode(os.urandom(16))
    initialization_vector = iv_bytes.decode('utf-8')
    pad = os.urandom(32)
    encryption_pad = self.derive_hkdf_key(pad, 'encryption_key'.encode('utf-8'),
                                          openssl_executable)
    auth_pad = base64.b16encode(
        self.derive_hkdf_key(pad, 'auth_key'.encode('utf-8'),
                             openssl_executable)).decode('utf-8')
    with tempfile.NamedTemporaryFile() as kf:
      kf.write(cluster_public_key.encode('utf-8'))
      kf.seek(0)
      encrypted_pad = self.run_openssl_command(
          openssl_executable,
          ['rsautl', '-oaep', '-encrypt', '-pubin', '-inkey', kf.name],
          stdin=base64.b64encode(pad))
    encoded_pad = base64.b64encode(encrypted_pad).decode('utf-8')

    with tempfile.NamedTemporaryFile() as pf:
      pf.write(encryption_pad)
      pf.seek(0)
      encrypt_args = [
          'enc', '-aes-256-ctr', '-salt', '-iv', initialization_vector, '-pass',
          'file:{}'.format(pf.name)
      ]
      encrypted_token = self.run_openssl_command(
          openssl_executable, encrypt_args, stdin=secret.encode('utf-8'))
    encoded_token = base64.b64encode(encrypted_token).decode('utf-8')

    hmac_input = bytearray(iv_bytes)
    hmac_input.extend(encrypted_token)
    hmac_tag = self.compute_hmac(auth_pad, hmac_input,
                                 openssl_executable).decode('utf-8')[0:32]
    return '{}:{}:{}:{}:{}'.format(cluster_key_hash, encoded_token, encoded_pad,
                                   initialization_vector, hmac_tag)

  def is_tink_library_installed(self):
    try:
      # pylint: disable=g-import-not-at-top
      # pylint: disable=unused-import
      import tink
      from tink import hybrid
      from tink import cleartext_keyset_handle
      # pylint: enable=g-import-not-at-top
      # pylint: enable=unused-import
      return True
    except ImportError:
      return False

  # def encrypt_with_cluster_key(self, cluster_public_key: str,
  #                              secret: str, openssl_executable: str) -> str:
  def encrypt_with_cluster_key(self, cluster_public_key, secret,
                               openssl_executable):
    if openssl_executable:
      return self.encode_token_using_openssl(cluster_public_key, secret,
                                             openssl_executable)
    try:
      # pylint: disable=g-import-not-at-top
      import tink
      from tink import hybrid
      from tink import cleartext_keyset_handle
      # pylint: enable=g-import-not-at-top
    except ImportError:
      raise exceptions.PersonalAuthError(
          'Cannot load the Tink cryptography library. Either the '
          'library is not installed, or site packages are not '
          'enabled for the Google Cloud SDK. Please consult Cloud '
          'Dataproc Personal Auth documentation on adding Tink to '
          'Google Cloud SDK for further instructions.\n'
          'https://cloud.google.com/dataproc/docs/concepts/iam/personal-auth')

    hybrid.register()
    context = b''

    # Extract value of key corresponding to primary key.
    public_key_value = json.loads(
        cluster_public_key)['key'][0]['keyData']['value']
    cluster_key_hash = hashlib.sha256(
        (public_key_value + '\n').encode('utf-8')).hexdigest()

    # Load public key and create keyset handle.
    reader = tink.JsonKeysetReader(cluster_public_key)
    kh_pub = cleartext_keyset_handle.read(reader)

    # Create encrypter instance.
    encrypter = kh_pub.primitive(hybrid.HybridEncrypt)
    ciphertext = encrypter.encrypt(secret.encode('utf-8'), context)

    encoded_token = base64.b64encode(ciphertext).decode('utf-8')
    return '{}:{}'.format(cluster_key_hash, encoded_token)

  # def inject_credentials(
  #     self, dataproc: dp.Dataproc, project: str, region: str,
  #     cluster_name: str, cluster_uuid: str, access_boundary_json: str,
  #     operation_poller: waiter.CloudOperationPollerNoResources),
  #     openssl_executable: str:
  def inject_credentials(self, dataproc, project, region, cluster_name,
                         cluster_uuid, cluster_key, access_boundary_json,
                         operation_poller, openssl_executable):
    downscoped_token = util.GetCredentials(access_boundary_json)
    if not downscoped_token:
      raise exceptions.PersonalAuthError(
          'Failure getting credentials to inject into {}'.format(cluster_name))
    credentials_ciphertext = self.encrypt_with_cluster_key(
        cluster_key, downscoped_token, openssl_executable)
    inject_operation = _inject_encrypted_credentials(dataproc, project, region,
                                                     cluster_name, cluster_uuid,
                                                     credentials_ciphertext)
    if inject_operation:
      waiter.WaitFor(operation_poller, inject_operation)

  # def Run(self, args: argparse.Namespace):
  def Run(self, args):
    message = ('A personal authentication session will propagate your personal '
               'credentials to the cluster, so make sure you trust the cluster '
               'and the user who created it.')
    console_io.PromptContinue(
        message=message,
        cancel_on_no=True,
        cancel_string='Enabling session aborted by user')
    dataproc = dp.Dataproc(self.ReleaseTrack())

    cluster_ref = args.CONCEPTS.cluster.Parse()
    project = cluster_ref.projectId
    region = cluster_ref.region
    cluster_name = cluster_ref.clusterName
    get_request = dataproc.messages.DataprocProjectsRegionsClustersGetRequest(
        projectId=project, region=region, clusterName=cluster_name)
    cluster = dataproc.client.projects_regions_clusters.Get(get_request)
    cluster_uuid = cluster.clusterUuid

    if args.access_boundary:
      with files.FileReader(args.access_boundary) as abf:
        access_boundary_json = abf.read()
    else:
      access_boundary_json = flags.ProjectGcsObjectsAccessBoundary(project)

    # ECIES keys should be used by default. If tink libraries are absent from
    # the system then fallback to using RSA keys.
    cluster_key_type = 'ECIES' if self.is_tink_library_installed() else 'RSA'

    cluster_key = None
    if cluster_key_type == 'ECIES':
      # Try to fetch ECIES keys from cluster control plane node's metadata.
      # If ECIES keys are not available then again fallback to RSA keys.
      cluster_key = clusters.ClusterKey(cluster, cluster_key_type)
      if not cluster_key:
        cluster_key_type = 'RSA'

    openssl_executable = None
    if cluster_key_type == 'RSA':
      cluster_key = clusters.ClusterKey(cluster, cluster_key_type)
      openssl_executable = args.openssl_command
      if not openssl_executable:
        try:
          openssl_executable = files.FindExecutableOnPath('openssl')
        except ValueError:
          log.fatal('Could not find openssl on your system. The enable-session '
                    'command requires openssl to be installed.')

    operation_poller = waiter.CloudOperationPollerNoResources(
        dataproc.client.projects_regions_operations,
        lambda operation: operation.name)
    try:
      if not cluster_key:
        raise exceptions.PersonalAuthError(
            'The cluster {} does not support personal auth.'.format(
                cluster_name))

      with progress_tracker.ProgressTracker(
          'Injecting initial credentials into the cluster {}'.format(
              cluster_name),
          autotick=True):
        self.inject_credentials(dataproc, project, region, cluster_name,
                                cluster_uuid, cluster_key, access_boundary_json,
                                operation_poller, openssl_executable)

      if not args.refresh_credentials:
        return

      update_message = (
          'Periodically refreshing credentials for cluster {}. This'
          ' will continue running until the command is interrupted'
      ).format(cluster_name)

      with progress_tracker.ProgressTracker(update_message, autotick=True):
        try:
          # Cluster keys are periodically regenerated, so fetch the latest
          # each time we inject credentials.
          cluster = dataproc.client.projects_regions_clusters.Get(get_request)
          cluster_key = clusters.ClusterKey(cluster, cluster_key_type)
          if not cluster_key:
            raise exceptions.PersonalAuthError(
                'The cluster {} does not support personal auth.'.format(
                    cluster_name))

          failure_count = 0
          while failure_count < 3:
            try:
              time.sleep(30)
              self.inject_credentials(dataproc, project, region, cluster_name,
                                      cluster_uuid, cluster_key,
                                      access_boundary_json, operation_poller,
                                      openssl_executable)
              failure_count = 0
            except ValueError as err:
              log.error(err)
              failure_count += 1
          raise exceptions.PersonalAuthError(
              'Credential injection failed three times in a row, giving up...')
        except (console_io.OperationCancelledError, KeyboardInterrupt):
          return
    except exceptions.PersonalAuthError as err:
      log.error(err)
      return
