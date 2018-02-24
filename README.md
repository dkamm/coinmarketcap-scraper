# coinmarketcap-scraper

Historical data scraper for [coinmarketcap](https://coinmarketcap.com/) written in python 3. Takes ~2 min to download and parse all historical data for all coins.

## Dependencies
- bs4
- numpy
- pandas
- requests
- tqdm
```
pip install bs4 numpy pandas requests tqdm
```

## Usage
Scrape all historical data for all coins:
```
python scrape.py --outfile all.csv
```

Filter on date range and coins:
```
python scrape.py --outfile small.csv --start 20180101 --end 20180131 --symbols BTC ETH
```

Read data into pandas dataframe:
```
import pandas as pd
df = pd.read_csv('all.csv', index_col=['date', 'symbol'], parse_dates=True)
```

## Notes

- Marketcap is computed off of open price.

```
btc = df.xs('BTC', level='symbol')
btc.sort_index(inplace=True)
btc['open_money_supply'] = btc.marketcap / btc.open
btc['close_money_supply'] = btc.marketcap / btc.close
btc[['open_money_supply', 'close_money_supply', 'marketcap']][:10]

Out[9]: 
            open_money_supply  close_money_supply     marketcap
date                                                           
2013-04-28       1.109032e+07        1.118039e+07  1.500520e+09
2013-04-29       1.109131e+07        1.031659e+07  1.491160e+09
2013-04-30       1.109569e+07        1.149482e+07  1.597780e+09
2013-05-01       1.109942e+07        1.318762e+07  1.542820e+09
2013-05-02       1.110320e+07        1.228201e+07  1.292190e+09
2013-05-03       1.110654e+07        1.207233e+07  1.180070e+09
2013-05-04       1.110999e+07        9.687911e+06  1.089890e+09
2013-05-05       1.111391e+07        1.082530e+07  1.254760e+09
2013-05-06       1.111804e+07        1.148237e+07  1.289470e+09
2013-05-07       1.112223e+07        1.119704e+07  1.248470e+09
```
- Some coins have price but no marketcap or volume data on certain dates.
```
df[pd.isnull(df.marketcap)].head()

Out[10]: 
                        open       high        low      close      volume  \
date       symbol                                                           
2015-08-07 ETH       2.83162    3.53661    2.52112    2.77212    164329.0   
2017-08-01 BCH     294.60200  426.11000  210.38500  380.01000  65988800.0   
2017-07-31 BCH     346.36400  347.82500  266.18800  294.46100   1075960.0   
2017-07-30 BCH     385.14000  385.14000  316.25200  345.66100    606695.0   
2017-07-29 BCH     410.56500  423.73100  323.73000  384.77300    737815.0   

                   marketcap          slug  
date       symbol                           
2015-08-07 ETH           NaN      ethereum  
2017-08-01 BCH           NaN  bitcoin-cash  
2017-07-31 BCH           NaN  bitcoin-cash  
2017-07-30 BCH           NaN  bitcoin-cash  
2017-07-29 BCH           NaN  bitcoin-cash
```