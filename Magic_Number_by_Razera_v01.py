# ==== Import Libraries ====================

import pandas as pd
import urllib.request


# %%
# ==== Build DataFrame of the fundamentus site data ====================
       # Stocks from B3 Brazilian stock market

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'

url = 'https://fundamentus.com.br/resultado.php'
headers={'User-Agent':user_agent,} 

request=urllib.request.Request(url,None,headers) #The assembled request
response = urllib.request.urlopen(request)
data = response.read() 
data = pd.read_html(data, decimal=',', thousands='.')[0] # Turn variable into a dataframe, converting decimal and thousand figures.


# %%
# ==== Transform percentage into float ====================
    # percentage values comes as a string in this dataframe, we're going to transform it in a float number like ('10%' => 0.10)
    # Value numbers in BRL

perc_columns = ['Div.Yield','Mrg Ebit','Mrg. Líq.','ROIC','ROE','Cresc. Rec.5a'] # list of columns with percentage numbers

for c in perc_columns: 
    data[c] = data[c].str.replace('.','')
    data[c] = data[c].str.replace(',','.')
    data[c] = data[c].str.rstrip('%').astype('float') / 100


# %%
# ==== Filter minor liquidity companies ====================
    # Remove companies with less than 1kk BRL liquidity

data = data[data['Liq.2meses'] > 1000000]


# %%
# ==== Obtain EV/EBIT ranking ====================

EV_EBIT_rank = data[['Papel','EV/EBIT']][data['EV/EBIT'] > 0].sort_values(by='EV/EBIT')[:200] # best ranked in this criteria, filtering only positive values
EV_EBIT_rank['pos EV_EBIT'] = range(1,201)


# %%
# ==== Obtain ROIC ranking ====================

ROIC_rank = data[['Papel','ROIC']][data['ROIC'] > 0].sort_values(by='ROIC', ascending=False)[:200] # best ranked in this criteria, filtering only positive values
ROIC_rank['pos ROIC'] = range(1,201)


# %%
# ==== Build Ranking dataframe ====================

ranking = pd.merge(left=EV_EBIT_rank, right=ROIC_rank, on='Papel', how='outer')
ranking['Magic Number'] = ranking['pos EV_EBIT'] + ranking['pos ROIC'] # Magic number is the sum of both ranks - the smaller the better
ranking = ranking.sort_values(by = 'Magic Number', ascending=True).dropna() # Drop companies that don't appear in both ranks
ranking['RANK'] = range(1,len(ranking)+1)
ranking.set_index('RANK',inplace=True)


# %%
# ==== View the 40 best stocks ====================

ranking.head(40)


# %%
# ==== Save an output file to excel ====================

from datetime import date
today = date.today()
ranking.to_excel('Ranking_Output_'+str(today)+'.xlsx')


# %%
# Next features intended
    # get "last processed balance data" - need to go in the detailed link: ex: "https://fundamentus.com.br/detalhes.php?papel=alup11"
    # get name of company
    # get sector


