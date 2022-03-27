import json
import time
from bs4 import BeautifulSoup as BS
from urllib import request as ulrlib2
from selenium import webdriver
import boto3
from botocore.exceptions import ClientError
import sqlalchemy as db
from sqlalchemy import Column, DateTime, Float, SmallInteger, String, TIMESTAMP
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from datetime import datetime

# declarative base class
Base = declarative_base()


def connect_db():
    engine = db.create_engine(
        'mysql+pymysql://admin:admin123@127.0.0.1:3306/apartments_pricing')
    connection = engine.connect()
    metadata = db.MetaData()
    return(connection, engine, metadata)


def send_email(sender, receiver, email_body, subject):
    CHARSET = "UTF-8"
    client = boto3.client('ses', region_name="us-east-1")

    html = f'''<html>
<head></head>
<body>
  <h1>Something changed</h1>
  <p>{email_body}</p>
</body>
</html>'''
# Try to send the email.
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    receiver,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': html
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': subject
                },
            },
            Source=sender
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


class Unit(Base):
    # A simple class
    # attribute
    __tablename__ = 'price_log'
    unit_number = Column('unit_no', String(10), primary_key=True)
    price = Column('price', Float)
    bedroom = Column('bedrooms', SmallInteger)
    available_on = Column('availability', String(45))
    lease_term = Column('lease_term', String(45))
    timestamp = Column('timestamp', TIMESTAMP, primary_key=True,
                       nullable=False, default=datetime.now())

    def __init__(self, unit_number, price, bedroom, available_on, lease_term):
        self.unit_number = unit_number
        self.price = price
        self.bedroom = bedroom
        self.available_on = available_on
        self.lease_term = lease_term

    def __hash__(self):
        return hash(self.unit_number)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.unit_number == other.unit_number

    def print_data(self):
        print(self.unit_number)
        print(self.price)
        print(self.bedroom)
        print(self.available_on)
        print(self.lease_term)
        print(self.timestamp)

    def text_data(self):
        text = "\n*******\n"
        text += "Unit Number: "
        text += str(self.unit_number)
        text += "\n"
        text += "Price: "
        text += str(self.price)
        text += "\n"
        text += "Bedrooms: "
        text += str(self.bedroom)
        text += "\n"
        text += "Available: "
        text += str(self.available_on)
        text += "\n"
        text += "Lease term: "
        text += str(self.lease_term)
        text += "\n"
        text += "TimeStamp: "
        text += str(self.timestamp)
        text += "\n"
        return text


def get_parse_data(url):
    response = ulrlib2.urlopen(url)
    json_data = json.loads(response.read())
    unit_list = []

    for item in json_data['data']['units']:
        u = Unit(item['unit_number'], item['price'], item['filters']['custom_16512'][1], item['display_available_on'],
                 item['display_lease_term'])
        unit_list.append(u)

    return unit_list


def compare_data(old_list, new_list):
    new_apartments = []
    updated_apartments = []
    sold_out_apartments = []
    old_set = set(old_list)
    new_set = set(new_list)
    for item1 in new_list:
        if item1 in old_set:
            for e in old_set:
                if e.unit_number == item1.unit_number and item1.price != e.price or item1.available_on != e.available_on or item1.lease_term != e.lease_term:
                    updated_apartments.append(item1)
        else:
            new_apartments.append(item1)

    for item2 in old_list:
        if item2 not in new_set:
            sold_out_apartments.append(item2)

    return new_apartments, updated_apartments, sold_out_apartments


def get_text(l1, l2, l3):
    result = "New Apartments:\n"
    for i in l1:
        result += i.text_data()
    result += "\n\n"
    result += "Updated Apartments:\n"
    for i in l2:
        result += i.text_data()
    result += "\n\n"
    result += "Sold out Apartments:\n"
    for i in l3:
        result += i.text_data()
    return result


def getEmbedURL(pageUrl):
    page = ulrlib2.urlopen(pageUrl).read()
    soup = BS(page)
    return (soup.find_all("div", {"class": "displayTextBlockText"})[
          0].find_all("iframe")[0]['src'])


def getDataURL(pageUrl):
    embedUrl = getEmbedURL(pageUrl)
    options = webdriver.ChromeOptions()

    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu-sandbox')
    options.add_argument("--single-process")
    options.add_argument('window-size=1920x1080')
    options.add_argument(
        '"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36"')

    options.binary_location = "/Users/shreyas/workspace/AptPricingHistory/bin/headless-chromium"
    browser = webdriver.Chrome(
        executable_path="/Users/shreyas/workspace/AptPricingHistory/bin/chromedriver", options=options)
    browser.get(embedUrl)
    retries = 10
    data = None
    while not data and retries:
        time.sleep(1)
        cdata = browser.execute_script("return window.__APP_CONFIG__;")
        if cdata:
            data = cdata
        retries -= 1
    return data["sightmaps"][0]["href"]


def insert_data_in_log(list, session):
    for d in list:
        session.add(d)
    session.commit()


def entry_main(a1, a2):
    c, e, m = connect_db()
    session = Session(e)
    url = "https://www.avanasunnyvale.com/floor-plans"
    dataURL = getDataURL(url)
    list = get_parse_data(dataURL)
    insert_data_in_log(list, session)
    price_log = db.Table('price_log', m, autoload=True, autoload_with=e)
    query = db.select([price_log])
    result_proxy = c.execute(query)
    result_set = result_proxy.fetchall()
    print(result_set)
    # l1 = []
    # obj = Unit("912", 2329, 3, "Available Now", "15 Months")
    # l1.append(obj)
    # m1, m2, m3 = compare_data(list, l1)
    # t = get_text(m1, m2, m3)
    # send_email("ps.alchemist@gmail.com", "apurwaj2@gmail.com", t, "test email")


if __name__ == "__main__":
    entry_main("1", "2")
