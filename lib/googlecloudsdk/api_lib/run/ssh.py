# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Library to SSH into a Cloud Run Deployment."""

import argparse
from collections.abc import Sequence
import dataclasses
import enum
import json
import subprocess
from typing import Any

from googlecloudsdk.api_lib.run import constants
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import requests as core_requests
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import platforms


def _GetProjectNumberFromWorkloadJson(
    workload_json: dict[str, Any],
) -> str:
  """Retrieves the project number from the workload JSON.

  Args:
    workload_json: dict, The JSON representation of the Cloud Run workload.

  Returns:
    str, The project number.

  Raises:
    ValueError: If the project number is not found in the workload JSON.
  """
  project_number = workload_json.get(constants.METADATA, {}).get(
      constants.NAMESPACE
  )
  if not project_number:
    raise ValueError("Project number not found in workload.")
  return project_number


def _ValidateGen2(workload_json: dict[str, Any]) -> None:
  """Validates that the workload is gen2.

  Args:
    workload_json: dict, The JSON representation of the Cloud Run workload.

  Raises:
    ValueError: If the workload is a gen1 deployment.
  """
  template = workload_json.get(constants.SPEC, {}).get(constants.TEMPLATE, {})
  execution_environment = (
      template.get(constants.METADATA, {})
      .get(constants.ANNOTATIONS, {})
      .get(k8s_object.EXECUTION_ENVIRONMENT_ANNOTATION)
  )
  if execution_environment == constants.GEN1:
    raise ValueError(
        "SSH is not supported for Cloud Run gen1 deployments. If you"
        " already switched the execution environment to gen2, please wait a"
        " few minutes for the deployment to be updated."
    )


def CreateSshTunnelArgs(
    track,
    project_number,
    project,
    deployment_name,
    workload_type,
    region,
    instance_id=None,
    container_id=None,
    iap_tunnel_url_override=None,
):
  """Construct an SshTunnelArgs from command line args and values.

  Args:
    track: ReleaseTrack, The currently running release track.
    project_number: str, the project number (string with digits).
    project: str, the project id.
    deployment_name: str, the name of the deployment. For services this will be
        of the form {service-name}/revisions/{revision-id}.
    workload_type: Ssh.WorkloadType, the type of the workload.
    region: str, the region of the deployment.
    instance_id: str, the instance id (optional).
    container_id: str, the container id (optional).
    iap_tunnel_url_override: str, the IAP tunnel URL override (optional).

  Returns:
    SshTunnelArgs.
  """

  cloud_run_args = {}
  cloud_run_args["deployment_name"] = deployment_name
  cloud_run_args["workload_type"] = workload_type
  cloud_run_args["project_number"] = project_number
  cloud_run_args["instance_id"] = instance_id
  cloud_run_args["container_id"] = container_id

  res = iap_tunnel.SshTunnelArgs()
  res.track = track.prefix
  res.cloud_run_args = cloud_run_args
  res.region = region
  res.project = project

  if iap_tunnel_url_override:
    res.pass_through_args.append(
        f"--iap-tunnel-url-override={iap_tunnel_url_override}"
    )

  return res


# Double quotes around the type hint are used to avoid circular dependency
@dataclasses.dataclass(frozen=True)
class SshCommandComponents:
  """The components of an SSH command."""

  env: "ssh.Environment"
  remote: "ssh.Remote"
  cert_file: str
  iap_tunnel_args: "iap_tunnel.SshTunnelArgs"
  options: dict[str, str]
  identity_file: str


class Ssh:
  """SSH into a Cloud Run Deployment."""

  class WorkloadType(enum.Enum):
    """The type of the deployment."""

    WORKER_POOL = "worker_pool"
    JOB = "job"
    SERVICE = "service"
    INSTANCE = "instance"

  def __init__(self, args: argparse.Namespace, workload_type: WorkloadType):
    """Initialize the SSH library."""
    self.deployment_name = args.deployment_name
    self.workload_type = workload_type
    self.project = args.project
    self.instance = getattr(args, "instance", None)
    self.container = getattr(args, "container", None)
    self.revision = getattr(args, "revision", None)
    self.region = args.region
    self.release_track = args.release_track
    self.iap_tunnel_url_override = getattr(
        args, "iap_tunnel_url_override", None
    )

    workload_json = self._GetWorkloadJson()
    _ValidateGen2(workload_json)

    if (
        self.workload_type == self.WorkloadType.SERVICE
        and self.release_track != base.ReleaseTrack.ALPHA
    ):
      self.revision = self._GetOrValidateRevision(workload_json)

    self.service_account = self._GetServiceAccountFromWorkloadJson(
        workload_json
    )
    self.project_number = _GetProjectNumberFromWorkloadJson(workload_json)

    self.workload_type = (
        self.WorkloadType.SERVICE
        if self.workload_type == self.WorkloadType.INSTANCE
        else self.workload_type
    )

    if self._UseCloudRunDomainOverride():
      self.iap_tunnel_url_override = constants.SSH_URL_TEMPLATE.format(
          region=self.region
      )

  def _GetOrValidateRevision(self, workload_json):
    """Returns a valid revision or raises an error.

    Args:
      workload_json: dict, The JSON representation of the Cloud Run workload.

    Returns:
      str, The revision name.

    Raises:
      ValueError: If the revision is invalid, or if there is a traffic split and
        the user does not specify a revision when prompted.
    """
    revisions_serving_traffic = workload_json.get(constants.STATUS, {}).get(
        constants.TRAFFIC, []
    )
    active_revisions = [
        t.get(constants.REVISION_NAME)
        for t in revisions_serving_traffic
        if t.get(constants.PERCENT, 0) > 0
    ]

    if not active_revisions:
      raise ValueError("No serving revisions found for the service.")

    if self.revision and self.revision in active_revisions:
      return self.revision
    if self.revision:
      raise ValueError(
          f"Revision {self.revision} is invalid, or it is not serving"
          " traffic. Please specify one of the following revisions:"
          f" {active_revisions} using the --revision flag."
      )

    # The user did not specify a revision, and there is a traffic split.
    if len(active_revisions) > 1:
      if not console_io.CanPrompt():
        raise ValueError(
            "There is a traffic split. Please specify a revision from the"
            f" following list: {active_revisions} using the --revision flag."
        )

      idx = console_io.PromptChoice(
          active_revisions,
          message=(
              "There is a traffic split. Please specify which revision to SSH"
              " into:\n"
          ),
          cancel_option=True,
      )
      return active_revisions[idx]
    # The user did not specify a revision, and there is only one active
    # revision.
    return active_revisions[0]

  def _UseCloudRunDomainOverride(self):
    """Returns whether to use the Cloud Run domain override."""
    if self.iap_tunnel_url_override:
      return False
    if (
        self.release_track == base.ReleaseTrack.ALPHA
        and self.workload_type == self.WorkloadType.SERVICE
    ):
      return False
    return True

  def _UseQualDomain(self) -> bool:
    """Returns whether to use the Qual domain override."""
    if self.iap_tunnel_url_override is None:
      return False
    return (
        "cloud-run-qual" in self.iap_tunnel_url_override
        or "tunnel-staging" in self.iap_tunnel_url_override
        or "tunnel-testing" in self.iap_tunnel_url_override
    )

  def _GetWorkloadJson(self):
    """Retrieves the JSON representation of the Cloud Run workload."""
    command = execution_utils.ArgsForGcloud()

    if self.workload_type == self.WorkloadType.SERVICE:
      command.extend(["run", "services", "describe"])
    elif self.workload_type == self.WorkloadType.WORKER_POOL:
      command.extend(["beta", "run", "worker-pools", "describe"])
    elif self.workload_type == self.WorkloadType.JOB:
      command.extend(["run", "jobs", "describe"])
    elif self.workload_type == self.WorkloadType.INSTANCE:
      command.extend(["alpha", "run", "instances", "describe"])
    else:
      raise ValueError(f"Unsupported workload type: {self.workload_type}")

    command.extend([
        self.deployment_name,
        "--region",
        self.region,
        "--project",
        self.project,
        "--format",
        "json",
    ])
    try:
      output = subprocess.check_output(command, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
      raise ValueError(
          f"Error describing deployment: {e.stderr.decode('utf-8')}"
      ) from e
    return json.loads(output)

  def _GetServiceAccountFromWorkloadJson(
      self, workload_json: dict[str, Any]
  ) -> str:
    """Retrieves the service account from the workload JSON.

    Args:
      workload_json: A dict, the JSON representation of the Cloud Run workload.

    Returns:
      A str, the service account name.

    Raises:
      ValueError: If the service account is not found in the workload JSON.
    """
    if self.workload_type == self.WorkloadType.INSTANCE:
      service_account = workload_json.get(constants.SPEC, {}).get(
          constants.SERVICE_ACCOUNT_NAME
      )
    else:
      template = workload_json.get(constants.SPEC, {}).get(
          constants.TEMPLATE, {}
      )
      service_account = template.get(constants.SPEC, {}).get(
          constants.SERVICE_ACCOUNT_NAME
      )
    if not service_account:
      raise ValueError("Service account not found for workload.")
    return service_account

  def HostKeyAlias(self):
    """Returns the host key alias for the SSH connection."""
    return constants.SSH_HOST_KEY_ALIAS

  def GetSshCommandComponents(self):
    """Returns the SSH command components."""
    # The PuTTY binary in gcloud does not natively support passing signed
    # certificates via flags. Since OpenSSH is now officially supported on
    # Windows 10 and later, and Cloud Run SSH is a completely new feature,
    # falling back to OpenSSH on Windows is safe.
    if platforms.OperatingSystem.IsWindows():
      env = ssh.Environment(ssh.Suite.OPENSSH, None, is_windows=True)
    else:
      env = ssh.Environment.Current()
    env.RequireSSH()
    keys = ssh.Keys.FromFilename(env=env)
    keys.EnsureKeysExist(overwrite=False)
    user = constants.SSH_ROOT_USER

    # Note: this actually creates the certificate.
    ssh.GetOsloginState(
        None,
        None,
        user,
        keys.GetPublicKey().ToEntry(),
        None,
        self.release_track,
        cloud_run_params={
            "deployment_name": self.deployment_name,
            "project_id": self.project,
            "region": self.region,
            "service_account": self.service_account,
            "workload_type": self.workload_type,
        },
        env=env,
    )
    cert_file = ssh.CertFileFromCloudRunDeployment(
        project=self.project,
        region=self.region,
        deployment=self.deployment_name,
        workload_type=self.workload_type,
    )
    dest_addr = self.HostKeyAlias()
    remote = ssh.Remote(dest_addr, user)

    ca_keys = self._FetchSshCaPublicKeys()
    if ca_keys:
      known_hosts = ssh.KnownHosts.FromDefaultFile()
      known_hosts.AddCertAuthority(
          host_pattern=dest_addr, ca_public_keys=list(ca_keys)
      )
      known_hosts.Write()

    deployment_name = (
        f"{self.deployment_name}/revisions/{self.revision}"
        if self.revision
        else self.deployment_name
    )
    iap_tunnel_args = CreateSshTunnelArgs(
        self.release_track,
        self.project_number,
        self.project,
        deployment_name,
        self.workload_type,
        self.region,
        self.instance,
        self.container,
        self.iap_tunnel_url_override,
    )

    ssh_helper = ssh_utils.BaseSSHCLIHelper()
    ssh_options = ssh_helper.GetConfig(
        host_key_alias=dest_addr,
        strict_host_key_checking="no",
    )

    return SshCommandComponents(
        env=env,
        remote=remote,
        cert_file=cert_file,
        iap_tunnel_args=iap_tunnel_args,
        options=ssh_options,
        identity_file=keys.key_file,
    )

  def Run(self):
    """Run the SSH command."""

    cmd_components = self.GetSshCommandComponents()

    return ssh.SSHCommand(
        remote=cmd_components.remote,
        cert_file=cmd_components.cert_file,
        iap_tunnel_args=cmd_components.iap_tunnel_args,
        options=cmd_components.options,
        identity_file=cmd_components.identity_file,
    ).Run(cmd_components.env)

  def _FetchSshCaPublicKeys(self) -> Sequence[str] | None:
    """Retrieves the CA public keys for the current region from a gstatic URL.

    Returns:
      A Sequence of strings, where each string is a public key, or None if
      the keys could not be fetched.
    """

    template = (
        constants.SSH_CA_PUBLIC_KEY_URL_QUAL_TEMPLATE
        if self._UseQualDomain()
        else constants.SSH_CA_PUBLIC_KEY_URL_TEMPLATE
    )
    endpoint = template.format(
        region=self.region
    )

    try:
      with core_requests.GetSession() as session:
        response = session.get(endpoint, timeout=10)
    except core_requests.requests.exceptions.RequestException:
      log.debug(
          "Failed to fetch SSH CA public keys from %s.",
          endpoint,
          exc_info=True,
      )
      return None
    else:
      if response.status_code != 200:
        log.debug(
            "Failed to fetch SSH CA public keys from %s. Received status"
            " code: %s",
            endpoint,
            response.status_code,
        )
        return None
      return [k.strip() for k in response.text.splitlines() if k.strip()]
