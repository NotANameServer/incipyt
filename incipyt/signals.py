"""Signals for tools."""
from signalslot.signal import Signal


build_dependency = Signal(args=["dep_name"])
classifier = Signal(args=["classifier"])
project_url = Signal(args=["url_kind", "url_value"])
vcs_ignore = Signal(args=["pattern"])
