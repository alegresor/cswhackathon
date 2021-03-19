import requests
import pandas as pd
import re
import urllib.parse

def get_data():
    '''
    Requests data from Chicagos Food Bank (CFB) website and extracts table 
    of mobile food pantrys for that day. 

    Note:
        In the future, we may be able to integrate with the CFB database
        in order to get the changes more directly. 
    '''
    reqget = requests.get(
        url = 'https://www.chicagosfoodbank.org/find-food/covid-19-neighborhood-sites/',
        headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'})
    html = reqget.content
    df_list = pd.read_html(html)
    df = df_list[-1]
    df.columns = df.iloc[1]
    df = df[2:]
    df.to_csv('data.csv',index=False)

def clean():
    df = pd.read_csv('data.csv')
    # remove location info between () and add Chicago, IL
    df['Location(s)'] = [re.sub(r'\([^)]*\)','',l)+', Chicago, IL' for l in df['Location(s)'].tolist()] 
    return df    

def add_lat_long(df):
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
    return df

if __name__ == '__main__':
    #get_data()
    df = clean()
    df = add_lat_long(df)
    

    
