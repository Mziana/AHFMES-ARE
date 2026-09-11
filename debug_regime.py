import sys
sys.path.insert(0, 'D:/Hermes/AHFMES-ARE')

from strategy_v2 import zones as Z

def make_m15(n, start=1788739200, base=4400.0, drift=0.08):
    out = []
    for i in range(n):
        c = base + drift * i
        out.append({'time': start + i * 900, 'open': c, 'high': c + 0.5, 'low': c - 0.5,
                    'close': c, 'volume': 400 + (i % 3)})
    return out

m15 = make_m15(288)
closes = [b['close'] for b in m15]

# Check EMA values
e20 = Z.ema(closes, 20)
e9 = Z.ema(closes, 9)
e21 = Z.ema(closes, 21)

print(f'EMA20 (last 5): {e20[-5:]}')
print(f'EMA9 (last 5): {e9[-5:]}')
print(f'EMA21 (last 5): {e21[-5:]}')

# Check RSI for each bar
for i in range(50, 100):
    r = Z.rsi(closes[:i+1], 14)
    close = closes[i]
    e20_val = e20[i]
    e9_val = e9[i]
    e21_val = e21[i]
    
    buy = close > e20[i] and e9[i] > e21[i] and (r or 0) > 50
    sell = close < e20[i] and e9[i] < e21[i] and (r or 0) < 50
    
    if buy or sell:
        print(f'Bar {i}: close={close:.2f}, e20={e20[i]:.2f}, e9={e9[i]:.2f}, e21={e21[i]:.2f}, rsi={r:.1f}, BUY={buy}, SELL={sell}')

# Check how many bars have valid RSI
valid_rsi = sum(1 for i in range(len(closes)) if Z.rsi(closes[:i+1], 14) is not None)
print(f'\nTotal bars with valid RSI: {valid_rsi}/{len(closes)}')

# Check regime conditions for all bars
buy_count = 0
sell_count = 0
no_trade = 0
for i in range(50, len(closes)):
    close = closes[i]
    r = Z.rsi(closes[:i+1], 14)
    
    buy = close > e20[i] and e9[i] > e21[i] and (r or 0) > 50
    sell = close < e20[i] and e9[i] < e21[i] and (r or 0) < 50
    
    if buy:
        buy_count += 1
    elif sell:
        sell_count += 1
    else:
        no_trade += 1

print(f'\nRegime summary:')
print(f'  BUY_ONLY: {buy_count}')
print(f'  SELL_ONLY: {sell_count}')
print(f'  NO_TRADE: {no_trade}')
print(f'  Total evaluated: {buy_count + sell_count + no_trade}')