from datetime import date
import pandas as pd
import json
import requests
from yaml import load, CLoader as Loader
import os
today = date.today()
#path = os.path.abspath(os.path.join("./", os.pardir))

apikeys = load( open("api_keys.yaml",
                    'rb'), Loader=Loader)




keywords ={"Verizon",
	"Netflix",
	"Goldman Sachs",
	"Teledyne Technologies",
	"Etsy",
	"Activision Blizzard",
	"Kellogg's",
	"Disney",
	"Pfizer",
	"United Parcel Service"
}


column_name = ["date of publication",
               "hour:minute of publication",
               "Title",
               "Summary/Description", 
               "Body/Contents",
               "Source",
               "Metadata"]
