import argparse

from tourism_forecasting.workflows import backtest_workflow

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ml", action="store_true", help="Run statistical baselines only")
    parser.add_argument("--no-tune", action="store_true", help="Use first pre-specified ML setting")
    args = parser.parse_args()
    for artifact in backtest_workflow(include_ml=not args.no_ml, tune_ml=not args.no_tune):
        print(artifact)
