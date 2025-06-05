#!/usr/bin/env python3
# SEQUENCE ANALYZER & SUGGESTER v1.0
# Powered by Anuj & AI God (Enhanced by Sachin & AI)

import os
import sys
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from colorama import Fore, Style, init

init(autoreset=True)

# --- Configuration & Constants ---
APP_NAME = "SEQUENCE ANALYZER"
APP_VERSION = "v1.0"
POWERED_BY = "Anuj & AI God (Enhanced by Sachin & AI)"
BOX_WIDTH = 80
DATA_DIR = "data"
LOG_DIR = "logs" # For potential future logging

NUM_JODI_SUGGESTIONS = 4
NUM_OPEN_ANK_SUGGESTIONS = 3
MIN_OCCURRENCES_FOR_STRONG_SUGGESTION = 2 # A sequence must have occurred at least this many times

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
    print_box_sep(); print_box_line(f"{C_BANNER_TEXT}Historical Sequence Pattern Suggester", align="center"); print_box_bottom(); print("\n")

def parse_data_line(line_str):
    try:
        date_part_str, result_part_str = map(str.strip, line_str.split('/', 1))
        p1, jodi, p2 = map(str.strip, result_part_str.split('-', 2))
        if not (re.fullmatch(r"\d{3}",p1) and re.fullmatch(r"\d{2}",jodi) and re.fullmatch(r"\d{3}",p2)): return None
        dt = datetime.strptime(date_part_str, "%d-%m-%Y")
        return {"date_obj": dt, "date_str": date_part_str, "p1": p1, "jodi": jodi, "p2": p2, "open_ank": p1[-1], "close_ank": jodi[-1]}
    except: return None

def read_data_file(market_name):
    filepath = os.path.join(DATA_DIR, f"{market_name}.txt")
    try:
        with open(filepath, 'r', encoding='utf-8') as f: lines = [line.strip() for line in f if line.strip()]
        parsed_data = [parse_data_line(line) for line in lines]
        # Sort by date just in case data is not perfectly ordered
        return sorted([d for d in parsed_data if d is not None], key=lambda x: x['date_obj'])
    except FileNotFoundError: print(C_ERROR_BRIGHT + f"[!] File missing: {filepath}"); return []
    except Exception as e: print(C_ERROR_BRIGHT + f"[!] Read error {filepath}: {e}"); return []

def analyze_sequences(historical_data):
    """
    Analyzes sequences:
    - jodi_after_jodi: Counts which jodi follows a given jodi on the next day.
    - open_ank_after_open_ank: Counts which open_ank follows a given open_ank on the next day.
    Returns:
        tuple: (jodi_after_jodi_counts, open_ank_after_open_ank_counts)
               Each is a dict like: { "prev_value": Counter({"next_value1": count1, ...}), ... }
    """
    jodi_after_jodi = defaultdict(Counter)
    open_ank_after_open_ank = defaultdict(Counter)
    # Add more sequence types here in future, e.g., open_ank_after_jodi

    if len(historical_data) < 2:
        return jodi_after_jodi, open_ank_after_open_ank

    for i in range(len(historical_data) - 1):
        prev_day = historical_data[i]
        curr_day = historical_data[i+1]

        # Jodi -> Next Day's Jodi
        jodi_after_jodi[prev_day["jodi"]][curr_day["jodi"]] += 1
        
        # Open Ank -> Next Day's Open Ank
        open_ank_after_open_ank[prev_day["open_ank"]][curr_day["open_ank"]] += 1
        
    return jodi_after_jodi, open_ank_after_open_ank

def get_suggestions_from_sequences(latest_day_data, sequence_counts_dict, num_suggestions):
    """
    Gets suggestions based on the latest day's value and pre-calculated sequence counts.
    Args:
        latest_day_value (str): The value from the latest day (e.g., last jodi or last open ank).
        sequence_counts_dict (dict): The pre-calculated counts, e.g., jodi_after_jodi_counts.
        num_suggestions (int): How many top suggestions to return.
    Returns:
        list: List of tuples (suggested_value, count, percentage_chance)
    """
    if not latest_day_data: return []
    
    # Determine the key to use from latest_day_data based on what sequence_counts_dict represents
    # This is a bit implicit. Let's assume if sequence_counts_dict has keys like "00", "01" it's for jodi.
    # If keys are "0", "1", it's for anks.
    # A better way would be to pass the key explicitly.

    latest_value_key = None
    if all(len(k) == 2 and k.isdigit() for k in sequence_counts_dict.keys()): # Heuristic for jodi keys
        latest_value_key = "jodi"
    elif all(len(k) == 1 and k.isdigit() for k in sequence_counts_dict.keys()): # Heuristic for ank keys
        latest_value_key = "open_ank" # Assuming open_ank for now
    
    if not latest_value_key or latest_value_key not in latest_day_data:
        # Try to infer: if 'jodi' is in the name of the sequence_counts_dict variable (hacky)
        # This part needs to be more robust. For now, this is a placeholder.
        # The caller should ideally specify what 'latest_value' it's providing.
        # For this version, we'll call this function specifically for jodi and anks.
        print(C_WARNING + "Could not determine key for latest_day_data in get_suggestions_from_sequences")
        return []


    latest_value = latest_day_data[latest_value_key]

    if latest_value not in sequence_counts_dict:
        return [] # No historical sequences found for this latest_value

    following_counts = sequence_counts_dict[latest_value]
    total_occurrences_after_latest = sum(following_counts.values())

    if total_occurrences_after_latest == 0:
        return []

    suggestions = []
    for suggested_val, count in following_counts.most_common():
        if count >= MIN_OCCURRENCES_FOR_STRONG_SUGGESTION: # Only suggest if it occurred a few times
            percentage = (count / total_occurrences_after_latest) * 100
            suggestions.append((suggested_val, count, percentage))
    
    return suggestions[:num_suggestions]


def display_sequence_suggestions(market_name, latest_day_data, jodi_suggestions, ank_suggestions):
    tomorrow_date_str = (latest_day_data["date_obj"] + timedelta(days=1)).strftime('%d-%m-%Y (%A)')
    last_jodi = latest_day_data["jodi"]
    last_open_ank = latest_day_data["open_ank"]

    print_box_top(c=C_SUCCESS_BRIGHT)
    title = f"{C_ACCENT_BRIGHT}Sequence-Based Suggestions for {market_name} - {tomorrow_date_str}"
    print_box_line(title, bc=C_SUCCESS_BRIGHT, align="center")
    print_box_sep(c=C_SUCCESS_BRIGHT)
    print_box_line(f"{C_INFO_BRIGHT}Based on last result: Jodi={C_ACCENT_BRIGHT}{last_jodi}{C_INFO_BRIGHT}, Open Ank={C_ACCENT_BRIGHT}{last_open_ank}", bc=C_SUCCESS_BRIGHT, align="center", p=1)
    print_box_sep(c=C_SUCCESS_BRIGHT)

    # Jodi Suggestions
    print_box_line(f"{C_WARNING_BRIGHT}Top Suggested Jodis (after Jodi {last_jodi}):", bc=C_SUCCESS_BRIGHT, p=1)
    if not jodi_suggestions:
        print_box_line(C_PRIMARY + "  No strong jodi sequences found.", bc=C_SUCCESS_BRIGHT, p=1)
    else:
        for i, (sugg_jodi, count, percent) in enumerate(jodi_suggestions):
            line = f"  {i+1}. {C_ACCENT_BRIGHT}{sugg_jodi}{C_PRIMARY} (occurred {count} times, {percent:.0f}% chance)"
            print_box_line(C_PRIMARY + line, bc=C_SUCCESS_BRIGHT, p=1)
    
    print_box_sep(c=C_SUCCESS_BRIGHT)

    # Open Ank Suggestions
    print_box_line(f"{C_WARNING_BRIGHT}Top Suggested Open Anks (after Open Ank {last_open_ank}):", bc=C_SUCCESS_BRIGHT, p=1)
    if not ank_suggestions:
        print_box_line(C_PRIMARY + "  No strong open ank sequences found.", bc=C_SUCCESS_BRIGHT, p=1)
    else:
        for i, (sugg_ank, count, percent) in enumerate(ank_suggestions):
            line = f"  {i+1}. {C_ACCENT_BRIGHT}{sugg_ank}{C_PRIMARY} (occurred {count} times, {percent:.0f}% chance)"
            print_box_line(C_PRIMARY + line, bc=C_SUCCESS_BRIGHT, p=1)

    print_box_bottom(c=C_SUCCESS_BRIGHT)


def main():
    show_banner()
    # Market Selection
    print_box_top(w=BOX_WIDTH//2,c=C_PRIMARY_BRIGHT); print_box_line("Select Market",w=BOX_WIDTH//2,bc=C_PRIMARY_BRIGHT,align="center")
    for i,m in enumerate(MARKETS): print_box_line(f"{C_WARNING}{i+1}. {C_SECONDARY}{m}",w=BOX_WIDTH//2,bc=C_PRIMARY_BRIGHT)
    print_box_bottom(w=BOX_WIDTH//2,c=C_PRIMARY_BRIGHT)
    mk_idx = -1
    while not (0 <= mk_idx < len(MARKETS)):
        try: mk_idx = int(input(C_PRIMARY_BRIGHT+"Enter market number: "+C_RESET))-1
        except ValueError: print(C_ERROR+"Invalid input.")
        if not (0 <= mk_idx < len(MARKETS)): print(C_ERROR+"Invalid choice.")
    market_name = MARKETS[mk_idx]
    print(C_INFO_BRIGHT+f"\nAnalyzing Market: {C_ACCENT_BRIGHT}{market_name}{C_RESET}\n")
    
    historical_data = read_data_file(market_name)
    if not historical_data or len(historical_data) < 5: # Need at least a few days for sequence analysis
        print(C_ERROR_BRIGHT+f"Not enough historical data for {market_name} (found {len(historical_data)}). Sequence analysis requires more entries."); sys.exit(1)

    print(C_INFO_BRIGHT + f"Analyzing sequences from {len(historical_data)} historical records...")
    j2j_counts, oa2oa_counts = analyze_sequences(historical_data)

    latest_day_data = historical_data[-1]
    
    # Modify how get_suggestions_from_sequences is called to be more explicit
    # For Jodi suggestions based on previous Jodi:
    jodi_suggestions = []
    if latest_day_data["jodi"] in j2j_counts:
        following_counts = j2j_counts[latest_day_data["jodi"]]
        total_occurrences = sum(following_counts.values())
        if total_occurrences > 0:
            for sugg_val, count in following_counts.most_common(NUM_JODI_SUGGESTIONS):
                if count >= MIN_OCCURRENCES_FOR_STRONG_SUGGESTION:
                    percentage = (count / total_occurrences) * 100
                    jodi_suggestions.append((sugg_val, count, percentage))

    # For Open Ank suggestions based on previous Open Ank:
    open_ank_suggestions = []
    if latest_day_data["open_ank"] in oa2oa_counts:
        following_counts = oa2oa_counts[latest_day_data["open_ank"]]
        total_occurrences = sum(following_counts.values())
        if total_occurrences > 0:
            for sugg_val, count in following_counts.most_common(NUM_OPEN_ANK_SUGGESTIONS):
                if count >= MIN_OCCURRENCES_FOR_STRONG_SUGGESTION:
                    percentage = (count / total_occurrences) * 100
                    open_ank_suggestions.append((sugg_val, count, percentage))


    display_sequence_suggestions(market_name, latest_day_data, jodi_suggestions, open_ank_suggestions)


if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print(C_WARNING_BRIGHT+"\n\n[!] User interrupted."+C_RESET)
    except Exception as e:
        print(C_ERROR_BRIGHT+f"\n[!!!] CRITICAL ERROR: {e}"); import traceback; traceback.print_exc()
        print(C_ERROR_BRIGHT+"Please report this."+C_RESET)
    finally: print(C_PRIMARY_BRIGHT+f"\n✨ Thank you for using {APP_NAME}! ✨"+C_RESET)
