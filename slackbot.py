import os
import logging
import requests
import random
import calendar
import datetime
import pymysql
import csv
from slack_bolt import App, Say
from flask import Flask, request
from typing import Callable
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler


# token
slacktoken = open("token.txt", "r").readline()
slacksigningtoken = open("token_signing.txt", "r").readline()
os.environ['SLACK_BOT_TOKEN'] = slacktoken
os.environ['SLACK_SIGNING_SECRET'] = slacksigningtoken
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
logger = logging.getLogger(__name__)


# flask
flask_app = Flask(__name__)


# slack post message
def says(channel_id, thread_ts, msg):
    if thread_ts is None:
        client.chat_postMessage(channel=channel_id, text=msg)
    else:
        client.chat_postMessage(channel=channel_id, thread_ts=thread_ts, text=msg)


# daily schedule post
def daily_schedule():
    client.chat_postMessage(channel="CD18BT321", text=weather())
    client.chat_postMessage(channel="CD18BT321", text=salaly())


# weather
def weather():
    html1 = requests.get('https://weather.naver.com/today')
    soup = BeautifulSoup(html1.text, 'html.parser')
    post = soup.find('strong', {'class': 'current'}).text
    minimum = soup.find('span', {'class': 'lowest'}).text
    maximum = soup.find('span', {'class': 'highest'}).text

    html2 = requests.get('https://www.weather.go.kr/w/weather/forecast/short-term.do')
    soup2 = BeautifulSoup(html2.text, 'html.parser')
    total = soup2.find('span', {'class': 'depth_1'}).text
    today = soup2.find('span', {'class': 'depth_2'}).text

    return "%s \n최저 %s \n최고 %s \n\n %s \n %s" % (post, minimum[4:], maximum[4:], total, today)


# stock info
def stock_code_gain(x):
    conn = pymysql.connect\
        (
            host="1.1.1.1",
            port=3307,
            user="id",
            password="pw",
            db='stockcode',
            charset='utf8'
        )
    cur = conn.cursor()
    stock_list = list()
    if cur.execute("SELECT * FROM stocknameandcode where 종목명 = '%s'" % x):
        db_result = cur.fetchall()
        stock_list = '0' * (6 - len(db_result[0][1])) + db_result[0][1]
        html = requests.get('https://finance.naver.com/item/main.naver?code=' + stock_list)
        soup = BeautifulSoup(html.text, 'html.parser')
        # 차트 이미지
        chart = soup.find('img', {'id': 'img_chart_area'})["src"]
        # 종목 정보
        info = soup.dl.text
        return info + chart
    else:
        cur.execute(f"SELECT * FROM stocknameandcode WHERE 종목명 LIKE '%{x}%'")
        for name in cur.fetchall():
            stock_list.append(name[0])
        return "종목명을 이 중에 찾아보세요\n%s" % str(stock_list)


# datetime
def getdays(yyyy, mm, dd):
    return datetime.date(yyyy, mm, dd).weekday()


# salaly
def salaly():
    today = datetime.date.today()

    # end of month
    yyyy_for_end_of_month = today.year
    mm_for_end_of_month = today.month
    dd_for_end_of_month = calendar.monthrange(today.year, today.month)[1]
    if getdays(yyyy_for_end_of_month, mm_for_end_of_month, dd_for_end_of_month) == 5:
        dd_for_end_of_month = dd_for_end_of_month - 1
    elif getdays(yyyy_for_end_of_month, mm_for_end_of_month, dd_for_end_of_month) == 6:
        dd_for_end_of_month = dd_for_end_of_month - 2
    diff_end_of_month = datetime.date(yyyy_for_end_of_month, mm_for_end_of_month, dd_for_end_of_month) - today

    # 10 days
    ten_day = datetime.date(today.year, today.month, 10)
    yyyy_for_ten = ten_day.year
    mm_for_ten = ten_day.month
    dd_for_ten = ten_day.day
    if getdays(yyyy_for_ten, mm_for_ten, dd_for_ten) == 5:
        dd_for_ten = dd_for_ten - 1
    elif getdays(yyyy_for_ten, mm_for_ten, dd_for_ten) == 6:
        dd_for_ten = dd_for_ten - 2
    diff_ten = datetime.date(yyyy_for_ten, mm_for_ten, dd_for_ten) - today

    # 25 days
    twentyfive_day = datetime.date(today.year, today.month, 25)
    yyyy_for_twentyfive = twentyfive_day.year
    mm_for_twentyfive = twentyfive_day.month
    dd_for_twentyfive = twentyfive_day.day
    if getdays(yyyy_for_twentyfive, mm_for_twentyfive, dd_for_twentyfive) == 5:
        dd_for_twentyfive = dd_for_twentyfive - 1
    elif getdays(yyyy_for_twentyfive, mm_for_twentyfive, dd_for_twentyfive) == 6:
        dd_for_twentyfive = dd_for_twentyfive - 2
    diff_twentyfive = datetime.date(yyyy_for_twentyfive, mm_for_twentyfive, dd_for_twentyfive) - today


    if diff_end_of_month.days == 0:
        return "31일 월급 날입니다!\n10일, 25일 월급은 이미 받았습니다"
    elif diff_twentyfive.days == 0:
        return "25일 월급 날입니다!\n31일 월급은 %s일 남았습니다\n10일 월급은 이미 받았습니다" % diff_end_of_month.days
    elif diff_ten.days == 0:
        return "10일 월급 날입니다!\n25일 월급은 %s일\n31일 월급은 %s일 남았습니다" % (diff_twentyfive.days, diff_end_of_month.days)
    elif diff_end_of_month.days > 0 and diff_twentyfive.days < 0:
        return "10, 25일 월급은 이미 받았습니다\n31일 월급은 %s일 남았습니다" % diff_end_of_month.days
    elif diff_ten.days < 0 and diff_twentyfive.days > 0:
        return "10일 월급은 이미 받았습니다\n25일 월급은 %s일\n31일 월급은 %s일 남았습니다" % (diff_twentyfive.days,diff_end_of_month.days)
    elif diff_end_of_month.days < 0:
        return "%s월 월급은 이미 받았습니다 다음 달 월급을 기다리세요" % mm_for_end_of_month
    else:
        return "%s월 월급\n10일 월급은 %s일\n25일 월급은 %s일\n31일 월급은 %s일 남았습니다" % (
        mm_for_end_of_month, diff_ten.days, diff_twentyfive.days, diff_end_of_month.days)


# message reply
@app.event("message")
def handle_message_events(body: dict, say: Callable):
    # ts = body.get('event', {}).get('ts')
    thread_ts = body.get('event', {}).get('thread_ts')
    channel_id = body.get('event', {}).get('channel')
    message = body.get("event", {}).get("text")

    if message == "나루":
        naru = [':naru_1:', ':naru_2:', ':naru_3:', ':naru_4:', ':naru_5:', ':naru_6:', ':naru_7:']
        says(channel_id, thread_ts, random.choice(naru))
    elif message == "퇴근":
        now = datetime.datetime.now()
        today19am = now.replace(hour=19, minute=0, second=0)
        diff_time = today19am - now
        if now < today19am:
            says(channel_id, thread_ts, "퇴근까지 %s 남았습니다" % diff_time)
        else:
            says(channel_id, thread_ts, "퇴근하세요! :naru_5:")


# mention reply
@app.event("app_mention")
def mention_handler(body: dict, say: Callable):
    # ts = body.get('event', {}).get('ts')
    thread_ts = body.get('event', {}).get('thread_ts')
    channel_id = body.get('event', {}).get('channel')
    bot_id = body.get("event", {}).get("text").split()[0]
    message = body.get("event", {}).get("text").replace(bot_id, "").strip()

    if message == "명령어":
        says(channel_id,
             thread_ts,
             """명령어 모음\n
             골라줘 : 하나 고르기 (ex: 골라줘 짜장 짬뽕)\n
             월급 : 월급날 언제인지\n
             날씨 : 현재 날씨\n
             주식 : 주식정보 (ex: 주식 삼성전자)\n"""
             )
    elif message[:3] == "골라줘":
        choose = message.split()
        choose = choose[1:]
        set(choose)
        if len(choose) == 1:
            says(channel_id, thread_ts, "리스트가 똑같습니다.")
        else:
            says(channel_id, thread_ts, "%s 입니다." % random.choice(choose))
    elif message == "날씨":
        says(channel_id, thread_ts, weather())
    elif message[:2] == "주식":
        says(channel_id, thread_ts, stock_code_gain(message[3:]))
    elif message[:2] == "월급":
        says(channel_id, thread_ts, salaly())
    else:
        says(channel_id, thread_ts, "없는 명령어입니다.")


# app home
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    try:
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "callback_id": "home_view",

                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Welcome to Naru's Home* :tada:"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*현재 날씨*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": weather()
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*월급*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": salaly()
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            }
        )

    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


# shortcut
@app.shortcut("naru_post")
def open_modal(ack, body, client):
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "naru_post",
            "title": {"type": "plain_text", "text": "My App"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "input_c",
                    "label": {"type": "plain_text", "text": "naru bot post?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "dreamy_input",
                        "multiline": True
                    }
                }
            ]
        }
    )


# app view
@app.view("naru_post")
def handle_view_events(ack, body, logger):
    ack()
    client.chat_postMessage(channel="CD18BT0GY",
                            text=body.get("view", {}).get("state").get("values").get("input_c").get("dreamy_input").get(
                                "value"))
    logger.info(body)


# handler
handler = SlackRequestHandler(app)


# flask app route
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


# scheduling
sched = BackgroundScheduler(daemon=True)
sched.add_job(daily_schedule, 'cron', week='1-53', day_of_week='0-4', hour='07')
sched.start()


# flask run
if __name__ == "__main__":
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 9998)))
