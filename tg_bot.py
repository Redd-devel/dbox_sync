import requests
from libs.api_acts import instantiate_dropbox, APIActions

drop_obj = APIActions(instantiate_dropbox())
token = ''
URL = 'https://api.telegram.org/bot' + token + '/'


def get_updates():
    url = URL + 'getUpdates'
    r = requests.get(url)
    return r.json()

def get_message():
    data = get_updates()

    last_object = data['result'][-1]

    chat_id = last_object['message']['chat']['id']
    message_text = last_object['message']['text']
    message = {
        'chat_id': chat_id,
        'text': message_text
    }
    return message

def send_message(chat_id, text='Wait a sec please...'):
    url = URL + f'sendMessage?chat_id={chat_id}&text={text}'
    requests.get(url)

def get_files():
    files = drop_obj.dbox_list_files("")[1][0][:5]
    answer = get_message()
    chat_id = answer['chat_id']
    text = answer['text']
    if text == '/dbox':
        # send_message(chat_id, files)
        for file in files:
            send_message(chat_id, file)
        

if __name__ == '__main__':
    get_files()