from tourism_forecasting.external_data import assess_external_data_files

if __name__ == "__main__":
    for artifact in assess_external_data_files():
        print(artifact)
