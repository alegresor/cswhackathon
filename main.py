from math import *
import requests
import pandas as pd
import re
import urllib.parse
import pickle


def get_data():
    reqget = requests.get(
        url = 'https://www.chicagosfoodbank.org/find-food/covid-19-neighborhood-sites/',
        headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'})
    html = reqget.content
    df_list = pd.read_html(html)
    df = df_list[-1]
    df.columns = df.iloc[1]
    df = df[2:]
    df.to_csv('data/raw.csv',index=False)

def clean():
    df = pd.read_csv('data/raw.csv')
    # remove location info between () and add Chicago, IL
    df['Location(s)'] = [re.sub(r'\([^)]*\)','',l)+', Chicago, IL' for l in df['Location(s)'].tolist()] 
    df.to_csv('data/clean.csv',index=False)  

def add_lat_long():
    df = pd.read_csv('data/clean.csv')
    l = len(df)
    adds = df['Location(s)'].tolist()
    lats = [.7 for i in range(l)]
    lons = [.7 for i in range(l)]
    for i in range(l):
        url = 'https://nominatim.openstreetmap.org/search/' + adds[i] +'?format=json'
        response = requests.get(url).json()
        lats[i] = response[0]["lat"]
        lons[i] = response[0]["lon"]
    df['lat'] = lats
    df['lon'] = lons
    df.to_csv('data/full.csv',index=False)  

def dist_from_ll(lat1,lon1,lat2,lon2):
    # https://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude
    R = 6373.0 # approximate radius of earth in km        
    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    dist_km = R * c
    dist_miles = 0.621371*dist_km
    return dist_miles

def get_nearby_users():
    # food dataframe
    dffull = pd.read_csv('data/full.csv')
    lfull = len(dffull)
    lats = dffull['lat'].tolist()
    lons = dffull['lon'].tolist()
    # users dataframe
    df = pd.read_csv('data/users.csv')
    l = len(df)
    adds = df['address'].tolist()
    rads = df['radius'].tolist() # radius for each user
    names = df['name'].tolist()
    emails = df['email'].tolist()
    dfemail = {'name':[],'email':[],'bullets':[]}
    for i in range(l):
        url = 'https://nominatim.openstreetmap.org/search/' + adds[i] +'?format=json'
        response = requests.get(url).json()
        ulat = response[0]["lat"]
        ulon = response[0]["lon"]
        urad = rads[i]
        # draft bullet points of email to user
        ustr = ''
        for j in range(lfull):
            dist = dist_from_ll(ulat,ulon,lats[j],lons[j])
            if dist < urad:
                row = dffull.loc[j]
                fields = row[['Partner','Location(s)','Community Area','Schedule']].tolist()
                ustr += '- %s at %s in %s on %s\n'%tuple(fields)
        if len(ustr)>0:
            dfemail['name'].append(names[i])
            dfemail['email'].append(emails[i])
            dfemail['bullets'].append(ustr)
    if len(dfemail['name'])==0: raise Exception("No users to email")
    pd.DataFrame(dfemail).to_csv('data/bullets.csv',index=False)

def draft_email():
    pbar = lambda: print('%s\n\n'%(100*'~'))
    pbar()
    df = pd.read_csv('data/bullets.csv')
    l = len(df)
    names = df['name'].tolist()
    emails = df['email'].tolist()
    bullets = df['bullets'].tolist()
    emails_lst = []
    for i in range(l):
        body = 'Dear %s,\n\nWe have identified the following food opportunities near you!\n\n%s\n\n'%(names[i],bullets[i])
        fullemail = 'From: %s\nTo: %s\nSubject: %s\n\n%s'%('customemail@gmail.com',emails[i],'Food Opportunity',body)
        emails_lst.append(fullemail)
        print('\n%s'%fullemail)
        pbar()
    with open('data/emails.pkl','wb') as f: pickle.dump(emails_lst,f)

if __name__ == '__main__':
    get_data()
    clean()
    add_lat_long(df)
    get_nearby_users()
    draft_email()

