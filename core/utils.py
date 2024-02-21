from datetime import datetime

api_keys_dir = './data/api_keys'

def getOpenAIKey():
    with open(f'{api_keys_dir}/openai') as f:
        key = f.read()
    return key

def getSerpKey():
    with open(f'{api_keys_dir}/serp') as f:
        key = f.read()
    return key

def getGoogleCloudKey():
    with open(f'{api_keys_dir}/google_cloud') as f:
        key = f.read()
    return key

def getCurrentDatetime():
    return datetime.now().strftime('%Y%m%d_%H%M%S%f')[:-3]
