from tourism_forecasting.workflows import audit_workflow

if __name__ == "__main__":
    for artifact in audit_workflow():
        print(artifact)
