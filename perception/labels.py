"""Canonical label taxonomy for the path-direction classification task.

This is the single source of truth for the class set, shared by data
generation (assigns ground truth), training (classification head order),
and the ROS inference node (decodes model output back into an action).
"""

LABELS = ("straight", "left", "right", "stop")
LABEL_TO_INDEX = {label: index for index, label in enumerate(LABELS)}
