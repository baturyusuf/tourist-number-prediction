from tourism_forecasting.gtd_analysis import build_gtd_robustness_artifacts

if __name__ == "__main__":
    for artifact in build_gtd_robustness_artifacts():
        print(artifact)
