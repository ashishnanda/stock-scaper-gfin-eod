import thread
import pandas as pd
from datetime import datetime
import data_scrape

print(datetime.now())

#variables

search_str = "ar24TM7TmCVY2gNIxtSt_g"

path = '/Users/ashishnanda/Code/Stock_data/EOD/'
tickers_filename = 'input/ticker_list.csv'
ticker_list = pd.read_csv(tickers_filename)['TICKER'].tolist()
exchange_list = ['NSE']

url_list = [f'https://www.google.com/finance/quote/{ticker}:{exchange}' for ticker in ticker_list for exchange in exchange_list]

results = thread.scrape_urls(url_list)

for i, soup in enumerate(results):
            if soup:
                tmp_df = data_scrape.scrape_today_price(soup)
                if i == 0:
                     price_df = tmp_df
                else:
                     price_df = pd.concat([price_df, tmp_df])
            else:
                print(f"Failed to fetch content from URL {url_list[i]}")


#today = datetime.today().strftime('%Y_%m_%d')
filename = f"data/stock_prices_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
price_df.to_csv(filename, index=False)

print(datetime.now())
print('Working')