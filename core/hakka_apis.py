import base64, json, requests
from pathlib import Path
from core.utils import getCurrentDatetime

class HakkaAPIs():
    def __init__(self):
        '''Using ASR and TTS APIs from 黑客松. Coding by Mao-Huan Hsu.'''
        self.asr_server_url = 'http://203.145.221.230:7004'
        self.tts_server_url = 'http://203.145.221.230:10101'
        self.headers = {'Content-Type': 'application/json'}
        self.audios_dir = Path('./data/audios')
        self.audios_dir.mkdir(parents=True, exist_ok=True)

    # ASR API
    def recognizeSpeech(self, audio_b64):
        '''Send a speech audio to API server and get the text.'''
        audio_url = 'data:audio/wav;base64,' + audio_b64

        return self.getASRResult(audio_url)

    def recognizeSpeechTest(self, path):
        '''Test for API.'''
        with open(path, 'rb') as file:
            audio_b64 = base64.b64encode(file.read()).decode('utf-8')
        audio_url = 'data:audio/wav;base64,' + audio_b64

        return self.getASRResult(audio_url)

    def getASRResult(self, audio_url):
        '''Get result from API Server.'''
        audio_json = json.dumps({'fn_index': 0, 'data': [None, {'data': audio_url, 'name': 'audio'}]})
        response = json.loads(requests.post(self.asr_server_url + '/run/predict', data=audio_json, headers=self.headers).text)
        result = response['data'][0]
        for s in ['，', '。', '？', ' ']:
            result = result.replace(s, '')

        return result
    

    # TTS API
    def textToSpeech(self, text, save=False):
        '''Send the text to API server and get a speech audio.'''
        text_json = json.dumps({'fn_index': 0, 'data': [text]})
        response = json.loads(requests.post(self.tts_server_url + '/run/predict', data=text_json, headers=self.headers).text)
        result = response['data'][0]['name']
        audio = requests.get(self.tts_server_url + f'/file={result}').content
        audio_url = 'data:audio/wav;base64,' + base64.b64encode(audio).decode('utf-8')

        if save:
            self.saveAudio(audio)

        return audio_url

    def saveAudio(self, audio):
        savename = getCurrentDatetime()
        with open(self.audios_dir/f'{savename}.wav', 'wb') as f:
            f.write(audio)