import argparse

from tourism_forecasting.workflows import reproduce_workflow

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ml", action="store_true", help="Skip the slower ML suite")
    args = parser.parse_args()
    for artifact in reproduce_workflow(include_ml=not args.no_ml):
        print(artifact)
