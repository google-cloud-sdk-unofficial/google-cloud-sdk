# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Supplementary help for gcloud startup options."""


from googlecloudsdk.calliope import base


@base.UniverseCompatible
class Startup(base.TopicCommand):
  """Supplementary help for gcloud startup options.


  This page provides supplementary help for configuring the gcloud command-line
  tool's startup behavior, including Python interpreter selection and
  environment variables.

  ## CONFIGURING THE PYTHON INTERPRETER

  The `gcloud` CLI requires a compatible Python version (3.10-3.14) to run. In
  most gcloud CLI installations, the gcloud installer manages the Python
  installation (version 3.13) for the user. Configuring the Python
  interpreter is only supported in specific scenarios described below.

  ### When to Use `CLOUDSDK_PYTHON` environment variable

  You can ONLY consider using the CLOUDSDK_PYTHON environment variable when you
  are on:

  - *Linux*: Installing from a versioned archives (`*.tar.gz*`) on ARM or x86
  architectures where Python is NOT included as part of the installation, gcloud
  will search for a compatible Python on your system PATH (looking for python3
  then python). You can set the `CLOUDSDK_PYTHON` environment variable to the
  full path of your preferred compatible Python interpreter if the default one
  found on PATH is not desired.
  - *macOS*: Available only for archived install and where the Python version
  matches the Python version managed by the gcloud CLI Tools install. Note
  that this is not available for Homebrew installations of gcloud CLI Tools.
  - *Windows*: gcloud installer includes the required Python interpreter by
  default. Only use `CLOUDSDK_PYTHON` if you need to use a different
  Python installation.

  Example Usages:

    # Use the python3 interpreter on your path
    $ export CLOUDSDK_PYTHON=python3

    # Use a python you have installed in a special location
    $ export CLOUDSDK_PYTHON=/usr/local/my-custom-python-install/python

  ### Other Components

  `gsutil` versions 5.0 and later support Python 3.10-3.13. To use a different
  interpreter for `gsutil` than for the other Python tools, set the
  `CLOUDSDK_GSUTIL_PYTHON` environment variable to the interpreter that you
  want.

  `bq` versions 2.0.99 and later support Python 3.10-3.14. To use a different
  interpreter for `bq` than for the other Python tools, set the
  `CLOUDSDK_BQ_PYTHON` environment variable to the interpreter that you want.

  ## SETTING CONFIGURATIONS AND PROPERTIES

  Your active configuration can also be set via the environment variable
  `CLOUDSDK_ACTIVE_CONFIG_NAME`. This allows you to specify a certain
  configuration in a given terminal session without changing the global
  default configuration.

  In addition to being able to set them via `gcloud config set`,
  each `gcloud` property has a corresponding environment variable. They take
  the form: `CLOUDSDK_SECTION_PROPERTY`. For example, if you wanted to
  change your active project for just one terminal you could run:

    $ export CLOUDSDK_CORE_PROJECT=my-project

  For more information, see `gcloud topic configurations`.
  """
