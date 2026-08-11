"""Build publication tables and figures from an immutable forecast run."""

from __future__ import annotations

import argparse

from tourism_forecasting.final_artifacts import build_publication_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--forecast-path",
        help="Explicit rolling_origin_forecasts.csv; defaults to the latest immutable run",
    )
    parser.add_argument("--results-root", default="results")
    parser.add_argument("--tables-dir", default="reports/tables")
    parser.add_argument("--figures-dir", default="reports/figures")
    parser.add_argument(
        "--models",
        nargs="+",
        help="Optional publication shortlist (default: seasonal naive plus top models)",
    )
    parser.add_argument("--bootstrap-repetitions", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=20250811)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifacts = build_publication_artifacts(
        args.forecast_path,
        results_root=args.results_root,
        tables_dir=args.tables_dir,
        figures_dir=args.figures_dir,
        shortlist=args.models,
        bootstrap_repetitions=args.bootstrap_repetitions,
        seed=args.seed,
    )
    print(f"Forecast source: {artifacts.forecast_path}")
    print(f"Shortlist: {', '.join(artifacts.shortlist)}")
    for path in (*artifacts.tables, *artifacts.figures):
        print(path)


if __name__ == "__main__":
    main()
