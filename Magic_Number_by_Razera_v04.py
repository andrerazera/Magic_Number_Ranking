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

# EV_EBIT_rank = data[['Papel','EV/EBIT']][data['EV/EBIT'] > 0].sort_values(by='EV/EBIT')[:200] # best ranked in this criteria, filtering only positive values
EV_EBIT_rank = data[['Papel','EV/EBIT','Cotação']][data['EV/EBIT'] > 0].sort_values(by='EV/EBIT')[:200] # best ranked in this criteria, filtering only positive values

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
# ==== Last result processed + company name, sector, subsector ====================
# ==== Feature developed in 29 Jul 2021 ==================== *****FEATURE*****


toggle1 = 'ON'

if toggle1 == 'ON':
    # ==== Import selenium chromedriver ====================

    # !pip install selenium
    from selenium import webdriver

    caminho_chromedriver = r"tools\chromedriver.exe"  #path to selenium chromedriver in your machine
    options = webdriver.ChromeOptions() #option to hide chrome while run the code
    options.add_argument("--headless")
    driver = webdriver.Chrome(caminho_chromedriver, options=options) 

    # ==== Last Result Processed Function ====================
    def GetDetails(ticker):
        # Function that returns data that is not contained in main fundamentus database
        # it gets website of the 'ticker' declared and fills the 'ranking' df in the line of the ticker

        URL = r"https://fundamentus.com.br/detalhes.php?papel="+ticker

        driver.get(URL)
        # sleep(2)  #in the test validations wasn't needed to wait to page fully render

        ### Scrape data ###
        # Last Processed Result
        data_ult_bal_xpath= r"/html/body/div[1]/div[2]/table[2]/tbody/tr[1]/td[4]/span"   #xpath of the field "last processed result"
        data_ult_bal = driver.find_element_by_xpath(data_ult_bal_xpath).text #get the text from field in str - don't see a need to convert it into a date format

        # Company name
        company_name_xpath = r"/html/body/div[1]/div[2]/table[1]/tbody/tr[3]/td[2]/span"
        company_name = driver.find_element_by_xpath(company_name_xpath).text

        # Sector
        sector_xpath = r"/html/body/div[1]/div[2]/table[1]/tbody/tr[4]/td[2]"
        sector = driver.find_element_by_xpath(sector_xpath).text

        # Subsector
        subsector_xpath = r"/html/body/div[1]/div[2]/table[1]/tbody/tr[5]/td[2]"
        subsector = driver.find_element_by_xpath(subsector_xpath).text

        ranking.loc[ranking[ranking['Papel'] == ticker].index[0], 'Last Result Processed'] = data_ult_bal  #using .loc, find the index of the ticker and fill in a specific column for this date
        ranking.loc[ranking[ranking['Papel'] == ticker].index[0], 'Company Name'] = company_name
        ranking.loc[ranking[ranking['Papel'] == ticker].index[0], 'Sector'] = sector
        ranking.loc[ranking[ranking['Papel'] == ticker].index[0], 'Subsector'] = subsector
    
    # ==== Call Function ====================
    for ticker in ranking['Papel'][0:100]:   #call function for the first 100 tickers
        GetDetails(ticker)



# %%
# ==== Save an output file to excel ====================

from datetime import date
today = date.today()
ranking.to_excel('Ranking_Output_'+str(today)+'.xlsx')


print('Salvo no arquivo Ranking_Output_'+str(today)+'.xlsx')


# %%
# ==== Compare with the last saved file ====================
## ===== Feature added 24/08/2021 ====================
toggle = 'ON'
if toggle == 'ON':
    # Gather last saved file
    import os
    output_files = os.listdir()
    output_files = list(filter(lambda x: x.startswith('Ranking_Output'), output_files))
    output_files

    # Last ranking dataframe dathered from folder
    ranking_last = pd.read_excel(output_files[-2])

    # Build merged dataframe from current ranking versus last ranking
    ## so it will be able to compare deviations
    columns_output = ['Papel', 'EV/EBIT', 'Cotação', 'pos EV_EBIT', 'ROIC', 'pos ROIC',
        'Magic Number', 'Last Result Processed', 'Company Name', 'Sector',
        'Subsector', 'RANK','Papel','Cotação_last','Last Result Processed_last']

    ranking_comparison = pd.merge(left=ranking, right=ranking_last, on='Papel', how='left', suffixes=("","_last"))[columns_output] 
    ranking_comparison['RANK_atual'] = range(1,len(ranking_comparison)+1)
    ranking_comparison.set_index('RANK_atual',inplace=True)

    # calculo de desvios
    ranking_comparison['% Cotação_deviation'] = (ranking_comparison['Cotação'] - ranking_comparison['Cotação_last']) / ranking_comparison['Cotação_last']
    ranking_comparison['RANK_desvio'] =  ranking_comparison['RANK'] - ranking_comparison.index

    # Save comparison to excel
    ranking_comparison.to_excel('Ranking_Comparison_'+str(today)+'.xlsx')

    print('Salvo no arquivo Ranking_Comparison_'+str(today)+'.xlsx')




# %%
# Next features intended
    # DONE - get "last processed balance data" - need to go in the detailed link: ex: "https://fundamentus.com.br/detalhes.php?papel=alup11"
    # DONE - get name of company
    # DONE - get sector
    # verify correlation
    # verify dupplicated tickers tasa4 tasa3 (get the most liquidity one)
    # get price
    # from previous file - get price back then and see the delta variation of price
    # get last position and the delta
    






