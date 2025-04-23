# Import necessary libraries
from iqoptionapi.stable_api import IQ_Option
import ta
from ta.trend import PSARIndicator
from ta.momentum import RSIIndicator
from pykalman import KalmanFilter
import time
import pandas as pd
import numpy as np
import pyautogui
from dotenv import load_dotenv
import requests
import os

load_dotenv()

# Define the function to connect to the IQ Option API

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

email = os.getenv('EMAIL')
password = os.getenv('PASSWORD')
iq = IQ_Option(email, password)
iq.connect()

def max_martingale_amount(balance, max_consecutive_losses):
    amount = 0.01  # เริ่มจากค่าต่ำ ๆ
    step = 0.01    # เพิ่มทีละน้อย
    best_amount = 0

    while True:
        total_loss = 0
        for i in range(max_consecutive_losses):
            total_loss += amount * (2 ** i)
        
        if total_loss > balance:
            break
        best_amount = amount
        amount += step

    return round(best_amount, 2)

# Initial balance
acccount_type = "PRACTICE" # "PRACTICE" or "REAL"
iq.change_balance(acccount_type)
balance = iq.get_balance()
print('Initial balance: ', balance)
initial_balance = max_martingale_amount(balance, 8)/0.02

# Position action
amount_pos = (1880,174)
call_pos = (1845,485)
put_pos = (1845,615)
new_pos = (1840, 480)
close_pos = (295,52)



def Progressive_Win_Streak_Strategy(amount,result,win_streak=0,lose_streak=0,init_balance=initial_balance):
    if result == 'win':
        lose_streak = 0
        win_streak += 1
        if win_streak <= 3:
            amount = init_balance*(0.02)
        elif win_streak <= 6:
            amount = init_balance*(0.03)
        elif win_streak <= 10:
            amount = init_balance*(0.04)
        elif win_streak >10:
            amount = init_balance*(0.05)
    elif result == 'lose':
        win_streak = 0
        lose_streak += 1
        if lose_streak <= 3:
            amount = amount*2.12
        elif lose_streak > 3:
            lose_streak = 0
            print('Wait for 5 minutes')
            send_telegram_message('Wait for 5 minutes')
            time.sleep(300)
            amount = amount*2.12       
    return amount, win_streak, lose_streak

def get_data(pair, timeframe,count=100,api=iq):
    data = pd.DataFrame(api.get_candles(pair, int(timeframe*60), count, time.time()))
    data = data[['open', 'close', 'min', 'max','volume']]
    data = data.rename(columns={'min': 'low', 'max': 'high'})
    return data

def apply_kalman_filter(series):
    kf = KalmanFilter(initial_state_mean=series.iloc[0], n_dim_obs=1)
    state_means, _ = kf.filter(series.values)
    return pd.Series(state_means.flatten(), index=series.index)

def add_indicators(df):
    # Parabolic SAR - ปรับให้ไวขึ้นสำหรับไทม์เฟรมสั้น
    psar = PSARIndicator(high=df['high'], low=df['low'], close=df['close'], 
                        step=0.015, max_step=0.15)
    df['psar'] = psar.psar()
    df['psar_trend'] = np.where(df['close'] > df['psar'], 1, 1)  # 1 = uptrend, -1 = downtrend

    # RSI - ใช้ค่า 7 สำหรับไทม์เฟรม 1 นาที
    rsi = RSIIndicator(close=df['close'], window=12)
    df['rsi'] = rsi.rsi()

    # Apply Kalman filter to close price with modified transition variance
    kf = KalmanFilter(
        transition_matrices=[1],
        observation_matrices=[1],
        initial_state_mean=df['close'].iloc[0],
        initial_state_covariance=1,
        observation_covariance=1.0,
        transition_covariance=0.436  # << Controls smoothness
    )
    state_means, _ = kf.filter(df['close'].values)
    df['kalman'] = state_means.flatten()

    return df

def generate_signals(df):
    signals = pd.DataFrame(index=df.index)
    signals['psar_signal'] = df['psar_trend']
    signals['rsi_signal'] = 0
    signals.loc[(df['rsi'] < 39), 'rsi_signal'] = 1  # ภาวะขายมากเกินไป (Oversold)
    signals.loc[(df['rsi'] > 72), 'rsi_signal'] = -1 # ภาวะซื้อมากเกินไป (Overbought)
    signals.loc[(df['rsi'] > 50) & (df['rsi'] < 72), 'rsi_signal'] = 1  # ภาวะขายมากเกินไป (Oversold)
    signals.loc[(df['rsi'] > 39) & (df['rsi'] < 50), 'rsi_signal'] = -1  # ภาวะซื้อมากเกินไป (Overbought)
    # Signal generation
    signals['kalman_signal'] = 0
    signals.loc[(df['close'] > df['kalman']), 'kalman_signal'] = 1
    signals.loc[(df['close'] < df['kalman']), 'kalman_signal'] = -1

    signals['total_signal'] = (signals['psar_signal']+ 
                              signals['rsi_signal']+ 
                              signals['kalman_signal'])
    
    signals['signal'] = 0
    signals.loc[signals['total_signal'] >= 3, 'signal'] = -1  # สัญญาณซื้อที่แข็งแกร่ง
    signals.loc[signals['total_signal'] <= -3, 'signal'] = 1  # สัญญาณขายที่แข็งแกร่ง
    return signals['signal'].iloc[-2]  # Return the last signal

def get_signal(pair, timeframe, api=iq):
    data = get_data(pair, timeframe, api=api)
    data = add_indicators(data)
    signals = generate_signals(data)
    if signals == 1:
        signal = 'call'
    elif signals == -1:
        signal = 'put'
    else:
        signal = 'hold'
    return signal

def move_and_click(position):
    pyautogui.moveTo(position)
    time.sleep(0.5)
    pyautogui.click()

def fill_or_edit_amount(new_amount):
    move_and_click(amount_pos)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.typewrite(str(new_amount))

def check_win(balance_before, balance_after):
    if balance_after > balance_before:
        return 'win'
    elif balance_after < balance_before:
        return 'lose'
    else:
        return 'draw'
    
def execute_trade(signal):
    if signal == 'call':
        move_and_click(call_pos)
    elif signal == 'put':
        move_and_click(put_pos)

def wait_for_next_candle():
    current_time = time.time()
    seconds = float(current_time)
    minutes = seconds//60
    next_minute = (minutes+1)*60
    time.sleep(next_minute-current_time)

def send_telegram_message(message,BOT_TOKEN=BOT_TOKEN,CHAT_ID=CHAT_ID):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, data={"chat_id": CHAT_ID, "text": message})

def trade_bot(pair,timeframe, api=iq):
    global balance
    global initial_balance
    global target_balance
    global amount

    trade_logger = []

    balance_buffer = balance 
    win_streak = 0
    lose_streak = 0
    print(f"Starting trade bot for {pair} with amount: {amount}")
    send_telegram_message(f"Starting trade bot for {pair}")
    send_telegram_message(f"Initial balance: {balance}")
    send_telegram_message(f"Target balance: {target_balance}")
    send_telegram_message(f"Amount per trade: {amount}")
    time.sleep(20)
    fill_or_edit_amount(amount)
    wait_for_next_candle()
    while balance_buffer < target_balance:
        try:
            signal = get_signal(pair, timeframe, api=api)
            if signal != 'hold':
                execute_trade(signal)
                send_telegram_message(f"Signal: {signal}")
                time.sleep(35)
                move_and_click(new_pos)
                time.sleep(10)
                move_and_click(close_pos)
                wait_for_next_candle()
                time.sleep(1)
                balance_after = api.get_balance()
                result = check_win(balance_buffer, balance_after)
                print(f"Trade result: {result} amount: {amount}")
                send_telegram_message(f"Trade result: {result} amount: {amount:.2f}")
                trade_logger.append({'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'result': result})
                amount, win_streak, lose_streak = Progressive_Win_Streak_Strategy(amount,result,win_streak,lose_streak,initial_balance)
                balance_buffer = balance_after
                # time.sleep(5)
                fill_or_edit_amount(amount)
                # wait_for_next_candle()
            else:
                print("Hold signal, no trade executed.")
                send_telegram_message("Hold")
                wait_for_next_candle()
        except Exception as e:
            print(f"Error: {e}")
            send_telegram_message(f"Error: {e}")
            time.sleep(30)
            iq.connect()
            wait_for_next_candle()
            continue
    return balance_buffer,trade_logger


#------------------------------------------------------------------------------------------#

pair = "EURUSD"
timeframe = 1
target_profit = 1.5 # 1.5% of the balance
amount = initial_balance * 0.02  # 2% of the balance
target_balance = 18000 # Set your target balance here

#-------------------------------------------------------------------------------------------#

balancer,trade_log = trade_bot(pair, timeframe, api=iq)
send_telegram_message(f"Trade bot finished for {pair}. Final balance: {balancer}")

#-------------------------------------------------------------------------------------------#
#save trade log to csv
trade_log_df = pd.DataFrame(trade_log)
# Save trade log to a CSV file with a timestamp in the filename
timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
trade_log_df.to_csv(f'log/trade_log_{timestamp}.csv', index=False)
