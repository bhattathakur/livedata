import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time as t
import datetime
import pytz
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#import pandas_ta as ta
#import talib

st.set_page_config(layout='wide') #wide page

st.markdown("<h4 Style='text-align:center;'>Real-Time Stock Dashboard</h4>",unsafe_allow_html=True)

est_timezone=pytz.timezone('US/Eastern')

#sidebar with datetime (updating) and options for ticker choice including BTC-USD And ETH-USD
debug=False

current_date_time=datetime.datetime.now(est_timezone)#
current_date=current_date_time.date()

current_time=current_date_time.time()
time_930=datetime.time(hour=9,minute=30)
time_16=datetime.time(hour=16)
#last bussiness day
last_bussiness_day=pd.bdate_range(end=current_date,periods=1)[0]

#check if current day is a business day and current time is in between 9:30 AM EST to 4:00 PM EST
check_date_time=(current_date==last_bussiness_day.date()) and (current_time>time_930) and (current_time<time_16)

if debug:st.write(f'current_date: {current_date}')
if debug:st.write(f'current_time: {current_time}')
if debug:st.write(f'last_bussiness_day: {last_bussiness_day}')
if debug:st.write(f'meet_live_stock_data_criterion: {check_date_time}')
#tickers and cryptocurrencies
#crypto=['BTC-USD','ETH-USD']

mag7=['AAPL','NVDA','TSLA','META','AMZN','GOOGL','MSFT','MSTR','AMD','GME','DJT','SMCI']
current_time_text=f"{current_date_time.strftime('%A, %I:%M %p, %Y-%m-%d')}"

#check_date_time=True
plot_placeholder=st.empty() #VERY important for refreshing the same plot otherwise each plot will append

if not check_date_time:
    st.warning('This app works only for regular market hours [9:30 AM - 4 PM EST, Business Day]',icon='⚠️')
    st.warning(f'Current Date Time: {current_time_text}')
    st.stop() #NOTE THIS 

#time information
#st.sidebar.text(current_date_time)

#selection box
#user has two options input their own ticker or choose from the options
choose_radio_options=['CHOOSE FROM LIST','INPUT YOUR TICKER']# if check_date_time else ['CHOOSE FROM LIST']

radio_value=st.sidebar.radio("INPUT METHOD",choose_radio_options,key='input_method')
#user_value=st.sidebar.selectbox("SELECT or INPUT YOUR TICKER",mag7,index=1,key='user_choice')
if radio_value==choose_radio_options[0]:
    user_value=st.sidebar.selectbox("SELECT",mag7,key='mag7',index=2)
else:
    user_value=st.sidebar.text_input("INPUT YOUR TICKER",key='user_input').upper()
#user_value='AMD'
#print
st.sidebar.markdown(f'Your choice: {user_value}')

#ticker
ticker=user_value #will be used in a plot

#function to get minute ticker data from yahoo finance with yfinance
#get sma5, msa10, rsi, vwap, change, cheang_pct, TR ATR, higher close or lower close for 3 minutes
# Custom CSS to change the font size of the delta
#st.markdown(
#    """
#    <style>
#    [data-testid="stMetricDelta"] {
#        font-size: 20px;
#    }
#    </style>
#    """,
#    unsafe_allow_html=True,
#)

def get_sma(df,parameter,period):
  'smas for close or volume '
  return df[parameter].rolling(period).mean()

def calculate_rsi(close_prices, timeperiod=14):
    """
    Calculate the Relative Strength Index (RSI) for a given series of close prices using pandas.
    
    Parameters:
    - close_prices (list or pd.Series): The closing prices for which to calculate the RSI.
    - timeperiod (int, optional): The period to use for calculating the RSI. Default is 14.
    
    Returns:
    - pd.Series: The RSI values.
    """
    # Convert the input to a pandas Series if it's not already
    close_prices = pd.Series(close_prices)
    
    # Calculate the daily price changes
    delta = close_prices.diff()
    
    # Separate the gains and losses
    gain = delta.where(delta > 0, 0)  # Gain is the positive change
    loss = -delta.where(delta < 0, 0)  # Loss is the negative change (as positive values)
    
    # Calculate the rolling average of gains and losses over the specified period
    avg_gain = gain.rolling(window=timeperiod, min_periods=1).mean()
    avg_loss = loss.rolling(window=timeperiod, min_periods=1).mean()
    
    # Calculate the relative strength (RS)
    rs = avg_gain / avg_loss
    
    # Calculate the RSI using the formula RSI = 100 - (100 / (1 + RS))
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

#define a function for text to audio
def text_to_audio(text,ticker=ticker):
    js_code = f"""
    <script>
        const msg = new SpeechSynthesisUtterance("{ticker} {text}");
        msg.lang = 'en-US';  // Set the language (customize as needed)
        msg.pitch=0.8;
        window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(js_code, height=0,width=0)


#get informative df
def get_informative_df(df):
  temp_df=df.copy()
  temp_df['sma5']=get_sma(temp_df,'Close',5)
  temp_df['sma10']=get_sma(temp_df,'Close',10)
  temp_df['vol5']=get_sma(temp_df,'Volume',5)
  temp_df['vol10']=get_sma(temp_df,'Volume',10)
  temp_df['typical_price']=(temp_df['High']+temp_df['Low']+temp_df['Close'])/3
  temp_df['vwap']=(temp_df['Volume']*temp_df['typical_price']).cumsum()/temp_df['Volume'].cumsum()
  temp_df['rsi']=calculate_rsi(temp_df['Close'])
  temp_df['TR1']=temp_df['High']-temp_df['Low']
  temp_df['TR2']=(temp_df['High']-temp_df['Close'].shift(1)).abs()
  temp_df['TR3']=(temp_df['Low']-temp_df['Close'].shift(1)).abs()
  temp_df['tr']=temp_df[['TR1','TR2','TR3']].max(axis=1)
  temp_df['atr5']=temp_df['tr'].rolling(window=5).mean()
  temp_df['change']=temp_df['Close'].diff()
  temp_df['pct_change']=temp_df['Close'].pct_change()*100
  temp_df['price_above_vwap']=temp_df['Close']>temp_df['vwap']
  temp_df['price_below_vwap']=temp_df['Close']<temp_df['vwap']
  temp_df['sma5>sma10']=temp_df['sma5']>temp_df['sma10']
  temp_df['sma5<sma10']=temp_df['sma5']<temp_df['sma10']
  temp_df['higher_close']=(temp_df['Close']>temp_df['Close'].shift(1)) & (temp_df['Close'].shift(1)>temp_df['Close'].shift(2))
  temp_df['lower_close']=(temp_df['Close']<temp_df['Close'].shift(1)) & (temp_df['Close'].shift(1)<temp_df['Close'].shift(2))
  temp_df['volume_sum']=df['volume'].cumsum() # Added sum su

  #dropping_columns
  dropping_cols=['TR1','TR2','TR3','typical_price']
  temp_df=temp_df.drop(dropping_cols,axis=1)
  return temp_df.round(2)

go_live=True
count=1
placeholder=st.empty()

while go_live and user_value:
    if count>1:t.sleep(50)
    #if count>3:
    #    st.stop()
    #    break
    count+=1
    #"""
    #get minute data for a ticker for a last business day
    #"""
    try:
        df=yf.download(ticker,period='1d',interval='1m',group_by='tickers')
        # Check if DataFrame is empty
        if df.empty:
            st.warning('Error Occured, Enter a correct ticker or try again later !',icon="⚠️")
            st.stop()
    except:
        st.warning('Error Occured, Enter a correct ticker or try again later !',icon="⚠️")
        st.stop()

    if(debug):st.write(df.tail())
    if(debug):st.write(f"df columns: {df.columns}")
    on_local=False
    if not on_local:df=df[ticker].reset_index(drop=False) #This is turned on the app deployment and turned off in local
    df=df.reset_index(drop=False)
    df['Datetime']=pd.to_datetime(df['Datetime']) #Needed for a local
    #df.loc[:,ticker]=ticker
    df['Volume']=df['Volume'].div(1e6)
    df['Datetime']=df['Datetime'].dt.tz_convert(est_timezone)#.dt.strftime('%Y-%m-%d %H:%M')
    info_df=get_informative_df(df)
    if(debug):st.write(f"info_df columns: {info_df.columns}")
    #last row
    last_row=info_df.iloc[-1]

    close=last_row.at['Close']
    change=last_row.at['change']
    pct_change=last_row.at['pct_change']
    volume=last_row.at['Volume']
    volume5=last_row.at['vol5']
    volume10=last_row.at['vol10']
    vwap=last_row.at['vwap']
    rsi=last_row.at['rsi']
    tr=last_row.at['tr']
    atr5=last_row.at['atr5']
    price_above_vwap=last_row.at['price_above_vwap']
    price_below_vwap=last_row.at['price_below_vwap']
    sma5_gt_sma10=last_row.at['sma5>sma10']
    sma5_lt_sma10=last_row.at['sma5<sma10']
    higher_close=last_row.at['higher_close']
    lower_close=last_row.at['lower_close']
    existing_date=last_row.at['Datetime']
    traded_volume=last_row.at['volume_sum'] #total volume 
    last_time=last_row.at['Datetime'].time()
    #st.write(f'last_time: {last_time}')

    if(debug):st.write(f"last_row: {last_row}")
    if(debug):st.write(f"close: {close}")
    if(debug):st.write(f"change: {change}")
    if(debug):st.write(f"pct_change: {pct_change}")
    if(debug):st.write(f"Volume: {volume}")
    if(debug):st.write(f"Volume5: {volume5}")
    if(debug):st.write(f"vwap: {vwap}")
    if(debug):st.write(f"rsi: {rsi}")
    if(debug):st.write(f"tr:{tr}")
    if(debug):st.write(f"atr5:{atr5}")
    if(debug):st.write(f"price_above_vwap:{price_above_vwap}")
    if(debug):st.write(f"price_below_vwap:{price_below_vwap}")
    if(debug):st.write(f"sma5_gt_sma10:{sma5_gt_sma10}")
    if(debug):st.write(f"sma5_lt_sma10:{sma5_lt_sma10}")
    if(debug):st.write(f"higher_close:{higher_close}")
    if(debug):st.write(f"lower_close:{lower_close}")
    #if(debug):st.write(f'info_df_date: {info_df.Datetime}')
    #candlestick chart data
    #existing date
    #placeholder=st.empty()  #already defined above

    with placeholder.container():

        fig=make_subplots(rows=3,cols=1,shared_xaxes=False,vertical_spacing=0.05,row_heights=[0.6,0.2,0.2])

        #first row
        fig.add_trace(go.Candlestick(x=info_df['Datetime'],open=info_df['Open'], high=info_df['High'],low=info_df['Low'],\
                close=info_df['Close'],name=f'{ticker}-Candlestick'),row=1,col=1)

        fig.add_trace(go.Scatter(x=info_df['Datetime'],y=info_df['sma5'],mode='lines',name='SMA5',line=dict(color='red')),row=1,col=1)
        fig.add_trace(go.Scatter(x=info_df['Datetime'],y=info_df['sma10'],mode='lines',name='SMA10',line=dict(color='blue')),row=1,col=1)
        fig.add_trace(go.Scatter(x=info_df['Datetime'],y=info_df['vwap'],mode='lines',name='vwap',line=dict(color='orange')),row=1,col=1)

        #Define the times for vertical lines (using the existing date)
        times = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00']
        for time_str in times:
            time = pd.to_datetime(f"{existing_date} {time_str}")  # Combine date and time
            #print(f'time: {time}')
            fig.add_vline(x=time, line=dict(color='brown', width=0.5, dash='dot'),row=1,col=1)

        #second row
        fig.add_trace(go.Bar(x=info_df['Datetime'], y=info_df['Volume'], text=info_df['Volume'],textposition='auto',name='Volume', marker_color='grey'), row=2, col=1)
        fig.add_trace(go.Scatter(x=info_df['Datetime'],y=info_df['vol5'],mode='lines',name='volume5',line=dict(color='skyblue')),row=2,col=1)

        #third row
        fig.add_trace(go.Bar(x=info_df['Datetime'], y=info_df['tr'], text=info_df['tr'],textposition='auto',name='TR', marker_color='magenta'), row=3, col=1)
        fig.add_trace(go.Scatter(x=info_df['Datetime'],y=info_df['atr5'],mode='lines',name='ATR5',line=dict(color='lightgreen')),row=3,col=1)

        #horizontal line in x_min and x_max
        #date min and max for creating a horizontal line
        date_min=info_df['Datetime'].min()
        date_max=info_df['Datetime'].max()
        max_price=info_df['High'].max()
        min_price=info_df['Low'].min()

        #add the horizontal line at min and max value
        fig.add_shape(type='line',x0=date_min,y0=max_price,x1=date_max,y1=max_price,line=dict(color='lightgreen',width=1,dash='dash'),row=1,col=1)
        fig.add_shape(type='line',x0=date_min,y0=min_price,x1=date_max,y1=min_price,line=dict(color='salmon',width=1,dash='dash'),row=1,col=1)
        
        #generate custom tickers
        start_time=info_df['Datetime'].iloc[0].floor('5min')
        end_time=info_df['Datetime'].iloc[-1].floor('5min')
        custom_ticks_vals=pd.date_range(start=start_time,end=end_time,freq='5min')
        custom_ticks_text=[x.strftime('%H:%M') for x in custom_ticks_vals]
        #printtick labels
        #st.write(f'custom_ticks_vals: {custom_ticks_vals}')
        #st.write(f'custom_ticks_text: {custom_ticks_text}')

        fig.update_layout(xaxis_rangeslider_visible=False,
                xaxis=dict(tickmode='array',tickvals=custom_ticks_vals,ticktext=custom_ticks_text),
                xaxis_tickformat='%H:%M',
                width=1200,height=700,
                )

        #row 1
        with st.container():
            col1,col2,col3,col4,col5,col6,col7=st.columns(7)

            with col1:
                st.metric(f'ticker'.upper(),ticker)
            with col2:
                st.metric(f'time'.upper(),str(last_time))

            with col3:
                st.metric(f'change'.upper(),close,change)
            with col4:
                st.metric('%Change'.upper(),"",pct_change)
            with col5:
               st.metric('TRADED_VOLUME (M)',total_volume)
            with col6:
                st.metric('TR',tr)
            with col7:
                st.metric('ATR_5',atr5)

        #row 2
        with st.container():
            col1,col2,col3,col4,col5=st.columns(5)
            text_size='30px'

            with col1:
                text_color='green' if sma5_gt_sma10 else 'salmon'
                display_text="SMA5 &gt SMA10" if sma5_gt_sma10 else "SMA5 &lt SMA10"
                audio_text="SMA5 is greater than  SMA10" if sma5_gt_sma10 else "SMA5 is less than SMA10"
                st.markdown(f"<h3 Style='color:{text_color};font-size:{text_size}'> {display_text}</h3>",unsafe_allow_html=True)
                text_to_audio(audio_text)
            with col2:
                condition=volume5>volume10
                text_color='green' if condition else 'salmon'
                display_text=''
                if condition:display_text='VOL5 &gt VOL10' #if volume>volume5 else 'VOL &lt VOL5'
                elif not condition:display_text='VOL5 &lt VOL10'
                st.markdown(f"<h3 Style='color:{text_color};font-size:{text_size}'> {display_text}</h3>",unsafe_allow_html=True)

            with col3:
                display_text=''
                text_color='green' if tr>atr5 else 'salmon'
                if tr>atr5:display_text='TR &gt ATR5' #if tr>atr5 else 'TR &lt ATR5'
                elif tr<atr5:display_text='TR &lt ATR5'
                st.markdown(f"<h3 Style='color:{text_color};font-size:{text_size}'> {display_text}</h3>",unsafe_allow_html=True)
            with col4:
                text_color='green' if price_above_vwap else 'salmon'
                display_text="ClOSE &gt VWAP" if price_above_vwap else " CLOSE &lt VWAP"
                st.markdown(f"<h3 Style='color:{text_color};font-size:{text_size}'> {display_text}</h3>",unsafe_allow_html=True)
            
            with col5:
                text_color='green' if higher_close else 'salmon'
                display_text=''
                if higher_close:
                    display_text='HIGHER CLOSE'
                    st.markdown(f"<h3 Style='color:{text_color};font-size:{text_size}'> {display_text}</h3>",unsafe_allow_html=True)
                    text_to_audio("HIGHER CLOSE FOR 3 MINUTES")
                elif lower_close:
                    display_text='LOWER CLOSE'
                    st.markdown(f"<h3 Style='color:{text_color};font-size:{text_size}'> {display_text}</h3>",unsafe_allow_html=True)
                    text_to_audio("LOWER CLOSE FOR 3 MINUTES")
                #st.markdown(f"<h3 Style='color:{text_color};font-size:{text_size}'> {display_text}</h3>",unsafe_allow_html=True)
                
        #row 3
        #plot_key=f'plot_{time.time()}'
        #st.write(f'Time now {time.time()}')
        with st.container():
            st.plotly_chart(fig,use_container_width=True)
    #return info_df.tail(2)

#whilte True:
#def get_ticker_minute_data(ticker):
#    """
#    get minute data for a ticker for a last business day
#    """
# live=True
# count=1
# while live and user_value:
#     if count==5:st.stop()
#     print(f"count: {count}")
#     count+=1
#     try:
#         df=yf.download(user_value,period='1d',interval='1m',group_by='tickers')
#         # Check if DataFrame is empty
#         if df.empty:
#             st.warning('Error Occured, Enter a correct ticker or try again later !',icon="⚠️")
#             st.stop()
#     except:
#         st.warning('Error Occured, Enter a correct ticker or try again later !',icon="⚠️")
#         st.stop()
#     #if(debug):st.dataframe(f'{df.tail()}')
#     st.dataframe(df.tail())
#     df=df.reset_index(drop=False)
#     st.write(f"length: {len(df)}")
#     get_live_plot(df)
#     #get live plot
#     # figg=get_live_plot(df)
#     # plot_placeholder.plotly_chart(figg,use_container_width=True)
#     time.sleep(61)
