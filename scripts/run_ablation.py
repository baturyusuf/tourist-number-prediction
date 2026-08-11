"""Run the snapshot-vintage macro/travel-cost feature-block sensitivity."""

from __future__ import annotations

import argparse

from tourism_forecasting.ablation import run_snapshot_vintage_ablation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-repetitions", type=int, default=2_000)
    args = parser.parse_args()
    artifacts = run_snapshot_vintage_ablation(bootstrap_repetitions=args.bootstrap_repetitions)
    print(f"Run ID: {artifacts.run_id}")
    for path in (*artifacts.immutable_paths, *artifacts.publication_paths):
        print(path)


if __name__ == "__main__":
    main()
