"""Custom exception hierarchy for demostackkit."""


class DemoStackKitError(Exception):
    """Base exception for all demostackkit errors."""


class IndustryNotFoundError(DemoStackKitError):
    """Raised when an industry slug cannot be found in the industries directory."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(
            f"Industry '{slug}' not found. Run 'demostackkit list' to see available industries."
        )


class InvalidIndustryConfigError(DemoStackKitError):
    """Raised when industry.yaml fails schema validation."""

    def __init__(self, path: str, errors: list[str]) -> None:
        self.path = path
        self.errors = errors
        joined = "\n  - ".join(errors)
        super().__init__(f"Invalid industry config at {path}:\n  - {joined}")


class DockerError(DemoStackKitError):
    """Raised when a Docker Compose operation fails."""

    def __init__(self, command: str, returncode: int, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Docker command failed (exit {returncode}): {command}\n{stderr}")


class BenchError(DemoStackKitError):
    """Raised when a bench CLI operation inside the container fails."""

    def __init__(self, command: str, returncode: int, output: str) -> None:
        self.command = command
        self.returncode = returncode
        self.output = output
        super().__init__(f"bench command failed (exit {returncode}): {command}\n{output}")


class SeederError(DemoStackKitError):
    """Raised when a seeder's run() method fails."""

    def __init__(self, seeder_class: str, cause: Exception) -> None:
        self.seeder_class = seeder_class
        self.cause = cause
        super().__init__(f"Seeder '{seeder_class}' failed: {cause}")


class SeedValidationError(DemoStackKitError):
    """Raised when a seeder's validate() method returns errors."""

    def __init__(self, seeder_class: str, errors: list[str]) -> None:
        self.seeder_class = seeder_class
        self.errors = errors
        joined = "\n  - ".join(errors)
        super().__init__(f"Seeder '{seeder_class}' pre-flight validation failed:\n  - {joined}")


class EnvironmentError(DemoStackKitError):
    """Raised when the host environment does not meet requirements."""
