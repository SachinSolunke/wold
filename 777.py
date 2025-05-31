#!/usr/bin/env python3
# MATKA MATH ANK FINDER v1.2 - Powered by Anuj & AI God (Inspired by Sachin)

import os
import sys
import re
import math
from datetime import datetime, timedelta # Ensure timedelta is imported
from collections import Counter, defaultdict
from decimal import Decimal, getcontext

from colorama import Fore, Style, init

init(autoreset=True)
getcontext().prec = 10

# --- Configuration & Constants ---
APP_NAME = "MATKA MATH ANK FINDER"
APP_VERSION = "v1.2" # Incremented for new features
POWERED_BY = "Anuj & AI God (Inspired by Sachin)"
BOX_WIDTH = 80
DATA_DIR = "data"
SUGGESTIONS_LOG_FILE = "daily_math_ank_suggestions.txt" # File to log daily suggestions

# Backtesting Config
OPERATOR_VALUE_RANGE_SMALL = range(1, 51) 
OPERATOR_VALUE_RANGE_LARGE = range(1, 201)
MIN_TESTS_FOR_RELIABILITY = 3 

# Color Palette (Same as v1.1)
C_PRIMARY_BRIGHT = Fore.CYAN + Style.BRIGHT; C_SECONDARY_BRIGHT = Fore.MAGENTA + Style.BRIGHT
C_SUCCESS_BRIGHT = Fore.GREEN + Style.BRIGHT; C_ERROR_BRIGHT = Fore.RED + Style.BRIGHT
C_WARNING_BRIGHT = Fore.YELLOW + Style.BRIGHT; C_INFO_BRIGHT = Fore.BLUE + Style.BRIGHT
C_ACCENT_BRIGHT = Fore.WHITE + Style.BRIGHT; C_PRIMARY = Fore.CYAN; C_SECONDARY = Fore.MAGENTA
C_ERROR = Fore.RED; C_RESET = Style.RESET_ALL; C_BANNER_BORDER = C_SECONDARY_BRIGHT
C_BANNER_TITLE = C_SUCCESS_BRIGHT; C_BANNER_SUBTITLE = C_WARNING_BRIGHT; C_BANNER_TEXT = C_PRIMARY

# --- Styling Utilities (Same as v1.1) ---
def print_box_top(w=BOX_WIDTH, c=C_SECONDARY_BRIGHT): print(c + f"╔{'═'*(w-2)}╗" + C_RESET)
def print_box_bottom(w=BOX_WIDTH, c=C_SECONDARY_BRIGHT): print(c + f"╚{'═'*(w-2)}╝" + C_RESET)
def print_box_sep(w=BOX_WIDTH, c=C_SECONDARY_BRIGHT): print(c + f"╠{'═'*(w-2)}╣" + C_RESET)
def strip_ansi(t): return re.sub(r'\x1b\[[0-9;]*[mK]', '', t)
def print_box_line(t, w=BOX_WIDTH, bc=C_SECONDARY_BRIGHT, tc="", align="left", p=2):
    st, cw = strip_ansi(t), w-2-(p*2); dsp_t = t; cl_diff = len(t)-len(st)
    slen = len(st)
    if slen > cw:
        cut_point = cw - 3 if cw > 3 else cw
        dsp_t = st[:cut_point] + ("..." if cw > 3 else "")
        cl_diff = 0 
    eff_w = cw + cl_diff
    at = dsp_t.center(eff_w) if align=="center" else (dsp_t.rjust(eff_w) if align=="right" else dsp_t.ljust(eff_w))
    final_text_segment = f"{tc}{at}{C_RESET if tc else ''}" if tc else at
    print(f"{bc}║{' '*p}{final_text_segment}{' '*p}{bc}║{C_RESET}")

def show_banner(): # Same as v1.1
    os.system("clear" if os.name == 'posix' else 'cls'); print_box_top(BOX_WIDTH, C_BANNER_BORDER)
    print_box_line(f"{C_BANNER_TITLE}{APP_NAME}",BOX_WIDTH,C_BANNER_BORDER, tc=C_BANNER_TITLE, align="center")
    print_box_line(f"{C_BANNER_SUBTITLE}{APP_VERSION}",BOX_WIDTH,C_BANNER_BORDER, tc=C_BANNER_SUBTITLE, align="center")
    print_box_sep(BOX_WIDTH,C_BANNER_BORDER); print_box_line(f"{C_BANNER_TEXT}Discovering Single Ank Patterns with Math",BOX_WIDTH,C_BANNER_BORDER, tc=C_BANNER_TEXT, align="center")
    print_box_bottom(BOX_WIDTH,C_BANNER_BORDER); print("\n")

# --- Data Parsing (Same as v1.1) ---
def parse_line_for_math_ank(line_str):
    try:
        date_part_str, result_part_str = map(str.strip, line_str.split('/', 1))
        p1, jodi_str, p2 = map(str.strip, result_part_str.split('-', 2))
        if not (re.fullmatch(r"\d{3}",p1) and re.fullmatch(r"\d{2}",jodi_str) and re.fullmatch(r"\d{3}",p2)): return None 
        dt_obj = datetime.strptime(date_part_str, "%d-%m-%Y")
        jodi_val = int(jodi_str)
        return {
            "date_obj": dt_obj, "jodi_val": jodi_val, "jodi_str": jodi_str,
            "p1": p1, "p2": p2, "open_ank_from_p1": p1[-1],
            "close_ank_from_jodi": jodi_str[-1]
        }
    except Exception: return None

def load_market_data_for_math(market_filename): # Same as v1.1
    filepath = os.path.join(DATA_DIR, market_filename)
    if not os.path.exists(filepath):
        print(C_ERROR_BRIGHT + f"Data file not found: {filepath}")
        return []
    parsed_entries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                parsed = parse_line_for_math_ank(line)
                if parsed: parsed_entries.append(parsed)
    return parsed_entries

# --- Formula Definitions (Same as v1.1) ---
FORMULAS = {
    "jodi_div_X": lambda num, x: Decimal(num) / Decimal(x) if x != 0 else Decimal(0),
    "jodi_mul_X": lambda num, x: Decimal(num) * Decimal(x),
    "jodi_add_X": lambda num, x: Decimal(num) + Decimal(x),
    "jodi_sub_X": lambda num, x: abs(Decimal(num) - Decimal(x)),
    "jodi_mod_X": lambda num, x: Decimal(num) % Decimal(x) if x != 0 else Decimal(0),
    "sum_digits_jodi_div_X": lambda num, x: (Decimal(str(num)[0]) + Decimal(str(num)[1])) / Decimal(x) if len(str(num))==2 and x != 0 else Decimal(0),
    "prod_digits_jodi_mul_X": lambda num, x: (Decimal(str(num)[0]) * Decimal(str(num)[1])) * Decimal(x) if len(str(num))==2 else Decimal(0),
    "sqrt_jodi_mul_X": lambda num, x: Decimal(math.sqrt(num)) * Decimal(x) if num >= 0 else Decimal(0),
}

# --- Ank Extraction Logic (Same as v1.1) ---
def extract_3_anks_from_result(result_decimal):
    anks = set()
    s = str(result_decimal)
    integer_part = s.split('.')[0].lstrip('-')
    for char in integer_part:
        if char.isdigit(): anks.add(int(char))
        if len(anks) >= 3: break
    if len(anks) >= 3: return sorted(list(anks))[:3]
    if '.' in s:
        fractional_part = s.split('.')[1]
        for char in fractional_part:
            if char.isdigit(): anks.add(int(char))
            if len(anks) >= 3: break
    if len(anks) >= 3: return sorted(list(anks))[:3]
    if anks:
        sum_val = sum(list(anks)) % 10
        anks.add(sum_val)
    if len(anks) >= 3: return sorted(list(anks))[:3]
    temp_anks_list = sorted(list(anks)) 
    if temp_anks_list:
        last_found_ank = temp_anks_list[-1]
        for _ in range(10):
            if len(anks) >= 3: break
            last_found_ank = (last_found_ank + 1) % 10
            if last_found_ank not in anks: anks.add(last_found_ank)
    padding_needed = 3 - len(anks)
    padding_sequence = [1,2,3,4,5,6,7,8,9,0]; current_padding_idx = 0
    while padding_needed > 0 and current_padding_idx < len(padding_sequence):
        ank_to_add = padding_sequence[current_padding_idx]
        if ank_to_add not in anks: anks.add(ank_to_add); padding_needed -=1
        current_padding_idx += 1
    return sorted(list(anks))[:3]

# --- Backtesting Engine (Same as v1.1) ---
def run_backtester(historical_data, formulas_to_test, operator_ranges):
    results = []
    if len(historical_data) < 2:
        print(C_WARNING_BRIGHT + "Not enough historical data (need at least 2 entries).")
        return []
    data_pairs = []
    for i in range(len(historical_data) - 1):
        data_pairs.append({
            "current_date_obj": historical_data[i]["date_obj"], # Store date for context
            "current_jodi_val": historical_data[i]["jodi_val"],
            "next_day_date_obj": historical_data[i+1]["date_obj"], # Store date for context
            "next_day_open_ank": historical_data[i+1]["open_ank_from_p1"],
            "next_day_close_ank": historical_data[i+1]["close_ank_from_jodi"]
        })
    if not data_pairs: return []
    
    first_test_date = data_pairs[0]["current_date_obj"].strftime("%d-%m-%Y")
    last_test_date_for_jodi = data_pairs[-1]["current_date_obj"].strftime("%d-%m-%Y")
    print(C_INFO_BRIGHT + f"Starting backtesting with {len(data_pairs)} data points.")
    print(C_INFO_BRIGHT + f"  (Jodis from {first_test_date} to {last_test_date_for_jodi} predicting for subsequent days)")

    formula_stats = defaultdict(lambda: {"tests": 0, "passes": 0})

    for i, pair_data in enumerate(data_pairs):
        current_jodi = pair_data["current_jodi_val"]
        actual_next_open_ank = pair_data["next_day_open_ank"]
        actual_next_close_ank = pair_data["next_day_close_ank"]
        if (i + 1) % (max(1, len(data_pairs) // 4)) == 0 or i == len(data_pairs) -1 :
            progress = (i + 1) / len(data_pairs) * 100
            # Removed date from progress line to keep it concise
            print(f"{C_PRIMARY}  Backtesting progress: {progress:.0f}% ({i+1}/{len(data_pairs)} days processed)")

        for f_name, formula_func in formulas_to_test.items():
            op_range_key_prefix = f_name.split('_')[1] 
            op_range = OPERATOR_VALUE_RANGE_SMALL 
            if "add" in op_range_key_prefix or "sub" in op_range_key_prefix : op_range = OPERATOR_VALUE_RANGE_LARGE
            elif "mod" in op_range_key_prefix: op_range = [x for x in OPERATOR_VALUE_RANGE_SMALL if x > 0]
            
            for x_val in op_range:
                if (f_name.endswith("_div_X") or f_name.endswith("_mod_X")) and x_val == 0: continue
                try: result_val = formula_func(current_jodi, x_val)
                except Exception: continue
                predicted_anks = extract_3_anks_from_result(result_val)
                key = (f_name, x_val); formula_stats[key]["tests"] += 1
                is_pass = any(str(p_ank) == actual_next_open_ank or str(p_ank) == actual_next_close_ank for p_ank in predicted_anks)
                if is_pass: formula_stats[key]["passes"] += 1
    
    for (f_name, x_val), stats in formula_stats.items():
        if stats["tests"] >= MIN_TESTS_FOR_RELIABILITY:
            pass_rate = (stats["passes"] / stats["tests"]) * 100 if stats["tests"] > 0 else 0
            sample_pred_anks = ["-","-","-"]
            if historical_data:
                 last_hist_jodi = historical_data[-1]["jodi_val"]
                 try:
                     sample_res = formulas_to_test[f_name](last_hist_jodi, x_val)
                     sample_pred_anks = extract_3_anks_from_result(sample_res)
                 except: pass
            results.append({
                "name":f_name, "x":x_val, "tests":stats["tests"], "passes":stats["passes"], 
                "rate":pass_rate, "sample_anks":sample_pred_anks
            })
    return sorted(results, key=lambda r: (r["rate"], r["passes"]), reverse=True)

# --- Saving Daily Suggestions ---
def save_daily_suggestion(market_name, prediction_for_date_str, formula_name, x_value, suggested_anks):
    """Appends the daily suggestion to the log file."""
    today_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    anks_str = ' '.join(map(str, suggested_anks))
    log_line = f"[{today_str}] Market: {market_name}, For_Date: {prediction_for_date_str}, Formula: {formula_name}(X={x_value}), Suggested_Anks: [{anks_str}]\n"
    
    try:
        with open(SUGGESTIONS_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
        print(C_INFO_BRIGHT + f"Suggestion logged to: {C_SECONDARY_BRIGHT}{SUGGESTIONS_LOG_FILE}{C_RESET}")
    except Exception as e:
        print(C_ERROR_BRIGHT + f"Error logging suggestion: {e}")


# --- Main Application ---
def select_market_file(): # Same as v1.1
    market_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".txt") and os.path.isfile(os.path.join(DATA_DIR, f))])
    if not market_files:
        print(C_ERROR_BRIGHT + f"No .txt files found in '{DATA_DIR}/' directory.")
        return None
    print_box_top(BOX_WIDTH, C_PRIMARY_BRIGHT)
    print_box_line(f"{C_ACCENT_BRIGHT}Select Market File for Analysis", BOX_WIDTH, C_PRIMARY_BRIGHT, tc=C_ACCENT_BRIGHT, align="center")
    print_box_sep(BOX_WIDTH, C_PRIMARY_BRIGHT)
    for i, market_file in enumerate(market_files, 1):
        line_text = f"{C_WARNING_BRIGHT}{i:>2}. {C_SECONDARY_BRIGHT}{market_file}"
        print_box_line(line_text, BOX_WIDTH, C_PRIMARY_BRIGHT, tc="")
    print_box_bottom(BOX_WIDTH, C_PRIMARY_BRIGHT)
    while True:
        try:
            choice = input(C_PRIMARY_BRIGHT + f"\n👉 Enter market number (or 0 to exit): {C_RESET}").strip()
            if not choice: continue
            choice_num = int(choice)
            if choice_num == 0: return None
            if 1 <= choice_num <= len(market_files):
                return market_files[choice_num - 1]
            else: print(C_ERROR + "Invalid market number." + C_RESET)
        except ValueError: print(C_ERROR + "Invalid input. Please enter a number." + C_RESET)

def main():
    show_banner()
    selected_market = select_market_file()
    if not selected_market:
        print(C_INFO_BRIGHT + "Exiting application.")
        return

    print(C_INFO_BRIGHT + f"\nLoading data for market: {C_SECONDARY_BRIGHT}{selected_market}{C_RESET}")
    historical_data = load_market_data_for_math(selected_market)

    if len(historical_data) < 2: 
        print(C_ERROR_BRIGHT + f"Not enough data in {selected_market} (found {len(historical_data)}, need at least 2).")
        return
    
    print(C_SUCCESS_BRIGHT + f"Loaded {len(historical_data)} historical records.")
    first_data_date = historical_data[0]["date_obj"].strftime("%d-%m-%Y")
    last_data_date = historical_data[-1]["date_obj"].strftime("%d-%m-%Y")
    print(C_INFO_BRIGHT + f"Data range: {C_ACCENT_BRIGHT}{first_data_date}{C_INFO_BRIGHT} to {C_ACCENT_BRIGHT}{last_data_date}{C_RESET}")


    operator_configs = {} # Not directly used by run_backtester in this version
    best_formulas = run_backtester(historical_data, FORMULAS, operator_configs)

    print_box_top(BOX_WIDTH, C_SUCCESS_BRIGHT)
    print_box_line(f"{C_ACCENT_BRIGHT}Top Performing Formulas for {selected_market}", BOX_WIDTH, C_SUCCESS_BRIGHT, tc=C_ACCENT_BRIGHT, align="center")
    print_box_sep(BOX_WIDTH, C_SUCCESS_BRIGHT)
    header = f"{'Formula':<30} | {'X':>3} | {'Rate%':>6} | {'P/T':>7} | Anks (Sample)"
    print_box_line(header, BOX_WIDTH, C_SUCCESS_BRIGHT, tc=C_WARNING_BRIGHT, p=1)
    print_box_sep(BOX_WIDTH, C_SUCCESS_BRIGHT)

    if not best_formulas:
        print_box_line("No formulas met reliability criteria.", BOX_WIDTH, C_SUCCESS_BRIGHT, tc=C_INFO_BRIGHT, align="center")
    else:
        for i, res in enumerate(best_formulas[:15]):
            anks_str = ' '.join(map(str, res['sample_anks']))
            line_str = f"{res['name']:<30} | {str(res['x']):>3} | {res['rate']:>6.2f} | {str(res['passes'])+'/'+str(res['tests']):>7} | {anks_str}"
            print_box_line(line_str, BOX_WIDTH, C_SUCCESS_BRIGHT, tc=C_PRIMARY, p=1)
    print_box_bottom(BOX_WIDTH, C_SUCCESS_BRIGHT)

    if best_formulas and historical_data:
        latest_jodi_val = historical_data[-1]["jodi_val"]
        latest_jodi_date_obj = historical_data[-1]["date_obj"]
        prediction_for_date_obj = latest_jodi_date_obj + timedelta(days=1) # Calculate next day's date
        prediction_for_date_str = prediction_for_date_obj.strftime("%d-%m-%Y")

        top_formula_spec = best_formulas[0]
        formula_to_use = FORMULAS[top_formula_spec['name']]
        x_to_use = top_formula_spec['x']
        try:
            prediction_result_val = formula_to_use(latest_jodi_val, x_to_use)
            predicted_anks_for_tomorrow = extract_3_anks_from_result(prediction_result_val)
            
            print("\n")
            print_box_top(BOX_WIDTH, C_PRIMARY_BRIGHT)
            title_text = f"{C_ACCENT_BRIGHT}Ank Suggestion for {prediction_for_date_str}" # Display date
            print_box_line(title_text, BOX_WIDTH, C_PRIMARY_BRIGHT, tc=C_ACCENT_BRIGHT, align="center")
            print_box_sep(BOX_WIDTH, C_PRIMARY_BRIGHT)
            print_box_line(f"Using: {C_SECONDARY_BRIGHT}{top_formula_spec['name']} (X={x_to_use})", BOX_WIDTH, C_PRIMARY_BRIGHT, tc=C_INFO_BRIGHT)
            print_box_line(f"On Jodi: {C_ACCENT_BRIGHT}{latest_jodi_val} (from {latest_jodi_date_obj.strftime('%d-%m-%Y')})", BOX_WIDTH, C_PRIMARY_BRIGHT, tc=C_INFO_BRIGHT)
            print_box_line(f"Formula Rate: {C_SUCCESS_BRIGHT}{top_formula_spec['rate']:.2f}% ({top_formula_spec['passes']}/{top_formula_spec['tests']})", BOX_WIDTH, C_PRIMARY_BRIGHT, tc=C_INFO_BRIGHT)
            print_box_sep(BOX_WIDTH, C_PRIMARY_BRIGHT)
            print_box_line(f"Suggested Anks: {C_WARNING_BRIGHT}{'   '.join(map(str, predicted_anks_for_tomorrow))}", BOX_WIDTH, C_PRIMARY_BRIGHT, tc=C_WARNING_BRIGHT, align="center")
            print_box_bottom(BOX_WIDTH, C_PRIMARY_BRIGHT)

            # Save the suggestion
            save_daily_suggestion(selected_market, prediction_for_date_str, top_formula_spec['name'], x_to_use, predicted_anks_for_tomorrow)

        except Exception as e: print(C_ERROR_BRIGHT + f"Error during prediction: {e}")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print(C_WARNING_BRIGHT + "\n\n[!] User interrupted." + C_RESET)
    except Exception as e:
        print(C_ERROR_BRIGHT + f"\n[!!!] Critical error: {e}")
        # import traceback; traceback.print_exc() 
        print(C_ERROR_BRIGHT + "      Please report." + C_RESET)
    finally: print(C_PRIMARY_BRIGHT + f"\n✨ Thank you for using {APP_NAME}! Good luck! ✨" + C_RESET)
