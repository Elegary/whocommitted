"""Exception hierarchy for whocommitted."""


class WhocommittedError(Exception):
    """Base class for all whocommitted errors."""

    exit_code = 1


class InvalidRepoSpecError(WhocommittedError):
    """The repository specification could not be understood by any provider."""

    exit_code = 2


class GitNotFoundError(WhocommittedError):
    """The ``git`` executable is not available."""

    exit_code = 3


class GitCommandError(WhocommittedError):
    """A git command (clone, fetch, log) failed."""

    exit_code = 4
