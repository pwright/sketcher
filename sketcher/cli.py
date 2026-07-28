"""Sketcher CLI - Command-line interface."""

import logging
import os
import sys
import glob
from pathlib import Path

from . import resolver, generator, executor, demo, minikube, kind, utils
from .exceptions import SketcherError


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sketcher - Python 3 framework for Skupper examples"
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

    # Run command (Phase 5 - implemented)
    run_parser = subparsers.add_parser(
        "run",
        help="Run steps from resolved skewer.yaml"
    )
    run_parser.add_argument(
        "yaml_file",
        nargs="?",
        default="skewer.yaml",
        help="Resolved yaml file (default: skewer.yaml)"
    )
    run_parser.add_argument(
        "kubeconfigs",
        nargs="*",
        help="Kubeconfig files for sites"
    )
    run_parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug output on failure"
    )
    run_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug output"
    )
    run_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )
    run_parser.add_argument(
        "--work-dir",
        help="Working directory (default: temp dir)"
    )

    # Demo command (Phase 6 - implemented)
    demo_parser = subparsers.add_parser(
        "demo",
        help="Run steps and pause for demo"
    )
    demo_parser.add_argument(
        "yaml_file",
        nargs="?",
        default="skewer.yaml",
        help="Resolved yaml file (default: skewer.yaml)"
    )
    demo_parser.add_argument(
        "kubeconfigs",
        nargs="*",
        help="Kubeconfig files for sites"
    )
    demo_parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug output on failure"
    )
    demo_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug output"
    )
    demo_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )
    demo_parser.add_argument(
        "--kind",
        action="store_true",
        help="Use Kind instead of Minikube (default: Minikube)"
    )

    # Demo-extend command (Phase 6 - implemented)
    demo_extend_parser = subparsers.add_parser(
        "demo-extend",
        help="Extend an active demo with additional steps"
    )
    demo_extend_parser.add_argument(
        "extend_file",
        help="Extension yaml file"
    )
    demo_extend_parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug output on failure"
    )
    demo_extend_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug output"
    )
    demo_extend_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )

    # Test command (Phase 7 - implemented)
    test_parser = subparsers.add_parser(
        "test",
        help="Generate README, run main steps, and run all extension files"
    )
    test_parser.add_argument(
        "yaml_file",
        nargs="?",
        default="skewer.yaml",
        help="Resolved yaml file (default: skewer.yaml)"
    )
    test_parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug output on failure"
    )
    test_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug output"
    )
    test_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )
    test_parser.add_argument(
        "--kind",
        action="store_true",
        help="Use Kind instead of Minikube (default: Minikube)"
    )

    # Clean command (Phase 7 - implemented)
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
            # Generate command doesn't have quiet/verbose flags yet
            generator.generate_readme(args.yaml_file, args.output)
        elif args.command == "run":
            executor.run_steps(
                args.yaml_file,
                kubeconfigs=args.kubeconfigs or None,
                work_dir=args.work_dir,
                debug=args.debug,
                quiet=quiet
            )
        elif args.command == "demo":
            # Set SKETCHER_DEMO env var
            os.environ["SKETCHER_DEMO"] = "1"

            # Check if any sites require Kubernetes
            from sketcher.model import Model
            temp_model = Model(args.yaml_file)
            needs_k8s = any(site.platform == "kubernetes" for _, site in temp_model.sites)

            # Use Kind or Minikube only if sites require Kubernetes and no kubeconfigs provided
            if not args.kubeconfigs and needs_k8s:
                if args.kind:
                    # Use Kind
                    with kind.Kind(args.yaml_file) as k:
                        executor.run_steps(
                            args.yaml_file,
                            kubeconfigs=k.kubeconfigs,
                            work_dir=str(k.work_dir),
                            debug=args.debug,
                            quiet=quiet
                        )
                else:
                    # Use Minikube (default)
                    with minikube.Minikube(args.yaml_file) as mk:
                        executor.run_steps(
                            args.yaml_file,
                            kubeconfigs=mk.kubeconfigs,
                            work_dir=str(mk.work_dir),
                            debug=args.debug,
                            quiet=quiet
                        )
            else:
                executor.run_steps(
                    args.yaml_file,
                    kubeconfigs=args.kubeconfigs if args.kubeconfigs else None,
                    debug=args.debug,
                    quiet=quiet
                )
        elif args.command == "demo-extend":
            # Load demo context
            context = demo.load_demo_context()
            demo.validate_demo_context(context)

            # Create extended model
            model = demo.create_extended_model(context, args.extend_file)

            # Run extension steps
            executor.run_steps(
                model.yaml_file,
                work_dir=context["work_dir"],
                debug=args.debug,
                quiet=quiet
            )
        elif args.command == "test":
            yaml_path = Path(args.yaml_file)

            # Check if any sites require Kubernetes
            from sketcher.model import Model
            temp_model = Model(args.yaml_file)
            needs_k8s = any(site.platform == "kubernetes" for _, site in temp_model.sites)

            # Use Kind or Minikube only if sites require Kubernetes
            if needs_k8s:
                cluster_mgr = kind.Kind(args.yaml_file) if args.kind else minikube.Minikube(args.yaml_file)
                with cluster_mgr as cm:
                    kubeconfigs = cm.kubeconfigs
                    work_dir = str(cm.work_dir)
            else:
                # No cluster needed - use temporary directory
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix="sketcher-")
                kubeconfigs = None
                work_dir = temp_dir

            try:
                # Generate README
                utils.info("Generating README...", quiet=quiet)
                generator.generate_readme(args.yaml_file)

                # Run main steps
                utils.info("Running main steps...", quiet=quiet)
                executor.run_steps(
                    args.yaml_file,
                    kubeconfigs=kubeconfigs,
                    work_dir=work_dir,
                    debug=args.debug,
                    quiet=quiet
                )

                # Find and run extension files
                pattern = str(yaml_path.parent / "skewer-*.yaml")
                extend_files = sorted(glob.glob(pattern))

                for extend_file in extend_files:
                    if extend_file == str(yaml_path):
                        continue

                    utils.info("\nRunning extension: {}", extend_file, quiet=quiet)

                    # Create extended model
                    context = {
                        "sites": {},
                        "work_dir": work_dir
                    }

                    # Build context from model
                    base_model = Model(args.yaml_file, kubeconfigs)
                    for site_name, site in base_model.sites:
                        context["sites"][site_name] = {
                            "platform": site.platform,
                            "env": dict(site.env),
                            "namespace": site.namespace if site.namespace else None
                        }

                    # Create and run extended model
                    extended_model = demo.create_extended_model(context, extend_file)
                    executor.run_steps(
                        extended_model.yaml_file,
                        work_dir=work_dir,
                        debug=args.debug,
                        quiet=quiet
                    )
            finally:
                # Clean up temp directory if we created one
                if not needs_k8s:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
        elif args.command == "clean":
            # Remove __pycache__ directories
            for pycache in Path(".").rglob("__pycache__"):
                import shutil
                shutil.rmtree(pycache)
                utils.info("Removed {}", pycache)

            # Remove .demo-context.json files
            for context_file in Path(".").rglob(".demo-context.json"):
                context_file.unlink()
                utils.info("Removed {}", context_file)

            utils.cprint("Clean complete", color="green")
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
