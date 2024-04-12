from pybit.unified_trading import HTTP
import json
import pandas as pd
import matplotlib.pyplot as plt

session= HTTP()
ticker= session.get_tickers(
    category="option",
    baseCoin="ETH",
)

json_file= f"option_chain.json"

with open(json_file,'w') as file:
    json.dump(ticker,file)


calls=[]
puts=[]

for option in ticker["result"]["list"]:
    symbol=option["symbol"]

    if symbol[-1]=="C":
        calls.append(option)
    else:
        puts.append(option)
    
df_calls=pd.DataFrame(calls)
df_puts=pd.DataFrame(puts)

"""
    dfs Columns:
    ['symbol', 'bid1Price', 'bid1Size', 'bid1Iv', 'ask1Price', 'ask1Size',
       'ask1Iv', 'lastPrice', 'highPrice24h', 'lowPrice24h', 'markPrice',   
       'indexPrice', 'markIv', 'underlyingPrice', 'openInterest',
       'turnover24h', 'volume24h', 'totalVolume', 'totalTurnover', 'delta', 
       'gamma', 'vega', 'theta', 'predictedDeliveryPrice', 'change24h']
"""

def transform(df, type):
    if type.lower() in ['call', 'c']:
        df['strikePrice']=df['symbol'].str.extract(r'(\d+)-C').astype(int)
    elif type.lower() in ['put', 'p']:
        df['strikePrice']=df['symbol'].str.extract(r'(\d+)-P').astype(int)
    df['gamma']=df['gamma'].astype(float)
    df['openInterest']=df['openInterest'].astype(float)
    df['underlyingPrice']=df['underlyingPrice'].astype(float)
    df['totalVolume']=df['totalVolume'].astype(float)
    df=df_calls[df['totalVolume']>0]
    

    return df
    
transform(df_calls,"call")
transform(df_puts,"put")

#GEX= gamma*OI*PCT_CHANGE*100 / (*-100 for puts)

PCT_CHANGE= 0.01
df_calls['calls_gex']=df_calls['gamma']*df_calls['openInterest']*100*PCT_CHANGE
df_puts['puts_gex']=df_puts['gamma']*df_puts['openInterest']*-100*PCT_CHANGE

#Gex flip

strike_prices=df_calls['strikePrice'].unique()
gex_delta=[]

for price in strike_prices:
    calls_gex_sum=df_calls[df_calls['strikePrice']==price]['calls_gex'].sum()
    puts_gex_sum=df_puts[df_puts['strikePrice']==price]['puts_gex'].sum()
    gex_delta.append(calls_gex_sum+puts_gex_sum)

flip_price= None

for i in range(1,len(gex_delta)):
    if gex_delta[i-1]>0 and gex_delta[i]<0:
        flip_price=strike_prices[i]
        break
print(f"El valor de flip es ${flip_price}")
#plt settings

plt.figure(figsize=(10,6))
ax=plt.gca()

#scatter plot for calls
plt.scatter(df_calls['strikePrice'],df_calls['calls_gex'],label='Call GEX',color='b',marker='o',alpha=0.7)

#scatter plot for puts
plt.scatter(df_puts['strikePrice'],df_puts['puts_gex'],label='Put GEX', color='r',marker='o',alpha=0.7)

# Línea vertical para Zero Gamma
price=df_calls['underlyingPrice'].iloc[0]
plt.axvline(x=price, color='green', linestyle='--', label=f'Price ({price:.2f})')
plt.axvline(x=flip_price, color='red', linestyle='--', label=f'flip price ({flip_price})')

#axis settings
plt.xlabel('Strike Price')
plt.ylabel('GEX')
plt.legend()
plt.title("ETH GEX (bybit option's chain)")

#
plt.show()


"""
    RESOURCES:

    https://squeezemetrics.com/download/white_paper.pdf
    https://perfiliev.co.uk/market-commentary/how-to-calculate-gamma-exposure-and-zero-gamma-level/
    https://bybit-exchange.github.io/docs/v5/market/tickers
    https://matplotlib.org/stable/gallery/index.html
"""