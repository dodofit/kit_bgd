import requests
from urllib import request
from shutil import copyfileobj
import pandas as pd
import urllib3
from bs4 import BeautifulSoup
import numpy as np
import openpyxl
import re
import datetime
from unidecode import *
import xlwings as xw


def convert_lat_lon(df):
    deg = df['Latitude'].replace(r'([0-9]{2})(°)?(\d*)\.?(\d+)(\'[A-Z]?)', r'\1', regex=True).astype(int)

    min = df['Latitude'].replace(r'([0-9]{2})(°)?(\d*)(\.?)(\d+)(\')([A-Z]?)', r'\3\4\5', regex=True).astype(float)


    cap = df['Latitude'].replace(r'([0-9]{2})(°)?(\d*)\.?(\d+)(\')([A-Z]?)', r'\6', regex=True)

    df['Latitude']=dms2dec(deg,min,cap)

    deg = df['Longitude'].replace(r'([0-9]{2})(°)?(\d*)\.?(\d+)(\'[A-Z]?)', r'\1', regex=True).astype(int)

    min = df['Longitude'].replace(r'([0-9]{2})(°)?(\d*)(\.?)(\d+)(\')([A-Z]?)', r'\3\4\5', regex=True).astype(float)


    cap = df['Longitude'].replace(r'([0-9]{2})(°)?(\d*)\.?(\d+)(\')([A-Z]?)', r'\6', regex=True)

    df['Longitude']=dms2dec(deg,min,cap)

    return df

def dms2dec(deg, mn, cap):
    map = {'N':1, 'E':1,'S':-1, 'W':-1}
    cap_m = cap.map(map)

    x = (deg + mn / 60)*cap_m

    return x



def obj_to_num(df):
    df['Depuis 30 minutes - VMG']=df['Depuis 30 minutes - VMG'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))
    df['Depuis 30 minutes - Distance']=df['Depuis 30 minutes - Distance'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))
    df['Depuis 30 minutes - Vitesse']=df['Depuis 30 minutes - Vitesse'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))

    df['Depuis 24 heures - VMG']=df['Depuis 24 heures - VMG'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))
    df['Depuis 24 heures - Distance']=df['Depuis 24 heures - Distance'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))
    df['Depuis 24 heures - Vitesse']=df['Depuis 24 heures - Vitesse'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))

    df['Depuis le dernier classement - VMG']=df['Depuis le dernier classement - VMG'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))
    df['Depuis le dernier classement - Distance']=df['Depuis le dernier classement - Distance'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))
    df['Depuis le dernier classement - Vitesse']=df['Depuis le dernier classement - Vitesse'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))

    df['DTL']=df['DTL'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))

    df['DTF']=df['DTF'].apply(lambda x : float(re.findall(r'(?<![a-zA-Z:])[-+]?\d*\.?\d+', x)[0]))

    df['Depuis 30 minutes - Cap']=df['Depuis 30 minutes - Cap'].replace(r'([0-9+])(°)?', r'\1', regex=True).astype(int)
    df['Depuis le dernier classement - Cap']=df['Depuis le dernier classement - Cap'].replace(r'([0-9+])(°)?', r'\1', regex=True).astype(int)
    df['Depuis 24 heures - Cap']=df['Depuis 24 heures - Cap'].replace(r'([0-9+])(°)?', r'\1', regex=True).astype(int)

    return df

def prep_df_(df):
    df=df.drop(df.loc[df['Rang'] == 'RET'].index.tolist())
    df=df.drop(df.loc[df['Rang'] == 'NL'].index.tolist())
    df[['Nationalité', 'Voile']]=df['Nat. / Voile'].str.split(pat=' ', expand=True)
    df[['Skipper', 'Bateau']]=df['Skipper / Bateau'].str.split(pat='\n', expand=True)
    df = df.replace('\n', '', regex=True)

    df['Skipper'] = df['Skipper'].apply(lambda x: unidecode(x))

    df = obj_to_num(df)

    df.Rang=df.Rang.astype(int)

    df = convert_lat_lon(df)

    df = df.drop(['Nat. / Voile', 'Skipper / Bateau'], axis=1)

    return df


def extract_inrace(filename, path):
    header_list_ = ['Rang', 'Nat. / Voile', 'Skipper / Bateau', 'Heure FR', 'Latitude', 'Longitude',
                    'Depuis 30 minutes - Cap', 'Depuis 30 minutes - Vitesse', 'Depuis 30 minutes - VMG',
                    'Depuis 30 minutes - Distance', 'Depuis le dernier classement - Cap',
                    'Depuis le dernier classement - Vitesse', 'Depuis le dernier classement - VMG',
                    'Depuis le dernier classement - Distance', 'Depuis 24 heures - Cap', 'Depuis 24 heures - Vitesse',
                    'Depuis 24 heures - VMG', 'Depuis 24 heures - Distance', 'DTF', 'DTL', 'Date']

    df = pd.read_csv(
        path + filename)
    # print(type(df.columns[1]))
    df = df.drop('Unnamed: 0', axis=1)
    df = df.drop('0', axis=1)

    df['Date'] = filename[12:]
    # print(df.columns)
    df.columns = header_list_
    # print(df["Rang"].astype(str))

    if df["Rang"][4] == '1\nARV':
        ind_st = df.loc[df["Rang"].astype(str).str.fullmatch("\d+"), 'Rang'].index
        df = df.iloc[ind_st]
    else:
        df = df.iloc[4:37]

    df['Date'] = df['Date'].apply(lambda x: datetime.datetime.strptime(x, "%Y%m%d_%H%M%S"))
    df = df.reset_index().drop('index', axis=1)

    return df


def get_voilier_info(url):
    soup = BeautifulSoup(requests.get(url).content)
    list_skipper={}

    j=0
    for i in soup.find_all(class_='boats-list__popup-specs-list'):
        dict_voilier = {}
        skipper = soup.find_all(class_='boats-list__skipper-name')[j].text
        for spec in i:
            if spec.text.split(':')[0] != '\n':
                sp_desc = spec.text.split(':')[0].rstrip()
                sp = spec.text.split(':')[1]
                dict_voilier["{}".format(sp_desc)] = sp
        list_skipper["{}".format(skipper)] = dict_voilier
        j+=1
    df_voiliers = pd.DataFrame.from_dict(list_skipper, orient='index')

    df_voiliers = df_voiliers.reset_index()
    df_voiliers=df_voiliers.replace(',','.', regex=True)


    df_voiliers[['Longueur', 'Largeur', "Tirant d'eau",'Déplacement (poids)', 'Hauteur mât', 'Surface de voiles au près','Surface de voiles au portant']]=df_voiliers[['Longueur', 'Largeur', "Tirant d'eau",'Déplacement (poids)', 'Hauteur mât', 'Surface de voiles au près','Surface de voiles au portant']].replace(r'\s([0-9]+\.?[0-9]*)(\s?[a-zA-Z0-9_.-]*²?)', r'\1', regex=True)

    df_voiliers[['Longueur', 'Largeur', "Tirant d'eau",'Déplacement (poids)', 'Hauteur mât']]=df_voiliers[['Longueur', 'Largeur', "Tirant d'eau",'Déplacement (poids)', 'Hauteur mât']].replace(' nc', '0').replace(' NC', '0').fillna('0').astype(float)

    df_voiliers[['Surface de voiles au près','Surface de voiles au portant']]=df_voiliers[['Surface de voiles au près','Surface de voiles au portant']].fillna('0').astype(int)

    df_voiliers['index']=df_voiliers['index'].str.title().apply(lambda x : unidecode(x))

    df_voiliers = df_voiliers.rename(columns={'index' : 'Skipper'})

    df_voiliers['Skipper'] =df_voiliers['Skipper'].replace('  ', ' ', regex=True)

    df_voiliers['Skipper'] = df_voiliers['Skipper'].replace('Sam', 'Samantha', regex=True)






    return df_voiliers