"""Explicit entry point for the dependency-ordered warehouse and mart build.

The warehouse runner owns the dependency ordering, so this module delegates to it
and keeps the public command name requested by the project plan.
"""

from src.build_warehouse import main


if __name__ == "__main__":
    main()