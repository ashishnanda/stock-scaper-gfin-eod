import pandas as pd
from bs4 import BeautifulSoup
import json
import re



def data_process(soup, class_search):
    return float(soup.find(class_=class_search).text.strip()[1:].replace(',', ''))

def scrape_today_price(soup):
    df = pd.DataFrame(columns=['ticker', 'exchange', 'date', 'time', 'price', 'volume'])

    # Find all <script> tags
    script_tags = soup.find_all('script')

    # Iterate over each <script> tag to find the one containing 'key: \'ds:10\''
    for script_tag in script_tags:
        if script_tag.string and 'key: \'ds:10\'' in script_tag.string:
            # Extract the content of the <script> tag
            script_content = script_tag.string
            
            # Extract the JSON-like data from the JavaScript function call
            json_data_match = re.search(r'AF_initDataCallback\((.*)\);', script_content)
            
            if json_data_match:
                json_data_str = json_data_match.group(1)
                
                # Clean up the JSON string to make it valid
                json_data_str = json_data_str.replace("key:", '"key":').replace("hash:", '"hash":').replace("data:", '"data":').replace("sideChannel:", '"sideChannel":').replace("'", '"')
                
                # Parse the JSON data
                json_data = json.loads(json_data_str)
                
                # Access the lists inside the parsed JSON data
                data_lists = json_data['data'] #main data
                # Accessing the first level within "data"
                first_level = data_lists[0]

                # Accessing the second level within "data"
                second_level = first_level[0]
                
                # Print the lists
                for l in second_level[3][0][1]:
                    date = str(l[0][2]) + '-' + str(l[0][1]) + '-' + str(l[0][0])
                    time = str(l[0][3]) + '_' + str(l[0][4])     
                    df.loc[len(df)] = second_level[0] + [date, time, l[1][0], l[2]]    #['ticker', 'exchange', 'date', 'time', 'price', 'volume']
                    
            else:
                print("No JSON data found in the script tag.")
    df['time'] = df['time'].apply(lambda x: x.replace('None','0'))
    return df