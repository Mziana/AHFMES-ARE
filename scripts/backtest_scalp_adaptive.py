"""
Backtest Scalp Adaptive — 1 minggu data MT5 nyata (termasuk hari ini).

Mereplikasi sinyal decision engine (scalp: M5 + M15, konfirmasi 2/2)
persis seperti UI/src/app/api/are/decision/route.ts, lalu membandingkan
4 strategi SL/TP/exit:

  A. Baseline  : SL = 1.0xATR(M5), TP = 2.0xATR(M5), exit hanya SL/TP
  B. Regime SL : SL = ATR x (0.75 + 0.75 x ATR-percentile-100), TP = 2xSL
  C. B + BE/Time: breakeven setelah +1R + time-exit 60 bar M1
  D. C + Momentum: exit saat RSI(M5) + EMA21(M5) melawan posisi

Plus audit MAE/MFE per entri untuk menentukan lebar SL optimal per regime.

Pemakaian:
    python scripts/backtest_scalp_adaptive.py
"""

import sys
import math
import bisect
from datetime import datetime, timedelta

import MetaTrader5 as mt5

SYMBOL = "XAUUSD"
STYLE = "scalp"
RISK_PCT = 1.0
MAX_POSITIONS = 5
COOLDOWN_SECONDS = 60
MIN_SL_PTS = 8.0
MAX_LOT = 0.10
SPREAD_PTS = 35.0          # spread nyata Finex saat ini (0.35 harga = 35 poin)
COMMISSION_PER_LOT = 1.0   # $/lot per sisi
TICK_VALUE = 0.01
CONTRACT = 100
MARGIN_PER_LOT = 200.0
START_BALANCE = 1605.33
DAYS = 7
TIME_EXIT_BARS = 60        # 60 bar M1 = 1 jam
BE_AFTER_R = 1.0           # breakeven setelah profit 1R
MOM_MIN_HOLD_M5 = 3        # momentum exit minimal 3 bar M5 (15 menit)

# ─── INDIKATOR (port persis dari UI/src/lib/indicators.ts) ──────────────────

def ema(arr, period):
    k = 2 / (period + 1)
    prev = None
    out = []
    for i, v in enumerate(arr):
        if i < period - 1:
            out.append(float('nan'))
            continue
        if i == period - 1:
            prev = sum(arr[:period]) / period
            out.append(prev)
            continue
        prev = v * k + prev * (1 - k)
        out.append(prev)
    return out


def rsi_series(closes, period=14):
    n = len(closes)
    out = [float('nan')]
    if n < 2:
        return out
    gains = [max(closes[i] - closes[i - 1], 0) for i in range(1, n)]
    losses = [max(closes[i - 1] - closes[i], 0) for i in range(1, n)]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(n - 1):
        if i < period - 1:
            out.append(float('nan'))
            continue
        if i == period - 1:
            rs = avg_gain / avg_loss if avg_loss > 0 else 100.0
            out.append(100 - 100 / (1 + rs))
            continue
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss > 0 else 100.0
        out.append(100 - 100 / (1 + rs))
    return out


def atr_series(highs, lows, closes, period=14):
    n = len(closes)
    tr = [highs[0] - lows[0]]
    for i in range(1, n):
        tr.append(max(highs[i] - lows[i],
                      abs(highs[i] - closes[i - 1]),
                      abs(lows[i] - closes[i - 1])))
    out = []
    for i in range(n):
        if i < period - 1:
            out.append(float('nan'))
        else:
            out.append(sum(tr[i - period + 1:i + 1]) / period)
    return out


def find_swings(highs, lows, lookback=5):
    swings = []
    n = len(highs)
    for i in range(lookback, n - lookback):
        is_high = True
        for k in range(1, lookback + 1):
            if highs[i] <= highs[i - k] or highs[i] <= highs[i + k]:
                is_high = False
                break
        if is_high:
            swings.append((i, highs[i], 'high'))
        is_low = True
        for k in range(1, lookback + 1):
            if lows[i] >= lows[i - k] or lows[i] >= lows[i + k]:
                is_low = False
                break
        if is_low:
            swings.append((i, lows[i], 'low'))
    return swings


def nearest_sr(swings, price, atr_val):
    supports = sorted([s for s in swings if s[2] == 'low' and s[1] < price],
                      key=lambda s: -s[1])
    resistances = sorted([s for s in swings if s[2] == 'high' and s[1] > price],
                         key=lambda s: s[1])
    return {
        'nearestSupport': supports[0][1] if supports else price - atr_val * 2,
        'nearestResistance': resistances[0][1] if resistances else price + atr_val * 2,
        'supportCount': len(supports),
        'resistanceCount': len(resistances),
    }


def tf_signal(highs, lows, closes, vols):
    """Signal per timeframe persis decision/route.ts (zone entry mode)."""
    n = len(closes)
    if n < 30:
        return None
    atr_v = atr_series(highs, lows, closes)[-1]
    rsi_v = rsi_series(closes)[-1]
    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    ema_bull = ema9[-1] > ema21[-1]
    swings = find_swings(highs, lows, 5)
    sr = nearest_sr([(s[0], s[1], s[2]) for s in swings], closes[-1], atr_v)

    buy, sell = 0.0, 0.0
    if rsi_v < 30:
        buy += 2
    elif rsi_v < 40:
        buy += 1
    elif rsi_v > 70:
        sell += 2
    elif rsi_v > 60:
        sell += 1

    if ema_bull:
        buy += 1.5
    else:
        sell += 1.5

    price = closes[-1]
    range_to_res = (sr['nearestResistance'] - price) / price
    range_to_sup = (price - sr['nearestSupport']) / price
    if range_to_res < 0.003 and sr['resistanceCount'] > 0:
        sell += 2
    elif range_to_res < 0.008:
        sell += 1
    if range_to_sup < 0.003 and sr['supportCount'] > 0:
        buy += 2
    elif range_to_sup < 0.008:
        buy += 1

    avg_vol = sum(vols[-20:]) / 20 if len(vols) >= 20 else 1
    last_vol = vols[-1]
    if last_vol > avg_vol * 1.5:
        if closes[-1] > closes[-2]:
            buy += 0.5
        else:
            sell += 0.5

    if buy > sell:
        return {'signal': 'BUY', 'atr': atr_v}
    if sell > buy:
        return {'signal': 'SELL', 'atr': atr_v}
    return {'signal': 'NEUTRAL', 'atr': atr_v}


# ─── SL/TP PER STRATEGI ──────────────────────────────────────────────────────

def atr_percentile(atr_hist, idx, window=100):
    """Peringkat persentil ATR saat ini terhadap window bar sebelumnya."""
    lo = max(0, idx - window)
    window_vals = atr_hist[lo:idx + 1]
    cur = atr_hist[idx]
    below = sum(1 for v in window_vals if v <= cur)
    return below / len(window_vals)


def compute_sltp(atr_val, atr_hist, idx, strategy):
    """SL/TP dalam POIN MT5 sejati. R:R selalu 2:1."""
    if strategy == 'A':
        mult = 1.0
    else:  # B, C, D — regime-aware
        pctl = atr_percentile(atr_hist, idx)
        mult = 0.75 + 0.75 * pctl  # 0.75x .. 1.5x ATR
    sl_pts = max(atr_val * mult * 100, MIN_SL_PTS)
    tp_pts = max(atr_val * mult * 200, MIN_SL_PTS * 2)
    return round(sl_pts), round(tp_pts)


def lot_size(balance, sl_pts):
    risk_usd = balance * RISK_PCT / 100
    lots = risk_usd / (sl_pts * TICK_VALUE * CONTRACT)  # $/poin/lot = 1.0
    lots = round(lots * 100) / 100
    max_by_margin = math.floor(balance / MARGIN_PER_LOT) / 100
    lots = min(lots, max_by_margin, MAX_LOT)
    if lots < 0.01 and balance >= MARGIN_PER_LOT:
        lots = 0.01
    return max(0, round(lots * 100) / 100)


# ─── REPLAY ──────────────────────────────────────────────────────────────────

def m15_signal_at(t, m5, m15, m5_t, m5_h, m5_l, m5_c, m5_v, m15_t, m15_h, m15_l, m15_c, m15_v):
    """
    Sinyal M15 pada waktu t tanpa lookahead: bar M15 yang sedang terbentuk
    direkonstruksi parsial dari bar M5 yang SUDAH SELESAI sampai t.
    (Engine live membaca bar forming via copy_rates_from_pos(0).)
    """
    t15 = t - (t % 900)
    # Bar M15 selesai terakhir (time <= t15-900)
    c_idx = bisect.bisect_right(m15_t, t15 - 900) - 1
    if c_idx < 0:
        return None
    # Bar M5 selesai di dalam window [t15, t): time di [t15, t-300]
    p_lo = bisect.bisect_left(m5_t, t15)
    p_hi = bisect.bisect_left(m5_t, t - 300)  # eksklusif; bar time=t-300 menutup tepat di t
    if p_hi > p_lo:
        part = {'h': max(m5_h[p_lo:p_hi]), 'l': min(m5_l[p_lo:p_hi]),
                'c': m5_c[p_hi - 1], 'v': sum(m5_v[p_lo:p_hi])}
    else:
        # Tepat di batas M15: bar baru kosong, harga = close M5 terakhir
        part = {'h': m5_c[p_hi - 1], 'l': m5_c[p_hi - 1],
                'c': m5_c[p_hi - 1], 'v': 0}
    # Gabung: 199 bar M15 selesai + 1 bar parsial = 200
    lo = max(0, c_idx - 198)
    highs = list(m15_h[lo:c_idx + 1]) + [part['h']]
    lows = list(m15_l[lo:c_idx + 1]) + [part['l']]
    closes = list(m15_c[lo:c_idx + 1]) + [part['c']]
    vols = list(m15_v[lo:c_idx + 1]) + [part['v']]
    return tf_signal(highs, lows, closes, vols)


def run_strategy(m1, m5, m15, strategy):
    """Jalankan satu strategi. m1/m5/m15 = list tuple (time,o,h,l,c,vol)."""
    m1_t, m1_o, m1_h, m1_l, m1_c = ([x[i] for x in m1] for i in range(5))
    m5_t, m5_o, m5_h, m5_l, m5_c, m5_v = ([x[i] for x in m5] for i in range(6))
    m15_t, m15_h, m15_l, m15_c, m15_v = ([x[i] for x in m15] for i in (0, 2, 3, 4, 5))

    # Pra-hitung indikator M5 (per bar, window 200)
    m5_atr = atr_series(m5_h, m5_l, m5_c)
    m5_rsi = rsi_series(m5_c)
    m5_ema21 = ema(m5_c, 21)
    m5_ema9 = ema(m5_c, 9)

    balance = START_BALANCE
    positions = []  # dict: ticket(dummy), dir, entry, sl, tp, sl_pts, lot,
    #               entry_idx, entry_t, mae, mfe, bars_held, be_done, opened_at_m5
    trades = []
    last_action_t = -1e9
    equity_peak = balance
    max_dd = 0.0

    def settle(pos, m1_i, reason):
        nonlocal balance, equity_peak, max_dd
        if pos['closed']:
            return
        # Exit pada LEVEL SL/TP (bukan tutup bar) untuk akurasi P/L,
        # dan batasi MAE/MFE sesuai level yang benar-benar tersentuh.
        if reason == 'SL':
            exit_px = pos['sl']
            pos['mae'] = max(pos['mae'], pos['sl_pts'])
        elif reason == 'TP':
            exit_px = pos['tp']
            pos['mfe'] = max(pos['mfe'], pos['sl_pts'] * 2)
        else:
            exit_px = m1_c[m1_i]
        if pos['dir'] == 'SELL':
            pts = (pos['entry'] - exit_px) * 100
        else:
            pts = (exit_px - pos['entry']) * 100
        pnl = pts * pos['lot'] - (SPREAD_PTS + 2 * COMMISSION_PER_LOT) * pos['lot']
        balance += pnl
        equity_peak = max(equity_peak, balance)
        max_dd = max(max_dd, equity_peak - balance)
        pos['closed'] = True
        pos['reason'] = reason
        pos['exit_px'] = exit_px
        pos['pnl'] = pnl
        pos['exit_idx'] = m1_i
        trades.append(pos)

    n_m5 = len(m5_t)
    warmup = 60
    for j in range(warmup, n_m5):
        t_close = m5_t[j]

        # ── 1. Selesaikan posisi terbuka pada bar M1 yang SELESAI di (prev_close, t_close)
        prev_t = m5_t[j - 1]
        lo_idx = bisect.bisect_left(m1_t, prev_t)
        hi_idx = bisect.bisect_left(m1_t, t_close)  # bar dengan time < t_close (sudah tutup)
        for i in range(lo_idx, min(hi_idx, len(m1_t))):
            for pos in positions:
                if pos['closed']:
                    continue
                pos['bars_held'] += 1
                if pos['dir'] == 'SELL':
                    # Cek SL/TP DULU — bar pemicu tidak ikut menambah MAE/MFE
                    # (level sudah tercatat persis saat settle).
                    if m1_h[i] >= pos['sl']:
                        settle(pos, i, 'SL')
                        continue
                    if m1_l[i] <= pos['tp']:
                        settle(pos, i, 'TP')
                        continue
                    pos['mae'] = max(pos['mae'], (m1_h[i] - pos['entry']) * 100)
                    pos['mfe'] = max(pos['mfe'], (pos['entry'] - m1_l[i]) * 100)
                    # breakeven: harga turun 1R → SL ke entry
                    if strategy in ('C', 'D') and not pos['be_done']:
                        if m1_l[i] <= pos['entry'] - pos['sl_pts'] * 0.01:
                            pos['sl'] = pos['entry']
                            pos['be_done'] = True
                    # time exit
                    if strategy in ('C', 'D') and pos['bars_held'] >= TIME_EXIT_BARS:
                        settle(pos, i, 'TIME')
                        continue
                else:  # BUY
                    if m1_l[i] <= pos['sl']:
                        settle(pos, i, 'SL')
                        continue
                    if m1_h[i] >= pos['tp']:
                        settle(pos, i, 'TP')
                        continue
                    pos['mae'] = max(pos['mae'], (pos['entry'] - m1_l[i]) * 100)
                    pos['mfe'] = max(pos['mfe'], (m1_h[i] - pos['entry']) * 100)
                    if strategy in ('C', 'D') and not pos['be_done']:
                        if m1_h[i] >= pos['entry'] + pos['sl_pts'] * 0.01:
                            pos['sl'] = pos['entry']
                            pos['be_done'] = True
                    if strategy in ('C', 'D') and pos['bars_held'] >= TIME_EXIT_BARS:
                        settle(pos, i, 'TIME')
                        continue

        # ── 2. Momentum exit (strategi D) — dinilai saat M5 tutup
        if strategy == 'D':
            for pos in positions:
                if pos['closed']:
                    continue
                held_m5 = (j - pos['opened_m5'])
                if held_m5 < MOM_MIN_HOLD_M5:
                    continue
                r5 = m5_rsi[j]
                c5 = m5_c[j]
                e21 = m5_ema21[j]
                if math.isnan(r5) or math.isnan(e21):
                    continue
                if pos['dir'] == 'SELL' and r5 > 55 and c5 > e21:
                    # tutup di harga tutup M5 (harga pada t_close)
                    if pos['dir'] == 'SELL':
                        pts = (pos['entry'] - c5) * 100
                    else:
                        pts = (c5 - pos['entry']) * 100
                    pnl = pts * pos['lot'] - (SPREAD_PTS + 2 * COMMISSION_PER_LOT) * pos['lot']
                    balance += pnl
                    equity_peak = max(equity_peak, balance)
                    max_dd = max(max_dd, equity_peak - balance)
                    pos['closed'] = True
                    pos['reason'] = 'MOM'
                    pos['exit_px'] = c5
                    pos['pnl'] = pnl
                    pos['exit_idx'] = hi_idx - 1
                    trades.append(pos)
                elif pos['dir'] == 'BUY' and r5 < 45 and c5 < e21:
                    if pos['dir'] == 'SELL':
                        pts = (pos['entry'] - c5) * 100
                    else:
                        pts = (c5 - pos['entry']) * 100
                    pnl = pts * pos['lot'] - (SPREAD_PTS + 2 * COMMISSION_PER_LOT) * pos['lot']
                    balance += pnl
                    equity_peak = max(equity_peak, balance)
                    max_dd = max(max_dd, equity_peak - balance)
                    pos['closed'] = True
                    pos['reason'] = 'MOM'
                    pos['exit_px'] = c5
                    pos['pnl'] = pnl
                    pos['exit_idx'] = hi_idx - 1
                    trades.append(pos)

        # ── 3. Evaluasi sinyal di tutup M5
        open_count = sum(1 for p in positions if not p['closed'])
        if open_count < MAX_POSITIONS and (t_close - last_action_t) >= COOLDOWN_SECONDS:
            # data fresh? (mirror engine: bar M1 terakhir selesai <= 11 menit)
            last_m1 = m1_t[min(hi_idx - 1, len(m1_t) - 1)]
            if t_close - last_m1 <= 660:
                sig5 = tf_signal(m5_h[j - 199:j + 1], m5_l[j - 199:j + 1],
                                 m5_c[j - 199:j + 1], m5_v[j - 199:j + 1])
                if sig5 and sig5['signal'] != 'NEUTRAL':
                    sig15 = m15_signal_at(t_close, m5, m15, m5_t, m5_h, m5_l, m5_c, m5_v,
                                          m15_t, m15_h, m15_l, m15_c, m15_v)
                    if sig15 and sig15['signal'] == sig5['signal']:
                        sl_pts, tp_pts = compute_sltp(sig5['atr'], m5_atr, j, strategy)
                        if tp_pts / max(sl_pts, 1) >= 1.5:
                            lot = lot_size(balance, sl_pts)
                            if lot >= 0.01:
                                entry_idx = bisect.bisect_left(m1_t, t_close)
                                if entry_idx < len(m1_t):
                                    entry_px = m1_o[entry_idx]
                                    if sig5['signal'] == 'SELL':
                                        sl = entry_px + sl_pts * 0.01
                                        tp = entry_px - tp_pts * 0.01
                                    else:
                                        sl = entry_px - sl_pts * 0.01
                                        tp = entry_px + tp_pts * 0.01
                                    positions.append({
                                        'dir': sig5['signal'], 'entry': entry_px,
                                        'sl': sl, 'tp': tp, 'sl_pts': sl_pts,
                                        'lot': lot, 'entry_idx': entry_idx,
                                        'entry_t': t_close, 'mae': 0.0, 'mfe': 0.0,
                                        'bars_held': 0, 'be_done': False,
                                        'opened_m5': j, 'closed': False,
                                        'reason': 'OPEN', 'exit_px': None,
                                        'pnl': 0.0, 'exit_idx': None,
                                    })
                                    last_action_t = t_close

    # Tutup posisi tersisa di akhir data
    end_i = len(m1_t) - 1
    for pos in positions:
        if not pos['closed']:
            settle(pos, end_i, 'EOF')

    return trades, balance, max_dd


# ─── AUDIT MAE/MFE ───────────────────────────────────────────────────────────

def audit(trades_a):
    if not trades_a:
        return {}
    mae = [t['mae'] for t in trades_a]
    mfe = [t['mfe'] for t in trades_a]
    sl_hits = [t for t in trades_a if t['reason'] == 'SL']
    tp_hits = [t for t in trades_a if t['reason'] == 'TP']
    # trade kena SL padahal harga SEMPAT mencapai jarak TP (arah benar, stop salah)
    would_win = [t for t in sl_hits if t['mfe'] >= t['sl_pts'] * 2 * 0.99]
    pctl = lambda arr, p: sorted(arr)[min(len(arr) - 1, int(len(arr) * p))]
    # Hanya MAE/MFE trade yang TAMAT (bukan EOF) agar distribusi adil
    mae = [t['mae'] for t in trades_a if t['reason'] != 'EOF']
    mfe = [t['mfe'] for t in trades_a if t['reason'] != 'EOF']
    return {
        'n': len(trades_a),
        'sl_hits': len(sl_hits),
        'tp_hits': len(tp_hits),
        'sl_hit_pct': 100 * len(sl_hits) / len(trades_a),
        'mae_median': round(pctl(mae, 0.5), 1),
        'mae_p75': round(pctl(mae, 0.75), 1),
        'mae_p90': round(pctl(mae, 0.90), 1),
        'mfe_median': round(pctl(mfe, 0.5), 1),
        'mfe_p75': round(pctl(mfe, 0.75), 1),
        'would_win_with_wider_sl': len(would_win),
    }


def summarize(trades, balance, max_dd):
    n = len(trades)
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    total = sum(t['pnl'] for t in trades)
    hold_mins = [(t['exit_idx'] - t['entry_idx']) for t in trades if t['exit_idx'] is not None]
    reasons = {}
    for t in trades:
        reasons[t['reason']] = reasons.get(t['reason'], 0) + 1
    return {
        'n': n,
        'win': len(wins), 'loss': len(losses),
        'winrate': 100 * len(wins) / n if n else 0,
        'total_pnl': round(total, 2),
        'avg_win': round(sum(t['pnl'] for t in wins) / len(wins), 2) if wins else 0,
        'avg_loss': round(sum(t['pnl'] for t in losses) / len(losses), 2) if losses else 0,
        'profit_factor': round(sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses)), 2) if losses and sum(t['pnl'] for t in losses) else float('inf') if wins else 0,
        'max_dd': round(max_dd, 2),
        'end_balance': round(balance, 2),
        'avg_hold_min': round(sum(hold_mins) / len(hold_mins), 1) if hold_mins else 0,
        'reasons': reasons,
    }


def main():
    if not mt5.initialize():
        print("MT5 init failed:", mt5.last_error())
        sys.exit(1)

    now = datetime.now()
    since = now - timedelta(days=DAYS + 1)

    m1 = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M1, since, now)
    m5 = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M5, since, now)
    m15 = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M15, since, now)
    mt5.shutdown()

    if m1 is None or m5 is None or m15 is None:
        print("Data MT5 tidak tersedia")
        sys.exit(1)

    to_list = lambda arr, cols: [tuple(r[c] for c in cols) for r in arr]
    m1 = to_list(m1, (0, 1, 2, 3, 4, 5))
    m5 = to_list(m5, (0, 1, 2, 3, 4, 5))
    m15 = to_list(m15, (0, 1, 2, 3, 4, 5))

    # Potong ke DAYS hari terakhir
    cutoff = m1[-1][0] - DAYS * 86400
    m1 = [x for x in m1 if x[0] >= cutoff]
    m5 = [x for x in m5 if x[0] >= cutoff]
    m15 = [x for x in m15 if x[0] >= cutoff]

    print(f"Data: {len(m1)} bar M1, {len(m5)} bar M5, {len(m15)} bar M15 "
          f"({datetime.fromtimestamp(m1[0][0])} s/d {datetime.fromtimestamp(m1[-1][0])})\n")

    names = {'A': 'A. Baseline (1.0x/2.0x ATR)',
             'B': 'B. Regime SL (ATR percentile 0.75-1.5x)',
             'C': 'C. B + Breakeven 1R + Time-exit 1 jam',
             'D': 'D. C + Momentum exit (RSI+EMA21)'}

    results = {}
    for strat in ('A', 'B', 'C', 'D'):
        trades, balance, max_dd = run_strategy(m1, m5, m15, strat)
        results[strat] = summarize(trades, balance, max_dd)
        s = results[strat]
        print(f"{names[strat]}")
        print(f"  Trades={s['n']}  Win={s['win']}  Loss={s['loss']}  "
              f"Winrate={s['winrate']:.1f}%  P/L=${s['total_pnl']:.2f}")
        print(f"  AvgWin=${s['avg_win']}  AvgLoss=${s['avg_loss']}  "
              f"PF={s['profit_factor']}  MaxDD=${s['max_dd']}  "
              f"Hold={s['avg_hold_min']}m  Exit: {s['reasons']}")
        print()

    # Audit MAE/MFE (pakai entri strategi A — sinyal sama semua strategi)
    trades_a, _, _ = run_strategy(m1, m5, m15, 'A')
    a = audit(trades_a)
    print("=== AUDIT MAE/MFE (entri baseline) ===")
    print(f"  Trades={a['n']}  SL hits={a['sl_hits']} ({a['sl_hit_pct']:.0f}%)  TP hits={a['tp_hits']}")
    print(f"  MAE: median {a['mae_median']}pt | p75 {a['mae_p75']}pt | p90 {a['mae_p90']}pt")
    print(f"  MFE: median {a['mfe_median']}pt | p75 {a['mfe_p75']}pt")
    print(f"  Kena SL tapi harga sempat capai jarak TP (arah benar, stop salah): "
          f"{a['would_win_with_wider_sl']} trade")
    print()

    # Sub-laporan hari ini (Sep 4, UTC)
    day_start = m1[-1][0] - (m1[-1][0] % 86400)
    for strat in ('A', 'D'):
        trades, balance, max_dd = run_strategy(m1, m5, m15, strat)
        today = [t for t in trades if t['entry_t'] >= day_start]
        if today:
            s = summarize(today, balance, max_dd)
            print(f"[HARI INI] {names[strat]}: Trades={s['n']} Win={s['win']} "
                  f"Winrate={s['winrate']:.0f}% P/L=${s['total_pnl']:.2f} Exit: {s['reasons']}")
    print("\nCatatan: biaya per round-trip = spread 35pt + komisi 2x$1/lot. "
          "Entri di open bar M1 berikutnya setelah sinyal M5 tutup.")


if __name__ == '__main__':
    main()