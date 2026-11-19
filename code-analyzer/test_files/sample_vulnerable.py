"""
Sample vulnerable Python module containing intentional security, bug, style,
and maintainability issues for static analysis engine verification.
"""

# Issue 1: Unused imports
import math
import sys
import sqlite3

# Issue 2: Hardcoded secrets
password = "SuperSecretAdminPassword123!"
api_key = "sk_live_abcdef1234567890xyz"


# Issue 3: Mutable default argument
def add_user(username: str, roles: list = []) -> list:
    roles.append(username)
    return roles


# Issue 4: Dynamic eval usage
def calculate_expression(expr: str):
    return eval(expr)


# Issue 5: Dynamic exec usage
def run_dynamic_code(code_str: str):
    exec(code_str)


# Issue 6: Bare except clause
def parse_record(data: str):
    try:
        val = int(data)
        return val
    except:
        return 0


# Issue 7: Comparison to None with ==
def check_status(status_code):
    if status_code == None:
        return "Unknown"
    return "Valid"


# Issue 8: SQL injection via string formatting
def query_user_account(cursor, user_id: str):
    query = "SELECT * FROM users WHERE id = '%s'" % user_id
    cursor.execute(query)
    return cursor.fetchall()


# Issue 9: Long function (exactly 55 lines)
def process_data_pipeline(records: list) -> dict:
    summary = {}
    total_processed = 0
    error_count = 0
    step_one_success = 0
    step_two_success = 0
    step_three_success = 0
    val_a = 1
    val_b = 2
    val_c = 3
    val_d = 4
    val_e = 5
    val_f = 6
    val_g = 7
    val_h = 8
    val_i = 9
    val_j = 10
    val_k = 11
    val_l = 12
    val_m = 13
    val_n = 14
    val_o = 15
    val_p = 16
    val_q = 17
    val_r = 18
    val_s = 19
    val_t = 20
    val_u = 21
    val_v = 22
    val_w = 23
    val_x = 24
    val_y = 25
    val_z = 26
    val_aa = 27
    val_bb = 28
    val_cc = 29
    val_dd = 30
    val_ee = 31
    val_ff = 32
    val_gg = 33
    val_hh = 34
    val_ii = 35
    val_jj = 36
    val_kk = 37
    val_ll = 38
    val_mm = 39
    val_nn = 40
    val_oo = 41
    val_pp = 42
    val_qq = 43
    val_rr = 44
    val_ss = 45
    val_tt = 46
    val_uu = 47
    summary["metric"] = total_processed
    return summary
