import argparse
import concurrent.futures
import datetime
from datetime import datetime as dt
import bs4
import numpy as np
import pandas as pd
import requests
import tqdm


def parse_all_response(resp):
    soup = bs4.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table')
    # use id instead of text to determine column names because its values are nicely formatted already
    # remove 'th-' prefix from id. the only column without an id is # so use 'th-#' as default
    columns = ['slug'] + [x.get('id', 'th-#')[3:] for x in table.thead.find_all('th')]

    def get_val(td):
        tag = td
        # some columns like price store values within inner <a>
        if tag.find('a'):
            tag = tag.find('a')
        # numeric columns store their value in these attributes in addition to text.
        # use these attributes to avoid parsing $ and , in text
        for key in ['data-usd', 'data-supply']:
            val = tag.get(key)
            if val:
                try:
                    return np.float64(val)
                except ValueError:
                    return np.nan
        return tag.text

    rows = []
    for tr in table.tbody.find_all('tr'):
        slug = tr.get('id')[3:]  # remove 'id-' prefix from id
        rows.append([slug] + [get_val(x) for x in tr.find_all('td')])
    # index has the same information as #
    # name has the same value as symbol because its first <a> is the currency symbol
    # slug also has basically the same information that name is supposed to so just drop name
    return pd.DataFrame(columns=columns, data=rows).drop(['name', '#'], axis=1)


def parse_historical_coin_response(resp):
    soup = bs4.BeautifulSoup(resp.text, 'lxml')
    table = soup.find(id='historical-data').find('table')
    columns = [x.text.lower().replace(' ', '') for x in table.thead.find_all('th')]

    def get_val(td):
        # numeric columns store their value in this attribute in addition to text
        val = td.get('data-format-value')
        if val:
            try:
                return np.float64(val)
            except ValueError:
                return np.nan
        return td.text

    rows = []
    for tr in table.tbody.find_all('tr'):
        if tr.td.text == 'No data was found for the selected time period.':
            return pd.DataFrame(columns=columns).set_index('date')
        rows.append([get_val(x) for x in tr.find_all('td')])

    df = pd.DataFrame(columns=columns, data=rows)
    df['date'] = pd.to_datetime(df.date)
    return df.set_index('date')


def all_url():
    return 'https://coinmarketcap.com/all/views/all/'


def historical_coin_url(slug, start, end):
    return 'https://coinmarketcap.com/currencies/{slug}/historical-data/?start={start}&end={end}'.format(
        slug=slug, start=start.strftime('%Y%m%d'), end=end.strftime('%Y%m%d'))


# possible future use
def markets_url(slug):
    return 'https://coinmarketcap.com/currencies/{slug}/#markets'.format(slug=slug)


def valid_date(s):
    try:
        return dt.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outfile', type=str)
    parser.add_argument('--start', type=valid_date, default=datetime.date(2013, 4, 28))
    parser.add_argument('--end', type=valid_date, default=datetime.date.today())
    parser.add_argument('--symbols', type=str, nargs='*')
    args = parser.parse_args()

    all_df = parse_all_response(requests.get(all_url()))

    slugs = all_df.slug.values
    if args.symbols:
        slugs = all_df.loc[all_df.symbol.isin(args.symbols)].slug.values
    symbols = all_df.loc[all_df.slug.isin(slugs)].symbol.values

    urls = [historical_coin_url(x, args.start, args.end) for x in slugs]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        responses = [x for x in tqdm.tqdm(executor.map(requests.get, urls),
                                          desc='downloading historical coin pages',
                                          total=len(urls))]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        historical_coin_dfs = [x for x in tqdm.tqdm(executor.map(parse_historical_coin_response, responses),
                                                    desc='parsing historical coin pages',
                                                    total=len(responses))]

    for slug, symbol, historical_coin_df in zip(slugs, symbols, historical_coin_dfs):
        historical_coin_df['slug'] = slug
        historical_coin_df['symbol'] = symbol

    pd.concat(historical_coin_dfs).to_csv(args.outfile)


if __name__ == '__main__':
    main()