import pandas as pd
import pandas_ta as ta
import logging
import numpy as np
from dateutil.parser import parse

logger = logging.getLogger(__name__)

def load_data(file_path):
    logger.info(f"Loading data from {file_path}")
    
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Check if 'date' column exists
        if 'date' not in df.columns:
            raise ValueError("CSV file does not contain a 'date' column")
        
        logger.info(f"Original DataFrame shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        logger.info(f"First few rows of date column:\n{df['date'].head().to_string()}")
        
        # Function to parse dates flexibly
        def parse_date(date_string):
            try:
                return parse(date_string)
            except ValueError:
                return pd.NaT

        # Convert 'date' column to datetime using the flexible parser
        df['date'] = df['date'].apply(parse_date)
        
        # Remove rows with NaT values in the date column
        original_shape = df.shape
        df = df.dropna(subset=['date'])
        logger.info(f"Rows removed due to invalid dates: {original_shape[0] - df.shape[0]}")
        
        logger.info(f"DataFrame shape after date parsing and NaT removal: {df.shape}")
        
        if df.empty:
            raise ValueError("After cleaning, the DataFrame is empty. Check your date formats.")
        
        # Set 'date' as the index
        df.set_index('date', inplace=True)
        
        # Sort the index
        df.sort_index(inplace=True)
        
        logger.info(f"Final DataFrame shape: {df.shape}")
        logger.info(f"Date range: {df.index.min()} to {df.index.max()}")
        
        # Ensure all required columns are present
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' is missing from the CSV file")
        
        return df
    except Exception as e:
        logger.error(f"Error in load_data: {str(e)}")
        raise

def perform_analysis(df):
    logger.info("Performing technical analysis")
    # Add technical indicators
    df['SMA_20'] = ta.sma(df['close'], length=20)
    df['SMA_50'] = ta.sma(df['close'], length=50)
    df['EMA_20'] = ta.ema(df['close'], length=20)
    df['RSI'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'])
    df = df.join(macd)
    bollinger = ta.bbands(df['close'], length=20)
    df = df.join(bollinger)
    stoch = ta.stoch(df['high'], df['low'], df['close'])
    df = df.join(stoch)
    
    # Handle Ichimoku Cloud
    ichimoku = ta.ichimoku(df['high'], df['low'], df['close'])
    for i, component in enumerate(ichimoku):
        component = component.add_prefix(f'ICH_{i}_')
        df = df.join(component)
    
    df['CCI'] = ta.cci(df['high'], df['low'], df['close'])
    
    # New ADX indicator
    adx = ta.adx(df['high'], df['low'], df['close'])
    df = df.join(adx)
    
    # New Williams %R indicator
    df['WILLR'] = ta.willr(df['high'], df['low'], df['close'])

    # Replace NaN values with None for JSON serialization
    df = df.replace({np.nan: None})

    # Prepare data for frontend
    data = df.reset_index().apply(lambda x: x.where(x.notnull(), None))
    data['date'] = data['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    data = data.to_dict('records')

    # Generate indicator signals
    indicator_data = []
    signals = {
        'SMA': [], 'EMA': [], 'RSI': [], 'MACD': [], 'BB': [], 'Stoch': [], 'Ichimoku': [], 'CCI': [], 'ADX': [], 'WILLR': []
    }
    trades = []
    open_trades = {}

    for index, row in df.iterrows():
        date_str = index.strftime('%Y-%m-%d %H:%M:%S')
        active_signals = []

        # SMA
        if row['SMA_20'] is not None and row['SMA_50'] is not None:
            if row['SMA_20'] > row['SMA_50']:
                signals['SMA'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                indicator_data.append({'date': date_str, 'indicator': 'SMA', 'value': row['SMA_20'], 'action': 'buy'})
                active_signals.append('SMA')
            elif row['SMA_20'] < row['SMA_50']:
                signals['SMA'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                indicator_data.append({'date': date_str, 'indicator': 'SMA', 'value': row['SMA_20'], 'action': 'sell'})

        # EMA
        if row['EMA_20'] is not None and row['close'] is not None:
            if row['close'] > row['EMA_20']:
                signals['EMA'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                indicator_data.append({'date': date_str, 'indicator': 'EMA', 'value': row['EMA_20'], 'action': 'buy'})
                active_signals.append('EMA')
            elif row['close'] < row['EMA_20']:
                signals['EMA'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                indicator_data.append({'date': date_str, 'indicator': 'EMA', 'value': row['EMA_20'], 'action': 'sell'})

        # RSI
        if row['RSI'] is not None:
            if row['RSI'] < 30:
                signals['RSI'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                indicator_data.append({'date': date_str, 'indicator': 'RSI', 'value': row['RSI'], 'action': 'buy'})
                active_signals.append('RSI')
            elif row['RSI'] > 70:
                signals['RSI'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                indicator_data.append({'date': date_str, 'indicator': 'RSI', 'value': row['RSI'], 'action': 'sell'})

        # MACD
        if row['MACD_12_26_9'] is not None and row['MACDs_12_26_9'] is not None:
            prev_index = df.index[df.index.get_loc(index) - 1] if df.index.get_loc(index) > 0 else None
            if prev_index is not None:
                prev_macd = df.loc[prev_index, 'MACD_12_26_9']
                prev_signal = df.loc[prev_index, 'MACDs_12_26_9']
                if prev_macd is not None and prev_signal is not None:
                    if row['MACD_12_26_9'] > row['MACDs_12_26_9'] and prev_macd <= prev_signal:
                        signals['MACD'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                        indicator_data.append({'date': date_str, 'indicator': 'MACD', 'value': row['MACD_12_26_9'], 'action': 'buy'})
                        active_signals.append('MACD')
                    elif row['MACD_12_26_9'] < row['MACDs_12_26_9'] and prev_macd >= prev_signal:
                        signals['MACD'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                        indicator_data.append({'date': date_str, 'indicator': 'MACD', 'value': row['MACD_12_26_9'], 'action': 'sell'})

        # Bollinger Bands
        if all(row[col] is not None for col in ['close', 'BBL_20_2.0', 'BBU_20_2.0']):
            if row['close'] < row['BBL_20_2.0']:
                signals['BB'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                indicator_data.append({'date': date_str, 'indicator': 'BB', 'value': row['BBL_20_2.0'], 'action': 'buy'})
                active_signals.append('BB')
            elif row['close'] > row['BBU_20_2.0']:
                signals['BB'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                indicator_data.append({'date': date_str, 'indicator': 'BB', 'value': row['BBU_20_2.0'], 'action': 'sell'})

        # Stochastic Oscillator
        if all(row[col] is not None for col in ['STOCHk_14_3_3', 'STOCHd_14_3_3']):
            if row['STOCHk_14_3_3'] < 20 and row['STOCHk_14_3_3'] > row['STOCHd_14_3_3']:
                signals['Stoch'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                indicator_data.append({'date': date_str, 'indicator': 'Stoch', 'value': row['STOCHk_14_3_3'], 'action': 'buy'})
                active_signals.append('Stoch')
            elif row['STOCHk_14_3_3'] > 80 and row['STOCHk_14_3_3'] < row['STOCHd_14_3_3']:
                signals['Stoch'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                indicator_data.append({'date': date_str, 'indicator': 'Stoch', 'value': row['STOCHk_14_3_3'], 'action': 'sell'})

        # Ichimoku Cloud
        if all(row[f'ICH_0_{col}'] is not None for col in ['ISA_9', 'ISB_26', 'ITS_9', 'IKS_26']) and row['close'] is not None:
            if row['close'] > row['ICH_0_ISA_9'] and row['close'] > row['ICH_0_ISB_26'] and row['ICH_0_ITS_9'] > row['ICH_0_IKS_26']:
                signals['Ichimoku'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                indicator_data.append({'date': date_str, 'indicator': 'Ichimoku', 'value': row['ICH_0_ISA_9'], 'action': 'buy'})
                active_signals.append('Ichimoku')
            elif row['close'] < row['ICH_0_ISA_9'] and row['close'] < row['ICH_0_ISB_26'] and row['ICH_0_ITS_9'] < row['ICH_0_IKS_26']:
                signals['Ichimoku'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                indicator_data.append({'date': date_str, 'indicator': 'Ichimoku', 'value': row['ICH_0_ISA_9'], 'action': 'sell'})

        # CCI
        if row['CCI'] is not None:
            if row['CCI'] < -100:
                signals['CCI'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                indicator_data.append({'date': date_str, 'indicator': 'CCI', 'value': row['CCI'], 'action': 'buy'})
                active_signals.append('CCI')
            elif row['CCI'] > 100:
                signals['CCI'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                indicator_data.append({'date': date_str, 'indicator': 'CCI', 'value': row['CCI'], 'action': 'sell'})

        # ADX
        if all(row[col] is not None for col in ['ADX_14', 'DMP_14', 'DMN_14']):
            if row['ADX_14'] > 25:
                if row['DMP_14'] > row['DMN_14']:
                    signals['ADX'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                    indicator_data.append({'date': date_str, 'indicator': 'ADX', 'value': row['ADX_14'], 'action': 'buy'})
                    active_signals.append('ADX')
                elif row['DMP_14'] < row['DMN_14']:
                    signals['ADX'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                    indicator_data.append({'date': date_str, 'indicator': 'ADX', 'value': row['ADX_14'], 'action': 'sell'})

        # Williams %R
        if row['WILLR'] is not None:
            if row['WILLR'] < -80:
                signals['WILLR'].append({'date': date_str, 'close': row['close'], 'action': 'buy'})
                indicator_data.append({'date': date_str, 'indicator': 'WILLR', 'value': row['WILLR'], 'action': 'buy'})
                active_signals.append('WILLR')
            elif row['WILLR'] > -20:
                signals['WILLR'].append({'date': date_str, 'close': row['close'], 'action': 'sell'})
                indicator_data.append({'date': date_str, 'indicator': 'WILLR', 'value': row['WILLR'], 'action': 'sell'})

        # Check for multiple buy signals
        if len(active_signals) > 5:
            for indicator in active_signals:
                if indicator not in open_trades:
                    open_trades[indicator] = {
                        'buy_date': date_str,
                        'buy_price': row['close'],
                        'indicators': active_signals
                    }

        # Check for sell signals and close trades
        for indicator, trade in list(open_trades.items()):
            if (indicator == 'SMA' and row['SMA_20'] is not None and row['SMA_50'] is not None and row['SMA_20'] < row['SMA_50']) or \
               (indicator == 'EMA' and row['close'] is not None and row['EMA_20'] is not None and row['close'] < row['EMA_20']) or \
               (indicator == 'RSI' and row['RSI'] is not None and row['RSI'] > 70) or \
               (indicator == 'MACD' and row['MACD_12_26_9'] is not None and row['MACDs_12_26_9'] is not None and row['MACD_12_26_9'] < row['MACDs_12_26_9']) or \
               (indicator == 'BB' and row['close'] is not None and row['BBU_20_2.0'] is not None and row['close'] > row['BBU_20_2.0']) or \
               (indicator == 'Stoch' and row['STOCHk_14_3_3'] is not None and row['STOCHk_14_3_3'] > 80) or \
               (indicator == 'Ichimoku' and row['close'] is not None and row['ICH_0_ISA_9'] is not None and row['close'] < row['ICH_0_ISA_9']) or \
               (indicator == 'CCI' and row['CCI'] is not None and row['CCI'] > 100) or \
               (indicator == 'ADX' and row['DMP_14'] is not None and row['DMN_14'] is not None and row['DMP_14'] < row['DMN_14']) or \
               (indicator == 'WILLR' and row['WILLR'] is not None and row['WILLR'] > -20):
                if row['close'] is not None and trade['buy_price'] is not None:
                    profit = row['close'] - trade['buy_price']
                else:
                    profit = None
                trades.append({
                    'buy_date': trade['buy_date'],
                    'buy_price': trade['buy_price'],
                    'sell_date': date_str,
                    'sell_price': row['close'],
                    'profit': profit,
                    'indicators': trade['indicators']
                })
                del open_trades[indicator]

    logger.info(f"Analysis complete. Generated {len(indicator_data)} indicator data points and {len(trades)} trades")
    return data, indicator_data, signals, trades