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
"""Key generation utilities."""


import enum
import os
import sys

from googlecloudsdk.command_lib.privateca import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

KEY_OUTPUT_WARNING = """A private key was exported to {}.

Possession of this key file could allow anybody to act as this certificate's
subject. Please make sure that you store this key file in a secure location at
all times, and ensure that only authorized users have access to it.
"""


class KeyAlgorithm(enum.Enum):
  """Supported key generation algorithms."""

  RSA_2048 = 'rsa-2048'
  RSA_3072 = 'rsa-3072'
  RSA_4096 = 'rsa-4096'
  EC_P256 = 'ec-p256'
  EC_P384 = 'ec-p384'


_RSA_KEY_SIZES = {
    KeyAlgorithm.RSA_2048: 2048,
    KeyAlgorithm.RSA_3072: 3072,
    KeyAlgorithm.RSA_4096: 4096,
}


def _ResolveKeyAlgorithm(algorithm):
  """Resolves a KeyAlgorithm enum from an enum value or CLI choice string."""
  if isinstance(algorithm, KeyAlgorithm):
    return algorithm
  if isinstance(algorithm, str):
    try:
      return KeyAlgorithm(algorithm)
    except ValueError:
      return None
  return None


def RSAKeyGen(key_size=2048):
  """Generates an RSA public-private key pair.

  Args:
    key_size: The size of the RSA key, in number of bytes. Defaults to 2048.

  Returns:
    A tuple with: (private_key, public_key) both serialized in PKCS1 as bytes.
  """
  import_error_msg = ('Cannot load the Pyca cryptography library. Either the '
                      'library is not installed, or site packages are not '
                      'enabled for the Google Cloud SDK. Please consult Cloud '
                      'KMS documentation on adding Pyca to Google Cloud SDK '
                      'for further instructions.\n'
                      'https://cloud.google.com/kms/docs/crypto')
  try:
    # TODO(b/141249289): Move imports to the top of the file. In the
    # meantime, until we're sure that all Private CA SDK users have the
    # cryptography module available, let's not error out if we can't load the
    # module unless we're actually going down this code path.
    # pylint: disable=g-import-not-at-top
    from cryptography.hazmat.primitives.asymmetric import rsa
  except ImportError:
    log.err.Print(import_error_msg)
    sys.exit(1)

  # The serialization modules have moved in cryptography version 3.4 and above.
  # Try both the old and new locations to support both versions. See b/183521338
  # for more context.
  try:
    # pylint: disable=g-import-not-at-top
    from cryptography.hazmat.primitives.serialization.base import Encoding
    from cryptography.hazmat.primitives.serialization.base import PrivateFormat
    from cryptography.hazmat.primitives.serialization.base import PublicFormat
    from cryptography.hazmat.primitives.serialization.base import NoEncryption
  except ImportError:
    try:
      # pylint: disable=g-import-not-at-top
      from cryptography.hazmat.primitives.serialization import Encoding
      from cryptography.hazmat.primitives.serialization import PrivateFormat
      from cryptography.hazmat.primitives.serialization import PublicFormat
      from cryptography.hazmat.primitives.serialization import NoEncryption
    except ImportError:
      log.err.Print(import_error_msg)
      sys.exit(1)

  private_key = rsa.generate_private_key(
      public_exponent=65537, key_size=key_size
  )

  private_key_bytes = private_key.private_bytes(
      Encoding.PEM,
      PrivateFormat.TraditionalOpenSSL,  # PKCS#1
      NoEncryption())

  public_key_bytes = private_key.public_key().public_bytes(
      Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

  return private_key_bytes, public_key_bytes


def _GetEcCurve(curve, ec):
  """Resolves the EC curve object from a KeyAlgorithm enum or curve instance."""
  if isinstance(curve, ec.EllipticCurve):
    return curve
  if isinstance(curve, type) and issubclass(curve, ec.EllipticCurve):
    return curve()
  algorithm_enum = _ResolveKeyAlgorithm(curve)
  if algorithm_enum == KeyAlgorithm.EC_P256:
    return ec.SECP256R1()
  if algorithm_enum == KeyAlgorithm.EC_P384:
    return ec.SECP384R1()
  raise ValueError(
      "Unsupported EC curve '{}'. Supported algorithms are '{}' and '{}'."
      .format(
          curve,
          KeyAlgorithm.EC_P256.value,
          KeyAlgorithm.EC_P384.value,
      )
  )


def ECKeyGen(curve=KeyAlgorithm.EC_P256):
  """Generates an EC public-private key pair.

  Args:
    curve: The EC KeyAlgorithm enum (e.g. KeyAlgorithm.EC_P256,
      KeyAlgorithm.EC_P384), CLI choice string ('ec-p256', 'ec-p384'), or an
      EllipticCurve instance. Defaults to KeyAlgorithm.EC_P256.

  Returns:
    A tuple with: (private_key, public_key) serialized as PEM bytes.
  """
  # pylint: disable=g-import-not-at-top
  from cryptography.hazmat.primitives.asymmetric import ec
  from cryptography.hazmat.primitives.serialization import Encoding
  from cryptography.hazmat.primitives.serialization import NoEncryption
  from cryptography.hazmat.primitives.serialization import PrivateFormat
  from cryptography.hazmat.primitives.serialization import PublicFormat

  ec_curve = _GetEcCurve(curve, ec)
  private_key = ec.generate_private_key(ec_curve)

  private_key_bytes = private_key.private_bytes(
      Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
  )

  public_key_bytes = private_key.public_key().public_bytes(
      Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
  )

  return private_key_bytes, public_key_bytes


def KeyGenForAlgorithm(key_algorithm):
  """Generates a key pair for the specified algorithm.

  Args:
    key_algorithm: The algorithm choice string (e.g. 'rsa-2048', 'rsa-3072',
      'rsa-4096', 'ec-p256', 'ec-p384') or KeyAlgorithm enum.

  Returns:
    A tuple with: (private_key, public_key) serialized as PEM bytes.
  """
  algorithm_enum = _ResolveKeyAlgorithm(key_algorithm)
  if algorithm_enum in _RSA_KEY_SIZES:
    return RSAKeyGen(_RSA_KEY_SIZES[algorithm_enum])
  if algorithm_enum in (
      KeyAlgorithm.EC_P256,
      KeyAlgorithm.EC_P384,
  ):
    return ECKeyGen(algorithm_enum)
  raise ValueError("Unsupported key algorithm '{}'.".format(key_algorithm))


def ExportPrivateKey(private_key_output_file, private_key_bytes):
  """Export a private key to a filename, printing a warning to the user.

  Args:
    private_key_output_file: The path of the file to export to.
    private_key_bytes: The content in byte format to export.
  """

  try:
    # Make sure this file is only accessible to the running user before writing.
    files.PrivatizeFile(private_key_output_file)
    files.WriteFileContents(private_key_output_file, private_key_bytes)
    # Make file readable only by owner.
    os.chmod(private_key_output_file, 0o400)
    log.warning(KEY_OUTPUT_WARNING.format(private_key_output_file))
  except (files.Error, OSError, IOError):
    raise exceptions.FileOutputError(
        "Error writing to private key output file named '{}'".format(
            private_key_output_file))
