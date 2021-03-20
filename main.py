from math import *
import requests
import pandas as pd
import re
import urllib.parse
import pickle
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import smtplib, ssl
from email.mime.text import MIMEText

def get_data():
    # available locations
    print('Scraping data from CFB website')
    reqget = requests.get(
        url = 'https://www.chicagosfoodbank.org/find-food/covid-19-neighborhood-sites/',
        headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'})
    html = reqget.content
    df_list = pd.read_html(html)
    df = df_list[-1]
    df.columns = df.iloc[1]
    df = df[2:]
    df.to_csv('data/raw.csv',index=False)
    # Google Form Responses
    print('Gathering responses from google form')
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('_ags_google_credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("Greater Chicago Food Depository (Responses)").sheet1
    list_of_hashes = sheet.get_all_values()
    df = pd.DataFrame(list_of_hashes[1:],columns=['time','email','name','email2','address','radius'])
    df = df[['name','email','address','radius']]
    df.to_csv('data/users.csv',index=False)

def clean():
    print('Cleaning CFB location data')
    df = pd.read_csv('data/raw.csv')
    # remove location info between () and add Chicago, IL
    df['Location(s)'] = [re.sub(r'\([^)]*\)','',l)+', Chicago, IL' for l in df['Location(s)'].tolist()] 
    df.to_csv('data/clean.csv',index=False)  

def add_lat_long():
    print('Gathering lat/lon data for CFB locations')
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
    print('Determining nearby users')
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

def send_emails()
    print('Sending emails to nearby users')
    with open('_ags/google_pw.txt','r') as f: pw = f.read()
    sender = 'asorokin@hawk.iit.edu'
    s = smtplib.SMTP_SSL(host='smtp.gmail.com',port=465)
    s.login(user=sender, password=pw)
    df = pd.read_csv('data/bullets.csv')
    l = len(df)
    names = df['name'].tolist()
    emails = df['email'].tolist()
    bullets = df['bullets'].tolist()
    emails_lst = []
    for i in range(l):
        body = 'Dear %s,\n\nWe have identified the following food opportunities near you!\n\n%s\n\nBest Wishes,\nGreater Chicago Food Depository'%(names[i],bullets[i])
        msg = MIMEText(body.replace('\n','<br>'),'html')
        msg['Subject'] = 'Mobile Food Banks Near You - GCFD'
        msg['From'] = sender
        msg['To'] = emails[i]
        s.sendmail(sender, [emails[i]], msg.as_string())
    s.quit()

if __name__ == '__main__':
    get_data()
    clean()
    add_lat_long()
    get_nearby_users()
    send_emails()
