import ccavutil
import random
from config import LIVE_BINS

def gen_ccs(bin_type="visa", count=10):
    """Generate valid CC|MM/YY|CVV"""
    bin_prefix = LIVE_BINS.get(bin_type, LIVE_BINS["visa"])
    ccs = []
    for _ in range(count):
        full_cc = ccavutil.generate_luhn(bin_prefix)
        exp_month = random.randint(12, 60)
        exp_year = random.randint(25, 99)
        cvv = random.randint(100, 999)
        ccs.append(f"{full_cc}|{exp_month:02d}/{exp_year:02d}|{cvv:03d}")
    return ccs

def get_bin_info(cc_line):
    """BIN: 453201 (VISA)"""
    cc = cc_line.split("|")[0]
    bin6 = cc[:6]
    if cc.startswith("4"): ctype = "VISA"
    elif cc.startswith("5"): ctype = "MASTERCARD" 
    elif cc.startswith(("34", "37")): ctype = "AMEX"
    else: ctype = "UNKNOWN"
    return f"**BIN:** `{bin6}` **({ctype})**"