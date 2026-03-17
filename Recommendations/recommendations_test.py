# importing the requests library
import requests
from pprint import pprint

asset = str(input('please enter the asset name for searching for recommendations'))
# api-endpoint
URL= "http://entity.de.search.sky.com/suggest/v1/ethan/search/4/0/6763a321151506567878?limit=54&src=svod&term= %s" % asset
r = requests.get(url=URL)
# extracting data in json format
data = r.json()
uuid= data['results'][0]['uuid']
print("UUID of asset {} is : {} \n" .format(asset, uuid))
#fetching more like Dthis
more_like_this = "https://almanac.search.sky.com/eeg/4/0/more-like-this/%s" %uuid
print(more_like_this)
PARAMS= {'contentSegment': 'Cinema'}

headers = {'X-SkyOTT-Territory' : 'DE',
'X-SkyOTT-Proposition': 'SKYQ',
'X-SkyOTT-Provider': 'SKY',
'X-SkyOTT-Device':'MOBILE',
'X-SkyOTT-Platform': 'ANDROID',
'X-SkyOTT-Application': 'SKYQ/21.3.0'}

data = requests.get(url=more_like_this, params=PARAMS, headers=headers)
read_data = data.json()
recs = read_data['results'][0]['recommendations']
pprint('The recommendations for asset {} are'.format(asset))
for rec in recs:
    title_rec = rec['t']
    pprint(title_rec)