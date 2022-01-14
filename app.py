from flask import Flask, request, abort, render_template
from urllib.parse import parse_qsl
# import linebot related
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,ImageMessage,
    LocationSendMessage, ImageSendMessage, StickerSendMessage,
    VideoSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction, MessageAction, URIAction,
    PostbackEvent, ConfirmTemplate, CarouselTemplate, CarouselColumn,
    ImageCarouselTemplate, ImageCarouselColumn, FlexSendMessage
)
import sqlite3
import string
import random
import os
import shutil

app = Flask(__name__, static_url_path='/static')

@app.route("/")
def index():
    return render_template('index.html')

line_bot_api = LineBotApi('lT8CQ+Ctv3CP8IovOJdw5nB80vDQKhWainVP8RXfUKiD3FaeapzrRSSsIKikg1xC/7dU2PD/OX5niDeMCyaAVIiOZcVgCE5rJ4PIlXECy5oEkMV7MagXxhU5l/EdG2uZI0PGWSycKom3hn5BsxFrvgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('252fdc00930ada746fdfba3782622e52')
global lot_class
lot_class = 62

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        print('receive msg')
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# linebot處理照片訊息
@handler.add(MessageEvent, message = ImageMessage)
def handle_image_message(event):
    # 整理圖片存取資料夾
    image_filenames = os.listdir('linebot_image')
    for img_del in image_filenames:
        os.remove(f'linebot_image/{img_del}')
    image_filenames = os.listdir('detect_image')
    for img_del in image_filenames:
        shutil.rmtree(f'detect_image/{img_del}')

    # 使用者傳送的照片
    message_content = line_bot_api.get_message_content(event.message.id)

    # 照片儲存名稱
    fileName = event.message.id + '.jpg'

    # 儲存照片
    with open('./linebot_image/' + fileName, 'wb')as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)
    
    # # linebot回傳訊息
    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextSendMessage(text='數位廟公解籤中!!!施主請稍待'))
    
    # 接圖片辨識模型
    os.system('python3 yolov5/detect.py --weights best.pt --source linebot_image --project detect_image --save-txt')
    image_filenames = os.listdir('detect_image')
    exp_floder = image_filenames[0]
    txt_file = os.listdir(f'detect_image/{exp_floder}/labels')
    if txt_file:
        if '.txt' in txt_file[0]:
            f = open(f'detect_image/{exp_floder}/labels/{txt_file[0]}','r')
            temp_string = f.readline()
            global lot_class
            lot_class = int(temp_string.split(' ')[0])
            # linebot回傳訊息

            # lot_class = 1

            reply_content = reply_lot_content_first(lot_class)
            reply_string = f'{reply_content[0]}\n\n【籤詩釋義】\n{reply_content[1]}\n\n【籤詩解析】\n{reply_content[2]}\n\n【籤詩典故】\n{reply_content[3]}\n\n請問有無想問之事?'
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_string))
        else:
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f'線上廟公無法解析靈籤，請清楚拍攝並再上傳一次~'))
 
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f'線上廟公無法解析靈籤，請清楚拍攝並再上傳一次~'))
 
@handler.add(MessageEvent, message = TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    user_name = line_bot_api.get_profile(user_id).display_name
    question_name_list = ['討海','作塭','魚苗','求財','耕作','經商','月令','六甲','婚姻','家運','失物','尋人','遠信','六畜','築室','移居','墳墓','出外','行舟','凡事','治病','作事','功名','官事','家事','求兒']
    user_question = event.message.text
    global lot_class
    question_type = None
    for queation_index in range(len(question_name_list)):
        if question_name_list[queation_index] in user_question:
            question_type = queation_index
            reply_question = str(reply_lot_question(lot_class,question_type))
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_question)) 
        elif '電子籤詩' in user_question:
            lot_img = reply_lot_image(lot_class)
            if lot_img == 62:
                reply_question = '線上廟公還未看到靈籤，請清楚拍攝靈籤並上傳~'
                line_bot_api.reply_message(
                    event.reply_token,
                TextSendMessage(text=reply_question)) 
            else:           
                line_bot_api.reply_message(
                    event.reply_token,
                    ImageSendMessage(original_content_url=lot_img,preview_image_url=lot_img))
        elif '使用說明'  in user_question:
            reply_question = f'{user_name} 您好!\n使用方法請遵循以下步驟:\n\n1. 上傳靈籤圖片並耐心等待。\n\n2. 收到線上廟公回覆後，可詢問欲解之事。\n\n3. 點擊下方"電子籤詩"可獲得線上廟公贈與之靈籤籤詩一張。\n\n求籤祈福、心誠則靈\n線上廟公祝您使用愉快!'
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_question)) 
    if question_type ==None:
            reply_question = str(reply_lot_question(lot_class,question_type))
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_question)) 


def reply_lot_image(lot_class):
    #ngrok_url = 'https://ai110110.ncuedu.tw'
    ngrok_url = 'https://ailots.ncuedu.tw'

    print(lot_class)
    if lot_class == 62:
        reply_content = 62
        return reply_content
    else :
        img_path = f'/static/img/{lot_class}.jpg'
        reply_content = f'{ngrok_url}{img_path}'
        return reply_content

def db_connection(func):
    def warp(*args):
        global conn
        conn = sqlite3.connect('Linebot.db')
        output = func(*args)
        if conn is not None:
            conn.close()
        return output
    return warp 

@db_connection 
def reply_lot_content_first(lot_class = 61):
    if lot_class == 61:
        reply_content = '線上廟公無法解析靈籤，請清楚拍攝並再上傳一次~'
        return reply_content
    sql = f"SELECT `lot_name`, `translation`,`explaination`,`story` from `lots` WHERE `serial`='{lot_class}'"
    cursor = conn.cursor()
    cursor.execute(sql)
    data = cursor.fetchone()
    return data

@db_connection 
def reply_lot_question(lot_class,question_type = None):
    if lot_class==62:
        reply_content = '線上廟公還未看到靈籤，請清楚拍攝靈籤並上傳~'
        return reply_content
    if question_type == None:
       reply_content = '線上廟公不了解您的問題，可問之事有:討海、作塭、魚苗、求財、耕作、經商、月令、六甲、婚姻、家運、失物、尋人、遠信、六畜、築室、移居、墳墓、出外、行舟、凡事、治病、作事、功名、官事、家事、求兒。'
       return reply_content


    sql = f"SELECT `t{question_type}` from `lots` WHERE `serial`='{lot_class}'"
    cursor = conn.cursor()
    cursor.execute(sql)
    data = cursor.fetchone()
    return data[0]






# run app
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5007, debug=True)
