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
"""Implementation of gcloud scc artifact-guard images scan."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import subprocess
import tempfile

from googlecloudsdk.api_lib.scc.artifact_guard import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files


class SbomExtractorError(exceptions.Error):
  """Error for sbom-extractor failures."""


class SbomExtractorCommand(binary_operations.BinaryBackedOperation):
  """Wrapper for call to the sbom-extractor binary."""

  def __init__(self, **kwargs):
    super(SbomExtractorCommand, self).__init__(
        binary='sbom-extractor', **kwargs
    )

  def _ParseArgsForCommand(
      self, resource_uri, sbom_file, purl_file, remote, **kwargs
  ):
    return [
        '-remote=' + str(remote).lower(),
        '-resource_uri=' + resource_uri,
        '-sbom_file=' + sbom_file,
        '-purls_file=' + purl_file,
    ]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.DefaultUniverseOnly
class Scan(base.Command):
  """Scan an image with Artifact Guard."""

  detailed_help = {
      'DESCRIPTION': """
          Scan a container image with Artifact Guard.
          """,
      'EXAMPLES': """
          To scan an image:

            $ {command} my-image:tag --parent=organizations/123/locations/global --scan-type=pipeline --connector-id=my-connector --jenkins-build-tag=t --jenkins-build-id=i
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds arguments to the parser."""
    parser.add_argument(
        'RESOURCE_URI',
        help=(
            'URI of the image to scan (e.g., `my-image:tag` or'
            ' `my-image@digest`).'
        ),
    )
    parser.add_argument(
        '--remote',
        action='store_true',
        default=False,
        help=(
            'If true, treat resource_uri as a remote image. If false, treats '
            'it as a local tarball or daemon image.'
        ),
    )
    parser.add_argument(
        '--parent',
        required=True,
        help=(
            'Parent resource for artifact guard, e.g., '
            '`organizations/123/locations/global`.'
        ),
    )
    parser.add_argument(
        '--scan-type',
        required=True,
        type=str,
        choices=['pipeline'],
        help='Type of scan to perform.',
    )
    parser.add_argument(
        '--connector-id',
        help='The ID of the pipeline connector. Required for pipeline scans.',
    )

    cicd_group = parser.add_mutually_exclusive_group(
        help='CI/CD pipeline context. Required for pipeline scans.'
    )
    jenkins_group = cicd_group.add_group('Jenkins CI Pipeline context flags.')
    jenkins_group.add_argument(
        '--jenkins-build-tag', required=True, help='Jenkins build tag.'
    )
    jenkins_group.add_argument(
        '--jenkins-build-id', required=True, help='Jenkins build ID.'
    )
    github_group = cicd_group.add_group(
        'GitHub Actions workflow context flags.'
    )
    github_group.add_argument(
        '--github-run-id', required=True, help='GitHub run ID.'
    )
    github_group.add_argument('--github-workflow', help='GitHub workflow.')
    github_group.add_argument('--github-repository', help='GitHub repository.')
    cb_group = cicd_group.add_group('Google Cloud Build context flags.')
    cb_group.add_argument(
        '--cloud-build-id', required=True, help='Cloud Build ID.'
    )
    cb_group.add_argument(
        '--cloud-build-project-id',
        required=True,
        help='Cloud Build project ID.',
    )
    cb_group.add_argument(
        '--cloud-build-trigger-id', help='Cloud Build trigger ID.'
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def _ParseImageUri(self, uri):
    """Parses image URI into name, digest, and tags."""
    image_digest = None
    image_tags = []
    name_and_tag = uri

    if '@' in uri:
      # Case: name@digest or name:tag@digest
      name_and_tag, image_digest = uri.split('@', 1)

    # check for tag in name_and_tag
    tag_parts = name_and_tag.split(':')
    if len(tag_parts) > 1 and '/' not in tag_parts[-1]:
      image_tags = [tag_parts[-1]]
      image_name = ':'.join(tag_parts[:-1])
    else:
      image_name = name_and_tag

    return image_name, image_digest, image_tags

  def _GetProperty(self, response_value, key):
    for prop in response_value.additionalProperties:
      if prop.key == key:
        return prop.value.string_value
    raise exceptions.Error('Property {} not found in response'.format(key))

  def Run(self, args):
    """Runs the scan command."""
    if args.scan_type == 'pipeline':
      if not args.connector_id:
        raise exceptions.Error(
            '--connector-id is required for --scan-type=pipeline.'
        )
      if not (
          args.jenkins_build_id or args.github_run_id or args.cloud_build_id
      ):
        raise exceptions.Error(
            'one of the arguments --jenkins-build-id --github-run-id'
            ' --cloud-build-id is required'
        )

    image_name, image_digest, image_tags = self._ParseImageUri(
        args.RESOURCE_URI
    )
    if not image_digest:
      try:
        inspect_cmd = [
            'docker',
            'inspect',
            args.RESOURCE_URI,
        ]
        log.debug('Running docker inspect command: %s', ' '.join(inspect_cmd))
        inspect_result = subprocess.run(
            inspect_cmd, check=False, capture_output=True, text=True
        )
        if inspect_result.returncode == 0:
          try:
            docker_id = json.loads(inspect_result.stdout)[0]['Id']
            if docker_id:
              image_digest = docker_id
              log.status.Print('Found digest: %s', image_digest)
            else:
              log.warning('Docker inspect did not return an Id.')
          except (json.JSONDecodeError, IndexError, KeyError) as e:
            log.warning('Failed to parse docker inspect output: %s', e)
        else:
          log.warning(
              'docker inspect failed with exit code %s: %s',
              inspect_result.returncode,
              inspect_result.stderr,
          )
      except FileNotFoundError:
        log.warning('docker command not found, cannot determine digest.')
      except OSError as e:
        log.warning('Failed to run docker inspect: %s', e)

    if not image_tags and image_digest:
      log.status.Print('No image tag provided, attempting to find one...')
      try:
        inspect_cmd = [
            'docker',
            'inspect',
            args.RESOURCE_URI,
        ]
        log.debug('Running docker inspect command: %s', ' '.join(inspect_cmd))
        inspect_result = subprocess.run(
            inspect_cmd, check=False, capture_output=True, text=True
        )
        if inspect_result.returncode == 0:
          try:
            repo_tags = json.loads(inspect_result.stdout)[0]['RepoTags']
            if repo_tags:
              # extract tag from first repo tag. RepoTag is like name:tag
              image_tags = [repo_tags[0].split(':')[-1]]
              log.status.Print('Found tag: %s', image_tags[0])
            else:
              log.warning('Docker inspect did not return any RepoTags.')
          except (json.JSONDecodeError, IndexError, KeyError) as e:
            log.warning('Failed to parse docker inspect output: %s', e)
        else:
          log.warning(
              'docker inspect failed with exit code %s: %s',
              inspect_result.returncode,
              inspect_result.stderr,
          )
      except FileNotFoundError:
        log.warning('docker command not found.')
      except OSError as e:
        log.warning('Failed to run docker inspect: %s', e)

    if not image_tags and image_digest:
      log.warning('Could not find image tag. Using placeholder "digest-scan".')
      image_tags = ['digest-scan']

    sbom_file = None
    purl_file = None
    run_extractor = True
    if run_extractor:
      log.status.Print(
          'No SBOM/pURL files provided, attempting to run SBOM extractor...'
      )
      try:
        update_manager.UpdateManager.EnsureInstalledAndRestart(
            ['sbom-extractor']
        )
      except update_manager.MissingRequiredComponentsError:
        raise
      except local_state.InvalidSDKRootError:
        # This happens when gcloud is run locally, but not when distributed.
        pass
      sbom_extractor = SbomExtractorCommand()
      try:
        sbom_fd, sbom_file = tempfile.mkstemp(suffix='.sbom.json')
        purl_fd, purl_file = tempfile.mkstemp(suffix='.purls.json')
        os.close(sbom_fd)
        os.close(purl_fd)
        result = sbom_extractor(
            resource_uri=args.RESOURCE_URI,
            sbom_file=sbom_file,
            purl_file=purl_file,
            remote=args.remote,
        )
        if result.exit_code != 0:
          raise SbomExtractorError(
              'SBOM extractor failed with exit code {}:\n{}'.format(
                  result.exit_code, result.stderr
              )
          )
        log.status.Print(
            'SBOM extractor finished, SBOM: [{}], pURLs: [{}]'.format(
                sbom_file, purl_file
            )
        )
        purl_content = files.ReadFileContents(purl_file)
        log.status.Print('pURL file content:\n{}'.format(purl_content))
      except (SbomExtractorError, binary_operations.BinaryExecutionError) as e:
        raise exceptions.Error('Failed to run SBOM extractor: {}'.format(e))

    try:
      log.status.Print(
          'Preparing to upload SBOM [{}] and pURLs [{}]...'.format(
              sbom_file, purl_file
          )
      )
      try:
        resp = util.GetSignedUrls(
            args.parent, image_name, image_digest, image_tags
        )
      except Exception as e:
        raise exceptions.Error('Failed to get signed URLs: {}'.format(e))

      # log.status.Print(resp)
      log.status.Print('Uploading SBOM file...')
      util.UploadFileToSignedUrl(
          self._GetProperty(resp, 'sbomFileSignedUrl'), sbom_file
      )
      log.status.Print('Uploading pURL file...')
      util.UploadFileToSignedUrl(
          self._GetProperty(resp, 'purlFileSignedUrl'), purl_file
      )

      pipeline_context = util.GetPipelineContext(args)

      log.status.Print('Initiating Artifact Guard scan...')
      op = util.RunArtifactEvaluation(
          parent_resource=args.parent,
          connector_id=args.connector_id,
          image_name=image_name,
          image_digest=image_digest,
          image_tag=image_tags,
          sbom_uri=self._GetProperty(resp, 'sbomUri'),
          purl_uri=self._GetProperty(resp, 'purlUri'),
          pipeline_context=pipeline_context,
      )
      if args.async_:
        log.status.Print('Scan in progress asynchronously.')
        return op
      result = util.WaitForOperation(op, 'Waiting for scan to complete...')
      log.status.Print('Scan complete.')
      return result
    finally:
      if run_extractor:
        log.debug('Removing temporary files: %s, %s', sbom_file, purl_file)
        try:
          if sbom_file:
            os.remove(sbom_file)
          if purl_file:
            os.remove(purl_file)
        except OSError as e:
          log.warning('Failed to remove temporary file: %s', e)
