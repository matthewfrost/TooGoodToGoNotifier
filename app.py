from tgtg import TgtgClient
import requests
import time
import configparser

class Bag:
    def __init__(self, location, availableBags):
        self.location = location
        self.availableBags = availableBags
    
    def __str__(self):
        return "Location: {location} \nAvailable bags: {count}\n".format(location=self.location, count=self.availableBags)

config = configparser.ConfigParser()
config.read("config.env")

tgtgSettings = config["Too good to go"]

client = TgtgClient(email=tgtgSettings["email"], password=tgtgSettings["password"])
bot_token=config["Telegram"]["botToken"]
chat_id=config["Telegram"]["chatId"]

sentObjects = []
while True: 
    print("Getting bags")
    availableObjects = []
    objectsToSend = [] 

    response = client.get_items(
        favorites_only=True,
        latitude=config["Location"]["latitude"],
        longitude=config["Location"]["longitude"],
        radius=config["Location"]["radius"],
    )

    #reading the response and adding to list
    for x in response:
        storeText = ""
        if x["items_available"] != 0:
            #storeText += "Location: {location} \n".format(location=x["display_name"])
            #storeText += "Available bags: {items} \n".format(items=x["items_available"])
            #availableLocations.append(storeText)
            availableObjects.append(Bag(x["display_name"], x["items_available"]))
      
    for bag in availableObjects:
        if not any(element.location == bag.location for element in sentObjects):
            sentObjects.append(bag)
            objectsToSend.append(bag)

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": "\n".join(str(x) for x in objectsToSend)
    }

    resp = requests.get(url, params=params)

    time.sleep(300)