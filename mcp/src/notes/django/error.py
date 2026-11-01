class NoteAPIError(Exception):
    """A safe message for callers; excludes response bodies and connection details."""
