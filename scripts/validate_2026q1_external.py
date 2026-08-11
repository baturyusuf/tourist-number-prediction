from tourism_forecasting.external_validation_2026q1 import (
    build_2026q1_external_validation_artifacts,
)

if __name__ == "__main__":
    for artifact in build_2026q1_external_validation_artifacts():
        print(artifact)
