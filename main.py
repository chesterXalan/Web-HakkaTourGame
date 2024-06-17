import time, random
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO, emit
from core.utils import get_openai_key, get_serp_key, get_google_cloud_key
from core.langchain_ import LangChain, StreamResponseHandler
from core.hakka_apis import HakkaAPIs
from core.county_selector import CountySelector


__title = '客語互動式觀光遊戲'
__description = '使用ChatGPT結合客語進行台灣觀光'
__version = '2024.0617'

app = Flask(__name__)
csrf = CSRFProtect() # CSRF protection
csrf.init_app(app)
socketio = SocketIO(app)
langchain = LangChain(get_openai_key(), get_serp_key())
hakka_apis = HakkaAPIs()
county_selector = CountySelector()
user_dict = {}


'''
用於 SSL 認證發放
@app.route('/.well-known/pki-validation/95CD7B4A2B56F22C883B0CDB0A23CBFE.txt')
def pkiValidation():
    return app.send_static_file('./files/95CD7B4A2B56F22C883B0CDB0A23CBFE.txt')
'''

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('./icons/coastline.png')

@app.route('/')
def index():
    return render_template('index.html', title=__title, description=__description, version=__version)

@app.route('/game')
def game():
    return render_template('game.html', title=__title, googleCloudKey=get_google_cloud_key())

@app.route('/settings')
def settings():
    return render_template('settings.html', title=__title)


def __api_warmup():
    hakka_apis.recognize_speech_test(path='./data/audios/_test-asr.wav')
    hakka_apis.text_to_speech('哈囉你好嗎？')

def show_taiwan_map():
    image = county_selector.show_map(county_selector.xml_root)
    emit('update_taiwan_map', {'map': image})

def update_taiwan_map(game_map, last_id, visited_id):
    county = county_selector.counties
    num_county = len(county)
    rand_id = num_county*2 + random.randrange(num_county)
    
    time.sleep(1)
    for i in range(rand_id, -1, -1):
        if i > num_county:
            time.sleep(0.1)
        elif i > 5:
            time.sleep(0.2)
        else:
            time.sleep(0.3)

        if last_id:
            new_id = (last_id+1) + (rand_id-i) % num_county
        else:
            new_id = (rand_id-i) % num_county

        if new_id >= num_county:
            new_id -= num_county
        while new_id in visited_id:
            new_id += 1
            if new_id == num_county:
                new_id = 0

        image = county_selector.update_map(county_selector.copy_map(game_map), new_id)
        emit('update_taiwan_map', {'map': image})
    new_game_map = county_selector.save_map(county_selector.copy_map(game_map), new_id)

    return new_game_map, new_id, county[new_id]

@socketio.on('game_startup')
def game_startup(data):
    connect_time = data['connect_time']
    game_params = data['game_params']

    chain_game = langchain.set_chain(prompt=langchain.prompt_game(game_params['num_county'], game_params['num_attr']),
                                    llm=langchain.chatgpt(streaming=True,
                                                          callbacks=[StreamResponseHandler(emit, 'update_output_text')]))
    chain_attr = langchain.set_chain(prompt=langchain.prompt_attraction(),
                                    llm=langchain.chatgpt())
    user_dict[connect_time] = dict(game_idx=1,
                                   num_county=game_params['num_county'],
                                   game=chain_game,
                                   attr=chain_attr,
                                   attr_list=None,
                                   game_map=county_selector.copy_map(),
                                   countyid_last=None,
                                   countyid_visited=[])
    show_taiwan_map()
    emit('game_start')

@socketio.on('get_user_text_input')
def text_to_speech(data):
    user_input = data['user_input']
    audio = hakka_apis.text_to_speech(text=user_input)
    emit('user_tts', {'audio': audio})

@socketio.on('get_game_text_output')
def text_to_speech(data):
    game_output = data['game_output']
    audio = hakka_apis.text_to_speech(text=game_output)
    emit('game_tts', {'audio': audio})

@socketio.on('voice_recorded')
def speech_to_text(data):
    voice = data['voice']
    text = hakka_apis.recognize_speech(audio_b64=voice)
    emit('speech_to_text', {'text': text})

@socketio.on('invalid_attr')
def invalid_attr(data):
    connect_time = data['connect_time']
    county_name = county_selector.counties[user_dict[connect_time]['countyid_last']]
    emit('update_google_map', {'text': county_name})

@socketio.on('submit_user_voice_input')
def play(data):
    connect_time = data['connect_time']
    user_input = data['user_input']
    user_data = user_dict[connect_time]
    
    if user_data['game_idx'] == 1: # 開始遊戲、回答題目
        emit('clear_output_text')
        user_data['game'].run(input=user_input); emit('game_tts_autoplay')
        if len(user_data['countyid_visited']) < user_data['num_county']:
            emit('show_taiwan_map')
            user_data['game_idx'] = 2
        else:
            image = county_selector.show_map(user_data['game_map'])
            emit('game_over', {'map': image}) # 顯示最後的遊戲地圖
            user_data['game_idx'] = 4

    elif user_data['game_idx'] == 2: # 抽選縣市
        user_data['game_map'], county_id, county_name = update_taiwan_map(user_data['game_map'], user_data['countyid_last'], user_data['countyid_visited'])
        user_data['countyid_last'] = county_id
        user_data['countyid_visited'].append(county_id)
    
        emit('clear_output_text')
        response_game = user_data['game'].run(input=county_name); emit('game_tts_autoplay')
        user_data['attr_list'] = langchain.get_list_output(user_data['attr'].run(input=response_game))
        user_data['game_idx'] = 3

    elif user_data['game_idx'] == 3: # 選擇景點
        if user_input in user_data['attr_list']:
            emit('show_google_map')
            emit('update_google_map', {'text': data['user_input']})

            emit('clear_output_text')
            user_data['game'].run(input=user_input); emit('game_tts_autoplay')
            user_data['game_idx'] = 1
        else:
            emit('wrong_choice')

    elif user_data['game_idx'] == 4: # 遊戲結束
        return

@socketio.on('page_close')
def page_close(data):
    connect_time = data['connect_time']
    langchain.save_chain_history(user_dict[connect_time]['game'], connect_time)
    del user_dict[connect_time] # delete key


if __name__ == '__main__':
    #__api_warmup()
    socketio.run(app,
                 host='127.0.0.1',
                 port=5000,
                 debug=False)
