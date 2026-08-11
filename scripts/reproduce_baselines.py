from tourism_forecasting.workflows import reproduction_workflow

if __name__ == "__main__":
    for artifact in reproduction_workflow():
        print(artifact)
