"""Tests for py.google.cloud.ml.dataflow.batch_prediction_pipeline."""

import tensorflow as tf


def create_identity_model(
    model_dir,
    signature_name=(
        tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY),
    tags=(tf.saved_model.tag_constants.SERVING,)):
  """Create a model and saved it in SavedModel format."""
  g, signature_def_map = _identity_string_graph(signature_name)
  _write_graph(g, signature_def_map, list(tags), model_dir)


def _identity_string_graph(serving_signature):
  """create a testing graph."""
  with tf.Graph().as_default() as g:
    x = tf.placeholder(dtype=tf.string)
    x = tf.Print(x, [x])
    out = tf.identity(x)
    out = tf.Print(out, [out])
    inputs = {"in": x}
    outputs = {"out": out}

    signature_inputs = {
        key: tf.saved_model.utils.build_tensor_info(tensor)
        for key, tensor in inputs.items()
    }
    signature_outputs = {
        key: tf.saved_model.utils.build_tensor_info(tensor)
        for key, tensor in outputs.items()
    }

    signature_def = tf.saved_model.signature_def_utils.build_signature_def(
        signature_inputs, signature_outputs,
        tf.saved_model.signature_constants.PREDICT_METHOD_NAME)

    signature_def_map = {serving_signature: signature_def}

  return g, signature_def_map


def _write_graph(graph, signature_def_map, tags, model_dir):
  """Write the model for given graph, signature, tags into model dir."""
  builder = tf.saved_model.builder.SavedModelBuilder(model_dir)
  with tf.Session(graph=graph) as sess:
    tf.initialize_all_variables().run()
    builder.add_meta_graph_and_variables(
        sess,
        tags=tags,
        signature_def_map=signature_def_map)
    builder.save()
