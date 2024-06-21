from datetime import datetime

api_keys_dir = "./data/api_keys"


def get_openai_key():
    with open(f"{api_keys_dir}/openai") as f:
        key = f.read()
    return key


def get_serp_key():
    with open(f"{api_keys_dir}/serp") as f:
        key = f.read()
    return key


def get_google_cloud_key():
    with open(f"{api_keys_dir}/google_cloud") as f:
        key = f.read()
    return key


def get_current_datetime():
    return datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
