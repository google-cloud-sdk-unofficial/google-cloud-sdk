# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Google Cloud Machine Learning SDK.
"""
from google.cloud.ml.dataflow._analyzer import AnalyzeModel
from google.cloud.ml.dataflow._analyzer import ConfusionMatrix
from google.cloud.ml.dataflow._analyzer import LogLoss
from google.cloud.ml.dataflow._analyzer import PrecisionRecall

from google.cloud.ml.dataflow._ml_transforms import DeployVersion
from google.cloud.ml.dataflow._ml_transforms import Evaluate
from google.cloud.ml.dataflow._ml_transforms import Predict
from google.cloud.ml.dataflow._ml_transforms import Train
from google.cloud.ml.dataflow._preprocessing import Preprocess

from google.cloud.ml.features._analysis import AnalyzeData
from google.cloud.ml.features._pipeline import TransformData as ExtractFeatures

from google.cloud.ml.util._decoders import DecodeError

from google.cloud.ml.version import __version__
from google.cloud.ml.version import sdk_location
