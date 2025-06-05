#!/usr/bin/env python3
# OTC MATH FORMULAS ANALYZER v1.0
# Powered by Anuj & AI God (Enhanced by Sachin & AI)

import os
import sys
import shutil
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import json

from colorama import Fore, Style, init

init(autoreset=True)

# --- Configuration & Constants ---
APP_NAME = "OTC MATH ANALYZER"
APP_VERSION = "v1.0"
POWERED_BY = "Anuj & AI God (Enhanced by Sachin & AI)"
BOX_WIDTH = 90 # Wider for more detailed formula output
DATA_DIR = "data"
LOG_DIR = "logs"

MIN_HIT_RATE_SUGGESTION = 0.39 # (40%+)
MIN_TRIES_SUGGESTION = 10    # Formula must have been tried at least this many times
NUM_ANK_SUGGESTIONS_COMBINED = 3 # Our target for combined OTC anks
NUM_INDIVIDUAL_FORMULA_SUGGESTIONS_TO_DISPLAY = 7 # Show top N performing formulas

# Color Palette
C_PRIMARY_BRIGHT = Fore.CYAN + Style.BRIGHT; C_SECONDARY_BRIGHT = Fore.MAGENTA + Style.BRIGHT
C_SUCCESS_BRIGHT = Fore.GREEN + Style.BRIGHT; C_ERROR_BRIGHT = Fore.RED + Style.BRIGHT
C_WARNING_BRIGHT = Fore.YELLOW + Style.BRIGHT; C_INFO_BRIGHT = Fore.BLUE + Style.BRIGHT
C_ACCENT_BRIGHT = Fore.WHITE + Style.BRIGHT; C_PRIMARY = Fore.CYAN; C_SECONDARY = Fore.MAGENTA
C_SUCCESS = Fore.GREEN; C_ERROR = Fore.RED; C_WARNING = Fore.YELLOW; C_INFO = Fore.BLUE
C_RESET = Style.RESET_ALL; C_BANNER_BORDER = C_SECONDARY_BRIGHT; C_BANNER_TITLE = C_SUCCESS_BRIGHT
C_BANNER_SUBTITLE = C_WARNING_BRIGHT; C_BANNER_TEXT = C_PRIMARY

MARKETS = [
    "KALYAN-NIGHT", "MAIN-BAZAR", "RAJDHANI-NIGHT", "SUPREME-NIGHT", "KALYAN",
    "MILAN-DAY", "SRIDEVI-NIGHT", "TIME-BAZAR", "MADHUR-DAY", "MILAN-NIGHT",
    "SRIDEVI", "MADHUR-NIGHT", "RAJDHANI-DAY", "SUPREME-DAY"
]

# --- Styling Utilities ---
def print_box_top(w=BOX_WIDTH, c=C_SECONDARY_BRIGHT): print(c + f"╔{'═'*(w-2)}╗" + C_RESET)
def print_box_bottom(w=BOX_WIDTH, c=C_SECONDARY_BRIGHT): print(c + f"╚{'═'*(w-2)}╝" + C_RESET)
def print_box_sep(w=BOX_WIDTH, c=C_SECONDARY_BRIGHT): print(c + f"╠{'═'*(w-2)}╣" + C_RESET)
def strip_ansi(t): return re.sub(r'\x1b\[[0-9;]*[mK]', '', t)
def print_box_line(t, w=BOX_WIDTH, bc=C_SECONDARY_BRIGHT, tc="", align="left", p=2):
    st, cw = strip_ansi(t), w-2-(p*2); dsp_t = t; cl_diff = len(t)-len(st)
    if len(st) > cw:
        cut_at=0; cur_st_len=0; max_st_len=cw-3 if cw>3 else cw
        for char_idx, char_val in enumerate(t):
            is_ansi_char=False
            if char_idx+1 < len(t) and t[char_idx]=='\x1b' and t[char_idx+1]=='[': is_ansi_char=True
            if not is_ansi_char and char_val not in ['\x1b']: cur_st_len+=1
            if cur_st_len >= max_st_len: cut_at=char_idx+1; break
        dsp_t = t[:cut_at] + ("..." if cw > 3 else "") if cut_at > 0 else t[:max_st_len] + ("..." if cw > 3 else "")
        cl_diff = len(dsp_t) - len(strip_ansi(dsp_t))
    eff_w = cw + cl_diff
    at = dsp_t.center(eff_w) if align=="center" else (dsp_t.rjust(eff_w) if align=="right" else dsp_t.ljust(eff_w))
    print(f"{bc}║{' '*p}{tc}{at}{' '*p}{bc}║{C_RESET}")

# --- Core Logic Functions ---
def show_banner():
    os.system("clear" if os.name == 'posix' else 'cls'); print_box_top();
    print_box_line(f"{C_BANNER_TITLE}{APP_NAME}", align="center"); print_box_line(f"{C_BANNER_SUBTITLE}{APP_VERSION}", align="center")
    print_box_sep(); print_box_line(f"{C_BANNER_TEXT}Math-Based OTC Ank Suggester", align="center"); print_box_bottom(); print("\n")

def parse_data_line(line_str):
    try:
        date_part_str, result_part_str = map(str.strip, line_str.split('/', 1))
        p1, jodi, p2 = map(str.strip, result_part_str.split('-', 2))
        if not (re.fullmatch(r"\d{3}",p1) and re.fullmatch(r"\d{2}",jodi) and re.fullmatch(r"\d{3}",p2)): return None
        dt = datetime.strptime(date_part_str, "%d-%m-%Y")
        return {
            "date_obj": dt, "p1": p1, "jodi": jodi, "p2": p2,
            "open_ank": p1[-1], "close_ank": jodi[-1],
            "jodi_d1": jodi[0], "jodi_d2": jodi[1], # For convenience
            "p1_digits": [d for d in p1], "p2_digits": [d for d in p2] # For convenience
        }
    except: return None

def read_data_file(market_name):
    filepath = os.path.join(DATA_DIR, f"{market_name}.txt")
    try:
        with open(filepath, 'r', encoding='utf-8') as f: lines = [line.strip() for line in f if line.strip()]
        parsed = [parse_data_line(line) for line in lines]
        return sorted([d for d in parsed if d is not None], key=lambda x: x['date_obj'])
    except FileNotFoundError: print(C_ERROR_BRIGHT + f"[!] File missing: {filepath}"); return []
    except Exception as e: print(C_ERROR_BRIGHT + f"[!] Read error {filepath}: {e}"); return []

# --- MATHEMATICAL FORMULA DEFINITIONS for OTC ANKS ---
# Each formula returns a set of 1 to 4 anks (strings).

def f_prev_oc_anks(prev_data, params=None): # Basic
    if not prev_data: return set()
    return {prev_data['open_ank'], prev_data['close_ank']}

def f_prev_jodi_digits(prev_data, params=None): # Basic
    if not prev_data: return set()
    return {prev_data['jodi_d1'], prev_data['jodi_d2']}

def f_sum_jodi_digits_plus_x(prev_data, params):
    if not prev_data or "X" not in params: return set()
    try:
        jd1, jd2 = int(prev_data['jodi_d1']), int(prev_data['jodi_d2'])
        x = int(params["X"])
        return {str((jd1 + jd2 + x) % 10)}
    except ValueError: return set()

def f_diff_jodi_digits_plus_x(prev_data, params):
    if not prev_data or "X" not in params: return set()
    try:
        jd1, jd2 = int(prev_data['jodi_d1']), int(prev_data['jodi_d2'])
        x = int(params["X"])
        return {str((abs(jd1 - jd2) + x) % 10)}
    except ValueError: return set()

def f_sum_oc_anks_plus_x(prev_data, params):
    if not prev_data or "X" not in params: return set()
    try:
        oa, ca = int(prev_data['open_ank']), int(prev_data['close_ank'])
        x = int(params["X"])
        return {str((oa + ca + x) % 10)}
    except ValueError: return set()

def f_ank_plus_x_and_cut(prev_data, params):
    """ Takes a specific ank (open or close), adds X, and returns that ank and its cut. """
    if not prev_data or "ank_type" not in params or "X" not in params: return set()
    try:
        ank_val = int(prev_data[params["ank_type"]]) # 'open_ank' or 'close_ank'
        x = int(params["X"])
        base_ank = (ank_val + x) % 10
        cut_ank = (base_ank + 5) % 10
        return {str(base_ank), str(cut_ank)}
    except ValueError: return set()

def f_panel_digit_op_plus_x(prev_data, params):
    """ Operates on two digits of a panel and adds X. """
    if not prev_data or "panel" not in params or "idx1" not in params \
        or "idx2" not in params or "op" not in params or "X" not in params: return set()
    try:
        panel_digits = prev_data[params["panel"] + "_digits"] # e.g., prev_data["p1_digits"]
        d1, d2 = int(panel_digits[params["idx1"]]), int(panel_digits[params["idx2"]])
        x = int(params["X"])
        res = 0
        if params["op"] == "add": res = d1 + d2
        elif params["op"] == "sub": res = abs(d1 - d2)
        elif params["op"] == "mul": res = d1 * d2 # Be careful with mul by 0
        
        return {str((res + x) % 10)}
    except (IndexError, ValueError, KeyError): return set()


ALL_FORMULA_SPECS = {} # Initialize

# Basic Formulas
ALL_FORMULA_SPECS["PrevOCAnks"] = {"func": f_prev_oc_anks, "params": {}, "display": "Prev O/C Anks", "type": "ank"}
ALL_FORMULA_SPECS["PrevJodiDigits"] = {"func": f_prev_jodi_digits, "params": {}, "display": "Prev Jodi Digits", "type": "ank"}

# Parameterized Formulas
for x_val in range(10):
    ALL_FORMULA_SPECS[f"SumJodiDigits_X{x_val}"] = {"func": f_sum_jodi_digits_plus_x, "params": {"X": x_val}, "display": f"SumJodi+({x_val})", "type": "ank"}
    ALL_FORMULA_SPECS[f"DiffJodiDigits_X{x_val}"] = {"func": f_diff_jodi_digits_plus_x, "params": {"X": x_val}, "display": f"DiffJodi+({x_val})", "type": "ank"}
    ALL_FORMULA_SPECS[f"SumOCAnks_X{x_val}"] = {"func": f_sum_oc_anks_plus_x, "params": {"X": x_val}, "display": f"SumO+C+({x_val})", "type": "ank"}

for ank_t in ["open_ank", "close_ank"]:
    for x_val in range(5): # Smaller range for X to reduce formula count
        display_ank_t = "OA" if ank_t == "open_ank" else "CA"
        ALL_FORMULA_SPECS[f"AnkPlusXCut_{display_ank_t}_X{x_val}"] = {
            "func": f_ank_plus_x_and_cut, "params": {"ank_type": ank_t, "X": x_val},
            "display": f"{display_ank_t}+{x_val} & Cut", "type": "ank"
        }

panel_indices = [(0,1), (0,2), (1,2)]
panel_ops = {"add":"+", "sub":"-", "mul":"*"}
for p_type in ["p1", "p2"]:
    for id1, id2 in panel_indices:
        for op_key, op_sym in panel_ops.items():
            # Only few X for panel ops to keep formula count manageable
            for x_val in [0, 1, 5]: 
                ALL_FORMULA_SPECS[f"PanelOp_{p_type.upper()}{id1}{op_sym}{id2}_X{x_val}"] = {
                    "func": f_panel_digit_op_plus_x,
                    "params": {"panel":p_type, "idx1":id1, "idx2":id2, "op":op_key, "X":x_val},
                    "display": f"{p_type.upper()}[{id1}]{op_sym}[{id2}]+{x_val}", "type": "ank"
                }
# --- END FORMULA DEFINITIONS ---

def backtest_all_formulas(historical_data):
    print(C_INFO_BRIGHT + f"Backtesting {len(ALL_FORMULA_SPECS)} OTC Ank formula variants...")
    stats = {f_id: {"hits":0,"tries":0,"type":spec["type"],"display_name":spec["display"],"params_str":str(spec["params"])} 
             for f_id, spec in ALL_FORMULA_SPECS.items()}
    if len(historical_data) < 2: print(C_WARNING+"Need min 2 days data for backtest."); return stats

    for i in range(1, len(historical_data)):
        prev_d, curr_d = historical_data[i-1], historical_data[i]
        actual_otc_relevant_anks = {curr_d['open_ank'], curr_d['close_ank']}
        
        for f_id, spec in ALL_FORMULA_SPECS.items():
            if prev_d is None : continue
            stats[f_id]["tries"] += 1
            generated_values = spec["func"](prev_d, spec["params"]) 
            if not generated_values: continue # Formula might return empty set
            # All formulas here are "ank" type
            if not actual_otc_relevant_anks.isdisjoint(generated_values): # Check if any generated ank hit
                stats[f_id]["hits"] += 1
    return stats

def get_otc_suggestions_for_tomorrow(latest_day_data, all_formula_stats):
    suggestions = [] # List of dicts
    if not latest_day_data: return suggestions
    
    eligible_formulas = []
    for f_id, perf_data in all_formula_stats.items():
        # All formulas are 'ank' type in this script
        if perf_data['tries'] >= MIN_TRIES_SUGGESTION:
            hit_rate = (perf_data['hits'] / perf_data['tries']) if perf_data['tries'] > 0 else 0
            if hit_rate >= MIN_HIT_RATE_SUGGESTION:
                eligible_formulas.append((f_id, perf_data, hit_rate))
    
    eligible_formulas.sort(key=lambda x: (x[2], x[1]['tries']), reverse=True) # Sort by hit_rate, then tries

    for f_id, perf_data, hit_rate in eligible_formulas:
        spec = ALL_FORMULA_SPECS.get(f_id)
        if not spec: continue
        generated_values = spec["func"](latest_day_data, spec["params"])
        if generated_values: # Only add if formula actually produced anks
            suggestions.append({
                "display_name": perf_data["display_name"], "params_str": perf_data["params_str"],
                "generated_anks": sorted(list(generated_values)), "hit_rate": hit_rate * 100,
                "hits_tries_str": f"{perf_data['hits']}/{perf_data['tries']}" })
    return suggestions


def log_top_suggestion(market_name, suggestion):
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "otc_math_daily_suggestions.txt") # Different log file
    today = datetime.now().strftime("%d-%m-%Y"); tomorrow = (datetime.now()+timedelta(days=1)).strftime("%d-%m-%Y")
    entry = (f"{today} (For {tomorrow}) | Mkt: {market_name} | "
             f"Formula: {suggestion['display_name']} {suggestion['params_str']} | "
             f"Rate: {suggestion['hit_rate']:.0f}% ({suggestion['hits_tries_str']}) | "
             f"Sugg. Anks: {' '.join(suggestion['generated_anks'])}\n")
    try:
        with open(log_file, 'a') as f: f.write(entry)
    except IOError: print(C_ERROR + f"Log write error: {log_file}")

def display_performance_summary(all_stats):
    print_box_top(c=C_INFO_BRIGHT); print_box_line(f"{C_ACCENT_BRIGHT}Math Formula Performance (OTC Anks)", bc=C_INFO_BRIGHT, align="center")
    print_box_sep(c=C_INFO_BRIGHT)
    header = f"{'Formula Display Name'.ljust(35)} | {'Parameters'.ljust(20)} | {'Rate'.rjust(7)} | {'Hits/Tries'.rjust(10)}"
    print_box_line(C_WARNING_BRIGHT + header, bc=C_INFO_BRIGHT, p=1); print_box_sep(c=C_INFO_BRIGHT)
    
    sorted_stats = sorted(all_stats.items(), key=lambda x: (x[1]['hits']/x[1]['tries'] if x[1]['tries']>0 else 0, x[1]['tries']), reverse=True)

    for f_id, data in sorted_stats[:20]: # Display top 20
        rate = (data['hits']/data['tries']*100) if data['tries']>0 else 0
        name = data.get('display_name', f_id)[:33]
        param = data.get('params_str', "{}")[:18]
        clr = C_SUCCESS if rate >= MIN_HIT_RATE_SUGGESTION*100 and data['tries'] >= MIN_TRIES_SUGGESTION else C_PRIMARY
        line = f"{name.ljust(35)} | {param.ljust(20)} | {f'{rate:.0f}%'.rjust(7)} | {f'''{data['hits']}/{data['tries']}'''.rjust(10)}"
        print_box_line(clr + line, bc=C_INFO_BRIGHT, p=1)
    if len(sorted_stats) > 20: print_box_line("... and more ...", bc=C_INFO_BRIGHT, align="center", p=1)
    print_box_bottom(c=C_INFO_BRIGHT)

def display_final_otc_suggestions(market_name, suggestions_from_formulas):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y (%A)')
    print_box_top(c=C_SUCCESS_BRIGHT)
    print_box_line(f"{C_ACCENT_BRIGHT}OTC Ank Suggestions for {market_name} - {tomorrow}", bc=C_SUCCESS_BRIGHT, align="center")
    print_box_sep(c=C_SUCCESS_BRIGHT)

    if not suggestions_from_formulas:
        print_box_line(C_WARNING+"No formulas met suggestion criteria today.", bc=C_SUCCESS_BRIGHT, align="center")
    else:
        # Display top N individual formulas that qualified
        header = f"{'Rank'.ljust(4)}| {'Formula'.ljust(35)}| {'Params'.ljust(20)}| {'Anks'.ljust(10)}| {'Rate'.rjust(7)}"
        print_box_line(C_WARNING_BRIGHT+header, bc=C_SUCCESS_BRIGHT,p=1); print_box_sep(c=C_SUCCESS_BRIGHT)
        
        final_combined_anks = set()
        contributing_details = []

        for i, sug in enumerate(suggestions_from_formulas[:NUM_INDIVIDUAL_FORMULA_SUGGESTIONS_TO_DISPLAY]):
            name = sug['display_name'][:33]; param = sug['params_str'][:18]
            anks = ' '.join(sug['generated_anks'])[:8]; rate = f"{sug['hit_rate']:.0f}%"
            clr = C_SUCCESS_BRIGHT # They already met criteria to be in this list
            line = f"{str(i+1).ljust(4)}| {name.ljust(35)}| {param.ljust(20)}| {anks.ljust(10)}| {rate.rjust(7)}"
            print_box_line(clr+line, bc=C_SUCCESS_BRIGHT, p=1)
            if i == 0: log_top_suggestion(market_name, sug) # Log the absolute top one

            for ank_val in sug['generated_anks']:
                if len(final_combined_anks) < NUM_ANK_SUGGESTIONS_COMBINED:
                    final_combined_anks.add(ank_val)
                    # Add reason only if it's contributing, and reason not already added for this ank
                    is_new_reason_for_ank = True
                    for existing_reason in contributing_details:
                        if existing_reason.startswith(f"{ank_val} ("): is_new_reason_for_ank = False; break
                    if is_new_reason_for_ank and len(contributing_details) < NUM_ANK_SUGGESTIONS_COMBINED:
                        contributing_details.append(f"{ank_val} (from {sug['display_name']} @{sug['hit_rate']:.0f}%)")
        
        print_box_sep(c=C_SUCCESS_BRIGHT)
        if final_combined_anks:
            display_list = sorted(list(final_combined_anks))[:NUM_ANK_SUGGESTIONS_COMBINED]
            while len(display_list) < NUM_ANK_SUGGESTIONS_COMBINED and NUM_ANK_SUGGESTIONS_COMBINED > 0: display_list.append('?') # Pad if needed
            
            print_box_line(f"{C_ACCENT_BRIGHT}Tomorrow's Top {NUM_ANK_SUGGESTIONS_COMBINED} Combined OTC Anks: {C_SUCCESS_BRIGHT}{'  '.join(display_list)}", bc=C_SUCCESS_BRIGHT, align="center", p=1)
            for detail in sorted(list(set(contributing_details)))[:NUM_ANK_SUGGESTIONS_COMBINED]: # Show unique reasons
                 print_box_line(f"{C_INFO_BRIGHT} {detail[:BOX_WIDTH-6]}", bc=C_SUCCESS_BRIGHT,p=1)
        else:
            print_box_line(C_WARNING+f"Could not determine a combined set of {NUM_ANK_SUGGESTIONS_COMBINED} OTC anks.", bc=C_SUCCESS_BRIGHT, align="center", p=1)
    print_box_bottom(c=C_SUCCESS_BRIGHT)

def main():
    show_banner()
    print_box_top(w=BOX_WIDTH//2,c=C_PRIMARY_BRIGHT); print_box_line("Select Market",w=BOX_WIDTH//2,bc=C_PRIMARY_BRIGHT,align="center")
    for i,m in enumerate(MARKETS): print_box_line(f"{C_WARNING}{i+1}. {C_SECONDARY}{m}",w=BOX_WIDTH//2,bc=C_PRIMARY_BRIGHT)
    print_box_bottom(w=BOX_WIDTH//2,c=C_PRIMARY_BRIGHT)
    mk_idx = -1
    while not (0 <= mk_idx < len(MARKETS)):
        try: mk_idx = int(input(C_PRIMARY_BRIGHT+"Enter market number: "+C_RESET))-1
        except ValueError: print(C_ERROR+"Invalid input.")
        if not (0 <= mk_idx < len(MARKETS)): print(C_ERROR+"Invalid choice.")
    market_name = MARKETS[mk_idx]
    print(C_INFO_BRIGHT+f"\nAnalyzing Market: {C_ACCENT_BRIGHT}{market_name}{C_RESET} for OTC Anks using Math Formulas\n")
    
    historical_data = read_data_file(market_name)
    if not historical_data or len(historical_data) < max(2, MIN_TRIES_SUGGESTION // 2): # Need some data
        print(C_ERROR_BRIGHT+f"Not enough data for {market_name} (found {len(historical_data)}). Backtesting needs more."); sys.exit(1)

    all_formula_stats = backtest_all_formulas(historical_data)
    if all_formula_stats: display_performance_summary(all_formula_stats)
    else: print(C_WARNING+"No formula performance data from backtest.")

    latest_day_data = historical_data[-1] if historical_data else None
    otc_ank_suggestions = get_otc_suggestions_for_tomorrow(latest_day_data, all_formula_stats)

    if otc_ank_suggestions:
        display_final_otc_suggestions(market_name, otc_ank_suggestions)
    else: 
        print(C_WARNING_BRIGHT + f"\nNo Math Formulas for {market_name} met the required hit rate ({MIN_HIT_RATE_SUGGESTION*100:.0f}%) and min tries ({MIN_TRIES_SUGGESTION}) for an OTC Ank suggestion today.")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print(C_WARNING_BRIGHT+"\n\n[!] User interrupted."+C_RESET)
    except Exception as e:
        print(C_ERROR_BRIGHT+f"\n[!!!] CRITICAL ERROR: {e}"); import traceback; traceback.print_exc()
        print(C_ERROR_BRIGHT+"Please report this."+C_RESET)
    finally: print(C_PRIMARY_BRIGHT+f"\n✨ Thank you for using {APP_NAME}! ✨"+C_RESET)
