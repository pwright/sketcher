"""Skewer CLI - YAML processing and documentation generation."""

import logging
import sys
from pathlib import Path

from . import resolver, generator, utils
from .exceptions import SketcherError


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Skewer - YAML processing and documentation generation for Skupper examples"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Resolve command (Phase 2 - implemented)
    resolve_parser = subparsers.add_parser(
        "resolve",
        help="Expand standard steps in skewer.yaml files (migration tool)"
    )
    resolve_parser.add_argument(
        "input_file",
        help="Input yaml file with standard: references"
    )
    resolve_parser.add_argument(
        "-o", "--output",
        help="Output file (default: print to stdout)"
    )
    resolve_parser.add_argument(
        "--in-place",
        action="store_true",
        help="Modify input file in-place"
    )

    # Generate command (Phase 4 - implemented)
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate README.md from resolved skewer.yaml"
    )
    generate_parser.add_argument(
        "yaml_file",
        nargs="?",
        default="skewer.yaml",
        help="Resolved yaml file (default: skewer.yaml)"
    )
    generate_parser.add_argument(
        "-o", "--output",
        help="Output file (default: README.md in same directory)"
    )

    # Clean command
    clean_parser = subparsers.add_parser(
        "clean",
        help="Remove generated files"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Configure logging based on verbosity flags
    # --verbose: Show debug-level messages (for troubleshooting)
    # --quiet: Suppress progress messages (for automation/scripting)
    # default: Info-level messages (normal operation)
    if hasattr(args, 'verbose') and args.verbose:
        utils.configure_logging(level=logging.DEBUG)
    elif hasattr(args, 'quiet') and args.quiet:
        utils.configure_logging(level=logging.WARNING)
    else:
        utils.configure_logging(level=logging.INFO)

    # Print version at start of every run
    from . import __version__
    print(f"Skewer {__version__}")

    # Extract quiet flag for passing to commands
    quiet = getattr(args, 'quiet', False)

    try:
        if args.command == "resolve":
            if args.in_place:
                if args.output:
                    print("Error: Cannot use both --in-place and --output", file=sys.stderr)
                    sys.exit(1)
                resolver.resolve_file_in_place(args.input_file)
            else:
                resolver.resolve_yaml_file(args.input_file, args.output)
        elif args.command == "generate":
            generator.generate_readme(args.yaml_file, args.output, quiet=quiet)
        elif args.command == "clean":
            # Remove __pycache__ directories (Python artifacts only)
            import shutil
            count = 0
            for pycache in Path(".").rglob("__pycache__"):
                shutil.rmtree(pycache)
                utils.info("Removed {}", pycache, quiet=quiet)
                count += 1

            if count == 0:
                utils.info("No Python artifacts to clean", quiet=quiet)
            else:
                utils.cprint(f"Cleaned {count} Python artifact(s)", color="green")
        else:
            print(f"Command '{args.command}' not yet implemented", file=sys.stderr)
            sys.exit(1)

    except SketcherError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
