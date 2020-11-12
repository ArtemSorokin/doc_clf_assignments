import requests
import bs4
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)\
              AppleWebKit/537.36 (KHTML, like Gecko)\
              Chrome/35.0.1916.47 Safari/537.36'


def get_tiks_and_field_names():
    url = 'http://notelections.online/region/region/st-petersburg?action=show&root=1&tvd=27820001217417&vrn=27820001217413&region=78&global=&sub_region=78&prver=0&pronetvd=null&vibid=27820001217417&type=222'

    page = requests.get(url, headers={'User-Agent': user_agent})
    soup = bs4.BeautifulSoup(page.text, 'lxml')

    # названия ТИКов
    tik_list = [x.text.split(' ', 1) for x in soup.find('body').findAll('tr')[6].find('form').find_all('option')][1:]
    tik_list = [x[1] for x in tik_list]
    tik_list += ['Цифровые избирательные участки']

    # названия полей
    field_td_list = soup.find('body').findAll('tr')[8].find_all('tr')[6].find_all('td', {'style': 'color:black'})
    field_list = [x.text for x in field_td_list[3:36:3]]
    field_list += ['Амосов Михаил Иванович', 'Беглов Александр Дмитриевич', 'Тихонова Надежда Геннадьевна']

    return tik_list, field_list


def fill_votes_general(tik_n):
    df = pd.DataFrame(columns=['ТИК', 'УИК'] + field_list)

    tik_id = 18 + tik_n
    url = f'http://notelections.online/region/region/st-petersburg?action=show&tvd=27820001217417&vrn=27820001217413&region=78&global=&sub_region=78&prver=0&pronetvd=null&vibid=278200012174{tik_id}&type=222'

    page = requests.get(url, headers={'User-Agent': user_agent})
    soup = bs4.BeautifulSoup(page.text, 'lxml')

    # список УИКов
    uik_list = []
    i = 5
    while True:
        try:
            uik_n = soup.find('body').findAll('tr')[8].find_all('td', {'align': 'center'})[i].text
            uik_n = int(uik_n.split('№')[1])
            uik_list.append(uik_n)
            i += 1
        except IndexError:
            break

    # данные основных полей
    for i in range(24, 35):
        vals = [int(x.find('nobr').text) for x in soup.find('body').findAll('tr')[8].find_all('tr')[i].find_all('td', {'align': 'right'})]
        df[df.columns[i - 22]] = vals

    # данные по кандидатам
    for i in range(3):
        val_list = soup.find('body').findAll('tr')[8].find_all('tr')[i+36].find_all('b')
        vals = [int(x.text) for x in val_list]
        df[df.columns[len(df.columns)-3+i]] = vals

    df['ТИК'] = tik_list[tik_n-1]
    df['УИК'] = uik_list
    return df


def fill_votes_digital():
    url = 'http://notelections.online/region/region/st-petersburg?action=show&tvd=27820001217417&vrn=27820001217413&region=78&global=&sub_region=78&prver=0&pronetvd=null&vibid=27820001217417&type=502'

    page = requests.get(url, headers={'User-Agent': user_agent})
    soup = bs4.BeautifulSoup(page.text, 'lxml')

    val_list = soup.find('body').findAll('tr')[7].find_all('b')
    vals = [[int(x.text)] for x in val_list[3:14]] + [[int(x.text)] for x in val_list[15:18]]
    df = pd.DataFrame(columns=['ТИК', 'УИК'] + field_list)
    for i in range(len(vals)):
        df[df.columns[i+2]] = vals[i]

    df['ТИК'] = 'Цифровые избирательные участки'
    return df


tik_list, field_list = get_tiks_and_field_names()
df = pd.concat([fill_votes_general(i) for i in range(1, len(tik_list) - 1)] + [fill_votes_digital()])
df = df.reset_index(drop=True)
df.to_csv('election_results.csv')