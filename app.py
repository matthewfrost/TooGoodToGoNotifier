from sqlite3.dbapi2 import Cursor
from tgtg import TgtgClient
import requests
import configparser
import sqlite3
import os

config = configparser.ConfigParser()
config.read("config.env")

con = sqlite3.connect("base.db")

class Bag:
    def __init__(self, store_id, location, availableBags):
        self.store_id = store_id
        self.location = location
        self.availableBags = availableBags
    
    def __str__(self):
        return "Location: {location} \nAvailable bags: {count}\n".format(location=self.location, count=self.availableBags)

def init_db():
    cursor = con.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS bags(store_id INTEGER PRIMARY KEY, store_name TEXT, available_bags INTEGER)")

    return cursor

def init_tgtg():
    if not "access_token" in os.enivron:
        client = TgtgClient(email=os.environ["email"])
        client.get_credentials()
    else:
        client = TgtgClient(access_token=os.enivron["access_token"], refresh_token=os.enivron["refresh_token"], user_id=os.enivron["user_id"])
    
    os.enivron["access_token"] = client.access_token
    os.enivron["refresh_token"] = client.refresh_token
    os.enivron["user_id"] = client.user_id
    # with open("config.env", "w") as configFile:
    #     config.write(configFile)
    return client

def get_saved_bags(cursor):
    savedBags = []
    for row in cursor.execute("SELECT * FROM bags"):
        print(row)
        savedBags.append(Bag(row[0], row[1], row[2]))
    return savedBags

#Compares the bags in the database with the ones retrieve from the API
#If a bag exists in the database but not in the API results then it is removed
def remove_old_bags(cursor, saved_bags, new_bags):
    bagsToRemove = []
    for bag in saved_bags:
        #if a saved bag does not exist in the new bags then it must not be available anymore
        if not any(element.location == bag.location for element in new_bags):
            bagsToRemove.append(bag)
    
    for bag in bagsToRemove:
        cursor.execute("DELETE FROM bags WHERE store_name = ?", [bag.location])
    
    con.commit()

    return list(set(bagsToRemove).difference(set(saved_bags)))

def get_new_bags(tgtgClient):
    response = tgtgClient.get_items(
        favorites_only=True,
        latitude=os.environ["latitude"],
        longitude=os.environ["longitude"],
        radius=os.environ["radius"],
    )

    newBags = []
    #reading the response and adding to list
    for x in response:
        if x["items_available"] != 0:
            cursor.execute("INSERT OR REPLACE INTO bags (store_id, store_name, available_bags) VALUES(?, ?, ?)", [x["store"]["store_id"], x["display_name"], x["items_available"]])
            newBags.append(Bag(x["store"]["store_id"], x["display_name"], x["items_available"]))
        con.commit()
    
    return newBags

def send_telegram_message(bags):
    telegramSettings = config["Telegram"]
    bot_token=os.environ["bottoken"]
    chat_id=os.environ["chatid"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": "\n".join(str(x) for x in bags)
    }

    resp = requests.get(url, params=params)




cursor = init_db()

#tgtgSettings = config["Too good to go"]

#locationSettings = config["Location"]

client = init_tgtg()



print("Getting bags")

objectsToSend = [] 

newBags = get_new_bags(client)
existingBags = get_saved_bags(cursor)
newBags = remove_old_bags(cursor, existingBags, newBags)

send_telegram_message(newBags)
