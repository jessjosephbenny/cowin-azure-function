import os
import logging
import time
import requests
import threading
import smtplib, ssl
from datetime import date,datetime,timedelta,timezone

import azure.functions as func

headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        }
API_URL = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict'

district_ids = [300, 301, 304, 306, 307]
EMAIL_MSG_PRE = 'Hi\nVaccine Slots are available on\n'
EMAIL_MSG_POS = '\nRegards\n Cowin Notification System'
EMAIL_SUBJECT = 'Update on Cowin Available slots'
port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = os.environ['mail_email']
receiver_email = os.environ['receiver_email']
password = os.environ['mail_auth']
last_email_time = datetime.fromisoformat('2021-05-01 00:00:00.000')


context = ssl.create_default_context()

def triggerCowinSlotCheck(server):
    currentDate = date.today()
    available_slots = []
    for district_id in district_ids:
        for day in range(0, 14,7):
            dateToCheck = (currentDate + timedelta(days=day)).strftime("%d-%m-%Y")
            response = requests.get(f'{API_URL}?district_id={district_id}&date={dateToCheck}', headers=headers)
            response = response.json()
            centers = response['centers']
            for center in centers:
                sessions = center['sessions']
                for session in sessions:
                    if session['min_age_limit']==18 and session['available_capacity'] >0:
                        available_slots.append(
                            {
                                'date': session['date'],
                                'location': center['name']
                            }
                        )
    global last_email_time
    email_needed = True if last_email_time + timedelta(hours=1) < datetime.now() else False
    if len(available_slots)>0 and email_needed :
        last_email_time = datetime.now()
        msg = EMAIL_MSG_PRE
        for available_slot in available_slots:
            msg = f"{msg}\nDate: {available_slot['date']} Location: {available_slot['location']}\n"
        msg = msg + EMAIL_MSG_POS
        print(msg)
        msg = 'Subject: {}\n\n{}'.format(EMAIL_SUBJECT, msg)
        logging.info('Email Notification Sent')
        server.sendmail(sender_email,receiver_email,msg)

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.utcnow().replace(
        tzinfo=timezone.utc).isoformat()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        triggerCowinSlotCheck(server)
    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
