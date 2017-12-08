"""Utilities for cleaning dataflow errors to be user friendly."""

TENSORFLOW_OP_MATCHER = "\n\nCaused by op"


def filter_tensorflow_error(error_string):
  """Removes information from a tensorflow error to hide Dataflow details.

  TF appends the operation details if they exist, but the stacktrace
  is not useful to the user, so we remove it if present.

  Args:
    error_string: PredictionError error detail, error caught during Session.run

  Returns:
    error_string with only base error message instead of full traceback.
  """
  return error_string.split(TENSORFLOW_OP_MATCHER)[0]
