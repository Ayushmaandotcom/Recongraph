import argparse
import sys

def main() -> None:
    parser = argparse.ArgumentParser(description="ReconGraph 2.0 Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: benchmark
    benchmark_parser = subparsers.add_parser("benchmark", help="Run the ReconBench evaluation suite")
    benchmark_parser.add_argument("--size", type=int, default=1000, help="Number of scenarios to generate and run")
    benchmark_parser.add_argument("--faf", action="store_true", help="Enable Failure Analysis Framework (FAF) generation")

    args = parser.parse_args()

    if args.command == "benchmark":
        from recongraph.benchmark.runner import execute_reconbench
        sys.exit(execute_reconbench(size=args.size, enable_faf=args.faf))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
