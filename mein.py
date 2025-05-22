#!/usr/bin/env python3
# OTC ANK ANALYZER & SUGGESTER v1.1
# Powered by Anuj & AI God (Enhanced by Sachin & AI)

import os
import sys
import shutil
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import json # For saving/loading formula performance

from colorama import Fore, Style, init

init(autoreset=True)

# --- Configuration & Constants ---
APP_NAME = "OTC ANK ANALYZER"
APP_VERSION = "v1.1" # Version up
POWERED_BY = "Anuj & AI God (Enhanced by Sachin & AI)"
BOX_WIDTH = 80 
DATA_DIR = "data"
PERFORMANCE_DIR = "performance_stats" 
LOG_DIR = "logs"

# ***** MODIFIED HERE *****
MIN_HIT_RATE_FOR_SUGGESTION = 0.39 # Lowered to 39% (shows 40%+ formulas)
                                   # Set to 0.0 to always show suggestions from top formulas if MIN_TRIES met
# *************************
MIN_TRIES_FOR_SUGGESTION = 10    
NUM_SUGGESTIONS_TO_SHOW = 5      

# Color Palette (same as before)
C_PRIMARY_BRIGHT = Fore.CYAN + Style.BRIGHT; C_SECONDARY_BRIGHT = Fore.MAGENTA + Style.BRIGHT
C_SUCCESS_BRIGHT = Fore.GREEN + Style.BRIGHT; C_ERROR_BRIGHT = Fore.RED + Style.BRIGHT
C_WARNING_BRIGHT = Fore.YELLOW + Style.BRIGHT; C_INFO_BRIGHT = Fore.BLUE + Style.BRIGHT
C_ACCENT_BRIGHT = Fore.WHITE + Style.BRIGHT; C_PRIMARY = Fore.CYAN; C_SECONDARY = Fore.MAGENTA
C_SUCCESS = Fore.GREEN; C_ERROR = Fore.RED; C_WARNING = Fore.YELLOW; C_INFO = Fore.BLUE
C_RESET = Style.RESET_ALL; C_BANNER_BORDER = C_SECONDARY_BRIGHT; C_BANNER_TITLE = C_SUCCESS_BRIGHT
C_BANNER_SUBTITLE = C_WARNING_BRIGHT; C_BANNER_TEXT = C_PRIMARY

MPV_PATH = shutil.which("mpv")

MARKETS = [ 
    "KALYAN-NIGHT", "MAIN-BAZAR", "RAJDHANI-NIGHT", "SUPREME-NIGHT", "KALYAN",
    "MILAN-DAY", "SRIDEVI-NIGHT", "TIME-BAZAR", "MADHUR-DAY", "MILAN-NIGHT",
    "SRIDEVI", "MADHUR-NIGHT", "RAJDHANI-DAY", "SUPREME-DAY"
]
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --- Styling Utilities (condensed, same functionality) ---
def print_box_top(w=BOX_WIDTH, c=C_SECONDARY_BRIGHT): print(c + f"╔{'═'*(w-2)}╗" + C_RESET)
def print_box_bottom(w=BOX_WIDTH, c=C_SECONDARY_BRIGHT): print(c + f"╚{'═'*(w-2)}╝" + C_RESET)
def print_box_sep(w=BOX_WIDTH, c=C_SECONDARY_BRIGHT): print(c + f"╠{'═'*(w-2)}╣" + C_RESET)
def strip_ansi(t): return re.sub(r'\x1b\[[0-9;]*[mK]', '', t)
def print_box_line(t, w=BOX_WIDTH, bc=C_SECONDARY_BRIGHT, tc="", align="left", p=2):
    st, cw = strip_ansi(t), w-2-(p*2); dsp_t = t; cl_diff = len(t)-len(st)
    if len(st) > cw:
        cut_at = 0; cur_st_len = 0; max_st_len = cw - 3 if cw > 3 else cw
        for char_idx, char_val in enumerate(t): # Basic ANSI aware truncate
            is_ansi_char = False
            if char_idx + 1 < len(t) and t[char_idx] == '\x1b' and t[char_idx+1] == '[':
                is_ansi_char = True
            if not is_ansi_char: cur_st_len +=1
            if cur_st_len >= max_st_len: cut_at = char_idx +1; break
        dsp_t = t[:cut_at] + ("..." if cw > 3 else "") if cut_at > 0 else t[:max_st_len] + ("..." if cw > 3 else "")
        cl_diff = len(dsp_t) - len(strip_ansi(dsp_t))
    eff_w = cw + cl_diff
    at = dsp_t.center(eff_w) if align=="center" else (dsp_t.rjust(eff_w) if align=="right" else dsp_t.ljust(eff_w))
    print(f"{bc}║{' '*p}{tc}{at}{' '*p}{bc}║{C_RESET}")

# --- Core Logic Functions ---
def show_banner():
    os.system("clear" if os.name == 'posix' else 'cls'); print_box_top(BOX_WIDTH, C_BANNER_BORDER)
    print_box_line(f"{C_BANNER_TITLE}{APP_NAME}",BOX_WIDTH,C_BANNER_BORDER,"","center")
    print_box_line(f"{C_BANNER_SUBTITLE}{APP_VERSION}",BOX_WIDTH,C_BANNER_BORDER,"","center")
    print_box_sep(BOX_WIDTH,C_BANNER_BORDER)
    print_box_line(f"{C_BANNER_TEXT}OTC Ank Formula Backtester & Suggester",BOX_WIDTH,C_BANNER_BORDER,"","center")
    print_box_bottom(BOX_WIDTH,C_BANNER_BORDER); print("\n")

def parse_data_line(line_str):
    try:
        date_part_str, result_part_str = map(str.strip, line_str.split('/', 1))
        p1, jodi, p2 = map(str.strip, result_part_str.split('-', 2))
        if not (re.fullmatch(r"\d{3}",p1) and re.fullmatch(r"\d{2}",jodi) and re.fullmatch(r"\d{3}",p2)): return None
        dt = datetime.strptime(date_part_str, "%d-%m-%Y")
        return {
            "date_obj": dt, "p1": p1, "jodi": jodi, "p2": p2,
            "open_ank": p1[-1], "close_ank": jodi[-1], "day_idx": dt.weekday(),
            "all_digits_today": {p1[0],p1[1],p1[2], jodi[0],jodi[1], p2[0],p2[1],p2[2]}
        }
    except: return None

def read_data_file(market_name):
    filepath = os.path.join(DATA_DIR, f"{market_name}.txt")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        parsed_data = [parse_data_line(line) for line in lines]
        return [d for d in parsed_data if d is not None]
    except FileNotFoundError: print(C_ERROR_BRIGHT + f"[!] File missing: {filepath}"); return []
    except Exception as e: print(C_ERROR_BRIGHT + f"[!] Read error {filepath}: {e}"); return []

# --- FORMULA DEFINITIONS ---
def f_jodi_digits(prev_day_data, params=None):
    if not prev_day_data or 'jodi' not in prev_day_data or len(prev_day_data['jodi']) != 2: return set()
    return {prev_day_data['jodi'][0], prev_day_data['jodi'][1]}

def f_open_close_anks(prev_day_data, params=None):
    if not prev_day_data: return set()
    return {prev_day_data['open_ank'], prev_day_data['close_ank']}

def f_jodi_sum_and_diff(prev_day_data, params=None):
    if not prev_day_data or 'jodi' not in prev_day_data or len(prev_day_data['jodi']) != 2: return set()
    try:
        d1, d2 = int(prev_day_data['jodi'][0]), int(prev_day_data['jodi'][1])
        return {str((d1 + d2) % 10), str(abs(d1 - d2))}
    except ValueError: return set()

def f_panel_sum_ank(prev_day_data, params):
    if not prev_day_data or not params or 'panel_type' not in params: return set()
    panel_key = params['panel_type']
    if panel_key not in prev_day_data or len(prev_day_data[panel_key]) != 3: return set()
    try:
        return {str(sum(int(d) for d in prev_day_data[panel_key]) % 10)}
    except ValueError: return set()

def f_fixed_offset_from_ank(prev_day_data, params):
    if not prev_day_data or not params or 'offset' not in params: return set()
    try:
        offset = int(params['offset'])
        oa, ca = int(prev_day_data['open_ank']), int(prev_day_data['close_ank'])
        return {str((oa + offset) % 10), str((ca + offset) % 10)}
    except ValueError: return set()

ALL_FORMULA_SPECS = {
    "JodiDigits_default": {"func": f_jodi_digits, "params": {}, "display": "Jodi Digits"},
    "OpenCloseAnks_default": {"func": f_open_close_anks, "params": {}, "display": "Open & Close Anks"},
    "JodiSumDiff_default": {"func": f_jodi_sum_and_diff, "params": {}, "display": "Jodi Sum & Diff"},
}
for i in range(10):
    ALL_FORMULA_SPECS[f"FixedOffset_off{i}"] = {
        "func": f_fixed_offset_from_ank, "params": {"offset": i}, "display": f"Fixed Offset Ank (X={i})" }
for pt in ['p1', 'p2']:
    ALL_FORMULA_SPECS[f"PanelSumAnk_{pt}"] = {
        "func": f_panel_sum_ank, "params": {"panel_type": pt}, "display": f"{pt.upper()} Panel Sum Ank" }
# --- END FORMULA DEFINITIONS ---

def get_performance_filepath(market_name): # Unused in this simplified version
    os.makedirs(PERFORMANCE_DIR, exist_ok=True)
    return os.path.join(PERFORMANCE_DIR, f"{market_name}_otc_formula_stats.json")

def backtest_all_formulas(historical_data): # Simplified: no loading/saving of stats here
    print(C_INFO_BRIGHT + f"Backtesting {len(ALL_FORMULA_SPECS)} formula variants...")
    current_formula_stats = {}
    for f_id, spec in ALL_FORMULA_SPECS.items():
         current_formula_stats[f_id] = {"hits": 0, "tries": 0, "display_name": spec["display"], "params_str": str(spec["params"])}

    if len(historical_data) < 2:
        print(C_WARNING + "Not enough historical data (need at least 2 days) for backtesting.")
        return current_formula_stats

    for i in range(1, len(historical_data)):
        prev_day_data = historical_data[i-1]
        current_day_data = historical_data[i]
        actual_otc_relevant_anks = {current_day_data['open_ank'], current_day_data['close_ank']}
        # To check against all digits that appeared:
        # actual_otc_relevant_anks.update(current_day_data['all_digits_today'])

        for f_id, spec in ALL_FORMULA_SPECS.items():
            generated_otc_anks = spec["func"](prev_day_data, spec["params"])
            current_formula_stats[f_id]["tries"] += 1
            if generated_otc_anks and not actual_otc_relevant_anks.isdisjoint(generated_otc_anks):
                current_formula_stats[f_id]["hits"] += 1
    return current_formula_stats

def get_otc_suggestions_for_tomorrow(latest_day_data, top_formulas_perf):
    suggestions = []
    if not latest_day_data: return suggestions
    for f_id, perf_data in top_formulas_perf:
        spec = ALL_FORMULA_SPECS.get(f_id)
        if not spec: continue
        generated_otc_anks = spec["func"](latest_day_data, spec["params"])
        hit_rate = (perf_data['hits'] / perf_data['tries'] * 100) if perf_data['tries'] > 0 else 0
        
        # Ensure we provide up to 3 anks. If formula gives fewer, pad. If more, truncate.
        final_suggested_anks = sorted(list(generated_otc_anks))
        if len(final_suggested_anks) > 3:
            final_suggested_anks = final_suggested_anks[:3] # Take first 3 if more
        while len(final_suggested_anks) < 3 and len(final_suggested_anks) > 0 : # Pad if 1 or 2 anks and non-empty
            # Simple padding: repeat last ank, or add 'X' if you prefer a clear placeholder
            # This padding is very basic. A better way might be to take from next best formula or other logic.
            # For now, let's just show what the formula gives, up to 3.
            if len(final_suggested_anks) == 1: final_suggested_anks.append(final_suggested_anks[0]) # Repeat if 1
            if len(final_suggested_anks) == 2: final_suggested_anks.append(final_suggested_anks[1]) # Repeat last if 2
            # Or, simply ensure it's a list and the display handles showing 1, 2, or 3.
            # The current request is "Daily ke liye 3 OTC de". So we aim for 3.

        # Let's just return what the formula gives, and the display can show it.
        # If strict 3 anks are needed, padding/selection logic here becomes complex.
        # For now, `generated_anks` will be shown as is.
        
        suggestions.append({
            "formula_id": f_id,
            "display_name": perf_data.get("display_name", spec["display"]),
            "params_str": perf_data.get("params_str", str(spec["params"])),
            "generated_anks": sorted(list(generated_otc_anks)), # These are the raw anks from formula
            "hit_rate": hit_rate,
            "hits_tries_str": f"{perf_data['hits']}/{perf_data['tries']}"
        })
    return suggestions

def log_top_suggestion(market_name, suggestion):
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "otc_daily_suggestions.txt")
    today_str = datetime.now().strftime("%d-%m-%Y")
    tomorrows_date_str = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
    log_entry = (
        f"{today_str} (For {tomorrows_date_str}) | Market: {market_name} | "
        f"Formula: {suggestion['display_name']} {suggestion['params_str']} | "
        f"Rate: {suggestion['hit_rate']:.0f}% ({suggestion['hits_tries_str']}) | "
        f"Suggested Anks: {' '.join(suggestion['generated_anks'])}\n")
    try:
        with open(log_file, 'a') as f: f.write(log_entry)
    except IOError: print(C_ERROR + f"Could not write to log file: {log_file}")

def display_performance_summary(all_stats):
    print_box_top(c=C_INFO_BRIGHT); print_box_line(f"{C_ACCENT_BRIGHT}Formula Performance Summary (All Tested)", bc=C_INFO_BRIGHT, align="center")
    print_box_sep(c=C_INFO_BRIGHT)
    header = f"{'Formula Name'.ljust(30)} | {'Params'.ljust(15)} | {'Hit Rate'.rjust(8)} | {'Hits/Tries'.rjust(10)}"
    print_box_line(C_WARNING_BRIGHT + header, bc=C_INFO_BRIGHT, p=1); print_box_sep(c=C_INFO_BRIGHT)
    sorted_stats = sorted(all_stats.items(), key=lambda x: (x[1]['hits']/x[1]['tries'] if x[1]['tries']>0 else 0, x[1]['tries']), reverse=True)
    for f_id, data in sorted_stats[:15]:
        rate = (data['hits'] / data['tries'] * 100) if data['tries'] > 0 else 0
        name_str = data.get('display_name', f_id.split('_')[0])[:28]
        param_str = data.get('params_str', str(ALL_FORMULA_SPECS[f_id]['params']))[:13]
        line_color = C_SUCCESS if rate >= MIN_HIT_RATE_FOR_SUGGESTION*100 and data['tries'] >= MIN_TRIES_FOR_SUGGESTION else C_PRIMARY
        data_line = f"{name_str.ljust(30)} | {param_str.ljust(15)} | {f'{rate:.0f}%'.rjust(8)} | {f'''{data['hits']}/{data['tries']}'''.rjust(10)}"
        print_box_line(line_color + data_line, bc=C_INFO_BRIGHT, p=1)
    if len(sorted_stats) > 15: print_box_line("... and more ...", bc=C_INFO_BRIGHT, align="center", p=1)
    print_box_bottom(c=C_INFO_BRIGHT)

def display_otc_suggestions(market_name, suggestions_for_tomorrow):
    tomorrows_date_str = (datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y (%A)')
    print_box_top(c=C_SUCCESS_BRIGHT)
    print_box_line(f"{C_ACCENT_BRIGHT}OTC Ank Suggestions for {market_name} - {tomorrows_date_str}", bc=C_SUCCESS_BRIGHT, align="center")
    print_box_sep(c=C_SUCCESS_BRIGHT)
    if not suggestions_for_tomorrow:
        print_box_line(C_WARNING + "No formulas met criteria for suggestions today.", bc=C_SUCCESS_BRIGHT, align="center")
    else:
        header = f"{'Rank'.ljust(4)} | {'Formula'.ljust(25)} | {'Params'.ljust(15)} | {'Anks'.ljust(10)} | {'Rate'.rjust(7)}"
        print_box_line(C_WARNING_BRIGHT + header, bc=C_SUCCESS_BRIGHT, p=1); print_box_sep(c=C_SUCCESS_BRIGHT)
        
        # Logic to ensure we get up to 3 distinct anks for the top suggestion
        final_otc_display_anks = set()
        reason_details = []

        for i, sug in enumerate(suggestions_for_tomorrow):
            if len(final_otc_display_anks) >= 3 and i > 0 : # If we already have 3 anks from top formula, we can stop for combined display
                # But we still list the top formulas in the table
                pass

            # For display table:
            name_str = sug['display_name'][:23]; param_str = sug['params_str'][:13]
            anks_str = ' '.join(sug['generated_anks'])[:8]; rate_str = f"{sug['hit_rate']:.0f}%"
            line_color = C_SUCCESS_BRIGHT if sug['hit_rate'] >= MIN_HIT_RATE_FOR_SUGGESTION * 100 else C_PRIMARY_BRIGHT
            data_line = f"{str(i+1).ljust(4)} | {name_str.ljust(25)} | {param_str.ljust(15)} | {anks_str.ljust(10)} | {rate_str.rjust(7)}"
            print_box_line(line_color + data_line, bc=C_SUCCESS_BRIGHT, p=1)

            # Collect anks for the "Daily 3 OTC" from the best formulas shown
            if i < NUM_SUGGESTIONS_TO_SHOW: # Consider anks from top N displayed suggestions
                for ank in sug['generated_anks']:
                    if len(final_otc_display_anks) < 3:
                        final_otc_display_anks.add(ank)
                        if len(reason_details) < 3 : # Add reason from top formulas contributing to the 3 anks
                             reason_details.append(f"{ank} (from {sug['display_name']} @{sug['hit_rate']:.0f}%)")


            if i == 0: log_top_suggestion(market_name, sug) # Log the absolute top one

        # Display the combined "Daily 3 OTC"
        print_box_sep(c=C_SUCCESS_BRIGHT)
        if final_otc_display_anks:
            # Pad to 3 if necessary for display, e.g., with 'X' or by repeating
            display_anks_list = sorted(list(final_otc_display_anks))
            while len(display_anks_list) < 3: display_anks_list.append('?') # Placeholder for <3 anks

            print_box_line(f"{C_ACCENT_BRIGHT}Tomorrow's Top 3 OTC Suggestion: {C_SUCCESS_BRIGHT}{'  '.join(display_anks_list[:3])}", bc=C_SUCCESS_BRIGHT, align="center", p=1)
            for rd in reason_details:
                 print_box_line(f"{C_INFO_BRIGHT} {rd}", bc=C_SUCCESS_BRIGHT, p=1, align="left")
        else:
            print_box_line(C_WARNING + "Could not determine a clear set of 3 OTC anks.", bc=C_SUCCESS_BRIGHT, align="center", p=1)


    print_box_bottom(c=C_SUCCESS_BRIGHT)

def main():
    show_banner()
    print_box_top(w=BOX_WIDTH // 2, c=C_PRIMARY_BRIGHT) # Market Selection Box
    print_box_line("Select Market", w=BOX_WIDTH // 2, bc=C_PRIMARY_BRIGHT, align="center")
    for i, m_name in enumerate(MARKETS): print_box_line(f"{C_WARNING}{i+1}. {C_SECONDARY}{m_name}", w=BOX_WIDTH // 2, bc=C_PRIMARY_BRIGHT)
    print_box_bottom(w=BOX_WIDTH // 2, c=C_PRIMARY_BRIGHT)
    
    market_choice_idx = -1
    while not (0 <= market_choice_idx < len(MARKETS)):
        try: market_choice_idx = int(input(C_PRIMARY_BRIGHT + "Enter market number: " + C_RESET)) - 1
        except ValueError: print(C_ERROR+"Invalid input.")
        if not (0 <= market_choice_idx < len(MARKETS)): print(C_ERROR+"Invalid choice.")

    market_name = MARKETS[market_choice_idx]
    print(C_INFO_BRIGHT + f"\nAnalyzing Market: {C_ACCENT_BRIGHT}{market_name}{C_RESET}\n")
    historical_data = read_data_file(market_name)

    if not historical_data or len(historical_data) < max(2, MIN_TRIES_FOR_SUGGESTION // 2) : # Looser check for running backtest
        print(C_ERROR_BRIGHT + f"Not enough historical data for {market_name} (found {len(historical_data)}). Meaningful backtesting requires more entries."); sys.exit(1)

    current_formula_stats = backtest_all_formulas(historical_data)
    if current_formula_stats: display_performance_summary(current_formula_stats)
    else: print(C_WARNING + "No formula performance data from backtest.")

    eligible_formulas = []
    for f_id, data in current_formula_stats.items():
        if data['tries'] >= MIN_TRIES_FOR_SUGGESTION:
            hit_rate = data['hits'] / data['tries']
            if hit_rate >= MIN_HIT_RATE_FOR_SUGGESTION: # Use the (potentially lowered) threshold
                eligible_formulas.append((f_id, data))
    
    eligible_formulas.sort(key=lambda x: ((x[1]['hits']/x[1]['tries']), x[1]['tries']), reverse=True)
    latest_day_data = historical_data[-1] if historical_data else None
    suggestions_for_tomorrow = get_otc_suggestions_for_tomorrow(latest_day_data, eligible_formulas)

    if suggestions_for_tomorrow:
        display_otc_suggestions(market_name, suggestions_for_tomorrow)
    else: # This message will show if MIN_HIT_RATE is high and nothing meets it
        print(C_WARNING_BRIGHT + f"\nNo formulas for {market_name} met the required hit rate ({MIN_HIT_RATE_FOR_SUGGESTION*100:.0f}%) and min tries ({MIN_TRIES_FOR_SUGGESTION}) for a suggestion today.")
        # Fallback: Show top N even if they don't meet criteria, if user wants "always suggest"
        if MIN_HIT_RATE_FOR_SUGGESTION < 0.1: # Check if user set it to effectively zero
            print(C_INFO + "Showing top formulas by tries even if below hit rate threshold...")
            all_tried_formulas = sorted(
                [(f_id, data) for f_id, data in current_formula_stats.items() if data['tries'] >= MIN_TRIES_FOR_SUGGESTION],
                key=lambda x: ((x[1]['hits']/x[1]['tries']), x[1]['tries']), reverse=True
            )
            fallback_suggestions = get_otc_suggestions_for_tomorrow(latest_day_data, all_tried_formulas)
            if fallback_suggestions:
                display_otc_suggestions(market_name, fallback_suggestions)


if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print(C_WARNING_BRIGHT+"\n\n[!] User interrupted."+C_RESET)
    except Exception as e:
        print(C_ERROR_BRIGHT+f"\n[!!!] CRITICAL ERROR: {e}"); import traceback; traceback.print_exc()
        print(C_ERROR_BRIGHT+"Please report this issue."+C_RESET)
    finally: print(C_PRIMARY_BRIGHT+f"\n✨ Thank you for using {APP_NAME}! ✨"+C_RESET)
