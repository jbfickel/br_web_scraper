from configparser import BasicInterpolation
from curses.ascii import isalpha
from http.client import BadStatusLine
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import numpy as np
import csv

from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

user = False

while user == False:
    #Determine url from user input and test if valid
    base_url = 'https://www.baseball-reference.com/players/'
    p_first_name = str(input("Player's first name: ")).lower().strip()
    p_last_name = str(input("Player's last name: ")).lower().strip()
    p_first_letter = p_last_name[0]
    p_name_code = p_last_name[0:5] + p_first_name[0:2]
    p_ident = str(input("Player's identifier: ")).strip()
    p_ident_int = int(p_ident)
    if p_ident_int > 9:
        url = base_url + p_first_letter + '/' + p_name_code + str(p_ident_int) + '.shtml'
    else:
        url = base_url + p_first_letter + '/' + p_name_code + '0' + str(p_ident_int) + '.shtml'

    options = webdriver.FirefoxOptions()
    options.headless = True
    driver = Firefox(executable_path=r'C:... geckodriver.exe', options=options)
    
    #Load all data from page
    driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    source = requests.get(url).text
    soup = BeautifulSoup(source, "lxml")
    url_title = soup.title.text
    p_summary = soup.find('div', id='meta')
        
    p_name_error = False
        
    try:
        p_summary.p
    except AttributeError:
        print('\nIncorrect or invalid player name. Please try again.\n')
        p_name_error = True

    if p_name_error == False:
        
        driver.get(url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        #Determine player position from player summary
        pitcher = True
        ohtani = False

        position = p_summary.p.text
        array_position = position.split()

        np_position = ['Catcher', 'First', 'Second', 'Shortstop', 'Third',  'Baseman', 'Infielder', 
                       'Rightfielder', 'Centerfielder', 'Lefttfielder', 'Outfielder', 'Designated', 'Hitter']
        p_position = ['Pitcher', 'pitcher']
            
        for x in array_position:
            if x in np_position:
                pitcher = False
                break
        
        #Determine if player is non-pitcher and pitcher
        for x in array_position:
            if x in p_position:
                ohtani = True
                break
    
        #Basic career (and current year if active) stats table from player summary
        def basic_career_stats():
            position = p_summary.p.text

            position_label = " ".join(position.split())

            string_1 = ''
            string_2 = ''
            string_3 = ''

            cstats_1 = soup.find('div', class_="p1")
            for cstats_1.p in cstats_1:
                string_1 = string_1 + cstats_1.p.text
                
            cstats_2 = soup.find('div', class_="p2")
            for cstats_2.p in cstats_2:
                string_2 = string_2 + cstats_2.p.text
                
            cstats3 = soup.find('div', class_="p3")
            for cstats3.p in cstats3:
                string_3 = string_3 + cstats3.p.text

            string_c = string_1 + string_2 + string_3
            array_c = string_c.split()

            column1 = array_c[::2]
            column2 = array_c[1::2]

            this_year = False

            if '.' in ''.join(column1):
                string_1 = ''.join(column1)
                res1 = re.split('[^a-zA-Z+]', string_1)
                new_list = [x for x in res1 if x != '']
                column1 = new_list
                
                res2 = re.findall('\d*\.?\d+', string_1)
                temp = column2
                column2 = res2
                column3 = temp
                this_year = True

            if this_year is False:
                print('\n' + url_title + '\n' + position_label + '\n')
                data = {'Stat': column1, 
                        'Career': column2}
                df_not_active = pd.DataFrame(data)
                print(df_not_active)
                print('\n')  
            else:
                print('\n' + url_title + '\n' + position_label + '\n')
                data = {'Stat': column1,
                        '2022': column2, 
                        'Career': column3}
                df_active = pd.DataFrame(data)
                print(df_active)
                print('\n')

        #Data tables for non-pitcher player
        def batting_standard():
            batting_standard = soup.find('div', id='all_batting_standard')

            #Body data from standard batting table
            batting_standard_mod = batting_standard.findAll('tr', class_="full")
            batting_standard_bulk = batting_standard.find('tr', class_="full")

            string_bulk = ''
            array_bulk = []
            i = 0

            for batting_standard_bulk in batting_standard_mod:
                for batting_standard_bulk.th in batting_standard_bulk:
                    string_bulk = batting_standard_bulk.th.text
                    array_bulk.append(string_bulk)
                batting_standard_bulk = batting_standard_bulk.find_next_sibling('tr', class_="full")
                i += 1

            splits_bulk = np.array_split(array_bulk, i)
            # for array in splits_bulk:
            #     print(list(array))

            #Header from standard batting table
            array_header =[]

            batting_standard_header = batting_standard.findAll('th', scope='col')
            for batting_standard_header.th in batting_standard_header:
                array_header.append(batting_standard_header.th.text)
            # print(array_header)

            #Body data from standard batting table footer
            string_footer = ''
            array_footer = []
            j = 0

            batting_standard_footer = batting_standard.tfoot
            batting_standard_mod = batting_standard_footer.findAll('tr')
            batting_standard_footer = batting_standard.tr

            #Determine if player played for multiple teams in career
            p_one_team = False
            
            for batting_standard_footer in batting_standard_mod:
                #Remove unwanted row
                if j == 2:
                    batting_standard_footer = batting_standard_footer.find_next_sibling('tr')
                    try:
                        batting_standard_footer.p
                    except AttributeError:
                        p_one_team = True
                if p_one_team == False:
                    for batting_standard_footer.th in batting_standard_footer:
                        string_footer = batting_standard_footer.th.text
                        array_footer.append(string_footer)
                    batting_standard_footer = batting_standard_footer.find_next_sibling('tr')
                    j += 1

            # if 'G' in array_footer:
            #     index = array_footer.index('G')
            #     array_footer = array_footer[0:index - 3]
            #     j -= 1
                
            splits_footer = np.array_split(array_footer, j)
            # for array in splits_footer:
            #     print(list(array))

            #Create dataframe from footer
            df_footer = pd.DataFrame(splits_footer)
            df_footer.insert(1, 'A', " ")
            df_footer.insert(2, 'B', " ")
            df_footer.insert(3, 'C', " ")
            df_footer.columns = array_header
            
            #Remove empty row(s) from footer dataframe 
            nan_value = float("NaN")
            df_footer.replace('', nan_value, inplace = True)
            df_footer.dropna(subset = ['Year'], inplace = True)
            df_footer.replace(nan_value, '', inplace = True)

            #Create dataframe from body and header, and combine with footer dataframe
            df_bulk = pd.DataFrame(splits_bulk, columns = array_header)

            df_s_batting = pd.concat([df_bulk,df_footer])
            # print(df_concat)

            #Export combined dataframe as .csv file
            file_location = r'C:... .csv'

            df_s_batting.to_csv(file_location, index = False)

        #Data tables for only-pitcher player
        def pitching_standard():
            pitching_standard = soup.find('div', id='div_pitching_standard')
                
            #Body data from standard pitching table
            pitching_standard_mod = pitching_standard.findAll('tr', class_="full")
            pitching_standard_bulk = pitching_standard.find('tr', class_="full")

            string_bulk = ''
            array_bulk = []
            i = 0

            for pitching_standard_bulk in pitching_standard_mod:
                for pitching_standard_bulk.th in pitching_standard_bulk:
                    string_bulk = pitching_standard_bulk.th.text
                    array_bulk.append(string_bulk)
                pitching_standard_bulk = pitching_standard_bulk.find_next_sibling('tr', class_="full")
                i += 1

            splits_bulk = np.array_split(array_bulk, i)
            # for array in splits_bulk:
            #     print(list(array))
            
            #Header from standard pitching chart
            array_header = []

            pitching_standard_header = pitching_standard.findAll('th', scope='col')
            for pitching_standard_header.th in pitching_standard_header:
                array_header.append(pitching_standard_header.th.text)
            # print(array_header)

            #Body data from stndard batting chart footer
            string_footer = '' 
            array_footer = []
            j = 0

            pitching_standard_footer = pitching_standard.tfoot
            pitching_standard_mod = pitching_standard_footer.findAll('tr')
            pitching_standard_footer = pitching_standard.tr

            #Determine if player played for multiple teams in career
            p_one_team = False

            for pitching_standard_footer in pitching_standard_mod:
                #Remove unwanted row
                if j == 2:
                    pitching_standard_footer = pitching_standard_footer.find_next_sibling('tr')
                    try:
                        pitching_standard_footer.p
                    except AttributeError:
                        p_one_team = True
                if p_one_team == False:
                    for pitching_standard_footer.th in pitching_standard_footer:
                        string_footer = pitching_standard_footer.th.text
                        array_footer.append(string_footer)
                    pitching_standard_footer = pitching_standard_footer.find_next_sibling('tr')
                    j += 1

            splits_footer = np.array_split(array_footer, j)
            # for array in splits_footer:
            #     print(list(array))

            #Create dataframe from footer
            df_footer = pd.DataFrame(splits_footer)
            df_footer.insert(1, 'A', " ")
            df_footer.insert(2, 'B', " ")
            df_footer.insert(3, 'C', " ")
            df_footer.columns = array_header
            
            #Remove empty row(s) from footer dataframe 
            nan_value = float("NaN")
            df_footer.replace('', nan_value, inplace = True)
            df_footer.dropna(subset = ['Year'], inplace = True)
            df_footer.replace(nan_value, '', inplace = True)
            
            #Create dataframe from body and header, and combine with footer dataframe
            df_bulk = pd.DataFrame(splits_bulk, columns = array_header)

            df_s_pitching = pd.concat([df_bulk,df_footer])
            # print(df_concat)

            #Export combined dataframe as .csv file
            file_location = r'C:... .csv'

            df_s_pitching.to_csv(file_location, index = False)

        #Data tables for non-pitcher and pitcher player
        def ohtani_pitching_standard():
            pitching_standard = soup.find('div', id='all_pitching_standard')

            #Body data from standard pitching chart
            pitching_standard_mod = pitching_standard.findAll('tr', class_="full")
            pitching_standard_bulk = pitching_standard.find('tr', class_="full")

            string_bulk = ''
            array_bulk = []
            i = 0

            for pitching_standard_bulk in pitching_standard_mod:
                for pitching_standard_bulk.th in pitching_standard_bulk:
                    string_bulk = pitching_standard_bulk.th.text
                    array_bulk.append(string_bulk)
                pitching_standard_bulk = pitching_standard_bulk.find_next_sibling('tr', class_="full")
                i += 1

            splits_bulk = np.array_split(array_bulk, i)
            # for array in splits_bulk:
            #     print(list(array))
            
            #Header from standard pitching chart
            array_header = []

            pitching_standard_header = pitching_standard.findAll('th', scope='col')
            for pitching_standard_header.th in pitching_standard_header:
                array_header.append(pitching_standard_header.th.text)
            # print(array_header)

            #Body data from standard batting chart footer
            string_footer = '' 
            array_footer = []
            j = 0

            pitching_standard_footer = pitching_standard.tfoot
            pitching_standard_mod = pitching_standard_footer.findAll('tr')
            pitching_standard_footer = pitching_standard.tr

            #Determine if player played for multiple teams in career
            p_one_team = False
    
            for pitching_standard_footer in pitching_standard_mod:
                #Remove unwanted row
                if j == 2:
                    pitching_standard_footer = pitching_standard_footer.find_next_sibling('tr')
                    try:
                        pitching_standard_footer.p
                    except AttributeError:
                        p_one_team = True
                if p_one_team == False:
                    for pitching_standard_footer.th in pitching_standard_footer:
                        string_footer = pitching_standard_footer.th.text
                        array_footer.append(string_footer)
                    pitching_standard_footer = pitching_standard_footer.find_next_sibling('tr')
                    j += 1

            splits_footer = np.array_split(array_footer, j)
            # for array in splits_footer:
            #     print(list(array))

            #Create dataframe from footer
            df_footer = pd.DataFrame(splits_footer)
            df_footer.insert(1, 'A', " ")
            df_footer.insert(2, 'B', " ")
            df_footer.insert(3, 'C', " ")
            df_footer.columns = array_header

            #Remove empty row(s) from footer dataframe 
            nan_value = float("NaN")
            df_footer.replace('', nan_value, inplace = True)
            df_footer.dropna(subset = ['Year'], inplace = True)
            df_footer.replace(nan_value, '', inplace = True)

            #Create dataframe from body and header, and combine with footer dataframe
            df_bulk = pd.DataFrame(splits_bulk, columns = array_header)

            df_s_pitching = pd.concat([df_bulk,df_footer])
            # print(df_concat)

            #Export combined dataframe as .csv file
            file_location = r'C:... .csv'

            df_s_pitching.to_csv(file_location, index = False)
        
        basic_career_stats()
        
        if pitcher == False:
            batting_standard()
        else:
            pitching_standard()

        if ohtani == True:
            ohtani_pitching_standard()
                
        #User determines whether to re-run through loop for player data again
        feedback = input("Would you like to see the statistics of another player?\nType Y or N: ")
        if (feedback.strip() == 'Y') or (feedback.strip() == 'y'):
            print('\n')
            user = False
        else:
            print('\n')
            user = True
    else:
        feedback = input("Would you like to see the statistics of another player?\nType Y or N: ")
        if (feedback.strip() == 'Y') or (feedback.strip() == 'y'):
            print('\n')
            user = False
        else:
            print('\n')
            user = True

#End selenium task
driver.quit()