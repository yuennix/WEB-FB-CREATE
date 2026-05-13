import os
import sys
import re
import random
import string
import time
import json
import platform
import requests
import subprocess
from typing import Set, Optional
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from faker import Faker
import pyotp
import logging

import threading
import concurrent.futures
from os import path
from urllib.request import Request, urlopen

# Setup logging
logging.basicConfig(level=logging.INFO, filename="app.log", format="%(asctime)s - %(levelname)s - %(message)s")

# ANSI color codes
W  = '\033[97m'      # Bright white
G  = '\033[96m'      # Cyan  (primary accent)
R  = '\033[91m'      # Red   (errors / warnings)
M  = '\033[95m'      # Magenta (secondary accent)
Y  = '\033[93m'      # Yellow (numbers / highlights)
V  = '\033[95m'      # Magenta alias
B  = '\033[1;30m'    # Dark grey
DIM = '\033[2;37m'   # Dim grey
RESET = '\033[0m'    # Reset

# Initialize Faker and UserAgent
fake = Faker()
try:
    ua = UserAgent()
except Exception:
    ua = None



# File storage functions
def save_to_file(data: str, file_path: str):
    """Save data to file in plain text."""
    full_path = file_path
    os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
    with open(full_path, "a", encoding="utf-8") as f:
        f.write(data + "\n")

# Install dependencies
def install_dependencies():
    """Install required packages if not present."""
    try:
        import pyotp
    except ImportError:
        logging.warning("pyotp not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyotp"])
        except Exception as e:
            logging.error(f"Failed to install pyotp: {e}")
            print(f"{R}Failed to install pyotp: {e}{W}")
            sys.exit(1)

# Clear screen
def clear_screen():
    """Clear terminal screen based on platform."""
    os.system('cls' if platform.system().lower() == 'windows' else 'clear')

# Device information (for Android-specific properties)
try:
    android_version = subprocess.check_output('getprop ro.build.version.release', shell=True).decode('utf-8').strip()
    model = subprocess.check_output('getprop ro.product.model', shell=True).decode('utf-8').strip()
    build = subprocess.check_output('getprop ro.build.id', shell=True).decode('utf-8').strip()
    fbmf = subprocess.check_output('getprop ro.product.manufacturer', shell=True).decode('utf-8').strip()
    fbbd = subprocess.check_output('getprop ro.product.brand', shell=True).decode('utf-8').strip()
    fbca = subprocess.check_output('getprop ro.product.cpu.abilist', shell=True).decode('utf-8').replace(',', ':').strip()
    fbdm = f"{{density=2.25,height={subprocess.check_output('getprop ro.hwui.text_large_cache_height', shell=True).decode('utf-8').strip()},width={subprocess.check_output('getprop ro.hwui.text_large_cache_width', shell=True).decode('utf-8').strip()}}}"
    try:
        fbcr = subprocess.check_output('getprop gsm.operator.alpha', shell=True).decode('utf-8').split(',')[0].strip()
    except:
        fbcr = 'ZONG'
except:
    android_version, model, build, fbmf, fbbd, fbca, fbdm, fbcr = '10', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'arm64-v8a', '{density=2.25,height=720,width=1280}', 'ZONG'

device = {
    'android_version': android_version,
    'model': model,
    'build': build,
    'fblc': 'en_US',
    'fbmf': fbmf,
    'fbbd': fbbd,
    'fbdv': model,
    'fbsv': android_version,
    'fbca': fbca,
    'fbdm': fbdm
}


# User-Agent generation
try:
    ua = UserAgent()
except Exception:
    ua = None

_FALLBACK_UA = (
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Build/RP1A.200720.011; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
    "Chrome/109.0.5414.118 Mobile Safari/537.36"
)

def ugenX():
    try:
        if ua:
            ualist = [ua.random for _ in range(50)]
            return str(random.choice(ualist))
    except Exception:
        pass
    return _FALLBACK_UA

ugen=[]
for xd in range(10000):
        rr = random.randint
        build_b = random.choice(["001","002","003","011","012","014","015","020","021","022","023","024"])
        bl_typ = random.choice(["TKQ1","SKQ1","TP1A","RKQ1","SP1A","RP1A","PPR1","QP1A"])
        oppo = random.choice(["CPH2461","CPH2451","PCGM00","PBBM00","PFZM10","PGGM10","PECT30","PCHM10","PEAT00","PEYM00","PESM10","PFGM00"])
        infinix = random.choice(["Infinix X669C","Infinix X6823","Infinix X676C","Infinix X683","Infinix X689C","Infinix X6811","Infinix X612B","Infinix X6810","Infinix X665E"])
        redmi = random.choice(["2211133G","M2004J19C","22041219I","22101316UG","2209116AG","M2010J19SY","M2012K11C","Redmi Note 7","Redmi Note 8","Redmi Note 5"])
        um2 = f"Mozilla/5.0 (Linux; Android {str(rr(6,12))}; {oppo} Build/{bl_typ}.{str(rr(120000,220000))}.{build_b}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(rr(80,114))}.0.{str(rr(4200,5400))}.{str(rr(70,150))} Mobile Safari/537.36"
        um1 = f"Mozilla/5.0 (Linux; Android {str(rr(6,12))}; {redmi} Build/{bl_typ}.{str(rr(120000,220000))}.{build_b}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(rr(80,114))}.0.{str(rr(4200,5400))}.{str(rr(70,150))} Mobile Safari/537.36"
        um3 = f"Mozilla/5.0 (Linux; Android {str(rr(6,12))}; {infinix} Build/{bl_typ}.{str(rr(120000,220000))}.{build_b}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(rr(80,114))}.0.{str(rr(4200,5400))}.{str(rr(70,150))} Mobile Safari/537.36"
        um4 = f"Mozilla/5.0 (Linux; Android {str(rr(6,12))}; {infinix}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{str(rr(100,114))}.0.{str(rr(4900,5700))}.{str(rr(70,150))} Mobile Safari/537.36"
        ugen.append(um2)
        ugen.append(um3)
        ugen.append(um1)
        ugen.append(um4)
for xhd in range(1000):
        a = random.choice(['de-at','in-id','ms-my','uk-ua','en-us','en-gb','id-id','de-de','ru-ru','en-sg','fr-fr','fa-ir','ja-jp','pt-br','cs-cz','zh-hk','zh-cn','vi-vn','en-ph','en-in','tr-tr','en-au','th-th','hi-in','zh-tw','my-zg','en-nz','en-ca','es-mx','ko-kr','el-gr','en-ez','ar-ae','fr-ch','nl-nl','gu-in'])
        b = random.choice(['A','B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])
        c = random.choice(['A','B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])
        b2 = random.choice(['A','B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])
        c2 = random.choice(['A','B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'])
        d = f"Mozilla/5.0 (Linux; U; Android {str(random.randint(6,14))}; {a}; OPPO {b}{str(random.randint(10,99))}{c} Build/{b2}{str(random.randint(1,999))}{c2}) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(random.randint(75,117))}.0.{str(random.randint(2500,5900))}.{str(random.randint(80,200))} Mobile Safari/537.36 HeyTapBrowser/{str(random.randint(6,47))}.{str(random.randint(7,8))}.{str(random.randint(2,40))}.{str(random.randint(1,9))}"
        ugen.append(d)
for xd in range(1000):
   rr = random.randint; rc = random.choice
   aZ = str(rc(['A','B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']))
   lonte = f"{str(rc(aZ))}{str(rc(aZ))}{str(rc(aZ))}{str(rr(11,99))}{str(rc(aZ))}"
   build_nokiax = ['JDQ39','JZO54K']
   oppo = ["CPH1869", "CPH1929","CPH2107", "CPH2238", "CPH2389","CPH2401", "CPH2407", "CPH2413", "CPH2415", "CPH2417", "CPH2419", "CPH2455", "CPH2459", "CPH2461", "CPH2471", "CPH2473", "CPH2477", "CPH8893", "CPH2321", "CPH2341", "CPH2373", "CPH2083", "CPH2071", "CPH2077", "CPH2185", "CPH2179", "CPH2269", "CPH2421", "CPH2349", "CPH2271", "CPH1923", "CPH1925", "CPH1837", "CPH2015", "CPH2073", "CPH2081", "CPH2029", "CPH2031", "CPH2137", "CPH1605", "CPH1803", "CPH1853", "CPH1805", "CPH1809", "CPH1851", "CPH1931", "CPH1959", "CPH1933", "CPH1935", "CPH1943", "CPH2061", "CPH2069", "CPH2127", "CPH2131", "CPH2139", "CPH2135", "CPH2239", "CPH2195", "CPH2273", "CPH2325", "CPH2309", "CPH1701", "CPH2387", "CPH1909", "CPH1920", "CPH1912", "CPH1901", "CPH1903", "CPH1905", "CPH1717", "CPH1801", "CPH2067", "CPH2099", "CPH2161", "CPH2219", "CPH2197", "CPH2263", "CPH2375", "CPH2339", "CPH1715", "CPH2385", "CPH1729", "CPH1827", "CPH1938", "CPH1937", "CPH1939", "CPH1941", "CPH2001", "CPH2021", "CPH2059", "CPH2121", "CPH2123", "CPH2203", "CPH2333", "CPH2365", "CPH1913", "CPH1911", "CPH1915", "CPH1969", "CPH2209", "CPH1987", "CPH2095", "CPH2119", "CPH2285", "CPH2213", "CPH2223", "CPH2363", "CPH1609", "CPH1613", "CPH1723", "CPH1727", "CPH1725", "CPH1819", "CPH1821", "CPH1825", "CPH1881", "CPH1823", "CPH1871", "CPH1875", "CPH2023", "CPH2005", "CPH2025", "CPH2207", "CPH2173", "CPH2307", "CPH2305", "CPH2337", "CPH1955", "CPH1707", "CPH1719", "CPH1721", "CPH1835", "CPH1831", "CPH1833", "CPH1879", "CPH1893", "CPH1877", "CPH1607", "CPH1611", "CPH1917", "CPH1919", "CPH1907", "CPH1989", "CPH1945", "CPH1951", "CPH2043", "CPH2035", "CPH2037", "CPH2036", "CPH2009", "CPH2013", "CPH2113", "CPH2091", "CPH2125", "CPH2109", "CPH2089", "CPH2065", "CPH2159", "CPH2145", "CPH2205", "CPH2201", "CPH2199", "CPH2217", "CPH1921", "CPH2211", "CPH2235", "CPH2251", "CPH2249", "CPH2247", "CPH2237", "CPH2371", "CPH2293", "CPH2353", "CPH2343", "CPH2359", "CPH2357", "CPH2457", "CPH1983", "CPH1979"]
   redmi = ["2201116SI", "M2012K11AI", "22011119TI", "21091116UI", "M2102K1AC", "M2012K11I", "22041219I", "22041216I", "2203121C", "2106118C", "2201123G", "2203129G", "2201122G", "2201122C", "2206122SC", "22081212C", "2112123AG", "2112123AC", "2109119BC", "M2002J9G", "M2007J1SC", "M2007J17I", "M2102J2SC", "M2007J3SY", "M2007J17G", "M2007J3SG", "M2011K2G", "M2101K9AG ", "M2101K9R", "2109119DG", "M2101K9G", "2109119DI", "M2012K11G", "M2102K1G", "21081111RG", "2107113SG", "21051182G", "M2105K81AC", "M2105K81C", "21061119DG", "21121119SG", "22011119UY", "21061119AG", "21061119AL", "22041219NY", "22041219G", "21061119BI", "220233L2G", "220233L2I", "220333QNY", "220333QAG", "M2004J7AC", "M2004J7BC", "M2004J19C", "M2006C3MII", "M2010J19SI", "M2006C3LG", "M2006C3LVG", "M2006C3MG", "M2006C3MT", "M2006C3MNG", "M2006C3LII", "M2010J19SL", "M2010J19SG", "M2010J19SY", "M2012K11AC", "M2012K10C", "M2012K11C", "22021211RC"]
   realme =  ["RMX3516", "RMX3371", "RMX3461", "RMX3286", "RMX3561", "RMX3388", "RMX3311", "RMX3142", "RMX2071", "RMX1805", "RMX1809", "RMX1801", "RMX1807", "RMX1803", "RMX1825", "RMX1821", "RMX1822", "RMX1833", "RMX1851", "RMX1853", "RMX1827", "RMX1911", "RMX1919", "RMX1927", "RMX1971", "RMX1973", "RMX2030", "RMX2032", "RMX1925", "RMX1929", "RMX2001", "RMX2061", "RMX2063", "RMX2040", "RMX2042", "RMX2002", "RMX2151", "RMX2163", "RMX2155", "RMX2170", "RMX2103", "RMX3085", "RMX3241", "RMX3081", "RMX3151", "RMX3381", "RMX3521", "RMX3474", "RMX3471", "RMX3472", "RMX3392", "RMX3393", "RMX3491", "RMX1811", "RMX2185", "RMX3231", "RMX2189", "RMX2180", "RMX2195", "RMX2101", "RMX1941", "RMX1945", "RMX3063", "RMX3061", "RMX3201", "RMX3203", "RMX3261", "RMX3263", "RMX3193", "RMX3191", "RMX3195", "RMX3197", "RMX3265", "RMX3268", "RMX3269","RMX2027", "RMX2020","RMX2021", "RMX3581", "RMX3501", "RMX3503", "RMX3511", "RMX3310", "RMX3312", "RMX3551", "RMX3301", "RMX3300", "RMX2202", "RMX3363", "RMX3360", "RMX3366", "RMX3361", "RMX3031", "RMX3370", "RMX3357", "RMX3560", "RMX3562", "RMX3350", "RMX2193", "RMX2161", "RMX2050", "RMX2156", "RMX3242", "RMX3171", "RMX3430", "RMX3235", "RMX3506", "RMX2117", "RMX2173", "RMX3161", "RMX2205", "RMX3462", "RMX3478", "RMX3372", "RMX3574", "RMX1831", "RMX3121", "RMX3122", "RMX3125", "RMX3043", "RMX3042", "RMX3041", "RMX3092", "RMX3093", "RMX3571", "RMX3475", "RMX2200", "RMX2201", "RMX2111", "RMX2112", "RMX1901", "RMX1903", "RMX1992", "RMX1993", "RMX1991", "RMX1931", "RMX2142", "RMX2081", "RMX2085", "RMX2083", "RMX2086", "RMX2144", "RMX2051", "RMX2025", "RMX2075", "RMX2076", "RMX2072", "RMX2052", "RMX2176", "RMX2121", "RMX3115", "RMX1921"]
   infinix = ["X676B", "X687", "X609", "X697", "X680D", "X507", "X605", "X668", "X6815B", "X624", "X655F", "X689C", "X608", "X698", "X682B", "X682C", "X688C", "X688B", "X658E", "X659B", "X689B", "X689", "X689D", "X662", "X662B", "X675", "X6812B", "X6812", "X6817B", "X6817", "X6816C", "X6816", "X6816D", "X668C", "X665B", "X665E", "X510", "X559C", "X559F", "X559", "X606", "X606C", "X606D", "X623", "X624B", "X625C", "X625D", "X625B", "X650D", "X650B", "X650", "X650C", "X655C", "X655D", "X680B", "X573", "X573B", "X622", "X693", "X695C", "X695D", "X695", "X663B", "X663", "X670", "X671", "X671B", "X672", "X6819", "X572", "X572-LTE", "X571", "X604", "X610B", "X690", "X690B", "X656", "X692", "X683", "X450", "X5010", "X501", "X401", "X626", "X626B", "X652", "X652A", "X652B", "X652C", "X660B", "X660C", "X660", "X5515", "X5515F", "X5515I", "X609B", "X5514D", "X5516B", "X5516C", "X627", "X680", "X653", "X653C", "X657", "X657B", "X657C", "X6511B", "X6511E", "X6511", "X6512", "X6823C", "X612B", "X612", "X503", "X511", "X352", "X351", "X530", "X676C", "X6821", "X6823", "X6827", "X509", "X603", "X6815", "X620B", "X620", "X687B", "X6811B", "X6810", "X6811"]
   samsung = ["E025F", "G996B", "A826S", "E135F", "G781B", "G998B", "F936U1", "G361F", "A716S", "J327AZ", "E426B", "A015F", "A015M", "A013G", "A013G", "A013M", "A013F", "A022M", "A022G", "A022F", "A025M", "S124DL", "A025U", "A025A", "A025G", "A025F", "A025AZ", "A035F", "A035M", "A035G", "A032F", "A032M", "A032F", "A037F", "A037U", "A037M", "S134DL", "A037G", "A105G", "A105M", "A105F", "A105FN", "A102U", "S102DL", "A102U1", "A107F", "A107M", "A115AZ", "A115U", "A115U1", "A115A", "A115M", "A115F", "A125F", "A127F", "A125M", "A125U", "A127M", "A135F", "A137F", "A135M", "A136U", "A136U1", "A136W", "A260F", "A260G", "A260F", "A260G", "A205GN", "A205U", "A205F", "A205G", "A205FN", "A202F", "A2070", "A207F", "A207M", "A215U", "A215U1", "A217F", "A217F", "A217M", "A225F", "A225M", "A226B", "A226B", "A226BR", "A235F", "A235M", "A300FU", "A300F", "A300H", "A310F", "A310M", "A320FL", "A320F", "A305G", "A305GT", "A305N", "A305F", "A307FN", "A307G", "A307GN", "A315G", "A315F", "A325F", "A325M", "A326U", "A326W", "A336E", "A336B", "A430F", "A405FN", "A405FM", "A3051", "A3050", "A415F", "A426U", "A426B", "A5009", "A500YZ", "A500Y", "A500W", "A500L", "A500X", "A500XZ", "A510F", "A510Y", "A520F", "A520W", "A500F", "A500FU", "A500H", "S506DL", "A505G", "A505FN", "A505U", "A505GN", "A505F", "A507FN", "A5070", "A515F", "A515U", "A515U1", "A516U", "A516V", "A516N", "A516B", "A525F", "A525M", "A526U", "A526U1", "A526B", "A526W", "A528B", "A536B", "A536U", "A536E", "A536V", "A600FN", "A600G", "A605FN", "A605G", "A605GN", "A605F", "A6050", "A606Y", "A6060", "G6200", "A700FD", "A700F", "A7000", "A700H", "A700YD", "A710F", "A710M", "A720F", "A750F", "A750FN", "A750GN", "A705FN", "A705F", "A705MN", "A707F", "A715F", "A715W", "A716U", "A716V", "A716U1", "A716B", "A725F", "A725M", "A736B", "A530F", "A810YZ", "A810F", "A810S", "A530W", "A530N", "G885F", "G885Y", "G885S", "A730F", "A805F", "G887F", "G8870", "A9000", "A920F", "A920F", "G887N", "A910F", "G8850", "A908B", "A908N", "A9080", "G313HY", "G313MY", "G313MU", "G316M", "G316ML", "G316MY", "G313HZ", "G313H", "G313HU", "G313U", "G318H", "G357FZ","G310HN", "G357FZ", "G850F", "G850M", "J337AZ", "G386T1", "G386T", "G3858", "G3858", "A226L", "C5000", "C500X", "C5010", "C5018", "C7000", "C7010", "C701F", "C7018", "C7100", "C7108", "C9000", "C900F", "C900Y", "G355H", "G355M", "G3589W", "G386W", "G386F", "G3518", "G3586V", "G5108Q", "G5108", "G3568V", "G350E", "G350", "G3509I", "G3508J", "G3502I", "G3502C", "S820L", "G360H", "G360F", "G360T", "G360M", "G361H", "E500H", "E500F", "E500M", "E5000", "E500YZ", "E700H", "E700F", "E7009", "E700M", "G3815", "G3815", "G3815", "F127G", "E225F", "E236B", "F415F", "E5260", "E625F", "F900U", "F907N", "F900F", "F9000", "F907B", "F900W", "G150NL", "G155S", "G1650", "W2015", "G7102", "G7105", "G7106", "G7108", "G7202", "G720N0", "G7200", "G720AX", "G530T1", "G530H", "G530FZ", "G531H", "G530BT", "G532F", "G531BT", "G531M", "J727AZ", "J100FN", "J100H", "J120FN", "J120H", "J120F", "J120M", "J111M", "J111F", "J110H", "J110G", "J110F", "J110M", "J105H", "J105Y", "J105B", "J106H", "J106F", "J106B", "J106M", "J200F", "J200M", "J200G", "J200H", "J200F", "J200GU", "J260M", "J260F", "J260MU", "J260F", "J260G", "J200BT", "G532G", "G532M", "G532MT", "J250M", "J250F", "J210F", "J260AZ", "J3109", "J320A", "J320G", "J320F", "J320H", "J320FN", "J330G", "J330F", "J330FN", "J337V", "J337P", "J337A", "J337VPP", "J337R4", "J327VPP", "J327V", "J327P", "J327R4", "S327VL", "S337TL", "S367VL", "J327A", "J327T1", "J327T", "J3110", "J3119S", "J3119", "S320VL", "J337T", "J400M", "J400F", "J400F", "J410F", "J410G", "J410F", "J415FN", "J415F", "J415G", "J415GN", "J415N", "J500FN", "J500M", "J510MN", "J510FN", "J510GN", "J530Y", "J530F", "J530G", "J530FM", "G570M", "G570F", "G570Y", "J600G", "J600FN", "J600GT", "J600F", "J610F", "J610G", "J610FN", "J710F", "J700H", "J700M", "J700F", "J700P", "J700T", "J710GN", "J700T1", "J727A", "J727R4", "J737T", "J737A", "J737R4", "J737V", "J737T1", "J737S", "J737P", "J737VPP", "J701F", "J701M", "J701MT", "S767VL", "S757BL", "J720F", "J720M", "G615F", "G615FU", "G610F", "G610M", "G610Y", "G611MT", "G611FF", "G611M", "J730G", "J730GM", "J730F", "J730FM", "S727VL", "S737TL", "J727T1", "J727T1", "J727V", "J727P", "J727VPP", "J727T", "C710F", "J810M", "J810F", "J810G", "J810Y", "A605K", "A605K", "A202K", "M336K", "A326K", "C115", "C115L", "C1158", "C1158", "C115W", "C115M", "S120VL", "M015G", "M015F", "M013F", "M017F", "M022G", "M022F", "M022M", "M025F", "M105G", "M105M", "M105F", "M107F", "M115F", "M115F", "M127F", "M127G", "M135M", "M135F", "M135FU", "M205FN", "M205F", "M205G", "M215F", "M215G", "M225FV", "M236B", "M236Q", "M305F", "M305M", "M307F", "M307FN", "M315F", "M317F", "M325FV", "M325F", "M326B", "M336B", "M336BU", "M405F", "M426B", "M515F", "M526BR", "M526B", "M536B", "M625F", "G750H", "G7508Q", "G7509", "N970U", "N970F", "N971N", "N970U1", "N770F", "N975U1", "N975U", "N975F", "N975F", "N976N", "N980F", "N981U", "N981B", "N985F", "N9860", "N986N", "N986U", "N986B", "N986W", "N9008V", "N9006", "N900A", "N9005", "N900W8", "N900", "N9009", "N900P", "N9000Q", "N9002", "9005", "N750L", "N7505", "N750", "N7502", "N910F", "N910V", "N910C", "N910U", "N910H", "N9108V", "N9100", "N915FY", "N9150", "N915T", "N915G", "N915A", "N915F", "N915S", "N915D", "N915W8", "N916S", "N916K", "N916L", "N916LSK", "N920L", "N920S", "N920G", "N920A", "N920C", "N920V", "N920I", "N920K", "N9208", "N930F", "N9300", "N930x", "N930P", "N930X", "N930W8", "N930V", "N930T", "N950U", "N950F", "N950N", "N960U", "N960F", "N960U", "N935F", "N935K", "N935S", "G550T", "G550FY", "G5500", "G5510", "G550T1", "S550TL", "G5520", "G5528", "G600FY", "G600F", "G6000", "G6100", "G610S", "G611F", "G611L", "G110M", "G110H", "G110B", "G910S", "G316HU", "G977N", "G973U1", "G973F", "G973W", "G973U", "G770U1", "G770F", "G975F", "G975U", "G970U", "G970U1", "G970F", "G970N", "G980F", "G981U", "G981N", "G981B", "G780G", "G780F", "G781W", "G781U", "G7810", "G9880", "G988B", "G988U", "G988B", "G988U1", "G985F", "G986U", "G986B", "G986W", "G986U1", "G991U", "G991B", "G990B", "G990E", "G990U", "G998U", "G996W", "G996U", "G996N", "G9960", "S901U", "S901B", "S908U", "S908U1", "S908B","S9080", "S908N", "S908E", "S906U", "S906E", "S906N", "S906B", "S906U1", "G730V", "G730A", "G730W8", "C105L", "C101", "C105", "C105K", "C105S", "G900F", "G900P", "G900H", "G9006V", "G900M", "G900V", "G870W", "G890A", "G870A", "G900FD", "G860P", "G901F", "G901F", "G800F", "G800H", "G903F", "G903W", "G920F", "G920K", "G920I", "G920A", "G920P", "G920S", "G920V", "G920T", "G925F", "G925A", "G925W8", "G928F", "G928C", "G9280", "G9287", "G928T", "G928I", "G930A", "G930F", "G930W8", "G930S", "G930V", "G930P", "G930L", "G891A", "G935F", "G935T", "G935W8", "G9350", "G950F", "G950W", "G950U", "G892A", "G892U", "G8750", "G955F", "G955U", "G955U1", "G955W", "G955N", "G960U", "G960U1", "G960F", "G965U", "G965F", "G965U1", "G965N", "G9650", "J321AZ", "J326AZ", "J336AZ", "T116", "T116NU", "T116NY", "T116NQ", "T2519", "G318HZ", "T255S", "W2016", "W2018", "W2019", "W2021", "W2022", "G600S", "E426S", "G3812", "G3812B", "G3818", "G388F", "G389F", "G390F", "G398FN"]
   gt = ['GT-1015','GT-1020','GT-1030','GT-1035','GT-1040','GT-1045','GT-1050','GT-1240','GT-1440','GT-1450','GT-18190','GT-18262','GT-19060I','GT-19082','GT-19083','GT-19105','GT-19152','GT-19192','GT-19300','GT-19505','GT-2000','GT-20000','GT-200s','GT-3000','GT-414XOP','GT-6918','GT-7010','GT-7020','GT-7030','GT-7040','GT-7050','GT-7100','GT-7105','GT-7110','GT-7205','GT-7210','GT-7240R','GT-7245','GT-7303','GT-7310','GT-7320','GT-7325','GT-7326','GT-7340','GT-7405','GT-7550 5GT-8005','GT-8010','GT-81','GT-810','GT-8105','GT-8110','GT-8220S','GT-8410','GT-9300','GT-9320','GT-93G','GT-A7100','GT-A9500','GT-ANDROID','GT-B2710','GT-B5330','GT-B5330B','GT-B5330L','GT-B5330ZKAINU','GT-B5510','GT-B5512','GT-B5722','GT-B7510','GT-B7722','GT-B7810','GT-B9150','GT-B9388','GT-C3010','GT-C3262','GT-C3310R','GT-C3312','GT-C3312R','GT-C3313T','GT-C3322','GT-C3322i','GT-C3520','GT-C3520I','GT-C3592','GT-C3595','GT-C3782','GT-C6712','GT-E1282T','GT-E1500','GT-E2200','GT-E2202','GT-E2250','GT-E2252','GT-E2600','GT-E2652W','GT-E3210','GT-E3309','GT-E3309I','GT-E3309T','GT-G530H','GT-g900f','GT-G930F','GT-H9500','GT-I5508','GT-I5801','GT-I6410','GT-I8150','GT-I8160OKLTPA','GT-I8160ZWLTTT','GT-I8258','GT-I8262D','GT-I8268','GT-I8505','GT-I8530BAABTU','GT-I8530BALCHO','GT-I8530BALTTT','GT-I8550E','GT-i8700','GT-I8750','GT-I900','GT-I9008L','GT-i9040','GT-I9080E','GT-I9082C','GT-I9082EWAINU','GT-I9082i','GT-I9100G','GT-I9100LKLCHT','GT-I9100M','GT-I9100P','GT-I9100T','GT-I9105UANDBT','GT-I9128E','GT-I9128I','GT-I9128V','GT-I9158P','GT-I9158V','GT-I9168I','GT-I9192I','GT-I9195H','GT-I9195L','GT-I9250','GT-I9303I','GT-I9305N','GT-I9308I','GT-I9505G','GT-I9505X','GT-I9507V','GT-I9600','GT-m190','GT-M5650','GT-mini','GT-N5000S','GT-N5100','GT-N5105','GT-N5110','GT-N5120','GT-N7000B','GT-N7005','GT-N7100T','GT-N7102','GT-N7105','GT-N7105T','GT-N7108','GT-N7108D','GT-N8000','GT-N8005','GT-N8010','GT-N8020','GT-N9000','GT-N9505','GT-P1000CWAXSA','GT-P1000M','GT-P1000T','GT-P1010','GT-P3100B','GT-P3105','GT-P3108','GT-P3110','GT-P5100','GT-P5200','GT-P5210XD1','GT-P5220','GT-P6200','GT-P6200L','GT-P6201','GT-P6210','GT-P6211','GT-P6800','GT-P7100','GT-P7300','GT-P7300B','GT-P7310','GT-P7320','GT-P7500D','GT-P7500M','GT-P7500R','GT-P7500V','GT-P7501','GT-P7511','GT-S3330','GT-S3332','GT-S3333','GT-S3370','GT-S3518','GT-S3570','GT-S3600i','GT-S3650','GT-S3653W','GT-S3770K','GT-S3770M','GT-S3800W','GT-S3802','GT-S3850','GT-S5220','GT-S5220R','GT-S5222','GT-S5230','GT-S5230W','GT-S5233T','GT-s5233w','GT-S5250','GT-S5253','GT-s5260','GT-S5280','GT-S5282','GT-S5283B','GT-S5292','GT-S5300','GT-S5300L','GT-S5301','GT-S5301B','GT-S5301L','GT-S5302','GT-S5302B','GT-S5303','GT-S5303B','GT-S5310','GT-S5310B','GT-S5310C','GT-S5310E','GT-S5310G','GT-S5310I','GT-S5310L','GT-S5310M','GT-S5310N','GT-S5312','GT-S5312B','GT-S5312C','GT-S5312L','GT-S5330','GT-S5360','GT-S5360B','GT-S5360L','GT-S5360T','GT-S5363','GT-S5367','GT-S5369','GT-S5380','GT-S5380D','GT-S5500','GT-S5560','GT-S5560i','GT-S5570B','GT-S5570I','GT-S5570L','GT-S5578','GT-S5600','GT-S5603','GT-S5610','GT-S5610K','GT-S5611','GT-S5620','G-S5670','GT-S5670B','GT-S5670HKBZTA','GT-S5690','GT-S5690R','GT-S5830','GT-S5830D','GT-S5830G','GT-S5830i','GT-S5830L','GT-S5830M','GT-S5830T','GT-S5830V','GT-S5831i','GT-S5838','GT-S5839i','GT-S6010','GT-S6010BBABTU','GT-S6012','GT-S6012B','GT-S6102','GT-S6102B','GT-S6293T','GT-S6310B','GT-S6310ZWAMID','GT-S6312','GT-S6313T','GT-S6352','GT-S6500','GT-S6500D','GT-S6500L','GT-S6790','GT-S6790L','GT-S6790N','GT-S6792L','GT-S6800','GT-S6800HKAXFA','GT-S6802','GT-S6810','GT-S6810B','GT-S6810E','GT-S6810L','GT-S6810M','GT-S6810MBASER','GT-S6810P','GT-S6812','GT-S6812B','GT-S6812C','GT-S6812i','GT-S6818','GT-S6818V','GT-S7230E','GT-S7233E','GT-S7250D','GT-S7262','GT-S7270','GT-S7270L','GT-S7272','GT-S7272C','GT-S7273T','GT-S7278','GT-S7278U','GT-S7390','GT-S7390G','GT-S7390L','GT-S7392','GT-S7392L','GT-S7500','GT-S7500ABABTU','GT-S7500ABADBT','GT-S7500ABTTLP','GT-S7500CWADBT','GT-S7500L','GT-S7500T','GT-S7560','GT-S7560M','GT-S7562','GT-S7562C','GT-S7562i','GT-S7562L','GT-S7566','GT-S7568','GT-S7568I','GT-S7572','GT-S7580E','GT-S7583T','GT-S758X','GT-S7592','GT-S7710','GT-S7710L','GT-S7898','GT-S7898I','GT-S8500','GT-S8530','GT-S8600','GT-STB919','GT-T140','GT-T150','GT-V8a','GT-V8i','GT-VC818','GT-VM919S','GT-W131','GT-W153','GT-X831','GT-X853','GT-X870','GT-X890','GT-Y8750']  
   strvoppo = f"Mozilla/5.0 (Linux; Android {str(rr(1,11))}; {str(rc(oppo))} Build/{str(rc(lonte))}) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(rr(10,107))}.0.{str(rr(111,6666))}.{str(rr(10,400))} UCBrowser/{str(rr(1,20))}.{str(rr(1,10))}.0.{str(rr(111,5555))} Mobile Safari/537.36 OPR/{str(rr(10,80))}.{str(rr(1,10))}.{str(rr(111,5555))}.{str(rr(111,99999))}"
   strvredmi = f"Mozilla/5.0 (Linux; Android {str(rr(1,11))}; {str(rc(redmi))}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{str(rr(10,107))}.0.{str(rr(111,6666))}.{str(rr(10,400))} Mobile Safari/537.36"
   strvoppo1 = f"Mozilla/5.0 (Linux; Android {str(rr(1,11))}; {str(rc(oppo))}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{str(rr(10,107))}.0.{str(rr(111,6666))}.{str(rr(10,400))} Mobile Safari/537.36"
   strvinfinix = f"Mozilla/5.0 (Linux; Android {str(rr(1,11))}; Infinix {str(rc(infinix))}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{str(rr(10,107))}.0.{str(rr(111,6666))}.{str(rr(10,400))} Mobile Safari/537.36"
   strvsamsung = f"Mozilla/5.0 (Linux; Android {str(rr(1,11))}; {str(rc(samsung))}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{str(rr(10,107))}.0.{str(rr(111,6666))}.{str(rr(10,400))} Mobile Safari/537.36"
   strvredmi1 = f"Mozilla/5.0 (Linux; Android {str(rr(1,11))}; {str(rc(redmi))} Build/{str(rc(lonte))}) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(rr(10,107))}.0.{str(rr(111,6666))}.{str(rr(10,400))} UCBrowser/{str(rr(1,20))}.{str(rr(1,10))}.0.{str(rr(111,5555))} Mobile Safari/537.36 OPR/{str(rr(10,80))}.{str(rr(1,10))}.{str(rr(111,5555))}.{str(rr(111,99999))}"
   strvnokiax = f"Mozilla/5.0 (Linux; Android 4.1.2; Nokia_X Build/{str(rc(build_nokiax))}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{str(rr(100,104))}.0.{str(rr(3900,4900))}.{str(rr(40,150))} Mobile Safari/537.36 NokiaBrowser/7.{str(rr(1,5))}.1.{str(rr(16,37))} {str(rc(aZ))}{str(rr(1,1000))}"
   strvgt = f"Mozilla/5.0 (Linux; Android {str(rr(4,12))}; {str(rc(gt))}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{str(rr(100,104))}.0.{str(rr(3900,4900))}.{str(rr(40,150))} Mobile Safari/537.36 {str(rc(aZ))}{str(rr(1,1000))}"
   ugen.append(strvoppo)
   ugen.append(strvredmi)
   ugen.append(strvoppo1)
   ugen.append(strvinfinix)
   ugen.append(strvsamsung)
   ugen.append(strvredmi1)
   ugen.append(strvnokiax)
   ugen.append(strvgt) 
for op in range(1000):
        rr = random.randint
        rc = random.choice
        bahasa = random.choice(["en","fr","ru","tr","id","pt","es","en-GB"])
        ua1 = f"Opera/9.80 (BlackBerry; Opera Mini/8.0.{str(rr(35000, 39000))}/{str(rr(190, 199))}.{str(rr(270, 290))}; U; {bahasa}) Presto/2.{str(rr(4, 20))}.{str(rr(420, 490))} Version/12.16"
        ua2 = f"SAMSUNG-GT-S3802 Opera/9.80 (J2ME/MIDP; Opera Mini/7.1.{str(rr(35000, 39000))}/{str(rr(190, 199))}.{str(rr(270, 290))}; U; {bahasa}) Presto/2.{str(rr(4, 20))}.{str(rr(420, 490))} Version/12.16"
        ua3 = f"Opera/9.80 (iPhone; Opera Mini/16.0.{str(rr(35000, 39000))}/{str(rr(190, 199))}.{str(rr(270, 290))}; U; {bahasa}) Presto/2.{str(rr(4, 20))}.{str(rr(420, 490))} Version/12.16"
        ua4 = f"Opera/9.80 (Android; Opera Mini/11.0.{str(rr(35000, 39000))}/{str(rr(190, 199))}.{str(rr(270, 290))}; U; {bahasa}) Presto/2.{str(rr(4, 20))}.{str(rr(420, 490))} Version/12.16"
        ua5 = f"Opera/9.80 (Windows Mobile; Opera Mini/5.1.{str(rr(35000, 39000))}/{str(rr(190, 199))}.{str(rr(270, 290))}; U; {bahasa}) Presto/2.{str(rr(4, 20))}.{str(rr(420, 490))} Version/12.16"
        ugen.append(ua1)
        ugen.append(ua2)
        ugen.append(ua3)
        ugen.append(ua4)
        ugen.append(ua5)
for generate in range(100):
        a=random.randrange(1, 9)
        b=random.randrange(1, 9)
        c=random.randrange(7, 13)
        c=random.randrange(73,100)
        d=random.randrange(4200,4900)
        e=random.randrange(40,150)
        uaku=f'Mozilla/5.0 (Linux; Android {a}.{b}; Pixel {b}) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{c}.0.{d}.{e} Mobile Safari/537.36'
        ugen.append(uaku)


# Name and password generation
first_names_male = [
'Juan', 'Jose', 'Miguel', 'Gabriel', 'Rafael', 'Antonio', 'Carlos', 'Luis',
'Marco', 'Paolo', 'Angelo', 'Joshua', 'Christian', 'Mark', 'John', 'James',
'Daniel', 'David', 'Michael', 'Jayson', 'Kenneth', 'Ryan', 'Kevin', 'Neil',
'Jerome', 'Renzo', 'Carlo', 'Andres', 'Felipe', 'Diego', 'Mateo', 'Lucas',
'Adrian', 'Albert', 'Aldrin', 'Alfred', 'Allen', 'Alonzo', 'Amiel',
'Andre', 'Andrew', 'Angelo', 'Anton', 'Arden', 'Aries', 'Arman', 'Arnel',
'Arnold', 'Arthur', 'August', 'Avery', 'Benito', 'Benjamin', 'Bernard',
'Blake', 'Bryan', 'Bryant', 'Caleb', 'Cameron', 'Cedric', 'Cesar',
'Charles', 'Christianne', 'Clarence', 'Clark', 'Clint', 'Clyde', 'Colin',
'Conrad', 'Crispin', 'Cyril', 'Damian', 'Darrel', 'Daryl', 'Darren',
'Dean', 'Denver', 'Derrick', 'Dexter', 'Dominic', 'Dylan', 'Earl', 'Edgar',
'Edison', 'Edward', 'Edwin', 'Eli', 'Elias', 'Elijah', 'Emil', 'Emmanuel',
'Eric', 'Ernest', 'Eron', 'Ethan', 'Eugene', 'Ferdinand', 'Francis',
'Frank', 'Fred', 'Frederick', 'Galen', 'Garry', 'Genesis', 'Geo', 'Gerald',
'Gilbert', 'Giovanni', 'Greg', 'Gregory', 'Hans', 'Harold', 'Henry',
'Hugh', 'Ian', 'Irvin', 'Isaac', 'Ivan', 'Jake', 'Jared',
'Jarred', 'Jason', 'Jasper', 'Jay', 'Jayden', 'Jerald', 'Jericho',
'Jethro', 'Jimmy', 'Joel', 'Jonas', 'Jonathan', 'Jordan', 'Joseph',
'Julius', 'Justin', 'Karl', 'Kayden', 'Keith', 'Kelvin', 'Kiel', 'King',
'Kirk', 'Kyle', 'Lance', 'Larry', 'Lawrence', 'Leandro', 'Leo', 'Leonard',
'Levi', 'Liam', 'Lorenzo', 'Louie', 'Lucas', 'Lucio', 'Luisito', 'Macario',
'Malcolm', 'Marcus', 'Mario', 'Martin', 'Marvin', 'Matthew', 'Max',
'Melvin', 'Mico', 'Miguelito', 'Milan', 'Mitch', 'Nathan', 'Nathaniel',
'Neilson', 'Nelson', 'Nicholas', 'Nico', 'Noel', 'Norman', 'Oliver',
'Oscar', 'Owen', 'Patrick', 'Paulo', 'Peter', 'Philip', 'Pierre', 'Ralph',
'Randall', 'Raymond', 'Reagan', 'Reggie', 'Rein', 'Reiner', 'Ricardo',
'Rico', 'Riel', 'Robbie', 'Robert', 'Rodney', 'Roldan', 'Romeo', 'Ronald',
'Rowell', 'Russell', 'Ryanne', 'Sam', 'Samuel', 'Santino', 'Sean', 'Seth',
'Shawn', 'Simon', 'Stephen', 'Steven', 'Taylor', 'Terrence', 'Theo',
'Timothy', 'Tomas', 'Tristan', 'Troy', 'Tyler', 'Vernon', 'Victor',
'Vincent', 'Virgil', 'Warren', 'Wayne', 'Wilfred', 'William', 'Winston',
'Wyatt', 'Xander', 'Zachary', 'Zion', 'Arvin', 'Dion', 'Harvey', 'Irvin',
'Jeriel', 'Kennard', 'Levin', 'Randel', 'Ramil', 'Rendon', 'Rome', 'Roven',
'Silas', 'Tobias', 'Uriel', 'Zandro', 'Axl', 'Brysen', 'Ced', 'Clarkson',
'Deo', 'Eion', 'Errol', 'Franco', 'Gavin', 'Hansel', 'Isidro', 'Jiro',
'Kiel', 'Loren', 'Matteo', 'Noelito', 'Omar', 'Paxton', 'Quinn', 'Ramon',
'Renz', 'Sandy', 'Tyrone', 'Ulrich', 'Vince', 'Wesley', 'Yvan', 'Zed',
'Alric', 'Brent', 'Caden', 'Dionel', 'Ethaniel', 'Fritz', 'Gerson',
'Hansley', 'Ivar', 'Jeric', 'Kenzo', 'Lex', 'Morris', 'Nate', 'Orville',
'Pio', 'Quentin', 'Rydel', 'Sergio', 'Tobit', 'Ulysses', 'Val', 'Wade',
'Yohan', 'Zyren', 'Adley', 'Cairo', 'Drey', 'Enzo', 'Ferris', 'Gale',
'Hector', 'Iven', 'Jaycee', 'Kaleb', 'Lyndon', 'Macky', 'Nash', 'Oren',
'Pierce', 'Quino', 'Rustin', 'Sylvio', 'Tanner', 'Ulian', 'Vaughn',
'Weston', 'Xeno', 'Yuri', 'Zandro', 'Andro', 'Basil', 'Crisanto', 'Derris',
'Efrain', 'Florenz', 'Gael', 'Hanz', 'Ismael', 'Jeromey', 'Kielan',
'Lucian', 'Marlo', 'Nerio', 'Osric', 'Patrik', 'Rion', 'Santino', 'Timo',
'Vin', 'Wilmer', 'Zaim', 'Zen', 'Gabriel', 'Joshua', 'John', 'Mark', 'James', 'Daniel', 'Matthew', 'Miguel', 'Nathan', 'David',
'Andrew', 'Joseph', 'Christian', 'Emmanuel', 'Adrian', 'Angelo', 'Carl', 'Marco', 'Kenneth', 'Ryan',
'Justin', 'Patrick', 'Paul', 'Francis', 'Anthony', 'Carlos', 'Rafael', 'Samuel', 'Sebastian', 'Elijah',
'Aiden', 'Brent', 'Cedric', 'Darren', 'Ethan', 'Felix',
'Gavin', 'Harold', 'Ian', 'Jacob', 'Kyle', 'Lance',
'Mason', 'Noel', 'Oscar', 'Preston', 'Quentin', 'Riley',
'Steven', 'Tristan', 'Ulysses', 'Vernon', 'Warren', 'Xander',
'Yves', 'Zachary', 'Aaron', 'Benjo', 'Calvin', 'Damien',
'Edward', 'Francis', 'Gerald', 'Harvey', 'Irvin', 'Jasper',
'Kevin', 'Lloyd', 'Marco', 'Nathaniel', 'Owen', 'Patrick',
'Ramon', 'Simon', 'Trevor', 'Vincent', 'Wilfred', 'Zion',
'Alfred', 'Bryan', 'Clarence', 'Daryl', 'Emil', 'Franco',
'Gilbert', 'Henry', 'Isaac', 'Jerome', 'Kristoffer', 'Leandro',
'Mario', 'Noah', 'Paolo', 'Rey', 'Santino', 'Troy',
'Vince', 'Wayne', 'Xian', 'Yohan', 'Zayne', 'Adonis',
'Brandon', 'Cyrus', 'Dominic', 'Enzo', 'Frederick', 'Gideon',
'Hanz', 'Jett', 'Kenzo', 'Luciano', 'Matteo',
'Nico', 'Orion', 'Pierce', 'Rafael', 'Stefan', 'Tobias',
'Valentin', 'Weston', 'Xavi', 'Yasser', 'Zedrick', 'Alonzo',
'Bryce', 'Coby', 'Dexter', 'Eli', 'Finn', 'Gael',
'Hector', 'Ismael', 'Joaquin', 'Keith', 'Lawrence', 'Maverick',
'Nash', 'Oliver', 'Pio', 'Reuben', 'Seth', 'Travis',
'Vaughn', 'Wyatt', 'Yuri', 'Zoren', 'Andrei', 'Benedict',
'Carlo', 'Denver', 'Earl', 'Franz', 'Giovanni', 'Hans',
'Ian', 'Julian', 'Kirk', 'Leo', 'Myles', 'Neo',
'Orlando', 'Philip', 'Rico', 'Sean', 'Thaddeus', 'Vito',
'Wendell', 'Yohan', 'Zayden', 'Adrianne', 'Blaine', 'Cliff',
'Dean', 'Elmer', 'Floyd', 'Gino', 'Hubert', 'Ivan',
'Jonas', 'Kyleen', 'Lemuel', 'Marlon', 'Nolan', 'Omar',
'Patrik', 'Rustin', 'Silas', 'Trent', 'Ulrich', 'Vern',
'Wesley', 'Yancy', 'Zaldy', 'Alaric', 'Blake', 'Chester',
'Dominique', 'Eros', 'Francois', 'Gerry', 'Holden', 'Ira',
'Jules', 'Kean', 'Luther', 'Mackenzie', 'Othello',
'Pax', 'Romeo', 'Samson', 'Tanner', 'Vince', 'Wylie',
'Yago', 'Zionel', 'Alec', 'Ben', 'Dion',
'Emerson', 'Fritz', 'Gareth', 'Hunter', 'Isidro', 'Jairo',
'Kale', 'Levi', 'Miles', 'Oren', 'Paxton',
'Ryder', 'Shawn', 'Theo', 'Urian', 'Victor', 'Wilmer',
'Yosef', 'Zain', 'Alvin', 'Brando', 'Clint', 'Dale',
'Everett', 'Fredrick', 'Garry', 'Howard', 'Isaias', 'Jansen',
'Kaleb', 'Lorenzo', 'Markus', 'Nicko', 'Owen', 'Parker',
'Raymond', 'Shane', 'Tyrone', 'Vince', 'Winston', 'Yusef',
'Zyler', 'Aron', 'Benedicto', 'Chris', 'Dariel', 'Eagan',
'Felipe', 'George', 'Hayden', 'Ivor', 'Justin', 'Kenrick',
'Lian', 'Mack', 'Nolan', 'Osric', 'Pio', 'Ramil',
'Sherwin', 'Tadeo', 'Vaughn', 'Wilbur', 'Yvan', 'Zarek',
'Albie', 'Briggs', 'Casper', 'Damon', 'Eliot', 'Farley',
'Garth', 'Hansel', 'Jayden', 'Kristian', 'Logan',
'Matias', 'Nixon', 'Orin', 'Paulo', 'Reagan', 'Soren',
'Trevin', 'Vernon', 'Wyatt', 'Yul', 'Zebedee', 'Alexei',
'Brock', 'Claudio', 'Derrick', 'Elijah', 'Fidel', 'Gavin',
'Hershel', 'Ismael', 'Jovan', 'Kieran', 'Lucian', 'Marvin',
'Nico', 'Ollie', 'Pablo', 'Roderick', 'Simeon', 'Terrence',
'Uriel', 'Virgil', 'Wayne', 'Yoshua', 'Zain', 'Aries',
'Bruno', 'Caden', 'Darwin', 'Ephraim', 'Finnley', 'Gomer',
'Harry', 'Indie', 'Jesse', 'Keaton', 'Lazaro', 'Mordecai',
'Nero', 'Orvin', 'Presley', 'Rufus', 'Stanley', 'Tomas',
'Uri', 'Vito', 'West', 'Yasir', 'Zev', 'Alton',
'Bernard', 'Carter', 'Dionisio', 'Edison', 'Fernando', 'Gabe',
'Hugh', 'Immanuel', 'Joel', 'Kristoff', 'Lucio', 'Mikel',
'Nevin', 'Osmond', 'Paulino', 'Rico', 'Stewart', 'Trent',
'Ulysses', 'Vince', 'Wylder', 'Yunus', 'Zarek', 'Abel',
'Benson', 'Claudio', 'Dennis', 'Ezekiel', 'Francis', 'Gavin',
'Harlan', 'Ivan', 'Jericho', 'Kendrick', 'Lars', 'Mathew',
'Nestor', 'Octavio', 'Perry', 'Rogelio', 'Sandy', 'Tyrone',
'Ulises', 'Vern', 'Wendel', 'Yves', 'Zac', 'Albert',
'Blair', 'Cruz', 'Dionel', 'Elvin', 'Fabian', 'Giancarlo',
'Hanzel', 'Iago', 'Jon', 'Kyle', 'Leif', 'Marcelo',
'Nigel', 'Orwell', 'Pierce', 'Roldan', 'Sage', 'Truman',
'Urbano', 'Vance', 'Wes', 'Yuki', 'Zandro', 'Amiel',
'Bert', 'Colin', 'Daryl', 'Erwin', 'Francisco', 'Geoff',
'Harris', 'Ian', 'Jayvee', 'Kristo', 'Logen', 'Manny',
'Nuel', 'Olan', 'Pablo', 'Riel', 'Simeon', 'Thane',
'Umar', 'Val', 'Wyler', 'Yarden', 'Zeke', 'Anton',
'Bryce', 'Caden', 'Devon', 'Eman', 'Fritz', 'Garry',
'Henri', 'Isagani', 'Jiro', 'Kael', 'Lauro', 'Mackie',
'Nash', 'Ogie', 'Pax', 'Roi', 'Stefano', 'Troy',
'Uno', 'Vaughn', 'Wayne', 'Yasir', 'Zaniel', 'Armand',
'Blas', 'Corbin', 'Dindo', 'Edric', 'Fermin', 'Gerry',
'Hendrick', 'Isidore', 'Jemuel', 'Kurt', 'Lemuel', 'Maurice',
'Natan', 'Olan', 'Paulo', 'Renz', 'Sandy', 'Tobit',
'Uriel', 'Vito', 'Weston', 'Yuri', 'Zander', 'Ariel',
'Benny', 'Carmelo', 'Darel', 'Earl', 'Flint', 'Gian',
'Henley', 'Jeff', 'Kiko', 'Louie', 'Marlon',
'Nash', 'Orion', 'Pietro', 'Rico', 'Stevan', 'Tomas',
'Ulric', 'Vernon', 'Wyatt', 'Yeshua', 'Zeb', 'Axel',
'Berto', 'Clyde', 'Darrel', 'Ely', 'Fredo', 'Gelo',
'Hector', 'Irving', 'Jomar', 'Ken', 'Lenny', 'Mico', 'Nashon', 'Owen', 'Pietro', 'Randel', 'Sergio', 'Tristan',
'Uziel', 'Vaughn', 'Warren', 'Yvan', 'Zain', 'Alaric',
'Briggs', 'Cyril', 'Drew', 'Evan', 'Floyd', 'Gareth',
'Hiro', 'Ismael', 'Jaden', 'Kurtis', 'Leandro', 'Miguelito',
'Nolan', 'Osmar', 'Paxton', 'Ronan', 'Soren', 'Trey',
'Ulises', 'Vann', 'Wilbert', 'Yuri', 'Zandro', 'Aiden',
'Brando', 'Carter', 'Dustin', 'Elian', 'Fermin', 'Gavin',
'Hudson', 'Isagani', 'Jonel', 'Kasey', 'Lyle', 'Marlon',
'Noel', 'Omar', 'Preston', 'Rufino', 'Santino', 'Toby',
'Uri', 'Val', 'Wade', 'Yeshua', 'Zed', 'Alvin',
'Bryant', 'Colby', 'Dante', 'Eliot', 'Franco', 'Gideon',
'Hershel', 'Isaiah', 'Jasper', 'Kenric', 'Luther', 'Marcus',
'Nathaniel', 'Orvin', 'Pio', 'Rodel', 'Simeon', 'Tanner',
'Urbano', 'Victor', 'Wyatt', 'Yancey', 'Zavier', 'Arnold',
'Blake', 'Chester', 'Diego', 'Evan', 'Felipe', 'Grayson',
'Hendrick', 'Ian', 'Jiro', 'Karlo', 'Luis', 'Matthias',
'Nestor', 'Odie', 'Paco', 'Ronaldo', 'Salvador', 'Tyrone',
'Ulric', 'Vincent', 'Wendell', 'Yusef', 'Zeke', 'Anderson',
'Bruce', 'Clark', 'Davin', 'Eugene', 'Felix', 'Gustavo',
'Hiram', 'Irvin', 'Julius', 'Karl', 'Leopoldo', 'Morgan',
'Nixon', 'Oberon', 'Percy', 'Roland', 'Sam', 'Travis',
'Uziel', 'Vern', 'Willard', 'Yuri', 'Zacharias', 'Arturo',
'Bryan', 'Coby', 'Dennis', 'Edison', 'Frank', 'Gilbert',
'Harry', 'Isaias', 'Jose', 'Kendrick', 'Lance', 'Marcel',
'Nilo', 'Owen', 'Patrick', 'Rico', 'Sean', 'Theo',
'Uriah', 'Vince', 'Walter', 'Yohan', 'Zachary', 'Amos',
'Bobby', 'Curtis', 'Dion', 'Elias', 'Fritz', 'Gerry',
'Hansel', 'Ivan', 'Jorge', 'Kiel', 'Leo', 'Manny',
'Niel', 'Oscar', 'Paul', 'Randy', 'Seth', 'Trent',
'Ulrich', 'Victor', 'Wesley', 'Yvan', 'Zane', 'Ariel',
'Benji', 'Chris', 'Domingo', 'Edwin', 'Freddie', 'Gino',
'Harvey', 'Irwin', 'Joel', 'Kirk', 'Lou', 'Martin',
'Noel', 'Ollie', 'Phillip', 'Randy', 'Samson', 'Timothy',
'Ulysses', 'Vaughn', 'Winston', 'Yves', 'Zion', 'Adriel',
'Benedict', 'Connor', 'Dionel', 'Emmanuel', 'Francis', 'Gerson',
'Hugh', 'Isidro', 'Joshua', 'Kean', 'Lemuel', 'Miguel',
'Neil', 'Omar', 'Paolo', 'Rainer', 'Simeon', 'Tadeo',
'Urbano', 'Vincent', 'Wendell', 'Yul', 'Zandro', 'Alexis',
'Brent', 'Clint', 'Dario', 'Edison', 'Felipe', 'Gareth',
'Humbert', 'Isidro', 'Jericho', 'Kiefer', 'Levi', 'Maverick',
'Nick', 'Orville', 'Pierre', 'Rufus', 'Stefano', 'Troy',
'Uziel', 'Val', 'Warren', 'Yancy', 'Zeke', 'Albert',
'Benny', 'Carmelo', 'Dindo', 'Elvin', 'Franco', 'Giovanni',
'Henri', 'Ivan', 'Jairus', 'Kaleb', 'Lucio', 'Maurice',
'Nathan', 'Orion', 'Paolo', 'Ruel', 'Santino', 'Thaddeus',
'Uri', 'Vince', 'Wyatt', 'Yvan', 'Zionel', 'Anton',
'Bryce', 'Cedric', 'Darrel', 'Eren', 'Fabian', 'Gelo',
'Hans', 'Isidro', 'Jonel', 'Kiko', 'Lars', 'Mico',
'Noel', 'Olan', 'Patrick', 'Rico', 'Stephen', 'Tristan',
'Uly', 'Vaughn', 'Wendell', 'Yeshua', 'Zadok', 'Alaric',
'Brad', 'Clyde', 'Dylan', 'Eugene', 'Fermin', 'Garry',
'Hendrick', 'Isaac', 'Julian', 'Kenneth', 'Lorenzo', 'Marco',
'Noah', 'Oren', 'Paco', 'Rian', 'Silas', 'Tommy',
'Urbie', 'Vince', 'Walter', 'Yvan', 'Zayden', 'Amiel',
'Blas', 'Colin', 'Darwin', 'Ernest', 'Felix', 'Gabe',
'Harris', 'Ian', 'Jerome', 'Kevin', 'Lyle', 'Matthew',
'Nico', 'Owen', 'Paul', 'Ramon', 'Simon', 'Trent',
'Uriel', 'Victor', 'Will', 'Yves', 'Zander', 'Arvin',
'Bryan', 'Cedrick', 'Dale', 'Elias', 'Fred', 'George',
'Hugh', 'Isaac', 'Jude', 'Karlo', 'Lance', 'Miguel',
'Nash', 'Oscar', 'Patrick', 'Ralph', 'Steven', 'Tyler',
'Urbano', 'Vince', 'Wes', 'Yuri', 'Zack', 'Aiden',
'Blake', 'Connor', 'Daryl', 'Eren', 'Franz', 'Gideon',
'Hansel', 'Ivan', 'Jonas', 'Kean', 'Levi', 'Morris',
'Niel', 'Omar', 'Paulo', 'Ricky', 'Seth', 'Tristan',
'Ulysses', 'Vaughn', 'Wyatt', 'Yohan', 'Zain', 'Aaron',
'Brett', 'Clark', 'Darren', 'Eugene', 'Felix', 'Gabriel',
'Henry', 'Isaiah', 'Jacob', 'Kyle', 'Logan', 'Martin',
'Nolan', 'Owen', 'Pierce', 'Roderick', 'Shawn', 'Troy',
'Ulric', 'Vernon', 'Wayne', 'Yves', 'Zach', 'Ariel',
'Bryce', 'Cliff', 'Dean', 'Eli', 'Francis', 'Gio',
'Harry', 'Ivan', 'Jett', 'Ken', 'Liam', 'Matthew',
'Noel', 'Omar', 'Parker', 'Rafael', 'Simon', 'Theo',
'Ulysses', 'Victor', 'Wesley', 'Yuri', 'Zane', 'Andre',
'Brent', 'Cyrus', 'Dion', 'Eden', 'Frank', 'Gabe',
'Hans', 'Isaac', 'Joel', 'Kyle', 'Lance', 'Mark',
'Nico', 'Oscar', 'Paul', 'Ryan', 'Seth', 'Trent',
'Urbano', 'Vince', 'Walter', 'Yvan', 'Zeke', 'Aiden',
'Blair', 'Clifford', 'Dionisio', 'Eliot', 'Franco', 'Gavin',
'Hendrick', 'Isidro', 'Jules', 'Kenji', 'Lucio', 'Marcus',
'Noel', 'Ollie', 'Pierce', 'Rico', 'Stefan', 'Tobias',
'Uriah', 'Vaughn', 'Wyatt', 'Yves', 'Zion', 'Jerome', 'Jayden', 'Daniel', 'Ezekiel', 'Russell', 'Francis', 'Erwin', 'Kenneth', 'Ramon', 'Leo', 'Brylle', 'Philip', 'Leandro', 'Gerald', 'Jonathan', 'Timothy', 'Earl', 'Harold', 'Mark', 'Ryan', 'Kevin', 'Romeo', 'Dominic', 'Marvin', 'Alexander', 'Joel', 'Ralph', 'Allan', 'Kian', 'Simon', 'James', 'Alfred', 'Thomas', 'Paolo', 'John', 'Elijah', 'Rene', 'Martin', 'Justin', 'Patrick', 'Lloyd', 'Jose', 'Allen', 'Jonathan', 'Ronald', 'Jeremiah', 'Rafael', 'Christopher', 'Rowell', 'Kurt', 'Angelo', 'Leonard', 'Jason', 'Reymond', 'Kenzo', 'Elric', 'Samuel', 'Nelson', 'Aiden', 'Kian', 'Ramon', 'Kurt', 'Alexander', 'Rome', 'Martin', 'Zachary', 'Erwin', 'Gabriel', 'Christian', 'Adrian', 'Zion', 'Sean', 'Miguel', 'Jayden', 'Renz', 'Ian', 'Arnold', 'Carlo', 'Gerald', 'Jared', 'Edgar', 'Tony', 'Kevin', 'Carl', 'Paolo', 'Earl', 'Clyde', 'Brylle', 'Kian', 'Robert', 'Nelson', 'Martin', 'Sean', 'Arthur', 'Roderick', 'Marvin', 'Kenneth', 'Leandro', 'Tony', 'Jacob', 'Miguel', 'Rome', 'Carlo', 'Arvin', 'Axel', 'Noel', 'Zane', 'Ramon', 'Daryl', 'Russell', 'Darren', 'Roland', 'Rafael', 'Joshua', 'Aaron', 'Paolo', 'Eugene', 'Arvin', 'Jason', 'Jared', 'Lance', 'Aiden', 'Daryl', 'Joshua', 'Lawrence', 'Jose', 'Ramon', 'Noah', 'Victor', 'Gerald', 'Alvin', 'Jeffrey', 'Kurt', 'Roland', 'Carlo', 'Harvey', 'Reymond', 'Allen', 'Victor', 'Adrian', 'Justin', 'Allan', 'Axel', 'Albert', 'Santino', 'Ferdinand', 'Jayden', 'Dominic', 'Vincent', 'Xander', 'Dennis', 'Kenzo', 'Edgar', 'Paolo', 'Leonard', 'Edward', 'Ralph', 'Allen', 'Mathew', 'Lance', 'Christian', 'Dominic', 'Nathan', 'Jonathan', 'Zachary', 'Gilbert', 'Ferdinand', 'Alonzo', 'Joel', 'Mark', 'Timothy', 'Anthony', 'Dean', 'Allen', 'Carl',
'Reginald', 'Valentino', 'Weston', 'Xavier', 'Zachariah', 'Adriel',
'Benedict', 'Constantine', 'Dashiell', 'Emmanuel', 'Francisco', 'Giovanni',
'Harrison', 'Ignatius', 'Jeremiah', 'Kingston', 'Leonardo', 'Montgomery',
'Nathaniel', 'Orlando', 'Princeton', 'Remington',
'Afton', 'Finley', 'Kearney', 'Keary', 'Kegan', 'Keir', 'Kendall', 'Mannix',
'Melvin', 'Merlin', 'Murray', 'Perth', 'Ronan', 'Sean',
'Tadc', 'Tegan', 'Tiernan', 'Torin', 'Vaughan',
'Hodding', 'Kyler', 'Maarten', 'Rembrandt', 'Rodolf', 'Roosevelt',
'Schuyler', 'Van', 'Vandyke', 'Wagner',
'Aldo', 'Aleyn', 'Alford', 'Anson', 'Archibald',
'Atley', 'Atwell', 'Audie', 'Avery', 'Ayers', 'Baker', 'Balder',
'Barker', 'Bayard', 'Bishop', 'Blake', 'Blaine', 'Bramwell',
'Brant', 'Bryce', 'Byron',
'Cage', 'Cedar', 'Churchill', 'Colton', 'Crandall',
'Dack', 'Dakin', 'Dallin', 'Dalton', 'Dartmouth', 'Dawson', 'Dax',
'Denton', 'Denver', 'Denzel', 'Diamond',
'Doane', 'Doc', 'Draper', 'Dugan', 'Dunley',
'Dunn', 'Dunstan', 'Dwyer', 'Dyson', 'Edison',
'Edred', 'Egbert', 'Eldwin', 'Elgin', 'Ellis',
'Elwood', 'Emmett', 'Errol', 'Everest', 'Ewing', 'Falkner',
'Farold', 'Farran', 'Fenton', 'Finch', 'Fitz', 'Fleming',
'Flint', 'Fox', 'Freedom', 'Gaines',
'Gale', 'Gallant', 'Garfield', 'Garrett', 'Geary',
'Gene', 'Gifford', 'Gomer', 'Graham',
'Green', 'Griffin', 'Grover',
'Hart', 'Haskel', 'Heathcliff', 'Heaton', 'Helmut', 'Houston',
'Howard', 'Howe', 'Hoyt', 'Hurst', 'Huxley', 'Indiana',
'Jagger', 'Jarrell', 'Jax', 'Jaxon', 'Jay',
'Jet', 'Judson', 'Julian', 'Kaid', 'Keane', 'Keaton',
'Kell', 'Kelsey', 'Kelvin', 'Kennard', 'Kenneth', 'Kentlee',
'Ker', 'Kester', 'Kingsley', 'Kirby', 'Klay',
'Knightley', 'Kody', 'Kolby', 'Kolton', 'Kyler',
'Lake', 'Langston', 'Lathrop', 'Leighton',
'Lex', 'Lindell', 'Lindsay', 'Livingston', 'Locke', 'London',
'Lord', 'Lowell', 'Ludlow', 'Luke', 'Lusk', 'Lyndal',
'Lynn', 'Maddox', 'Mander',
'Mansfield', 'Markham', 'Marley', 'Marsh',
'Marston', 'Martin', 'Marvin', 'Massey', 'Matheson', 'Maverick',
'Maxwell', 'Mayer', 'Meldon',
'Merrick', 'Merton', 'Miles', 'Monte', 'Montgomery',
'Moreland', 'Morley', 'Morrison', 'Myles', 'Ned',
'Newt', 'Nile', 'Norman',
'Norris', 'Norton', 'Norvin',
'Norwin', 'Odell',
'Orlan', 'Ormond', 'Orrick', 'Orson', 'Osborn',
'Osgood', 'Ossie', 'Overton', 'Parsifal',
'Peers', 'Pelton', 'Pierce', 'Piers',
'Powell', 'Radford', 'Radley',
'Randal', 'Reed', 'Reynold',
'Rhett', 'Rhodes', 'Richard', 'Ridge', 'Ridgley',
'Rivers', 'Roan', 'Robin', 'Robson', 'Rockwell',
'Roden', 'Roe', 'Roldan', 'Ross',
'Rowley', 'Royce', 'Rudd', 'Rune',
'Ryder', 'Sage', 'Salisbury', 'Sanborn',
'Saxon', 'Searles', 'Seaton',
'Seger', 'Selby', 'Seldon', 'Selwyn', 'Seton',
'Sewell', 'Shade', 'Shelby', 'Sheldon', 'Shepley',
'Sidwell', 'Simeon', 'Siward', 'Skye',
'Slate', 'Smith', 'Somerton',
'Spalding', 'Stafford', 'Stanbury',
'Stanwick', 'Starr', 'Steadman', 'Sterling', 'Stetson', 'Stiles',
'Stoke', 'Storm', 'Stuart', 'Sunny', 'Sydney',
'Sylvester', 'Taft', 'Talon', 'Templeton', 'Thompson',
'Thorley', 'Tolbert', 'Tyson', 'Udall',
'Ulmer', 'Upjohn', 'Upton', 'Usher', 'Uther', 'Vail',
'Valen', 'Vine', 'Vinson', 'Vinton',
'Wadell', 'Wadsworth', 'Wain',
'Waite', 'Walcott', 'Wales', 'Walford', 'Walker',
'Waller', 'Walsh', 'Walworth', 'Warburton',
'Ward', 'Wardley', 'Ware', 'Waring',
'Warley', 'Warrick', 'Warton', 'Warwick', 'Washburn', 'Wat',
'Wayde', 'Waylon', 'Webb', 'Weldon',
'Westbrook', 'Whitby', 'Whitcomb', 'Whittaker',
'Wiley', 'Wilford', 'Wilton', 'Wirt',
'Wisdom', 'Witton', 'Wolcott', 'Wolf', 'Wolfe',
'Woodson', 'Wythe', 'Yardley', 'Yule', 'Zani',
]

first_names_female = [
'Maria', 'Ana', 'Sofia', 'Isabella', 'Gabriela', 'Valentina', 'Camila',
'Angelica', 'Nicole', 'Michelle', 'Christine', 'Sarah', 'Jessica',
'Andrea', 'Patricia', 'Jennifer', 'Karen', 'Ashley', 'Jasmine', 'Princess',
'Angel', 'Joyce', 'Kristine', 'Diane', 'Joanna', 'Carmela', 'Isabel',
'Lucia', 'Elena',
'Abigail', 'Adeline', 'Adrienne', 'Agnes', 'Aileen', 'Aira', 'Aiza',
'Alana', 'Alexa', 'Alexis', 'Alice', 'Allyson', 'Alyssa', 'Amara',
'Amelia', 'Amirah', 'Anabelle', 'Anastasia', 'Andrea', 'Angela', 'Angelie',
'Angelyn', 'Anita', 'Annabelle', 'Anne', 'Annie', 'Antoinette', 'April',
'Ariana', 'Arlene', 'Aubrey', 'Audrey', 'Aurora', 'Ava', 'Bea', 'Bella',
'Bernadette', 'Bianca', 'Blessy', 'Brianna', 'Bridget', 'Carla', 'Carmel',
'Cassandra', 'Catherine', 'Cecilia', 'Celeste', 'Charisse', 'Charlene',
'Charlotte', 'Chelsea', 'Cherry', 'Cheska', 'Clarice', 'Claudia', 'Coleen',
'Colleen', 'Cristina', 'Cynthia', 'Dahlia', 'Danica', 'Daniela',
'Danielle', 'Darlene', 'Diana', 'Dominique', 'Donna', 'Dorothy', 'Eden',
'Elaine', 'Eleanor', 'Elisa', 'Eliza', 'Ella', 'Ellen', 'Eloisa', 'Elsa',
'Emerald', 'Emily', 'Emma', 'Erica', 'Erin', 'Esme', 'Eunice', 'Faith',
'Fatima', 'Felice', 'Flor', 'Frances', 'Francesca', 'Genevieve', 'Georgia',
'Gillian', 'Giselle', 'Glenda', 'Grace', 'Gretchen', 'Gwen', 'Hailey',
'Hannah', 'Hazel', 'Heather', 'Heidi', 'Helen', 'Helena', 'Hope', 'Iana',
'Irene', 'Irish', 'Isabelle', 'Ivana', 'Ivory', 'Jacqueline', 'Jamie',
'Jane', 'Janella', 'Janet', 'Janine', 'Janna', 'Jasmine', 'Jean',
'Jeanine', 'Jem', 'Jenica', 'Jessa', 'Jillian', 'Joan', 'Joanna', 'Joanne',
'Jocelyn', 'Jolina', 'Joy', 'Judith', 'Julia', 'Julianne', 'Juliet',
'Justine', 'Kaila', 'Kaitlyn', 'Karen', 'Karina', 'Kate', 'Katrina',
'Kayla', 'Keira', 'Kendra', 'Kim', 'Kimberly', 'Krisha', 'Krista',
'Krystel', 'Kyla', 'Kylie', 'Lara', 'Larissa', 'Laura', 'Lauren', 'Lea',
'Leanne', 'Lena', 'Leslie', 'Lexi', 'Lianne', 'Liza', 'Lorraine', 'Louisa',
'Louise', 'Lovely', 'Lucille', 'Luna', 'Lyndsay', 'Lyra', 'Mae', 'Maggie',
'Maja', 'Mandy', 'Marcia', 'Margaret', 'Marian', 'Mariel', 'Marilyn',
'Marina', 'Marissa', 'Marites', 'Martha', 'Mary', 'Matilda', 'Maureen',
'Maxine', 'May', 'Megan', 'Melissa', 'Mia', 'Mika', 'Mikayla', 'Mila',
'Mira', 'Miranda', 'Mirella', 'Monica', 'Nadia', 'Naomi', 'Natalie',
'Nathalie', 'Nerissa', 'Nika', 'Nina', 'Nora', 'Norma', 'Olivia',
'Ophelia', 'Pamela', 'Patricia', 'Paula', 'Pauline', 'Pearl', 'Phoebe',
'Pia', 'Precious', 'Queenie', 'Quiana', 'Rachelle', 'Rae', 'Rain', 'Raisa',
'Ramona', 'Raven', 'Reina', 'Rhea', 'Rica', 'Richelle', 'Rina', 'Rochelle',
'Rosa', 'Rosalie', 'Roseanne', 'Rowena', 'Ruth', 'Sabrina', 'Samantha',
'Samira', 'Sandra', 'Sara', 'Selene', 'Serena', 'Shaira', 'Shaina',
'Shanelle', 'Shanika', 'Sharon', 'Sheena', 'Sheila', 'Sherlyn', 'Shiela',
'Shirley', 'Siena', 'Sierra', 'Sofia', 'Sophia', 'Steffany', 'Stephanie',
'Summer', 'Susan', 'Suzette', 'Sylvia', 'Tanya', 'Tara', 'Tatiana',
'Tessa', 'Thea', 'Theresa', 'Trisha', 'Trista', 'Valeria', 'Vanessa',
'Veronica', 'Vicky', 'Victoria', 'Viel', 'Vina', 'Vivian', 'Wendy',
'Whitney', 'Yasmin', 'Ysabel', 'Yvette', 'Yvonne', 'Zara', 'Zelda', 'Zia',
'Zoe', 'Althea', 'Arya', 'Beatriz', 'Czarina', 'Dayanara', 'Elora',
'Fiona', 'Gianna', 'Helena', 'Indira', 'Janine', 'Kalista', 'Larraine',
'Maeve', 'Noelle', 'Odessa', 'Patrina', 'Rowan', 'Selina', 'Tahlia', 'Una',
'Vienna', 'Willow', 'Xandra', 'Yanna', 'Zyra', 'Clarissa', 'Diane',
'Fritzie', 'Harley', 'Ivette', 'Juliana', 'Karmina', 'Leira', 'Maricel',
'Nerina', 'Odette', 'Pia', 'Riona', 'Sandy', 'Tanya', 'Vielka', 'Winona',
'Xyla', 'Ysa', 'Zian', 'Adria', 'Aubriel', 'Celina', 'Devina', 'Emerie',
'Florence', 'Graciela', 'Hilary', 'Isla', 'Jaira', 'Kelsey', 'Lianne',
'Maika', 'Nashira', 'Orla', 'Perla', 'Quinley', 'Roxanne', 'Soleil',
'Therese', 'Ulani', 'Verona', 'Xaviera', 'Althea', 'Andrea', 'Angela', 'Anna', 'Sarah', 'Nicole', 'Ella', 'Sophia', 'Isabella',
'Jasmine', 'Kristine', 'Michelle', 'Patricia', 'Catherine', 'Victoria', 'Samantha', 'Ashley', 'Gabrielle', 'Maryanne',
'Christine', 'Angelica', 'Stephanie', 'Jennifer', 'Amanda', 'Diana', 'Clarissa', 'Erica', 'Theresa', 'Monica',
'Ariana', 'Bea', 'Camille', 'Danica', 'Elaine', 'Faith',
'Giselle', 'Hannah', 'Inara', 'Janelle', 'Kaila', 'Lianne',
'Monique', 'Nadine', 'Olivia', 'Phoebe', 'Queenie', 'Rachelle',
'Savannah', 'Tiffany', 'Uma', 'Venice', 'Wynona', 'Ysabelle',
'Zoey', 'Abigail', 'Bianca', 'Caitlyn', 'Dahlia', 'Eliza',
'Farrah', 'Georgia', 'Hailey', 'Ivy', 'Jasmine', 'Katrina',
'Lara', 'Maxine', 'Nathalie', 'Opal', 'Patricia', 'Renee',
'Sienna', 'Trisha', 'Vania', 'Willow', 'Yasmin', 'Zaira',
'Alaina', 'Bridget', 'Clarisse', 'Deborah', 'Erika', 'Fiona',
'Gemma', 'Hazel', 'Isla', 'Janine', 'Kayla', 'Lianne',
'Mikaela', 'Noreen', 'Odessa', 'Penelope', 'Quiana', 'Rafaela',
'Sabrina', 'Therese', 'Valerie', 'Whitney', 'Yvette', 'Zelda',
'Alessia', 'Bethany', 'Cassandra', 'Diana', 'Elyse', 'Freya',
'Grace', 'Harriet', 'Iana', 'Jessa', 'Kimberly', 'Lynette',
'Marielle', 'Noemi', 'Orla', 'Patrice', 'Rosalind', 'Sophia',
'Tamara', 'Veronica', 'Willa', 'Yara', 'Zion', 'Amara',
'Bernadette', 'Celine', 'Delaney', 'Estelle', 'Faye', 'Gianna',
'Hilary', 'Ivana', 'Jillian', 'Keziah', 'Larissa', 'Mara',
'Nika', 'Oriana', 'Pamela', 'Rianne', 'Selene', 'Talia',
'Vittoria', 'Wendy', 'Ysadora', 'Zia', 'Aubrey', 'Blythe',
'Carmela', 'Daphne', 'Eden', 'Florence', 'Gwen', 'Helena',
'Inez', 'Joanna', 'Keira', 'Lourdes', 'Mayumi', 'Nadine',
'Ondrea', 'Pauleen', 'Regina', 'Simone', 'Theresa', 'Vera',
'Wynne', 'Yumi', 'Zandra', 'Aimee', 'Brooklyn', 'Carla',
'Daria', 'Eloisa', 'Fritzie', 'Glenda', 'Haidee', 'Isabel',
'Juliana', 'Kirsten', 'Liana', 'Matilda', 'Noreen', 'Ophelia',
'Patty', 'Rina', 'Samantha', 'Trina', 'Vienna', 'Xyra',
'Ynah', 'Zyra', 'Alana', 'Bettina', 'Clarissa', 'Darlene',
'Evelyn', 'Faith', 'Giulia', 'Hana', 'Ivory', 'Jamie',
'Krista', 'Lianne', 'Macy', 'Nerissa', 'Odette', 'Pauline',
'Rhianna', 'Selina', 'Trixie', 'Verna', 'Willa', 'Yara',
'Zenia', 'Angelie', 'Brianna', 'Catrina', 'Denise', 'Ellaine',
'Fiona', 'Grace', 'Hillary', 'Imogen', 'Janice', 'Kiara',
'Lara', 'Marin', 'Nina', 'Odessa', 'Phoebe', 'Reina',
'Savina', 'Tanya', 'Vanna', 'Wendelyn', 'Yvette', 'Zaira',
'Arielle', 'Blanca', 'Cheska', 'Doreen', 'Emeraude', 'Francine',
'Gillian', 'Harley', 'Isha', 'Jasmine', 'Krizia', 'Laraine',
'Misha', 'Nashira', 'Olesya', 'Patrizia', 'Rachelle', 'Serena',
'Tracy', 'Vanessa', 'Wynette', 'Ysabel', 'Zoe', 'Alliah',
'Beatriz', 'Caren', 'Danielle', 'Elora', 'Fatima', 'Gina',
'Hazel', 'Isabelle', 'Jade', 'Katya', 'Liza', 'Margaux',
'Nina', 'Odette', 'Pia', 'Raquel', 'Sofia', 'Therese',
'Vivienne', 'Winter', 'Ynah', 'Zia', 'Aaliyah', 'Blaire',
'Czarina', 'Desiree', 'Eliza', 'Faith', 'Georgina', 'Heidi',
'Ingrid', 'Jemima', 'Kailyn', 'Layla', 'Mika', 'Nicole',
'Olive', 'Paola', 'Ruth', 'Selena', 'Tala', 'Valeria',
'Xandra', 'Ysabella', 'Zyrah', 'Amira', 'Bettina', 'Chantal',
'Diane', 'Eira', 'Fiona', 'Gretchen', 'Hana', 'Ina',
'Janelle', 'Kendra', 'Lani', 'Mara', 'Nadine', 'Orla',
'Pauleen', 'Rafaela', 'Sandy', 'Tina', 'Verna', 'Winnie',
'Ysa', 'Zara', 'Ariane', 'Bambi', 'Caitlin', 'Danna',
'Ella', 'Faith', 'Gabbie', 'Hellen', 'Inna', 'Jessamine',
'Kyla', 'Lara', 'Mikaela', 'Noreen', 'Oona', 'Penelope',
'Raina', 'Sophia', 'Theresa', 'Vina', 'Winter', 'Yumi',
'Zelene', 'Alyssa', 'Briar', 'Chesca', 'Danna', 'Erin',
'Faye', 'Gwyneth', 'Hannah', 'Ira', 'Jodie', 'Keira',
'Luna', 'Mariel', 'Nika', 'Olivia', 'Paula', 'Rachelle',
'Sienna', 'Tessa', 'Vera', 'Wynne', 'Yelena', 'Zaira',
'Annika', 'Bea', 'Corinne', 'Dahlia', 'Elara', 'Fritzie',
'Giselle', 'Hailey', 'Isla', 'Jamie', 'Kassandra', 'Lyra',
'Mira', 'Nadine', 'Ornella', 'Patrice', 'Quinn', 'Renee',
'Sabrina', 'Trixie', 'Valentina', 'Winnie', 'Ysabel', 'Zia',
'Abbie', 'Blanche', 'Cleo', 'Daisy', 'Eleni', 'Faith',
'Gretel', 'Helena', 'Ivana', 'Joyce', 'Kara', 'Lianne',
'Maeve', 'Nina', 'Oriana', 'Pia', 'Ruth', 'Sari',
'Tanya', 'Vivian', 'Wynona', 'Yanna', 'Zenya', 'Asha',
'Brielle', 'Carmina', 'Dina', 'Elaiza', 'Florence', 'Gia',
'Hazel', 'Isabel', 'Jasmin', 'Kristine', 'Lia', 'Marla',
'Nadine', 'Odette', 'Patty', 'Raquel', 'Samara', 'Tessa',
'Vicky', 'Winona', 'Yani', 'Zyra', 'Aileen', 'Briena', 'Carla', 'Dayanara', 'Evelina', 'Fiona',
'Gwen', 'Hazel', 'Isobel', 'Jenna', 'Kaila', 'Leona',
'Meg', 'Nadine', 'Odessa', 'Pamela', 'Queenie', 'Renee',
'Savina', 'Trisha', 'Valeria', 'Wynnie', 'Yuna', 'Zelia',
'Althea', 'Blaine', 'Celina', 'Delia', 'Ember', 'Francesca',
'Gianna', 'Helene', 'Ingrid', 'Jordyn', 'Kyla', 'Lyn',
'Mikhaela', 'Nella', 'Orla', 'Penelope', 'Renee', 'Sophia',
'Tamara', 'Vanna', 'Willow', 'Yvaine', 'Zinnia', 'Aimee',
'Bella', 'Clarisse', 'Daria', 'Ellaine', 'Faith', 'Grace',
'Hannah', 'Ivy', 'Jazmine', 'Krisha', 'Laraine', 'Marina',
'Nia', 'Odelle', 'Priscilla', 'Rhianna', 'Sierra', 'Tanya',
'Vanessa', 'Wren', 'Ysadora', 'Zoe', 'Ariella', 'Bianca',
'Cailin', 'Daniella', 'Eunice', 'Felicia', 'Gabrielle', 'Hillary',
'Isabela', 'Jemma', 'Kianna', 'Lianne', 'Mayumi', 'Noelle',
'Olivine', 'Patricia', 'Roselyn', 'Tala', 'Veronica', 'Wendy',
'Yen', 'Zandra', 'Alethea', 'Brynn', 'Catrina', 'Dianne',
]

surnames = [
'Reyes', 'Santos', 'Cruz', 'Bautista', 'Garcia', 'Flores', 'Gonzales',
'Martinez', 'Ramos', 'Mendoza', 'Rivera', 'Torres', 'Fernandez', 'Lopez',
'Castillo', 'Aquino', 'Villanueva', 'Santiago', 'Dela Cruz', 'Perez',
'Castro', 'Mercado', 'Domingo', 'Gutierrez', 'Ramirez', 'Valdez',
'Alvarez', 'Salazar', 'Morales', 'Navarro', 'Abad', 'Abella', 'Abellanosa',
'Acevedo', 'Aguinaldo', 'Aguilar', 'Alcantara', 'Almonte', 'Alonzo',
'Altamirano', 'Amador', 'Amparo', 'Ancheta', 'Andrada', 'Angeles',
'Antonio', 'Aquino', 'Araneta', 'Arceo', 'Arellano', 'Arias', 'Asuncion',
'Avila', 'Ayala', 'Bagasbas', 'Balagtas', 'Balane', 'Balbuena',
'Ballesteros', 'Baltazar', 'Banaga', 'Bao', 'Barcenas', 'Baron', 'Basa',
'Basco', 'Bautista', 'Beltran', 'Benitez', 'Bernal', 'Blanco', 'Borja',
'Briones', 'Buendia', 'Bustamante', 'Caballero', 'Cabanilla', 'Cabrera',
'Cadiz', 'Calderon', 'Camacho', 'Canlas', 'Capili', 'Carpio', 'Castaneda',
'Castroverde', 'Catapang', 'Celis', 'Ceniza', 'Cerda', 'Chavez',
'Clemente', 'Coloma', 'Concepcion', 'Cordova', 'Cornejo', 'Coronel',
'Corpuz', 'Cortez', 'Cruzado', 'Cuenca', 'Cuevas', 'Dacanay', 'Daguio',
'Dalisay', 'Daluz', 'Damaso', 'Dancel', 'Danganan', 'De Guzman',
'Del Mundo', 'Del Rosario', 'Delos Reyes', 'Deluna', 'Desamparado',
'Dimaandal', 'Dimaculangan', 'Dizon', 'Dolor', 'Duque', 'Ebarle',
'Echevarria', 'Elizalde', 'Encarnacion', 'Enriquez', 'Escalante',
'Escobar', 'Escueta', 'Espinosa', 'Espiritu', 'Estrella', 'Evangelista',
'Fabian', 'Fajardo', 'Falcon', 'Fernan', 'Ferrolino', 'Ferrer', 'Figueras',
'Florencio', 'Fonseca', 'Francisco', 'Fuentes', 'Galang', 'Galvez',
'Garay', 'Garing', 'Gaspar', 'Gavino', 'Giron', 'Godinez', 'Gomez',
'Gonzaga', 'Granado', 'Guerrero', 'Guevarra', 'Guinto', 'Hernandez',
'Herrera', 'Hilario', 'Ignacio', 'Ilagan', 'Inocencio', 'Intal', 'Isidro',
'Jacinto', 'Javier', 'Jimenez', 'Labao', 'Lacson', 'Ladines', 'Lagman',
'Lao', 'Lara', 'Lasala', 'Lazaro', 'Legaspi', 'Leones', 'Leviste',
'Liwanag', 'Lorenzo', 'Lucero', 'Lumibao', 'Luna', 'Macaraig', 'Madarang',
'Madrid', 'Magalong', 'Magbago', 'Magno', 'Magpantay', 'Malabanan',
'Malig', 'Malinao', 'Manalo', 'Mangahas', 'Mangubat', 'Manlapig', 'Manuel',
'Marasigan', 'Marquez', 'Martel', 'Matic', 'Melendres', 'Meneses',
'Miranda', 'Mojica', 'Montero', 'Montoya', 'Morante', 'Moreno', 'Moya',
'Naval', 'Nieva', 'Nieto', 'Nieves', 'Nolasco', 'Obando', 'Ocampo',
'Oliva', 'Olivares', 'Ong', 'Ordonez', 'Ortega', 'Ortiz', 'Osorio',
'Padilla', 'Paguio', 'Palacio', 'Palma', 'Pangan', 'Panganiban',
'Panlilio', 'Pantoja', 'Paredes', 'Parilla', 'Parungao', 'Pasco', 'Pastor',
'Patricio', 'Pineda', 'Pizarro', 'Po', 'Policarpio', 'Ponce', 'Quijano',
'Quimpo', 'Quinto', 'Quirino', 'Rafael', 'Ramoso', 'Razon', 'Redillas',
'Relucio', 'Remulla', 'Riego', 'Rigor', 'Rivadeneira', 'Rizal', 'Robles',
'Rocha', 'Rodriguez', 'Rojo', 'Romualdez', 'Rosa', 'Rosales', 'Rosario',
'Rueda', 'Ruiz', 'Sablan', 'Salas', 'Salcedo', 'Salinas', 'Samson',
'San Juan', 'San Miguel', 'Sandoval', 'Santillan', 'Santoson', 'Sarmiento',
'Segovia', 'Sereno', 'Sia', 'Silang', 'Silva', 'Sison', 'Soledad',
'Soliman', 'Soriano', 'Subido', 'Suarez', 'Sumangil', 'Sy', 'Tablante',
'Tabora', 'Tacorda', 'Tagle', 'Tamayo', 'Tan', 'Tangonan', 'Tantoco',
'Tapales', 'Taruc', 'Tejada', 'Tiongson', 'Tolentino', 'Tongco', 'Toribio',
'Trinidad', 'Tronqued', 'Tuazon', 'Ubaldo', 'Ugalde', 'Umali', 'Untalan',
'Uy', 'Valencia', 'Valenton', 'Valera', 'Valle', 'Vargas', 'Velasco',
'Velasquez', 'Vergara', 'Verzosa', 'Villafuerte', 'Villalobos', 'Villamor',
'Villanueva', 'Villareal', 'Vizcarra', 'Yamamoto', 'Yap', 'Yatco', 'Yumul',
'Zabala', 'Zamora', 'Zarate', 'Zavalla', 'Zialcita', 'dela Cruz',
'Perez', 'Gomez', 'Rodriguez', 'Sanchez', 'Ramirez', 'Francisco', 'Pascual', 'Hernandez', 'Aguilar',
'Diaz', 'Lim', 'Chua', 'Uy', 'Co', 'Lee', 'Chan', 'Yap', 'Manalo', 'Panganiban', 'Marasigan',
'Agbayani', 'Macapagal',
'Abad', 'Abadiano', 'Abalos', 'Abanilla', 'Abanto', 'Abarca',
'Abaya', 'Abella', 'Abesamis', 'Abiera', 'Abinoja', 'Abisamis',
'Ablan', 'Ablaza', 'Abordo', 'Abrigo', 'Abril', 'Abucay', 'Abunda',
'Acabo', 'Acal', 'Acedera', 'Acevedo', 'Acosta', 'Adajar',
'Adan', 'Adarlo', 'Adaza', 'Adlawan', 'Adolfo', 'Adriano',
'Agbayani', 'Agcaoili', 'Agda', 'Agdeppa', 'Agero', 'Agliam',
'Aglibot', 'Agmata', 'Agnes', 'Agoncillo', 'Agpaoa', 'Agregado',
'Aguado', 'Aguila', 'Aguilar', 'Aguilera', 'Aguinaldo', 'Aguirre',
'Alarcon', 'Alba', 'Albano', 'Alcaraz', 'Alcazar', 'Alcober',
'Alcoseba', 'Alcuizar', 'Aldaba', 'Alday', 'Alegria', 'Alejandrino',
'Alejo', 'Alfonso', 'Aliño', 'Alinsangan', 'Allarde', 'Almeda',
'Almirante', 'Almonte', 'Almuete', 'Almario', 'Alonte', 'Alonzo',
'Alvarado', 'Alvarez', 'Amador', 'Amante', 'Amarillo', 'Amatong',
'Ambao', 'Ambrosio', 'Amistoso', 'Amores', 'Amparo', 'Ampil',
'Amurao', 'Anacleto', 'Ancheta', 'Andal', 'Andrada', 'Andres',
'Andrin', 'Ang', 'Angara', 'Angeles', 'Angping', 'Aniban',
'Aniceto', 'Anonas', 'Antiporda', 'Antonio', 'Antoque', 'Anunciacion',
'Apolonio', 'Apostol', 'Aquino', 'Araneta', 'Arce', 'Arcega',
'Arceo', 'Arciaga', 'Arcilla', 'Arellano', 'Arevalo', 'Arguelles',
'Aristores', 'Arnaiz', 'Arnaldo', 'Arriola', 'Arroyo', 'Arsenio',
'Asis', 'Asistio', 'Asuncion', 'Atienza', 'Aurelio', 'Austria',
'Avila', 'Ayala', 'Ayson', 'Azarcon', 'Azores',
'Bacani', 'Baclig', 'Bacungan', 'Badajos', 'Badayos', 'Badillo',
'Bagalay', 'Bagatsing', 'Bagay', 'Bagongon', 'Baguio', 'Bahena',
'Bailon', 'Balanay', 'Balane', 'Balatbat', 'Baldonado', 'Baldo',
'Baldoza', 'Baldovino', 'Balingit', 'Ballesteros', 'Balmeo', 'Balmes',
'Balmonte', 'Baluyot', 'Banaag', 'Banal', 'Banaria', 'Bangayan',
'Bangco', 'Bangoy', 'Banlaoi', 'Banzon', 'Baranda', 'Barba',
'Barcena', 'Barcelona', 'Barela', 'Bargas', 'Bariso', 'Barlaan',
'Barrientos', 'Barroga', 'Barsaga', 'Bartolome', 'Basco', 'Basilio',
'Batungbakal', 'Bautista', 'Bayani', 'Baylon', 'Bayona', 'Bayot',
'Beltran', 'Belmonte', 'Benitez', 'Bernabe', 'Bernardo', 'Bersamin',
'Blanco', 'Bonifacio', 'Borja', 'Borlongan', 'Borromeo',
'Braganza', 'Bravo', 'Brillantes', 'Briones', 'Buenaventura', 'Buendia',
'Bueno', 'Bugay', 'Bulaon', 'Bulanadi', 'Bulatao', 'Bunag',
'Burgos', 'Bustamante', 'Caballero', 'Cabanilla', 'Cabrera',
'Cabatingan', 'Cadiz', 'Calderon', 'Camacho', 'Camara', 'Campos',
'Candelaria', 'Canlas', 'Canoy', 'Carandang', 'Caraig', 'Carating',
'Cariño', 'Carreon', 'Carrillo', 'Carungay', 'Casal', 'Casanova',
'Casimiro', 'Castaneda', 'Castillo', 'Castro', 'Catapang',
'Cayabyab', 'Cayetano', 'Celestino', 'Celis', 'Centeno', 'Cervantes',
'Chavez', 'Chua', 'Cipriano', 'Clarin', 'Claudio', 'Clemente',
'Co', 'Concepcion', 'Cordero', 'Cordova', 'Cornejo', 'Coronel',
'Corpuz', 'Corral', 'Cortez', 'Crisologo', 'Crisostomo', 'Cruz',
'Cuenca', 'Cunanan', 'Custodio', 'Dacanay', 'Daguio', 'Dalisay',
'Damasco', 'Dancel', 'Dantes', 'David', 'Davila', 'Decena',
'Delacruz', 'Delgado', 'Delima', 'Delos Reyes', 'Del Rosario',
'Desiderio', 'DeVera', 'Diaz', 'Dichoso', 'Dimalanta', 'Dimaculangan',
'Dimagiba', 'Dinglasan', 'Dionisio', 'Dizon', 'Docena', 'Dolor',
'Domingo', 'Dominguez', 'Donato', 'Duenas', 'Dulay', 'Dumo',
'Durano', 'Ebarle', 'Echevarria', 'Edralin', 'Elizalde',
'Encarnacion', 'Enriquez', 'Enrile', 'Escalante', 'Escobar',
'Escueta', 'Escudero', 'Espinosa', 'Espiritu', 'Estacion', 'Esteban',
'Estrella', 'Estrada', 'Evangelista', 'Fabian', 'Fajardo', 'Falcon',
'Fajardo', 'Feliciano', 'Felipe', 'Fernandez', 'Fernan', 'Ferraren',
'Ferrolino', 'Ferrer', 'Figueroa', 'Florencio', 'Flores', 'Fontanilla',
'Francisco', 'Fuentes', 'Galang', 'Galvez', 'Gamboa', 'Garay',
'Garcia', 'Garing', 'Garrido', 'Gaspar', 'Gatchalian', 'Gatdula',
'Gatmaitan', 'Gavino', 'Geronimo', 'Giron', 'Gomez', 'Gonzaga',
'Gonzales', 'Gonzalez', 'Guerrero', 'Guevarra', 'Guinto', 'Gutierrez',
'Guzman', 'Habana', 'Halili', 'Hernandez', 'Herrera', 'Hidalgo',
'Hilario', 'Honasan', 'Hontiveros', 'Ignacio', 'Ilagan', 'Imperial',
'Inocencio', 'Isidro', 'Jacinto', 'Javier', 'Jimenez', 'Joaquin',
'Jocson', 'Kalaw', 'Katigbak', 'Lacson', 'Lagman', 'Lapid',
'Laurel', 'Lazaro', 'Ledesma', 'Legarda', 'Legaspi', 'Leonico',
'Lim', 'Liwanag', 'Locsin', 'Lopez', 'Lorenzana', 'Lorenzo',
'Loyola', 'Lozada', 'Lucero', 'Luna', 'Mabini', 'Macapagal',
'Macaraig', 'Magsaysay', 'Manalo', 'Manalac', 'Manglapus', 'Marasigan',
'Marcos', 'Mariano', 'Marquez', 'Martinez', 'Mateo', 'Matias',
'Medalla', 'Medina', 'Mercado', 'Miranda', 'Molina', 'Montano',
'Montenegro', 'Montero', 'Morales', 'Moreno', 'Nakpil', 'Narciso',
'Navarro', 'Nepomuceno', 'Neri', 'Nicolas', 'Nieto', 'Nolasco',
'Ocampo', 'Ordonez', 'Ortigas', 'Osmeña', 'Padilla', 'Palma',
'Panganiban', 'Pangilinan', 'Panlilio', 'Pantaleon', 'Paraiso', 'Pascual',
'Pastor', 'Paterno', 'Pelayo', 'Peña', 'Peralta', 'Perez',
'Pimentel', 'Pineda', 'Ponce', 'Puno', 'Punsalan', 'Quezon',
'Quirino', 'Ramirez', 'Ramos', 'Razon', 'Recto', 'Regalado',
'Revilla', 'Ricarte', 'Rivera', 'Robles', 'Rodriguez', 'Rojo',
'Roldan', 'Romero', 'Romualdez', 'Romulo', 'Roque', 'Rosales',
'Rosario', 'Roxas', 'Rubio', 'Ruiz', 'Salas', 'Salazar',
'Salcedo', 'Salonga', 'Salvador', 'Samonte', 'San Agustin', 'San Jose',
'San Juan', 'San Pedro', 'Sanchez', 'Santiago', 'Santillan', 'Sarmiento',
'Sebastian', 'Segovia', 'Silang', 'Singson', 'Sison', 'Soliman',
'Soriano', 'Sotto', 'Suarez', 'Sumulong', 'Sy', 'Tagle', 'Tamayo',
'Tan', 'Tantoco', 'Tapales', 'Tayag', 'Teodoro', 'Teves',
'Tolentino', 'Tordesillas', 'Torres', 'Trinidad', 'Tuason', 'Tugade',
'Ty', 'Umali', 'Uy', 'Valdez', 'Valencia', 'Valenzuela', 'Valera',
'Vargas', 'Velasco', 'Velasquez', 'Ventura', 'Vergara', 'Verzosa',
'Villafuerte', 'Villamor', 'Villanueva', 'Villareal', 'Villegas',
'Vinluan', 'Yap', 'Yumul', 'Zabala', 'Zaldivar', 'Zamora',
'Zapanta', 'Zarate', 'Zerrudo', 'Zialcita', 'Zobel', 'Zulueta',
]

def get_bd_name():
    first = random.choice(first_names_male + first_names_female)
    last = random.choice(surnames)
    return first, last


rpw_first_names = [
'Luna', 'Aurora', 'Mystic', 'Crystal', 'Sapphire', 'Scarlet', 'Violet',
'Rose', 'Athena', 'Venus', 'Nova', 'Stella', 'Serena', 'Raven', 'Jade',
'Ruby', 'Pearl', 'Ivy', 'Willow', 'Hazel', 'Skye', 'Aria', 'Melody',
'Harmony', 'Grace', 'Faith', 'Hope', 'Trinity', 'Destiny', 'Serenity',
'Angel', 'Star', 'Astra', 'Lyra', 'Celeste', 'Elara', 'Elysia', 'Raine',
'Sylvie', 'Nahara', 'Isolde', 'Ophelia', 'Althea', 'Calista', 'Delara',
'Eira', 'Freya', 'Gaia', 'Helena', 'Ilara', 'Junia', 'Kaia', 'Liora',
'Maeve', 'Nara', 'Odessa', 'Phoebe', 'Quinn', 'Rhea', 'Selene', 'Thalia',
'Una', 'Vanya', 'Wynter', 'Xanthe', 'Yara', 'Zara', 'Amara', 'Aurelia',
'Brina', 'Celine', 'Dahlia', 'Eden', 'Fiona', 'Gwen', 'Helia', 'Isla',
'Jessa', 'Kara', 'Lilia', 'Mara', 'Nerine', 'Oona', 'Perse', 'Runa',
'Sana', 'Tara', 'Vera', 'Willa', 'Xena', 'Yvaine', 'Zinnia', 'Aislinn',
'Arielle', 'Belladonna', 'Briar', 'Cassia', 'Daphne', 'Eleni', 'Flora',
'Gemma', 'Hera', 'Ione', 'Jadea', 'Kaira', 'Lilith', 'Maven', 'Nerida',
'Orla', 'Petra', 'Quilla', 'Risa', 'Saphira', 'Tessa', 'Vixie', 'Wren',
'Yuna', 'Zelie', 'Aiyana', 'Ameera', 'Blaire', 'Camina', 'Daria', 'Eirene',
'Faye', 'Greta', 'Honora', 'Indira', 'Jolie', 'Kahlia', 'Lunara', 'Maris',
'Nixie', 'Oriana', 'Phaedra', 'Reina', 'Soleil', 'Tahlia', 'Viera',
'Whisper', 'Xylia', 'Yasmin', 'Zephyra', 'Adira', 'Ariya', 'Brienne',
'Coraline', 'Dove', 'Emberly', 'Fable', 'Giselle', 'Harlow', 'Ivyra',
'Jorah', 'Keira', 'Lyrra', 'Mirelle', 'Nimue', 'Ophira', 'Paloma', 'Rivka',
'Sarai', 'Tirzah', 'Velia', 'Wynna', 'Xaria', 'Yllia', 'Zalina', 'Amoura',
'Aven', 'Brisa', 'Cassidy', 'Diantha', 'Elva', 'Farrah', 'Giada', 'Hollis',
'Inara', 'Jadeen', 'Kiera', 'Leira', 'Maelle', 'Naida', 'Orra', 'Pyria',
'Riona', 'Saphine', 'Tova', 'Vanyael', 'Winry', 'Xavia', 'Ysella', 'Zyria',
'Alera', 'Arwen', 'Brielle', 'Cyrene', 'Deira', 'Evania', 'Fianna',
'Gwenna', 'Halyn', 'Irina', 'Jovina', 'Kaelia', 'Luneth', 'Mariel',
'Nayla', 'Orelle', 'Phaena', 'Ruelle', 'Sylph', 'Thessaly', 'Valea',
'Wynnair', 'Xenara', 'Ysolde', 'Zamira', 'Alira', 'Amaris', 'Brynna',
'Ceres', 'Delyra', 'Eislyn', 'Fiora', 'Gwyne', 'Haelia', 'Ismena', 'Jalyn',
'Katria', 'Liorael', 'Maelis', 'Nessara', 'Ovelyn', 'Prisma', 'Ravine',
'Seraphine', 'Tahlira', 'Vierael', 'Wyndra', 'Xylara', 'Yvanna', 'Zerina',
'Anora', 'Aveline', 'Brienne', 'Cynra', 'Danea', 'Eirlys', 'Fael', 'Giana',
'Hessia', 'Ilona', 'Janessa', 'Kyria', 'Lirael', 'Madria', 'Norelle',
'Ophirae', 'Paela', 'Quina', 'Rilith', 'Sienna', 'Tiriel', 'Velisse',
'Wrena', 'Xamira', 'Ysenne', 'Zynra', 'Aelina', 'Alessa', 'Belwyn',
'Carmine', 'Daelia', 'Elyndra', 'Fiorael', 'Gwyneth', 'Helis', 'Isola',
'Jynra', 'Kailen', 'Lunisse', 'Mynra', 'Nyelle', 'Orissa', 'Phira',
'Rylis', 'Saphyre', 'Thyra', 'Valyn', 'Wynelle', 'Xira', 'Ylith', 'Zayra',
'Avenia', 'Ariael', 'Blythe', 'Corra', 'Delyth', 'Elaina', 'Fara', 'Gisra',
'Hellen', 'Ionea', 'Jalisa', 'Kayle', 'Lysandra', 'Mirael', 'Nysa',
'Ophirael', 'Phaelia', 'Renelle', 'Saphra', 'Tirra', 'Viona', 'Wynlie',
'Xynna', 'Ylia', 'Zinnara', 'Azura', 'Bliss', 'Cassiel', 'Dionne',
'Elaris', 'Fawn', 'Gloria', 'Haelyn', 'Inessa', 'Jael', 'Koryn', 'Lissara',
'Marenne', 'Hiraya', 'Celestine', 'Aurora', 'Astrid', 'Brielle', 'Calista', 'Davina', 'Elara', 'Freya', 'Genevieve',
'Haven', 'Iris', 'Juliet', 'Kaia', 'Lyra', 'Mira', 'Nova', 'Ophelia', 'Persephone', 'Quinn',
'Rosalie', 'Seraphina', 'Thea', 'Valencia', 'Willow', 'Xandra', 'Yara', 'Zara', 'Athena', 'Bianca', 'Hiraya', 'Seraphina', 'Anastasia', 'Celestine', 'Evangeline', 'Isadora',
'Genevieve', 'Arabella', 'Josephine', 'Valentina', 'Alessandra', 'Cassandra',
'Gabriella', 'Penelope', 'Rosalind', 'Vivienne', 'Arabesque', 'Beatrice',
'Clementine', 'Delphine', 'Esmeralda', 'Francesca', 'Gwendolyn',
'Isolde', 'Juliette', 'Katarina', 'Lavender', 'Magdalena', 'Nicolette',
'Ophelia', 'Persephone', 'Queenie', 'Rosabelle', 'Sapphire', 'Theodora',
'Valencia', 'Wilhelmina', 'Xanthia', 'Zenaida', 'Aureliana',
'Bernadette', 'Celestia', 'Desdemona', 'Fallon', 'Flannery', 'Kaie',
'Kaitlyn', 'Kassidy', 'Kathleen', 'Keena', 'Keira',
'Kendall', 'Kenna', 'Kera', 'Kiara',
'Kirra', 'Kylee', 'Lachlan', 'Lorna', 'Maeve', 'Malise',
'Morgance', 'Morgandy', 'Nonnita', 'Nuala', 'Raelin', 'Rhonda',
'Saoirse', 'Saraid', 'Seanna', 'Shela', 'Shylah', 'Tara',
'Teranika', 'Tieve', 'Treasa', 'Treva', 'Addison', 'Alivia',
'Allaya', 'Amarie', 'Amaris', 'Annabeth', 'Annalynn', 'Araminta',
'Ardys', 'Ashland', 'Avery', 'Bernadette', 'Billie',
'Birdee', 'Bliss', 'Brice', 'Brittany', 'Bryony', 'Cameo',
'Carol', 'Chalee', 'Christy', 'Corky', 'Courage',
'Daelen', 'Dana', 'Darnell', 'Dawn', 'Delsie', 'Denita',
'Devon', 'Devona', 'Diamond', 'Divinity', 'Dusty',
'Ellen', 'Eppie', 'Evelyn', 'Everilda', 'Falynn',
'Fanny', 'Faren', 'Freedom', 'Gala', 'Galen', 'Gardenia',
'Germain', 'Gig', 'Gilda', 'Giselle', 'Githa', 'Haiden',
'Halston', 'Heather', 'Henna', 'Honey', 'Idalis',
'Ilsa', 'Jersey', 'Jette', 'Jill', 'Joanna',
'Kachelle', 'Kade', 'Kady', 'Kaela', 'Kalyn', 'Kandice',
'Karrie', 'Karyn', 'Katiuscia', 'Kempley', 'Kenda', 'Kennice',
'Kenyon', 'Kiandra', 'Kimber', 'Kimn', 'Kinsey',
'Kipp', 'Kismet', 'Kortney', 'Kourtney',
'Kristal', 'Kylar', 'Ladawn', 'Ladye', 'Lainey',
'Lake', 'Lalisa', 'Landen', 'Landon', 'Landry', 'Laney',
'Langley', 'Lanna', 'Laquetta', 'Lari', 'Lark', 'Laurel',
'Lavender', 'Leane', 'LeAnn', 'Leanna', 'Leanne', 'Leanore',
'Lee', 'Leeann', 'Leighanna', 'Lexie', 'Lexis', 'Liberty',
'Liliana', 'Lillian', 'Lindley', 'Linne', 'Liora', 'Lisabet',
'Liz', 'Lizette', 'Lona', 'London', 'Loni', 'Lorena',
'Loretta', 'Lovette', 'Lynde', 'Lyndon', 'Lyndsay', 'Lynette',
'Lynley', 'Lynna', 'Lynton', 'Mada', 'Maddox', 'Madison',
'Mae', 'Maggie', 'Mahogany', 'Maia', 'Maitane', 'Maitland',
'Malachite', 'Mamie', 'Manhattan', 'Maridel', 'Marla', 'Marley',
'Marliss', 'Maud', 'May', 'Merleen', 'Mildred',
'Milissa', 'Millicent', 'Mily', 'Mykala', 'Nan',
'Nautica', 'Nelda', 'Niki', 'Nikole', 'Nimue', 'Nineve',
'Norina', 'Ofa', 'Palmer', 'Pansy', 'Paris', 'Patience',
'Patricia', 'Peony', 'Petunia', 'Pixie', 'Pleasance', 'Polly',
'Primrose', 'Princell', 'Providence', 'Purity', 'Quanah', 'Queena',
'Quella', 'Quinci', 'Rae', 'Rainbow', 'Rainelle', 'Raleigh',
'Ralphina', 'Randi', 'Raven', 'Rayelle', 'Rea', 'Remington',
'Richelle', 'Ripley', 'Roberta', 'Robin', 'Rosemary', 'Rowan',
'Rumer', 'Ryesen', 'Sable', 'Sadie', 'Saffron', 'Saga',
'Saige', 'Salal', 'Salia', 'Sandora', 'Sebille', 'Sebrina',
'Selby', 'Serenity', 'Shae', 'Shandy', 'Shanice', 'Sharman',
'Shelbi', 'Sheldon', 'Shelley', 'Sheridan', 'Sherill', 'Sheryl',
'Sheyla', 'Shirley', 'Shirlyn', 'Silver', 'Skyla', 'Skylar',
'Sorilbran', 'Sparrow', 'Spring', 'Starleen', 'Stockard', 'Storm',
'Sudie', 'Summer', 'Sunniva', 'Suzana', 'Symphony', 'Tacey',
'Tahnee', 'Taite', 'Talon', 'Tambre', 'Tamia', 'Taniya',
'Tanner', 'Tanzi', 'Taria', 'Tate', 'Tatum', 'Tawnie',
'Taya', 'Tayla', 'Taylor', 'Tayna', 'Teddi', 'Tena',
'Tera', 'Teri', 'Teryl', 'Thistle', 'Timotha', 'Tinble',
'Tosha', 'Totie', 'Traci', 'Tru', 'Trudie', 'Trudy',
'Tryamon', 'Tuesday', 'Twila', 'Twyla', 'Tyne', 'Udele',
'Unity', 'Vail', 'Vala', 'Velvet', 'Venetta', 'Walker',
'Wallis', 'Waneta', 'Waverly', 'Wendy', 'Weslee', 'Whitley',
'Whitney', 'Whoopi', 'Wilda', 'Wilfreda', 'Willow', 'Wilona',
'Winifred', 'Winsome', 'Winter', 'Wisdom', 'Wrenn', 'Yale',
'Yardley', 'Yeardley', 'Yedda', 'Young', 'Ysolde', 'Zadie',
'Zanda', 'Zavannah', 'Zavia', 'Zeolia', 'Zinnia', 'Blaine',
'Blair', 'Eilis', 'Kalene', 'Keaira', 'Keelty', 'Keely',
'Keen', 'Keitha', 'Kellan', 'Kennis', 'Kerry', 'Kevina',
'Killian', 'Kyna', 'Lakyle', 'Lee', 'Mab', 'Maeryn',
'Maille', 'Mairi', 'Maisie', 'Meara', 'Meckenzie', 'Myrna',
'Nara', 'Neala', 'Nelia', 'Oona', 'Quinn', 'Rhoswen',
'Riane', 'Riley', 'Rogan', 'Rona', 'Ryan', 'Sadb',
'Shanley', 'Shelagh', 'Sine', 'Siobhan', 'Sorcha', 'Ultreia',
'Vevila', 'Acantha', 'Adara', 'Adelpha', 'Adrienne', 'Aegle',
'Afrodite', 'Agape', 'Agata', 'Aglaia', 'Agnes', 'Aileen',
'Alcina', 'Aldora', 'Alethea', 'Alexandra', 'Alice', 'Alida',
'Alisha', 'Alixia', 'Althea', 'Aludra', 'Amara', 'Ambrosia',
'Amethyst', 'Aminta', 'Amphitrite', 'Anastasia', 'Andrea', 'Andromache',
'Andromeda', 'Angela', 'Anstice', 'Antonia', 'Anysia', 'Aphrodite',
'Arali', 'Aretha', 'Ariadne', 'Ariana', 'Arissa',
'Artemia', 'Artemis', 'Astrid', 'Athena', 'Atropos', 'Aurora',
'Avel', 'Basilissa', 'Bernice', 'Calandra',
'Calantha', 'Calista', 'Calliope', 'Candace', 'Candra', 'Carina',
'Carisa', 'Cassandra', 'Cassiopeia', 'Catherine', 'Celandia', 'Cerelia', 'Charisma', 'Christina', 'Clio', 'Cloris',
'Clotho', 'Colette', 'Cora', 'Cressida', 'Cybill', 'Cyd',
'Cynthia', 'Damaris', 'Damia', 'Daphne', 'Daria', 'Daryn',
'Dasha', 'Dea', 'Delbin', 'Della', 'Delphine', 'Delta',
'Demetria', 'Desdemona', 'Desma', 'Despina', 'Dionne', 'Diotama',
'Dora', 'Dorcas', 'Doria', 'Dorian', 'Doris', 'Dorothy',
'Dorrit', 'Drew', 'Drucilla', 'Dysis', 'Ebony', 'Effie',
'Eileen', 'Elani', 'Eleanor', 'Electra', 'Elke', 'Elma',
'Elodie', 'Eos', 'Eppie', 'Eris', 'Ethereal', 'Eudora',
'Eugenia', 'Eulalia', 'Eunice', 'Euphemia', 'Euphrosyne', 'Euterpe',
'Evadne', 'Evangeline', 'Filmena', 'Gaea', 'Galina', 'Gelasia',
'Gemini', 'Georgia', 'Greer', 'Greta', 'Harmony', 'Hebe',
'Hecate', 'Hecuba', 'Helen', 'Hera', 'Hermia', 'Hermione',
'Hero', 'Hestia', 'Hilary', 'Hippolyta', 'Hyacinth', 'Hydra',
'Ianthe', 'Ilena', 'Iolite', 'Iona', 'Irene', 'Iris',
'Isidore', 'Jacey', 'Jacinta', 'Jolanta', 'Kacia', 'Kaethe',
'Kaia', 'Kaija', 'Kairi', 'Kairos', 'Kali', 'Kalidas',
'Kalika', 'Kalista', 'Kalli', 'Kalliope', 'Kallista', 'Kalonice',
'Kalyca', 'Kanchana', 'Kandace', 'Kara', 'Karana', 'Karen',
'Karin', 'Karis', 'Karissa', 'Karlyn', 'Kasandra', 'Kassandra',
'Katarina', 'Kate', 'Katherine', 'Katina', 'Khina', 'Kineta',
'Kirsten', 'Kolina', 'Kora', 'Koren', 'Kori', 'Korina',
'Kosma', 'Kristen', 'Kristi', 'Kristina', 'Kristine', 'Kristy',
'Kristyn', 'Krysten', 'Krystina', 'Kynthia', 'Kyra', 'Kyrene',
'Kyria', 'Lacy', 'Lali', 'Lareina', 'Laria', 'Larina',
'Larisa', 'Larissa', 'Lasthenia', 'Latona', 'Layna', 'Leandra',
'Leda', 'Ledell', 'Lenore', 'Leonora', 'Leta', 'Letha',
'Lethia', 'Lexi', 'Lexie', 'Lidia', 'Lilika', 'Lina',
'Linore', 'Litsa', 'Livana', 'Livvy', 'Lotus', 'Lyanne',
'Lycorida', 'Lycoris', 'Lydia', 'Lydie', 'Lykaios', 'Lyra',
'Lyric', 'Lyris', 'Lysandra', 'Macaria', 'Madalena', 'Madelia',
'Madeline', 'Madge', 'Maeve', 'Magan', 'Magdalen', 'Maia',
'Mala', 'Malissa', 'Mara', 'Margaret', 'Marigold', 'Marilee',
'Marjorie', 'Marlene', 'Marmara', 'Maya', 'Medea', 'Medora',
'Megan', 'Megara', 'Melanctha', 'Melanie', 'Melba', 'Melenna',
'Melia', 'Melinda', 'Melissa', 'Melitta', 'Melody', 'Melpomene',
'Minta', 'Mnemosyne', 'Mona', 'Muse', 'Myda', 'Myrtle',
'Naia', 'Naida', 'Naiyah', 'Narcissa', 'Narella', 'Natasha',
'Nell', 'Nellie', 'Nellis', 'Nelly', 'Neola', 'Neoma',
'Nerin', 'Nerina', 'Neysa', 'Nichole', 'Nicia', 'Nicki',
'Nicole', 'Nike', 'Nikita', 'Niobe', 'Nitsa', 'Noire',
'Nora', 'Nyla', 'Nysa', 'Nyssa', 'Nyx', 'Obelia',
'Oceana', 'Odea', 'Odessa', 'Ofelia', 'Olympia', 'Omega',
'Onyx', 'Ophelia', 'Ophira', 'Orea', 'Oriana', 'Padgett',
'Pallas', 'Pamela', 'Pandora', 'Panphila', 'Parthenia', 'Pelagia',
'Penelope', 'Phedra', 'Philadelphia', 'Philippa', 'Philomena', 'Phoebe',
'Phyllis', 'Pirene', 'Prisma', 'Psyche', 'Ptolema', 'Pyhrrha',
'Pyrena', 'Pythia', 'Raissa', 'Rasia', 'Rene', 'Rhea',
'Rhoda', 'Rhodanthe', 'Rita', 'Rizpah', 'Saba', 'Sandra',
'Sandrine', 'Sapphira', 'Sappho', 'Seema', 'Selena', 'Selina',
'Sema', 'Sherise', 'Sibley', 'Sirena', 'Sofi', 'Sondra',
'Sophie', 'Sophronia', 'Stacia', 'Stefania',
'Stephaney', 'Stesha', 'Sybella', 'Sybil', 'Syna', 'Tabitha',
'Talia', 'Talieya', 'Taliyah', 'Tallya', 'Tamesis', 'Tanith',
'Tansy', 'Taryn', 'Tasha', 'Tasia', 'Tedra', 'Teigra',
'Tekla', 'Telma', 'Terentia', 'Terpsichore', 'Terri', 'Tess',
'Thaddea', 'Thaisa', 'Thalassa', 'Thalia', 'Than', 'Thea',
'Thelma', 'Themis', 'Theodora', 'Theodosia', 'Theola', 'Theone',
'Theophilia', 'Thera', 'Theresa', 'Thisbe', 'Thomasa', 'Thracia',
'Thyra', 'Tiana', 'Tienette', 'Timandra', 'Timothea', 'Titania',
'Titian', 'Tomai', 'Tona', 'Tresa', 'Tressa', 'Triana',
'Trifine', 'Trina', 'Tryna', 'Urania', 'Uriana', 'Vanessa',
'Vasiliki', 'Velma', 'Venus', 'Voleta', 'Xandria', 'Xandy',
'Xantha', 'Xenia', 'Xenobia', 'Xianthippe', 'Xylia', 'Xylona',
'Yolanda', 'Yolie', 'Zagros', 'Zale', 'Zanaide', 'Zandra',
'Zanita', 'Zanthe', 'Zebina', 'Zelia', 'Zena', 'Zenaide',
'Zenia', 'Zenobia', 'Zenon', 'Zera', 'Zeta', 'Zeuti',
'Zeva', 'Zinaida', 'Zoe', 'Zosima', 'Ai', 'Aiko',
'Akako', 'Akanah', 'Aki', 'Akina', 'Akiyama', 'Amarante',
'Amaya', 'Aneko', 'Anzan', 'Anzu', 'Aoi', 'Asa',
'Asami', 'Ayame', 'Bankei', 'Chika', 'Chihiro',
'Chiyo', 'Cho', 'Chorei', 'Dai', 'Eido', 'Ema',
'Etsu', 'Fuyo', 'Hakue', 'Hama', 'Hanako',
'Haya', 'Hisa', 'Himari', 'Hoshi', 'Ima', 'Ishi',
'Iva', 'Jimin', 'Jin', 'Jun', 'Junko',
'Kaede', 'Kagami', 'Kaida', 'Kaiya', 'Kameko',
'Kamin', 'Kanako', 'Kane', 'Kaori', 'Kaoru', 'Kata',
'Kaya', 'Kei', 'Keiko', 'Kiaria', 'Kichi', 'Kiku',
'Kimi', 'Kin', 'Kioko', 'Kira', 'Kita', 'Kiwa',
'Kiyoshi', 'Kohana', 'Koto', 'Kozue',
'Kuma', 'Kumi', 'Kumiko', 'Kuniko', 'Kura', 'Kyoko',
'Leiko', 'Machi', 'Machiko', 'Maeko', 'Maemi', 'Mai',
'Maiko', 'Makiko', 'Mamiko', 'Mariko', 'Masago', 'Masako',
'Matsuko', 'Mayako', 'Mayuko', 'Michi', 'Michiko', 'Midori',
'Mieko', 'Mihoko', 'Mika', 'Miki', 'Minako', 'Minato',
'Mine', 'Misako', 'Misato', 'Mitsuko', 'Miwa', 'Miya',
'Miyoko', 'Miyuki', 'Momoko', 'Mutsuko', 'Myoki', 'Nahoko',
'Nami', 'Nanako', 'Nanami', 'Naoko', 'Naomi', 'Nariko',
'Natsuko', 'Nayoko', 'Nishi', 'Nori', 'Noriko', 'Nozomi',
'Nyoko', 'Oki', 'Rai', 'Raku', 'Rei', 'Reina',
'Reiko', 'Ren', 'Renora', 'Rieko', 'Rikako', 'Riku',
'Rinako', 'Rin', 'Rini', 'Risako', 'Ritsuko', 'Roshin',
'Rumiko', 'Ruri', 'Ryoko', 'Sachi', 'Sachiko', 'Sada',
'Saeko', 'Saiun', 'Saki', 'Sakiko', 'Sakuko', 'Sakura',
'Sakurako', 'Sanako', 'Sasa', 'Sashi', 'Sato', 'Satoko',
'Sawa', 'Sayo', 'Sayoko', 'Seki', 'Shika', 'Shikah',
'Shina', 'Shinko', 'Shoko', 'Sorano', 'Suki', 'Sumi',
'Tadako', 'Taido', 'Taka', 'Takako', 'Takara', 'Taki',
'Tamaka', 'Tamiko', 'Tanaka', 'Taney', 'Tani', 'Taree',
'Tazu', 'Tennen', 'Tetsu', 'Tokiko', 'Tomi', 'Tomiko',
'Tora', 'Tori', 'Toyo', 'Tsubame', 'Umeko', 'Usagi',
'Wakana', 'Washi', 'Yachi', 'Yaki', 'Yama', 'Yasu',
'Yayoi', 'Yei', 'Yoi', 'Yoko', 'Yori', 'Yoshiko',
'Yuka', 'Yukako', 'Yukiko', 'Yumi', 'Yumiko', 'Yuri',
'Yuriko', 'Yutsuko',
]

rpw_surnames = [
'Shadow', 'Dark', 'Light', 'Star', 'Moon', 'Sun', 'Sky', 'Night', 'Dawn',
'Storm', 'Frost', 'Fire', 'Stanley', 'Nero', 'Clifford', 'Volsckev',
'Draven', 'Smith', 'Greisler', 'Wraith', 'Hale', 'Voss', 'Lockhart',
'Ashford', 'Wynters', 'Grayson', 'Ravenwood', 'Langford', 'Averill',
'Cross', 'Kane', 'Holloway', 'Mercer', 'Devereux', 'Vale', 'Alden',
'Blackwell', 'Marcellis', 'Vossler', 'Crane', 'Laurent', 'Radcliffe',
'Hadrian', 'Vexley', 'Roth', 'Everhart', 'Winslow', 'Fayden', 'Crawford',
'Ashborne', 'Davenport', 'Drayton', 'Sutherland', 'Vayne', 'Rosenthal',
'Arkwright', 'Devere', 'Langley', 'Kingsley', 'Vanora', 'Astor',
'Carrington', 'Trevane', 'Remmington', 'Wolfe', 'Drayke', 'Hawke', 'Briar',
'Sterling', 'Crowhurst', 'Marlowe', 'Hastings', 'Westwood', 'Ravenshire',
'Locke', 'Harrow', 'Draxler', 'Valemont', 'Caine', 'Redgrave', 'Frost',
'Vanthorn', 'Ashcroft', 'Moreau', 'Rothwell', 'Varen', 'Lancaster',
'Ashfield', 'Sinclair', 'Duskwood', 'Vermillion', 'Whitlock', 'Halden',
'Faust', 'Ironwood', 'Drayven', 'Grey', 'Valeheart', 'Caldwell', 'Vosslyn',
'Avenhart', 'Nightray', 'Morraine', 'Leclair', 'Hartgrave', 'Thorne',
'Montclair', 'Ashen', 'Dreyer', 'Stormwell', 'Vossen', 'Gryphon',
'Reinhart', 'Claremont', 'Hartley', 'Nightborne', 'Valentine', 'Dreyson',
'Marchand', 'Blackburn', 'Lucan', 'Callister', 'Hartfield', 'Verden',
'Draymor', 'Feyr', 'Ravencroft', 'Ainsley', 'Crestfall', 'Silvera',
'Gravemont', 'Vinter', 'Beaumont', 'Lockridge', 'Thornefield', 'Ashcroft',
'Crowley', 'Winchester', 'Keller', 'Ravenholm', 'Rosier', 'Everett',
'Valeon', 'Marrow', 'Vossell', 'Ashenwald', 'Wyncrest', 'Durand',
'Montague', 'Dreyke', 'Carmine', 'Verlith', 'Harrington', 'Briarson',
'Corvin', 'Tessler', 'Delane', 'Rayven', 'Fletcher', 'Crosswell',
'Sterren', 'Valeric', 'Blackthorn', 'Davenport', 'Vanix', 'Dravien',
'Vexen', 'Rhyker', 'Krynn', 'Greymont', 'Elridge', 'Locksen', 'Harrowell',
'Valeis', 'Avenor', 'Gravelle', 'Dravenhart', 'Noxford', 'Rothen',
'Vallier', 'Devereaux', 'Stormvale', 'Kain', 'Drevis', 'Marchen',
'Langdon', 'Frostell', 'Haldenne', 'Ravenshade', 'Vairn', 'Wyncliff',
'Greystone', 'Vossmer', 'Ashborne', 'Drexel', 'Rykov', 'Drayven',
'Malvern', 'Greyhart', 'Holloway', 'Wraithson', 'Crowden', 'Valleris',
'Stark', 'Wynther', 'Creswell', 'Torrence', 'Arden', 'Fayre', 'Crawell',
'Thayen', 'Morrick', 'Vanier', 'Drevik', 'Hawthorne', 'Evers', 'Aldric',
'Larkson', 'Valemir', 'Dravelle', 'Rothenwald', 'Greyvale', 'Veyron',
'Craven', 'Frostwyn', 'Vares', 'Ashveil', 'Locken', 'Vandrell', 'Silvern',
'Dawncrest', 'Graves', 'Hartwell', 'Falconer', 'Varnell', 'Ashwynn',
'Dravenor', 'Vollaire', 'Kingswell', 'Vashier', 'Larkwell', 'Auren',
'Ravenson', 'Greyborne', 'Voltaire', 'Halewyn', 'Verrin', 'Blackmore',
'Crimson', 'Wrenford', 'Ravelle', 'Valenor', 'Frostfield', 'Vosswick',
'Hollowcrest', 'Veyson', 'Atheron', 'Veyra', 'Raines', 'Grimmond',
'Ashlynn', 'Draywell', 'Vander', 'Vortan', 'Nightwell', 'Vallence', 'Faye',
'Roswell', 'Stormen', 'Havelock', 'Greys', 'Whitmore', 'Thayne', 'Drevan',
'Halric', 'Ashmere', 'Westhall', 'Wray', 'Norring', 'Dane', 'Valeir',
'Kraiven', 'Vosslin', 'Rynhart', 'Eldren', 'Trevane', 'Greisler',
'Hawthorne', 'Morrin', 'Draylen', 'Aurel', 'Briarson', 'Carter', 'Rexford',
'Lynhart', 'Ashland', 'Frostwick', 'Vanloren', 'Crowe', 'Vynne',
'Rothmere', 'Duskhelm', 'Harron', 'Valecrest', 'Merrin', 'Hawken',
'Dreylor', 'Blackwell', 'Farron', 'Caldren', 'Vanora', 'Hollowen',
'Varelle', 'Draymore', 'Westcliff', 'Alder', 'Gryff', 'Ashlock', 'Volsen',
'Drehl', 'Vayden', 'Ravenholt', 'Vossane', 'Krell', 'Marwen', 'Drace',
'Varenne', 'Lockmere', 'Greysten', 'Hawking', 'Ryswell', 'Drayden',
'Cresden', 'Hallow', 'Ashven', 'Valter', 'Greyson', 'Morrinell', 'Wraith',
'Veyden', 'Falken', 'Ashwell', 'Nero', 'Scavendich', 'Volschev', 'Vermont', 'Suez', 'Ashford', 'Blackwood', 'Crane', 'Draven', 'Everhart',
'Frost', 'Grimshaw', 'Hawthorne', 'Ironwood', 'Kingsley', 'Lancaster', 'Mercer', 'Nightshade', 'Oakley', 'Pembroke',
'Radcliffe', 'Shadowfax', 'Thornfield', 'Underwood', 'Vance', 'Whitmore', 'Sterling', 'Ravencroft', 'Ashbury', 'Blackwell',
]

def get_rpw_name():
    return random.choice(rpw_first_names), random.choice(rpw_surnames)


import random
import string

def get_pass():
    name_part = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 7)))
    name_part = name_part.capitalize() if random.choice([True, False]) else name_part.lower()

    symbol_part = ''.join(random.choices('!@#$%^&*()_+=', k=random.randint(2, 3)))
    digit_part = ''.join(random.choices(string.digits, k=random.randint(2, 4)))
    end_part = ''.join(random.choices(string.ascii_letters, k=random.randint(2, 4)))

    optional_upper = ''.join(random.choices(string.ascii_uppercase, k=random.randint(1, 2)))

    parts = [name_part, symbol_part, digit_part, end_part, optional_upper]
    random.shuffle(parts)

    return ''.join(parts)

#######  
#######  

# ====================== EMAIL DOMAIN SELECTION ======================
import domains as _dm

EMAIL_DOMAIN = "1secmail.com"
DOMAIN_PASSWORD_VERIFIED = False

# ── temp-mail.io (with hyphen) support ────────────────────────────────────────
_TEMPMAIL_IO_DOMAIN_SET = {
    'bltiwd.com', 'wnbaldwy.com', 'bwmyga.com', 'ozsaip.com',
    'yzcalo.com', 'lnovic.com', 'ruutukf.com', 'gmeenramy.com',
}
_TEMPMAIL_IO_TOKEN_STORE = {}   # email -> token
_TEMPMAIL_IO_TOKEN_LOCK  = threading.Lock()
_TEMPMAIL_IO_API         = 'https://api.internal.temp-mail.io/api'
_TEMPMAIL_IO_HDRS        = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept':     'application/json',
    'Referer':    'https://temp-mail.io/',
}

def _get_CUSTOM_DOMAINS():
    return _dm.get_custom_domains()

def _get_DOMAIN_PASSWORD():
    return _dm.get_domain_password()

def _get_CUSTOM_DOMAIN_IMAP():
    info = _dm.get_all_info()
    return {e['domain']: e for e in info.get('custom', [])}

# Lazy-evaluated properties used throughout the module
CUSTOM_DOMAINS   = property(_get_CUSTOM_DOMAINS)
DOMAIN_PASSWORD  = property(_get_DOMAIN_PASSWORD)
CUSTOM_DOMAIN_IMAP = property(_get_CUSTOM_DOMAIN_IMAP)

def generate_natural_email(firstname, lastname, domain):
    """Generate a natural-looking email based on the account's real name."""
    fn  = re.sub(r'[^a-zA-Z]', '', firstname).lower()
    ln  = re.sub(r'[^a-zA-Z]', '', lastname).lower()
    fi  = fn[0] if fn else 'x'
    li  = ln[0] if ln else 'x'
    fn3 = fn[:3] if len(fn) >= 3 else fn
    fn4 = fn[:4] if len(fn) >= 4 else fn
    ln3 = ln[:3] if len(ln) >= 3 else ln
    ln4 = ln[:4] if len(ln) >= 4 else ln

    n2  = random.randint(1, 99)
    n3  = random.randint(100, 999)
    n4  = random.randint(1000, 9999)
    yr  = random.randint(1985, 2005)
    yr2 = str(yr)[2:]
    mo  = str(random.randint(1, 12)).zfill(2)
    day = str(random.randint(1, 28)).zfill(2)
    s   = random.choice(['', '_', '.'])
    s2  = random.choice(['_', '.'])

    patterns = [
        # plain name combos
        f"{fn}{ln}",
        f"{fn}{s}{ln}",
        f"{ln}{s}{fn}",
        f"{fn}{ln}{yr2}",
        f"{fn}{s}{ln}{yr2}",
        f"{fn}{s}{ln}{yr}",
        f"{fn}{ln}{yr}",
        # initial + lastname
        f"{fi}{ln}",
        f"{fi}{s}{ln}",
        f"{fi}{ln}{n2}",
        f"{fi}{ln}{yr2}",
        f"{fi}{ln}{yr}",
        f"{fi}{s}{ln}{n2}",
        f"{fi}{s}{ln}{yr2}",
        # firstname + initial
        f"{fn}{li}",
        f"{fn}{s}{li}",
        f"{fn}{li}{n2}",
        f"{fn}{li}{yr2}",
        # with numbers
        f"{fn}{s}{ln}{n2}",
        f"{fn}{s}{ln}{n3}",
        f"{fn}{ln}{n2}",
        f"{fn}{ln}{n3}",
        f"{fn}{ln}{n4}",
        f"{fn}{n2}",
        f"{fn}{n3}",
        f"{ln}{n2}",
        f"{fn}{n2}{s}{ln}",
        # shortened name patterns
        f"{fn3}{ln}",
        f"{fn4}{ln}",
        f"{fn}{ln3}",
        f"{fn}{ln4}",
        f"{fn3}{s2}{ln}",
        f"{fn4}{s2}{ln}",
        f"{fn}{s2}{ln3}",
        f"{fn3}{ln3}",
        f"{fn4}{ln4}",
        # date-based
        f"{fn}{mo}{day}",
        f"{fn}{day}{mo}",
        f"{fn}{s}{ln}{mo}{day}",
        f"{fi}{ln}{mo}{day}",
        f"{fn}{yr}{mo}",
        # personality / Filipino style
        f"its{fn}{ln}",
        f"im{fn}{ln}",
        f"real{fn}{ln}",
        f"the{fn}{ln}",
        f"{fn}{ln}ph",
        f"{fn}{ln}xo",
        f"{fn}{ln}real",
        f"{fn}{ln}official",
        f"hi{s}{fn}{s}{ln}",
        f"hey{fn}{ln}",
        f"just{fn}{ln}",
        f"{fn}{ln}tv",
        f"mr{fn}{ln}",
        f"ms{fn}{ln}",
        f"{fn}{ln}_{yr2}",
        f"{fn}{s2}{ln}{s2}{n2}",
        f"{fi}{s2}{ln}{yr2}",
        f"{fn3}{s2}{ln3}{n2}",
        f"{fn}{yr}{n2}",
        f"{fi}{ln}{yr}{n2}",
        f"{ln}{s2}{fi}{n2}",
    ]

    username = random.choice(patterns)
    username = re.sub(r'[^a-z0-9._-]', '', username)
    if not username:
        username = f"{fn}{ln}{n4}"
    return f"{username}@{domain}"


def get_custom_email(firstname='', lastname=''):
    """Generate name-based email using selected custom domain."""
    if not firstname:
        firstname = fake.first_name()
    if not lastname:
        lastname = fake.last_name()
    return generate_natural_email(firstname, lastname, EMAIL_DOMAIN)


def get_email_for_registration(firstname='', lastname='', domain=None):
    """Return an email for registration.
    For temp-mail.io domains, calls their API to get a real email+token.
    For all other domains, generates locally.
    Pass domain explicitly to avoid the global EMAIL_DOMAIN race condition
    when multiple jobs run concurrently."""
    _domain = domain or EMAIL_DOMAIN
    if not firstname:
        firstname = fake.first_name()
    if not lastname:
        lastname = fake.last_name()
    if _domain in _TEMPMAIL_IO_DOMAIN_SET:
        try:
            _r = requests.post(
                f'{_TEMPMAIL_IO_API}/v3/email/new',
                json={'domain': _domain,
                      'min_name_length': 8, 'max_name_length': 14},
                headers={**_TEMPMAIL_IO_HDRS, 'Content-Type': 'application/json'},
                timeout=10,
            )
            if _r.status_code == 200:
                _d = _r.json()
                _email = _d.get('email', '')
                _token = _d.get('token', '')
                if _email and _token:
                    with _TEMPMAIL_IO_TOKEN_LOCK:
                        _TEMPMAIL_IO_TOKEN_STORE[_email] = _token
                    return _email
        except Exception:
            pass
    return generate_natural_email(firstname, lastname, _domain)

def choose_email_domain():
    """Email Domain Selection Menu"""
    global EMAIL_DOMAIN, DOMAIN_PASSWORD_VERIFIED

    step = 1
    selected = None

    while True:
        # ── STEP 1: Domain selection ───────────────────────────────
        if step == 1:
            clear_screen()
            banner()
            print(f"{W}[{G}1{W}]{G} 1secmail       {G}(API - auto generate)")
            print(f"{W}[{G}2{W}]{G} weyn.store     {R}(domain password required)")
            print(f"{W}[{G}3{W}]{G} jhames.shop    {R}(domain password required)")
            print(f"{W}[{G}4{W}]{G} jakulan.site   {R}(domain password required)")
            linex()
            choice = input(f"{W}[{G}•{W}]{G} Choose Email Domain {W}:{G} ").strip()
            if choice.lower() == 'b':
                return
            if choice == "2":
                selected = "weyn.store"
                step = 2
            elif choice == "3":
                selected = "jhames.shop"
                step = 2
            elif choice == "4":
                selected = "jakulan.site"
                step = 2
            else:
                EMAIL_DOMAIN = "1secmail.com"
                print(f"{G}✓ Selected Domain → {EMAIL_DOMAIN}{W}")
                time.sleep(1.2)
                return

        # ── STEP 2: Domain password (asked only once per session) ──
        elif step == 2:
            if DOMAIN_PASSWORD_VERIFIED:
                EMAIL_DOMAIN = selected
                print(f"{G}✓ Selected Domain → {EMAIL_DOMAIN}{W}")
                time.sleep(1.2)
                return
            clear_screen()
            banner()
            linex()
            entered = input(f"{W}[{R}•{W}]{R} Enter Domain Password {W}:{G} ").strip()
            if entered.lower() == 'b':
                step = 1
                continue
            if entered != DOMAIN_PASSWORD:
                print(f"{R}✘ Wrong password! Access denied.{W}")
                time.sleep(2)
                step = 1
                continue
            DOMAIN_PASSWORD_VERIFIED = True
            EMAIL_DOMAIN = selected
            print(f"{G}✓ Selected Domain → {EMAIL_DOMAIN}{W}")
            time.sleep(1.2)
            return
# ===================================================================
# =================================================================== 

from faker import Faker
import random

fake = Faker()

def get_1secmail(firstname='', lastname=''):
    domain = random.choice(["1secmail.com", "1secmail.net", "1secmail.org"])
    if firstname and lastname:
        return generate_natural_email(firstname, lastname, domain)
    try:
        res = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1", timeout=10)
        data = res.json()
        if data and len(data) > 0:
            return data[0]
    except Exception:
        pass
    fn = fake.first_name()
    ln = fake.last_name()
    return generate_natural_email(fn, ln, domain)

# HTML form extractor
def extractor(data):
    soup = BeautifulSoup(data, "html.parser")
    data = {}
    for inputs in soup.find_all("input"):
        name = inputs.get("name")
        value = inputs.get("value")
        if name:
            data[name] = value
    return data


# Banner
def banner():
    """Display the script banner."""
    clear_screen()
    print(f"""{G}
██╗  ██╗██████╗ ██╗███████╗██╗  ██╗
██║ ██╔╝██╔══██╗██║██╔════╝╚██╗██╔╝
█████╔╝ ██████╔╝██║█████╗   ╚███╔╝ 
██╔═██╗ ██╔══██╗██║██╔══╝   ██╔██╗ 
██║  ██╗██║  ██║██║███████╗██╔╝ ██╗
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝
{M}  ▓▒░  {Y}[ AUTO-FB CREATOR ]{M}  ░▒▓
{DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{W}""")

def linex():
    """Print a separator line."""
    print(f"{DIM}┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄{W}")

# Facebook account creation
# Main account creation function
oks = []
cps = []

#mm2

def check_facebook_profile_picture(uid):
    """Check if a UID has a real profile picture using Facebook Graph API"""
    pic_url = f"https://graph.facebook.com/{uid}/picture?type=normal"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36"
    }
    try:
        response = requests.get(pic_url, headers=headers, allow_redirects=False, timeout=10)
        if response.status_code == 302:
            redirect_url = response.headers.get("Location", "")
            if "scontent" in redirect_url:
             #   print(f"{G}[LIVE] {uid} has a real profile picture.{W}")
                return "live"
            else:
             #   print(f"{R}[DEAD or DEFAULT PIC] {uid} has default/no profile picture.{W}")
                return "not_live"
        else:
          #  print(f"{R}[ERROR] Unexpected response for {uid}: {response.status_code}{W}")
            return
    except requests.RequestException as e:
        return 

FB_LITE_UA = (
    "Mozilla/5.0 (Linux; Android 12; 2201117TY Build/SKQ1.211006.001; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/109.0.5414.86 "
    "Mobile Safari/537.36 [FBAN/FB4A;FBAV/439.0.0.0.8;FBBV/443200018;"
    "FBDM/{density=2.75,width=1080,height=2280};FBLC/en_US;FBRV/0;FBCR/;"
    "FBMF/Xiaomi;FBBD/Redmi;FBPN/com.facebook.lite;FBDV/2201117TY;"
    "FBSV/12;FBOP/1;FBCA/armeabi-v7a:armeabi;]"
)


def _extract_token(patterns, text):
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return ""


def _poll_imap_inbox(to_addr, imap_host, imap_user, imap_pass, timeout_secs=90):
    """
    Poll a catch-all IMAP mailbox for a Facebook confirmation email sent to to_addr.
    Returns the full email body (HTML or text) or None if not found within timeout.
    Works with cPanel/shared hosting — connects to mail.{domain}:993 by default.
    """
    import imaplib
    import email as _email_lib
    from email.header import decode_header as _dh

    deadline = time.time() + timeout_secs
    # Try common IMAP host variants
    hosts_to_try = [imap_host, f"mail.{imap_host.replace('mail.', '')}", imap_host.replace('mail.', '')]
    hosts_to_try = list(dict.fromkeys(hosts_to_try))  # dedupe while preserving order

    while time.time() < deadline:
        for host in hosts_to_try:
            for port, use_ssl in [(993, True), (143, False)]:
                try:
                    if use_ssl:
                        conn = imaplib.IMAP4_SSL(host, port, timeout=15)
                    else:
                        conn = imaplib.IMAP4(host, port)
                    conn.login(imap_user, imap_pass)
                    conn.select("INBOX")

                    # Search for Facebook emails
                    search_criteria = [
                        '(FROM "facebook")',
                        '(SUBJECT "confirmation")',
                        '(SUBJECT "confirm")',
                        '(SUBJECT "registration")',
                        'ALL',
                    ]
                    for criteria in search_criteria:
                        try:
                            _, data = conn.search(None, criteria)
                            ids = data[0].split() if data[0] else []
                            # Check most recent first
                            for num in reversed(ids[-20:]):
                                try:
                                    _, msg_data = conn.fetch(num, '(RFC822)')
                                    raw = msg_data[0][1]
                                    msg = _email_lib.message_from_bytes(raw)

                                    # For catch-all: confirm email is TO our registered address
                                    to_header = msg.get('To', '').lower()
                                    from_header = msg.get('From', '').lower()
                                    subj = msg.get('Subject', '').lower()

                                    is_fb = 'facebook' in from_header or 'facebook' in subj or 'confirm' in subj or 'registration' in subj
                                    is_ours = to_addr.lower() in to_header or not to_header  # accept if TO header missing (some servers strip it)

                                    if is_fb and is_ours:
                                        body = ''
                                        if msg.is_multipart():
                                            for part in msg.walk():
                                                ct = part.get_content_type()
                                                if ct in ('text/plain', 'text/html'):
                                                    try:
                                                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                                    except Exception:
                                                        pass
                                        else:
                                            try:
                                                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                                            except Exception:
                                                body = str(msg.get_payload())
                                        if body:
                                            conn.logout()
                                            return body
                                except Exception:
                                    continue
                        except Exception:
                            continue
                    conn.logout()
                    break  # Connected OK — just no matching email yet, don't retry other ports
                except Exception:
                    continue  # try next host/port combo
        time.sleep(5)
    return None


def get_temp_code(email, timeout_secs=90):
    """
    Poll custom domain inbox for FB's confirmation code.
    Uses IMAP for known custom domains (weyn.store, jhames.shop, jakulan.site).
    Falls back to HTTP webmail endpoints for unknown domains.
    """
    login  = email.split('@')[0].lower()
    domain = email.split('@')[1].lower() if '@' in email else ''

    # Custom domains are webhook-only — code arrives via HTTP POST, not polling
    _imap_map = _dm.get_all_info()
    _imap_map = {e['domain']: e for e in _imap_map.get('custom', [])}
    if domain in _imap_map:
        # Webhook domain: code will be pushed via webhook, nothing to poll here
        return None

    # Fallback: HTTP webmail endpoints for unknown/generic domains
    sess  = requests.Session()
    heads = {
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
        "accept": "text/html,*/*;q=0.9",
        "accept-language": "en-US,en;q=0.9",
    }
    endpoints = [
        f"https://{domain}/inbox/{login}",
        f"https://{domain}/mail/{login}",
        f"https://{domain}/api/v1/inbox/{login}",
        f"https://{domain}/rss/{login}",
    ]
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        for url in endpoints:
            try:
                r = sess.get(url, headers=heads, timeout=10)
                if r.status_code == 200 and len(r.text) > 50:
                    code = re.search(r'\b(\d{5,8})\b', r.text)
                    if code:
                        return code.group(1)
            except Exception:
                continue
        time.sleep(3)
    return None


def save_result(uid, password, cookie):
    """Save confirmed account details to file."""
    try:
        with open('confirmed_accounts.txt', 'a') as f:
            f.write(f"UID: {uid} | PASS: {password} | COOKIE: {cookie}\n")
    except Exception:
        pass
    try:
        with open('/sdcard/Confirmed_Accounts.txt', 'a') as f:
            f.write(f"UID: {uid} | PASS: {password} | COOKIE: {cookie}\n")
    except Exception:
        pass


def confirm_id(mail, uid, otp, data, ses, password=''):
    """Submit confirmation code to FB's confirmation_cliff endpoint."""
    try:
        src     = str(data)
        fb_dtsg = _extract_token([
            r'"token":"([^"]+)"',
            r'name="fb_dtsg" value="([^"]+)"',
            r'\["DTSGInitData"[^\]]*\],\{"token":"([^"]+)"',
        ], src)
        jazoest = _extract_token([
            r'name="jazoest" value="(\d+)"',
            r'"jazoest":"(\d+)"',
        ], src)
        lsd     = _extract_token([
            r'name="lsd" value="([^"]+)"',
            r'"LSD",\[\],\{"token":"([^"]+)"\}',
            r'"lsd":"([^"]+)"',
        ], src)
        rev     = _extract_token(
            [r'"client_revision":(\d+)', r'"server_revision":(\d+)'], src
        ) or "1015920645"

        url    = "https://m.facebook.com/confirmation_cliff/"
        params = {
            'contact': mail,
            'type': 'submit',
            'is_soft_cliff': 'false',
            'medium': 'email',
            'code': otp,
        }
        payload = {
            'fb_dtsg': fb_dtsg,
            'jazoest': jazoest,
            'lsd': lsd,
            '__dyn': '7xeUmwlEnwn8K2WnFwn84a2i5U4e1Fx-ewSwAyUrxCG2O1aDxu2e0GE8xojxi3-4UABwrUmwlE8G-1-2h1px-0nE7i2i3iaohx2-0gKGq326EheV5mxvumFoqmCFoqm_9U9U2Jy5mzU',
            '__csr': '',
            '__req': str(random.randint(4, 12)),
            '__a': '1',
            '__user': uid,
            '__rev': rev,
            '__s': f'{random.randint(0,9)}:{random.randint(0,9)}:{random.randint(0,9)}',
            '__hsi': str(random.randint(7000000000000000000, 7999999999999999999)),
            '__comet_req': '0',
            'action': 'confirm',
        }
        post_headers = {
            'User-Agent': FB_LITE_UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://m.facebook.com',
            'Referer': f'https://m.facebook.com/confirmemail.php?soft=hjk',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-ch-ua': '"Android WebView";v="109", "Chromium";v="109", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-model': '"2201117TY"',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua-platform-version': '"12"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'x-requested-with': 'com.facebook.lite',
            'x-fb-lsd': lsd,
            'x-asbd-id': '129477',
        }
        response = ses.post(url, params=params, data=payload, headers=post_headers, allow_redirects=True, timeout=15)
        if "checkpoint" in str(response.url):
            pass
        else:
            cookie = ";".join([f"{k}={v}" for k, v in ses.cookies.get_dict().items()])
            print(f"\n{Colors.GREEN}╔{'═'*50}╗{Colors.RESET}")
            print(f"{Colors.GREEN}║{Colors.YELLOW}  ✓ EMAIL CONFIRMED{' '*31}{Colors.GREEN}║{Colors.RESET}")
            print(f"{Colors.GREEN}╠{'═'*50}╣{Colors.RESET}")
            print(f"{Colors.GREEN}║{Colors.WHITE}  UID    {Colors.GREEN}│ {Colors.GREEN}{uid}{' '*(39-len(uid))}{Colors.GREEN}║{Colors.RESET}")
            print(f"{Colors.GREEN}║{Colors.WHITE}  PASS   {Colors.GREEN}│ {Colors.GREEN}{password}{' '*(39-len(password))}{Colors.GREEN}║{Colors.RESET}")
            print(f"{Colors.GREEN}║{Colors.WHITE}  COOKIE {Colors.GREEN}│ {Colors.GREEN}{cookie[:35]}...{Colors.GREEN}║{Colors.RESET}")
            print(f"{Colors.GREEN}╚{'═'*50}╝{Colors.RESET}\n")
            save_result(uid, password, cookie)
    except Exception:
        pass


def _poll_1secmail_inbox(username, domain, timeout_secs=45):
    """Poll 1secmail inbox until a Facebook email arrives. Returns message body or None."""
    api = "https://www.1secmail.com/api/v1/"
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        try:
            r = requests.get(
                f"{api}?action=getMessages&login={username}&domain={domain}",
                timeout=10
            )
            msgs = r.json() if r.status_code == 200 else []
            for m in msgs:
                sender = m.get('from', '').lower()
                subj   = m.get('subject', '').lower()
                if 'facebook' in sender or 'facebook' in subj or 'registration' in subj or 'confirm' in subj:
                    # Read full message body
                    r2 = requests.get(
                        f"{api}?action=readMessage&login={username}&domain={domain}&id={m['id']}",
                        timeout=10
                    )
                    if r2.status_code == 200:
                        data = r2.json()
                        return data.get('body', '') or data.get('textBody', '') or data.get('htmlBody', '')
        except Exception:
            pass
        time.sleep(4)
    return None


def _extract_fb_confirm_link(body):
    """Extract Facebook confirmation link from email body."""
    # Try to find confirm link (HTML or plain text)
    patterns = [
        r'https://www\.facebook\.com/confirm[^\s"<>\]\)\\]+',
        r'https://m\.facebook\.com/confirm[^\s"<>\]\)\\]+',
        r'https://www\.facebook\.com/r\.php[^\s"<>\]\)\\]+',
        r'https://[a-z]+\.facebook\.com/[^\s"<>\]\)\\]*confirm[^\s"<>\]\)\\]+',
    ]
    for pat in patterns:
        matches = re.findall(pat, body, re.IGNORECASE)
        if matches:
            link = matches[0].replace('&amp;', '&').rstrip('.')
            return link
    return None


def _extract_fb_confirm_code(body):
    """Extract 5-8 digit confirmation code from email body if no link found."""
    # FB codes are typically 5-8 digits
    codes = re.findall(r'\b([0-9]{5,8})\b', body)
    # Filter out obvious non-codes (years, phone fragments)
    for c in codes:
        if not (1900 <= int(c) <= 2100):
            return c
    return None


def trigger_email_confirmation(ses, email, uid):
    """
    For custom domains: trigger FB to send the confirmation email.
    Strategy: POST the confirmemail form as-is (no injections) — this is
    exactly what the reference does and what actually triggers FB to send.
    Then fire backup resend GETs as belt-and-suspenders.
    1secmail: skip — email arrives on its own.
    """
    try:
        domain = email.split('@')[1].lower() if '@' in email else ''

        SECMAIL_DOMAINS = {
            '1secmail.com', '1secmail.net', '1secmail.org',
            'wwjmp.com', 'esiix.com', 'xojxe.com', 'yoggm.com',
        }

        if domain in SECMAIL_DOMAINS:
            return

        _ch = {
            'User-Agent': FB_LITE_UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://m.facebook.com/',
            'x-requested-with': 'com.facebook.lite',
        }
        _ph = {
            **_ch,
            'Origin': 'https://m.facebook.com',
            'Referer': 'https://m.facebook.com/confirmemail.php?soft=hjk',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        # ── Attempt 1: fetch confirmemail.php, POST form as-is ──────────
        # This exactly matches the reference and is what triggers FB to email.
        for _url in [
            'https://m.facebook.com/confirmemail.php?soft=hjk',
            'https://m.facebook.com/confirmemail.php?soft=1',
        ]:
            try:
                _cp = ses.get(_url, headers=_ch, timeout=12, allow_redirects=True)
                if _cp.status_code != 200 or len(_cp.text) < 100:
                    continue
                soup = BeautifulSoup(_cp.text, 'html.parser')
                form = soup.find('form')
                if form:
                    action = form.get('action', '')
                    if action and not action.startswith('http'):
                        action = 'https://m.facebook.com' + action
                    if not action:
                        action = 'https://m.facebook.com/confirmemail.php'
                    # POST exactly the form fields with no modification
                    fdata = {
                        i.get('name'): i.get('value', '')
                        for i in form.find_all('input') if i.get('name')
                    }
                    ses.post(action, data=fdata, headers=_ph, timeout=12, allow_redirects=True)
                    break
            except Exception:
                continue

        # ── Attempt 2: direct resend GET endpoints as backup ────────────
        for _resend in [
            'https://m.facebook.com/confirmemail.php?send=1',
            'https://m.facebook.com/confirmemail.php?soft=hjk&resend=1',
            'https://www.facebook.com/confirmemail.php?send=1',
        ]:
            try:
                ses.get(_resend, headers=_ch, timeout=8, allow_redirects=True)
            except Exception:
                continue

    except Exception:
        pass


def _full_email_confirm(ses, email, uid, password='', result_queue=None):
    """
    After account creation:
    - Custom domains (weyn.store etc): fire resend triggers so FB emails the inbox.
    - 1secmail domains: fire resend triggers + poll inbox + auto-fill code via queue.
    - harakirimail.com: scrape inbox page + auto-fill code via queue.
    - tempmail.io: poll REST API + auto-fill code via queue.
    """
    _SECMAIL_DOMAINS = {
        '1secmail.com', '1secmail.net', '1secmail.org',
        'wwjmp.com', 'esiix.com', 'xojxe.com', 'yoggm.com',
    }
    _HARAKIRI_DOMAINS    = {'harakirimail.com'}
    _WEYN_EMAILS_DOMAINS = {'cunt.abrdns.com', 'jinbilowg.cloud-ip.cc', 'yuennix.work.gd'}
    _WEYN_EMAILS_API     = 'https://weyn-emails-production.up.railway.app'
    _domain = email.split('@')[1].lower() if '@' in email else ''
    _is_secmail       = _domain in _SECMAIL_DOMAINS
    _is_harakiri      = _domain in _HARAKIRI_DOMAINS
    _is_tempmail_io   = _domain in _TEMPMAIL_IO_DOMAIN_SET
    _is_weyn_emails   = _domain in _WEYN_EMAILS_DOMAINS

    _ch = {
        'User-Agent': FB_LITE_UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://m.facebook.com/',
        'x-requested-with': 'com.facebook.lite',
    }
    _ph = {
        **_ch,
        'Origin': 'https://m.facebook.com',
        'Referer': 'https://m.facebook.com/confirmemail.php?soft=hjk',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    _resend_urls = [
        'https://m.facebook.com/confirmemail.php?send=1',
        'https://m.facebook.com/confirmemail.php?soft=hjk&send=1',
        'https://m.facebook.com/confirmemail.php?soft=hjk&resend=1',
        'https://m.facebook.com/confirmemail.php?soft=1&send=1',
        'https://www.facebook.com/confirmemail.php?send=1',
    ]

    import threading as _th2
    import concurrent.futures as _cf2

    def _fire_resends():
        """Fire ALL resend URLs simultaneously in parallel — completes in ~5s max."""
        def _hit(u):
            try:
                ses.get(u, headers={**_ch, 'Referer': 'https://m.facebook.com/confirmemail.php'},
                        timeout=6, allow_redirects=True)
            except Exception:
                pass
        with _cf2.ThreadPoolExecutor(max_workers=len(_resend_urls)) as _ex:
            _ex.map(_hit, _resend_urls)

    def _form_post_trigger():
        """Visit confirmemail.php, extract form, POST it — tells FB to send the email."""
        for _url in [
            'https://m.facebook.com/confirmemail.php?soft=hjk',
            'https://m.facebook.com/confirmemail.php',
            'https://m.facebook.com/confirmemail.php?soft=1',
        ]:
            try:
                _cp = ses.get(_url, headers=_ch, timeout=8, allow_redirects=True)
                if _cp.status_code == 200 and len(_cp.text) > 100:
                    soup = BeautifulSoup(_cp.text, 'html.parser')
                    form = soup.find('form')
                    if form:
                        action = form.get('action', '')
                        if action and not action.startswith('http'):
                            action = 'https://m.facebook.com' + action
                        if not action:
                            action = 'https://m.facebook.com/confirmemail.php'
                        fdata = {i.get('name'): i.get('value', '') for i in form.find_all('input') if i.get('name')}
                        ses.post(action, data=fdata, headers=_ph, timeout=8, allow_redirects=True)
                        return True
            except Exception:
                continue
        return False

    _stop_poll = _th2.Event()

    def _auto_submit_code(code):
        """
        Immediately submit a numeric FB confirmation code using the live session.
        Tries form-parse, then confirmation_cliff.
        Returns 'confirmed', 'checkpoint', or 'failed'.
        """
        _ph2 = {
            **_ch,
            'Content-Type':    'application/x-www-form-urlencoded',
            'Origin':          'https://m.facebook.com',
            'Cache-Control':   'max-age=0',
            'sec-ch-ua':       '"Android WebView";v="109", "Chromium";v="109", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile':    '?1',
            'sec-ch-ua-platform':  '"Android"',
            'sec-fetch-dest':  'document',
            'sec-fetch-mode':  'navigate',
            'sec-fetch-site':  'same-origin',
            'upgrade-insecure-requests': '1',
        }

        def _chk(url, text):
            u = url.lower(); t = text.lower()
            if 'checkpoint' in u:
                return 'checkpoint'
            if ('home.php' in u
                    or u.rstrip('/').endswith('facebook.com')
                    or 'confirmed' in t or 'verified' in t
                    or 'thank' in t):
                return 'confirmed'
            return None

        # ── A1: Parse the real form and POST with the code ────────────────────
        for _try_url in [
            'https://m.facebook.com/confirmemail.php',
            'https://m.facebook.com/confirmemail.php?soft=hjk',
            'https://m.facebook.com/confirmemail.php?soft=1',
        ]:
            try:
                _r = ses.get(_try_url, headers=_ch, timeout=12, allow_redirects=True)
                _ru = str(_r.url)
                q = _chk(_ru, _r.text)
                if q:
                    return q
                _html = _r.text
                _soup = BeautifulSoup(_html, 'html.parser')
                _fd   = {}
                _act  = _try_url
                _form = _soup.find('form')
                if _form:
                    _a = _form.get('action', '').strip()
                    if _a:
                        _act = (_a if _a.startswith('http')
                                else 'https://m.facebook.com' + _a)
                    for _i in _form.find_all('input'):
                        _n = _i.get('name', '').strip()
                        _v = _i.get('value', '')
                        if _n:
                            _fd[_n] = _v
                # Broaden token search if form is missing CSRF
                if not _fd.get('fb_dtsg'):
                    _mm = re.search(r'"token"\s*:\s*"([^"]{10,})"', _html)
                    if _mm:
                        _fd['fb_dtsg'] = _mm.group(1)
                if not _fd.get('lsd'):
                    _mm = re.search(r'"LSD"[^{]*\{"token":"([^"]+)"', _html)
                    if _mm:
                        _fd['lsd'] = _mm.group(1)
                # Inject code into every known field name
                for _fn in ['n', 'code', 'confirm_code']:
                    _fd[_fn] = code
                _resp = ses.post(_act, data=_fd,
                                 headers={**_ph2, 'Referer': _try_url},
                                 allow_redirects=True, timeout=15)
                q = _chk(str(_resp.url), _resp.text)
                if q:
                    return q
            except Exception:
                pass

        # ── A2: confirmation_cliff with tokens ────────────────────────────────
        try:
            _r    = ses.get('https://m.facebook.com/confirmemail.php',
                            headers=_ch, timeout=10)
            _html = _r.text
            _soup = BeautifulSoup(_html, 'html.parser')
            _fb_dtsg = _jazoest = _lsd = ''
            for _i in _soup.find_all('input', {'name': True}):
                _n = _i['name']; _v = _i.get('value', '')
                if _n == 'fb_dtsg':   _fb_dtsg  = _v
                elif _n == 'jazoest': _jazoest  = _v
                elif _n == 'lsd':     _lsd      = _v
            if not _fb_dtsg:
                _mm = re.search(r'"token"\s*:\s*"([^"]{10,})"', _html)
                if _mm:
                    _fb_dtsg = _mm.group(1)
            if _fb_dtsg:
                _resp = ses.post(
                    'https://m.facebook.com/confirmation_cliff/',
                    params={
                        'contact':       email,
                        'type':          'submit',
                        'is_soft_cliff': 'false',
                        'medium':        'email',
                        'code':          code,
                    },
                    data={
                        'fb_dtsg':  _fb_dtsg,
                        'jazoest':  _jazoest,
                        'lsd':      _lsd,
                        'action':   'confirm',
                        '__user':   uid,
                        '__a':      '1',
                        '__dyn':    '',
                        '__csr':    '',
                    },
                    headers={**_ph2,
                             'Referer':  'https://m.facebook.com/confirmemail.php',
                             'x-fb-lsd': _lsd},
                    allow_redirects=True,
                    timeout=15,
                )
                q = _chk(str(_resp.url), _resp.text)
                if q:
                    return q
        except Exception:
            pass

        return 'failed'

    def _run_triggers():
        """Fire form POST + ALL resend URLs simultaneously, zero delays."""
        try:
            all_jobs = [_form_post_trigger] + [
                (lambda u: (lambda: ses.get(
                    u,
                    headers={**_ch, 'Referer': 'https://m.facebook.com/confirmemail.php'},
                    timeout=6, allow_redirects=True
                )))(url) for url in _resend_urls
            ]
            with _cf2.ThreadPoolExecutor(max_workers=len(all_jobs)) as _ex:
                _futs = [_ex.submit(fn) for fn in all_jobs]
                _cf2.wait(_futs, timeout=10)
        except Exception:
            pass

    def _poll_secmail():
        """Poll 1secmail inbox every 2s. Prints code as soon as it arrives."""
        _login = email.split('@')[0]
        _api = 'https://www.1secmail.com/api/v1/'
        _seen_ids = set()
        _deadline = time.time() + 150
        while time.time() < _deadline and not _stop_poll.is_set():
            try:
                _r = requests.get(
                    f"{_api}?action=getMessages&login={_login}&domain={_domain}",
                    timeout=8
                )
                _msgs = _r.json() if _r.status_code == 200 else []
                for _m in _msgs:
                    _mid = _m.get('id')
                    if _mid in _seen_ids:
                        continue
                    _seen_ids.add(_mid)
                    _subj = _m.get('subject', '').lower()
                    _from = _m.get('from', '').lower()
                    if not ('facebook' in _from or 'confirm' in _subj or
                            'registration' in _subj or 'code' in _subj or 'meta' in _from):
                        continue
                    _r2 = requests.get(
                        f"{_api}?action=readMessage&login={_login}&domain={_domain}&id={_mid}",
                        timeout=8
                    )
                    if _r2.status_code != 200:
                        continue
                    _bd = _r2.json()
                    _body = _bd.get('htmlBody') or _bd.get('body') or _bd.get('textBody') or ''
                    # Try confirmation link first
                    _lm = re.search(
                        r'https://(?:www|m)\.facebook\.com/(?:confirm|r\.php)[^\s"<>\]\\]+',
                        _body, re.IGNORECASE
                    )
                    if _lm:
                        _link = _lm.group(0).replace('&amp;', '&').rstrip('.')
                        _el = email[:36]; _ll = _link[:36]
                        print(f"\n{G}╔{'═'*47}╗")
                        print(f"{G}║{Y}  ✉  CONFIRM LINK RECEIVED              {G}║")
                        print(f"{G}╠{'═'*47}╣")
                        print(f"{G}║{W}  EMAIL {DIM}│{G} {_el}{' '*(37-len(_el))}{G}║")
                        print(f"{G}║{W}  LINK  {DIM}│{C} {_ll}{' '*(37-len(_ll))}{G}║")
                        print(f"{G}╚{'═'*47}╝{W}")
                        # Auto-follow the link (no code to type) and report result
                        if result_queue:
                            try:
                                _lr = ses.get(_link, headers=_ch, timeout=12, allow_redirects=True)
                                if 'checkpoint' in str(_lr.url):
                                    result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': 'checkpoint'})
                                else:
                                    result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': 'confirmed'})
                            except Exception:
                                result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': 'link_error'})
                        _stop_poll.set()
                        return
                    # Try numeric code
                    _codes = re.findall(r'\b([0-9]{5,8})\b', _body)
                    for _c in _codes:
                        if not (1900 <= int(_c) <= 2100):
                            _el = email[:36]
                            print(f"\n{G}╔{'═'*47}╗")
                            print(f"{G}║{Y}  ✉  CONFIRMATION CODE RECEIVED         {G}║")
                            print(f"{G}╠{'═'*47}╣")
                            print(f"{G}║{W}  EMAIL {DIM}│{G} {_el}{' '*(37-len(_el))}{G}║")
                            print(f"{G}║{W}  CODE  {DIM}│{Y}  {_c}{' '*(36-len(_c))}{G}║")
                            print(f"{G}╚{'═'*47}╝{W}")
                            # Auto-submit immediately; fall back to manual UI
                            print(f"{G}  [auto] Submitting code {_c} for UID {uid}…{W}")
                            _as = _auto_submit_code(_c)
                            print(f"{G}  [auto] Result: {_as}{W}")
                            if result_queue:
                                if _as == 'confirmed':
                                    result_queue.put({'type': 'confirm_result', 'uid': uid,
                                                      'status': 'confirmed', 'method': 'code'})
                                elif _as == 'checkpoint':
                                    result_queue.put({'type': 'confirm_result', 'uid': uid,
                                                      'status': 'checkpoint'})
                                else:
                                    # Auto-submit failed → show code for manual entry
                                    result_queue.put({'type': 'confirm_code', 'uid': uid, 'code': _c})
                            _stop_poll.set()
                            return
            except Exception:
                pass
            time.sleep(2)
        if not _stop_poll.is_set():
            print(f"{Y}  [!] No code received for {email} within 2.5 min{W}")
            if result_queue:
                result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': 'timeout'})

    def _poll_harakiri():
        """
        Poll harakirimail.com for up to 2.5 min.
        Real endpoints discovered from /js/inbox-ck.js:
          - List : GET /api/v1/inbox/{login}  → {emails:[{_id,from,subject,received}]}
          - Email: GET /email/{_id}           → JSON with html/body/content field
        """
        _login    = email.split('@')[0]
        _deadline = time.time() + 150
        _seen_ids = set()

        _hdrs = {
            'User-Agent':     ('Mozilla/5.0 (Linux; Android 11; Redmi Note 8) '
                               'AppleWebKit/537.36 (KHTML, like Gecko) '
                               'Chrome/109.0.5414.118 Mobile Safari/537.36'),
            'Accept':         'application/json',
            'Accept-Language':'en-US,en;q=0.9',
            'Referer':        f'https://harakirimail.com/inbox/{_login}',
        }

        def _process_body(_body_str):
            """
            Extract FB confirmation link or numeric code from email body.
            Returns True if handled (code found and acted on).

            Strategy:
              1) Follow FB confirmation link if present (most reliable).
              2) Strip HTML → strip URLs → search for code near context keywords.
              3) Last-resort: any isolated 5–6 digit number not inside a URL.
            Searching raw HTML is intentionally avoided — it causes false positives
            from CSS pixel values, image dimensions, URL parameters, etc.
            """
            # ── 1) FB confirmation link ────────────────────────────────────────
            _lm = re.search(
                r'https://(?:www|m)\.facebook\.com/(?:confirm|r\.php)[^\s"<>\]\\]+',
                _body_str, re.IGNORECASE
            )
            if _lm:
                _link = _lm.group(0).replace('&amp;', '&').rstrip('.')
                print(f"{G}  [harakiri] Confirm link → {_link[:60]}{W}")
                if result_queue:
                    try:
                        _lr = ses.get(_link, headers=_ch, timeout=12, allow_redirects=True)
                        _st = ('checkpoint' if 'checkpoint' in str(_lr.url) else 'confirmed')
                    except Exception:
                        _st = 'link_error'
                    result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': _st})
                _stop_poll.set()
                return True

            # ── 2) Convert HTML → plain text ───────────────────────────────────
            try:
                _plain = BeautifulSoup(_body_str, 'html.parser').get_text(separator=' ')
            except Exception:
                _plain = _body_str

            # Remove URLs entirely before digit hunting — they contain many
            # fake numbers (tracking IDs, timestamps, pixel sizes, etc.)
            _clean = re.sub(r'https?://\S+', ' ', _plain)
            _clean = re.sub(r'\s+', ' ', _clean)

            def _try_code(_c):
                """Emit code to UI for display. Returns True if we should stop polling."""
                _n = int(_c)
                if 1900 <= _n <= 2100:
                    return False
                print(f"{G}  [harakiri] Code fetched → {_c}{W}")
                if result_queue:
                    result_queue.put({'type': 'confirm_code', 'uid': uid, 'code': _c})
                _stop_poll.set()
                return True

            # ── 3) Contextual patterns — number right next to confirm keywords ─
            # Facebook confirmation codes are always 5–6 digits.
            _ctx_pats = [
                r'(?:confirmation|verification|confirm(?:ation)?)\s*code[:\s\-]+(\d{5,6})',
                r'(?:your|the)\s+(?:confirmation\s+)?code\s+(?:is\s+)?[:\-]?\s*(\d{5,6})',
                r'code[:\s\-]+(\d{5,6})\b',
                r'\b(\d{5,6})\s+(?:is\s+your|to\s+confirm|to\s+verify)',
                r'enter\s+(?:the\s+)?(?:code|number)[:\s\-]+(\d{5,6})',
                r'(?:^|\s)(\d{5,6})(?:\s|$)',   # isolated 5–6 digit token on its own
            ]
            for _pat in _ctx_pats:
                for _c in re.findall(_pat, _clean, re.IGNORECASE | re.MULTILINE):
                    if _try_code(_c):
                        return True

            # ── 4) Last-resort: any standalone 5–6 digit number ───────────────
            # (URLs already stripped, so this won't match tracking IDs)
            for _c in re.findall(r'\b(\d{5,6})\b', _clean):
                if _try_code(_c):
                    return True

            return False

        while time.time() < _deadline and not _stop_poll.is_set():
            try:
                _r = requests.get(
                    f'https://harakirimail.com/api/v1/inbox/{_login}',
                    headers=_hdrs, timeout=15
                )
                if _r.status_code == 200:
                    _data   = _r.json()
                    _emails = _data.get('emails') or []

                    for _msg in _emails:
                        _mid = str(_msg.get('_id') or '')
                        if not _mid or _mid in _seen_ids:
                            continue

                        _from_t = str(_msg.get('from', '')).lower()
                        _subj_t = str(_msg.get('subject', '')).lower()
                        _is_fb  = ('facebook' in _from_t or 'facebookmail' in _from_t
                                   or 'meta'  in _from_t
                                   or 'confirm'      in _subj_t
                                   or 'registration' in _subj_t
                                   or 'code'         in _subj_t
                                   or 'verification' in _subj_t)
                        _seen_ids.add(_mid)

                        if not _is_fb:
                            print(f"  [harakiri] skip non-FB email: {_msg.get('from','')} / {_msg.get('subject','')}")
                            continue

                        print(f"{G}  [harakiri] FB email found — id={_mid} subj={_msg.get('subject','')}{W}")

                        # Fetch the full email body via /api/v1/email/{_id}
                        # Fields per main-ck.js: bodyhtml, bodytext
                        _body = ''
                        try:
                            _er = requests.get(
                                f'https://harakirimail.com/api/v1/email/{_mid}',
                                headers=_hdrs, timeout=15
                            )
                            if _er.status_code == 200:
                                try:
                                    _ed   = _er.json()
                                    # Prefer HTML body (has links/codes), fall back to plain text
                                    _body = str(_ed.get('bodyhtml') or _ed.get('bodytext') or
                                                _ed.get('html') or _ed.get('body') or
                                                _ed.get('text') or '')
                                    if not _body:
                                        _body = _er.text
                                except Exception:
                                    _body = _er.text
                        except Exception as _fe:
                            print(f"{Y}  [harakiri] email fetch error: {_fe}{W}")

                        if _body:
                            if _process_body(_body):
                                return
                        else:
                            print(f"{Y}  [harakiri] empty body for id={_mid}{W}")

            except Exception as _pe:
                print(f"{Y}  [harakiri] poll error: {_pe}{W}")

            time.sleep(3)

        if not _stop_poll.is_set():
            print(f"{Y}  [!] No harakiri code for {email} within 2.5 min{W}")
            if result_queue:
                result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': 'timeout'})

    def _poll_tempmail_io():
        """
        Poll temp-mail.io (with hyphen) REST API for up to 2.5 min.
        API base: https://api.internal.temp-mail.io/api
          - Create : POST /v3/email/new → {email, token}
          - Messages: GET /v3/email/{token}/messages → {messages:[...]}
        Token is pre-stored in _TEMPMAIL_IO_TOKEN_STORE at email-generation time.
        """
        _deadline = time.time() + 150
        _seen_ids = set()

        # Look up pre-stored token; if missing try to create a fresh one for same domain
        with _TEMPMAIL_IO_TOKEN_LOCK:
            _token = _TEMPMAIL_IO_TOKEN_STORE.get(email)
        if not _token:
            try:
                _domain_part = email.split('@')[1] if '@' in email else ''
                _cr = requests.post(
                    f'{_TEMPMAIL_IO_API}/v3/email/new',
                    json={'domain': _domain_part,
                          'min_name_length': 8, 'max_name_length': 14},
                    headers={**_TEMPMAIL_IO_HDRS, 'Content-Type': 'application/json'},
                    timeout=10,
                )
                if _cr.status_code == 200:
                    _cd = _cr.json()
                    _token = _cd.get('token', '')
                    _new_email = _cd.get('email', '')
                    if _token and _new_email:
                        with _TEMPMAIL_IO_TOKEN_LOCK:
                            _TEMPMAIL_IO_TOKEN_STORE[_new_email] = _token
            except Exception:
                pass

        if not _token:
            print(f"{Y}  [temp-mail.io] No token for {email} — cannot poll{W}")
            if result_queue:
                result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': 'timeout'})
            return

        _msg_url = f'{_TEMPMAIL_IO_API}/v3/email/{_token}/messages'

        while time.time() < _deadline and not _stop_poll.is_set():
            try:
                _r = requests.get(_msg_url, headers=_TEMPMAIL_IO_HDRS, timeout=12)
                _msgs = []
                if _r.status_code == 200:
                    _data = _r.json()
                    if isinstance(_data, list):
                        _msgs = _data
                    else:
                        _msgs = (_data.get('messages') or _data.get('mails') or
                                 _data.get('emails') or _data.get('data') or [])

                for _msg in _msgs:
                    _mid = str(_msg.get('id') or _msg.get('_id') or '')
                    if not _mid or _mid in _seen_ids:
                        continue

                    _from_t = str(_msg.get('from', '')).lower()
                    _subj_t = str(_msg.get('subject', '')).lower()
                    _is_fb  = ('facebook' in _from_t or 'facebookmail' in _from_t
                               or 'meta'         in _from_t
                               or 'confirm'      in _subj_t
                               or 'registration' in _subj_t
                               or 'code'         in _subj_t
                               or 'verification' in _subj_t)
                    _seen_ids.add(_mid)
                    if not _is_fb:
                        continue

                    print(f"{G}  [tempmail.io] FB email found — id={_mid} subj={_msg.get('subject','')}{W}")

                    # Body may already be in the list response
                    _body = str(_msg.get('body_html') or _msg.get('html') or
                                _msg.get('body') or _msg.get('text') or
                                _msg.get('bodyhtml') or _msg.get('bodytext') or '')

                    # If not, fetch the individual message via token-based endpoint
                    if not _body:
                        try:
                            _emurl = f'{_TEMPMAIL_IO_API}/v3/email/{_token}/messages/{_mid}'
                            _er = requests.get(_emurl, headers=_TEMPMAIL_IO_HDRS, timeout=12)
                            if _er.status_code == 200:
                                try:
                                    _ed = _er.json()
                                    _body = str(_ed.get('body_html') or _ed.get('html') or
                                                _ed.get('body') or _ed.get('text') or
                                                _ed.get('bodyhtml') or _ed.get('bodytext') or '')
                                except Exception:
                                    _body = _er.text
                        except Exception as _fe:
                            print(f"{Y}  [temp-mail.io] email fetch error: {_fe}{W}")

                    if _body:
                        # Reuse the same _process_body logic from harakiri
                        # ── 1) FB confirmation link ─────────────────────────────────────
                        _lm = re.search(
                            r'https://(?:www|m)\.facebook\.com/(?:confirm|r\.php)[^\s"<>\]\\]+',
                            _body, re.IGNORECASE
                        )
                        if _lm:
                            _link = _lm.group(0).replace('&amp;', '&').rstrip('.')
                            print(f"{G}  [tempmail.io] Confirm link → {_link[:60]}{W}")
                            if result_queue:
                                try:
                                    _lr = ses.get(_link, headers=_ch, timeout=12, allow_redirects=True)
                                    _st = ('checkpoint' if 'checkpoint' in str(_lr.url) else 'confirmed')
                                except Exception:
                                    _st = 'link_error'
                                result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': _st})
                            _stop_poll.set()
                            return

                        try:
                            _plain = BeautifulSoup(_body, 'html.parser').get_text(separator=' ')
                        except Exception:
                            _plain = _body
                        _clean = re.sub(r'https?://\S+', ' ', _plain)
                        _clean = re.sub(r'\s+', ' ', _clean)

                        _ctx_pats = [
                            r'(?:confirmation|verification|confirm(?:ation)?)\s*code[:\s\-]+(\d{5,6})',
                            r'(?:your|the)\s+(?:confirmation\s+)?code\s+(?:is\s+)?[:\-]?\s*(\d{5,6})',
                            r'code[:\s\-]+(\d{5,6})\b',
                            r'\b(\d{5,6})\s+(?:is\s+your|to\s+confirm|to\s+verify)',
                            r'enter\s+(?:the\s+)?(?:code|number)[:\s\-]+(\d{5,6})',
                            r'(?:^|\s)(\d{5,6})(?:\s|$)',
                        ]
                        _found = False
                        for _pat in _ctx_pats:
                            for _c in re.findall(_pat, _clean, re.IGNORECASE | re.MULTILINE):
                                _n = int(_c)
                                if 1900 <= _n <= 2100:
                                    continue
                                print(f"{G}  [tempmail.io] Code fetched → {_c}{W}")
                                # Always show code in UI first (same as harakirimail)
                                if result_queue:
                                    result_queue.put({'type': 'confirm_code', 'uid': uid, 'code': _c})
                                _stop_poll.set()
                                # Also try auto-submit; emit result if it worked
                                _as = _auto_submit_code(_c)
                                if result_queue:
                                    if _as == 'confirmed':
                                        result_queue.put({'type': 'confirm_result', 'uid': uid,
                                                          'status': 'confirmed', 'method': 'code'})
                                    elif _as == 'checkpoint':
                                        result_queue.put({'type': 'confirm_result', 'uid': uid,
                                                          'status': 'checkpoint'})
                                _found = True
                                break
                            if _found:
                                return

                        for _c in re.findall(r'\b(\d{5,6})\b', _clean):
                            _n = int(_c)
                            if 1900 <= _n <= 2100:
                                continue
                            print(f"{G}  [tempmail.io] Code (last-resort) → {_c}{W}")
                            if result_queue:
                                result_queue.put({'type': 'confirm_code', 'uid': uid, 'code': _c})
                            _stop_poll.set()
                            return
                    else:
                        print(f"{Y}  [tempmail.io] empty body for id={_mid}{W}")

            except Exception as _pe:
                print(f"{Y}  [tempmail.io] poll error: {_pe}{W}")

            time.sleep(3)

        if not _stop_poll.is_set():
            print(f"{Y}  [!] No tempmail.io code for {email} within 2.5 min{W}")
            if result_queue:
                result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': 'timeout'})

    def _poll_weyn_emails():
        """Poll weyn-emails API every 3s for up to 2.5 min."""
        _login   = email.split('@')[0]
        _seen    = set()
        _deadline = time.time() + 150
        print(f"{G}  [weyn-emails] Polling inbox for {email}…{W}")
        while time.time() < _deadline and not _stop_poll.is_set():
            try:
                _r = requests.get(f'{_WEYN_EMAILS_API}/api/emails', timeout=10)
                if _r.status_code == 200:
                    _msgs = _r.json() if isinstance(_r.json(), list) else []
                    for _msg in _msgs:
                        if str(_msg.get('toAddress', '')).lower() != email.lower():
                            continue
                        _mid = str(_msg.get('id', ''))
                        if _mid in _seen:
                            continue
                        _from_t = str(_msg.get('fromAddress', '')).lower()
                        _subj_t = str(_msg.get('subject', '')).lower()
                        _is_fb  = ('facebook' in _from_t or 'facebookmail' in _from_t
                                    or 'meta' in _from_t
                                    or 'confirm' in _subj_t or 'code' in _subj_t
                                    or 'verification' in _subj_t or 'registration' in _subj_t)
                        _seen.add(_mid)
                        if not _is_fb:
                            continue
                        _body     = str(_msg.get('bodyHtml') or _msg.get('bodyText') or '')
                        _combined = str(_msg.get('subject', '')) + ' ' + _body
                        _c = _process_body(_combined)
                        if _c:
                            print(f"{G}  [weyn-emails] Code found → {_c}{W}")
                            if result_queue:
                                result_queue.put({'type': 'confirm_code', 'uid': uid, 'code': _c})
                            _stop_poll.set()
                            _as = _auto_submit_code(_c)
                            print(f"{G}  [weyn-emails] Auto-submit result: {_as}{W}")
                            if result_queue:
                                if _as == 'confirmed':
                                    result_queue.put({'type': 'confirm_result', 'uid': uid,
                                                      'status': 'confirmed', 'method': 'code'})
                                elif _as == 'checkpoint':
                                    result_queue.put({'type': 'confirm_result', 'uid': uid,
                                                      'status': 'checkpoint'})
                            return
            except Exception as _we:
                print(f"{Y}  [weyn-emails] error: {_we}{W}")
            time.sleep(3)
        if not _stop_poll.is_set():
            print(f"{Y}  [!] No weyn-emails code for {email} within 2.5 min{W}")
            if result_queue:
                result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': 'timeout'})

    def _poll_webhook():
        """
        Poll storage every 3s for up to 2.5 min waiting for the webhook
        endpoint to store a confirmation code for this uid.
        When found, push confirm_code event and attempt auto-submit.
        """
        import storage as _storage
        _wh_key  = f'webhook_code_{uid}'
        _deadline = time.time() + 150
        print(f"{C}  [webhook] Waiting for code via webhook for {email} (uid={uid})…{W}")
        while time.time() < _deadline and not _stop_poll.is_set():
            try:
                _stored = _storage.load(_wh_key, None)
                if _stored and isinstance(_stored, dict) and _stored.get('code'):
                    _c = str(_stored['code'])
                    # Clear so retries don't re-use a stale code
                    _storage.save(_wh_key, {})
                    print(f"{G}  [webhook] Code received → {_c}{W}")
                    if result_queue:
                        result_queue.put({'type': 'confirm_code', 'uid': uid, 'code': _c})
                    _stop_poll.set()
                    # Attempt auto-submit; report result
                    _as = _auto_submit_code(_c)
                    print(f"{G}  [webhook] Auto-submit result: {_as}{W}")
                    if result_queue:
                        if _as == 'confirmed':
                            result_queue.put({'type': 'confirm_result', 'uid': uid,
                                              'status': 'confirmed', 'method': 'code'})
                        elif _as == 'checkpoint':
                            result_queue.put({'type': 'confirm_result', 'uid': uid,
                                              'status': 'checkpoint'})
                    return
            except Exception as _we:
                print(f"{Y}  [webhook] poll error: {_we}{W}")
            time.sleep(3)
        if not _stop_poll.is_set():
            print(f"{Y}  [!] No webhook code for {email} within 2.5 min{W}")
            if result_queue:
                result_queue.put({'type': 'confirm_result', 'uid': uid, 'status': 'timeout'})

    try:
        if _is_secmail:
            # Start polling immediately, triggers run in parallel
            _pt = _th2.Thread(target=_poll_secmail, daemon=True)
            _pt.start()
            _run_triggers()
            _pt.join(timeout=150)
        elif _is_harakiri:
            # Harakiri: poll inbox page + fire FB resend triggers
            _pt = _th2.Thread(target=_poll_harakiri, daemon=True)
            _pt.start()
            _run_triggers()
            _pt.join(timeout=150)
        elif _is_tempmail_io:
            # tempmail.io: poll REST API + fire FB resend triggers
            _pt = _th2.Thread(target=_poll_tempmail_io, daemon=True)
            _pt.start()
            _run_triggers()
            _pt.join(timeout=150)
        elif _is_weyn_emails:
            # weyn-emails: poll REST API + fire FB resend triggers
            _pt = _th2.Thread(target=_poll_weyn_emails, daemon=True)
            _pt.start()
            _run_triggers()
            _pt.join(timeout=150)
        else:
            # Webhook domain — fire FB resend triggers, then poll storage
            # for the code that the webhook endpoint will store when it arrives.
            _pt = _th2.Thread(target=_poll_webhook, daemon=True)
            _pt.start()
            _run_triggers()
            _pt.join(timeout=150)
    except Exception:
        pass


def createfb_method_1():
    global oks, cps, EMAIL_DOMAIN, DOMAIN_PASSWORD_VERIFIED

    step = 1
    name_choice = num = password_choice = pww = gender_choice = show_details = None
    chosen_domain = None

    while True:
        # ── STEP 1: Name type ──────────────────────────────────────
        if step == 1:
            clear_screen()
            banner()
            print(f"{W}[{G}1{W}]{G} FILIPINO NAMES")
            print(f"{W}[{G}2{W}]{G} RPW NAMES")
            linex()
            v = input(f"{W}[{G}•{W}]{G} CHOISE {W}:{G} ").strip()
            if v.lower() == 'b':
                return
            name_choice = v
            step = 2

        # ── STEP 2: Email domain ────────────────────────────────────
        elif step == 2:
            clear_screen()
            banner()
            print(f"{W}[{G}1{W}]{G} 1secmail       {G}(API - auto generate)")
            print(f"{W}[{G}2{W}]{G} weyn.store     {R}(domain password required)")
            print(f"{W}[{G}3{W}]{G} jhames.shop    {R}(domain password required)")
            print(f"{W}[{G}4{W}]{G} jakulan.site   {R}(domain password required)")
            linex()
            v = input(f"{W}[{G}•{W}]{G} EMAIL DOMAIN {W}:{G} ").strip()
            if v.lower() == 'b':
                step = 1
                continue
            if v == '2':
                chosen_domain = "weyn.store"
            elif v == '3':
                chosen_domain = "jhames.shop"
            elif v == '4':
                chosen_domain = "jakulan.site"
            else:
                EMAIL_DOMAIN = "1secmail.com"
                step = 3
                continue
            # custom domain needs password
            if not DOMAIN_PASSWORD_VERIFIED:
                clear_screen()
                banner()
                linex()
                pw = input(f"{W}[{R}•{W}]{R} Enter Domain Password {W}:{G} ").strip()
                if pw.lower() == 'b':
                    continue
                if pw != DOMAIN_PASSWORD:
                    print(f"{R}✘ Wrong password! Access denied.{W}")
                    time.sleep(1.5)
                    continue
                DOMAIN_PASSWORD_VERIFIED = True
            EMAIL_DOMAIN = chosen_domain
            step = 3

        # ── STEP 3: How many accounts ──────────────────────────────
        elif step == 3:
            clear_screen()
            banner()
            linex()
            v = input(f"{W}[{G}•{W}]{G} HOW MANY ACCOUNT {W}:{G} ").strip()
            if v.lower() == 'b':
                step = 2
                continue
            try:
                num = int(v)
            except ValueError:
                continue
            step = 4

        # ── STEP 4: Password type ──────────────────────────────────
        elif step == 4:
            clear_screen()
            banner()
            print(f"{W}[{G}1{W}]{G} AUTO PASSWORD")
            print(f"{W}[{G}2{W}]{G} CUSTOM PASSWORD")
            linex()
            v = input(f"{W}[{G}•{W}]{G} CHOISE {W}:{G} ").strip()
            if v.lower() == 'b':
                step = 3
                continue
            password_choice = v
            if password_choice == '2':
                step = 5
            else:
                pww = get_pass()
                step = 6

        # ── STEP 5: Custom password entry ─────────────────────────
        elif step == 5:
            clear_screen()
            banner()
            linex()
            v = input(f"{W}[{G}•{W}]{G} ENTER PASSWORD {W}:{G} ").strip()
            if v.lower() == 'b':
                step = 4
                continue
            pww = v
            step = 6

        # ── STEP 6: Gender ─────────────────────────────────────────
        elif step == 6:
            clear_screen()
            banner()
            print(f"{W}[{G}1{W}]{G} MALE")
            print(f"{W}[{G}2{W}]{G} FEMALE")
            print(f"{W}[{G}3{W}]{G} MIXED")
            linex()
            v = input(f"{W}[{G}•{W}]{G} GENDER {W}:{G} ").strip()
            if v.lower() == 'b':
                step = 4
                continue
            gender_choice = v
            step = 7

        # ── STEP 7: Show details ───────────────────────────────────
        elif step == 7:
            clear_screen()
            banner()
            linex()
            v = input(f"{W}[{G}•{W}]{G} Show All Details y{R}/{G}n {W}:{G} ").strip().lower()
            if v == 'b':
                step = 6
                continue
            show_details = v
            break   # all inputs collected, proceed

    banner()
    print(f"{G}  ◈ {W}ACCOUNT CREATION {G}STARTED")
    print(f"{DIM}  TARGET  {G}→  {Y}{num}{W} accounts")
    print(f"{DIM}  DOMAIN  {G}→  {M}{EMAIL_DOMAIN}{W}")
    print(f"{DIM}  TIP     {G}→  {R}Use 1.1.1 VPN for best results{W}")
    linex()

    import threading
    from concurrent.futures import ThreadPoolExecutor

    lock = threading.Lock()
    done = [0]  # accounts successfully created so far

    def _create_one():
        while True:
            with lock:
                if done[0] >= num:
                    return
            try:
                ses = requests.Session()
                response = ses.get("https://m.facebook.com/reg/", timeout=15)
                form = extractor(response.text)

                if not form.get("lsd") and not form.get("fb_dtsg"):
                    continue

                if name_choice == '2':
                    firstname, lastname = get_rpw_name()
                else:
                    base_first, base_last = get_bd_name()
                    if gender_choice == '1':
                        firstname = random.choice(first_names_male)
                    elif gender_choice == '2':
                        firstname = random.choice(first_names_female)
                    else:
                        firstname = random.choice(first_names_male + first_names_female)
                    lastname = base_last
                if gender_choice == '1':
                    fb_sex = "2"
                elif gender_choice == '2':
                    fb_sex = "1"
                else:
                    fb_sex = random.choice(["1", "2"])
                phone = get_email_for_registration(firstname, lastname)

                _pt = form.get('privacy_mutation_token', '')
                from urllib.parse import quote as _uq
                if _pt:
                    _reg_url = f"https://m.facebook.com/reg/submit/?privacy_mutation_token={_uq(_pt)}&multi_step_form=1&skip_suma=0"
                else:
                    _reg_url = "https://m.facebook.com/reg/submit/?multi_step_form=1&skip_suma=0"

                payload = {
                    'ccp': "2",
                    'reg_instance': form.get("reg_instance", ""),
                    'submission_request': "true",
                    'reg_impression_id': form.get("reg_impression_id", ""),
                    'ns': "1",
                    'logger_id': form.get("logger_id", ""),
                    'firstname': firstname,
                    'lastname': lastname,
                    'birthday_day': str(random.randint(1, 28)),
                    'birthday_month': str(random.randint(1, 12)),
                    'birthday_year': str(random.randint(1985, 2005)),
                    'reg_email__': phone,
                    'reg_passwd__': pww,
                    'sex': fb_sex,
                    'encpass': f'#PWD_BROWSER:0:{int(time.time())}:{pww}',
                    'submit': "Sign Up",
                    'privacy_mutation_token': _pt,
                    'fb_dtsg': form.get("fb_dtsg", ""),
                    'jazoest': form.get("jazoest", ""),
                    'lsd': form.get("lsd", ""),
                    '__dyn': '', '__csr': '', '__req': 'q', '__a': '', '__user': '0',
                }

                merged_headers = {
                    'User-Agent': FB_LITE_UA,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'max-age=0',
                    'Origin': 'https://m.facebook.com',
                    'Referer': 'https://m.facebook.com/reg/',
                    'sec-ch-prefers-color-scheme': 'light',
                    'sec-ch-ua': '"Android WebView";v="109", "Chromium";v="109", "Not_A Brand";v="24"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'x-requested-with': 'com.facebook.lite',
                    'viewport-width': '980',
                }

                reg_submit = ses.post(_reg_url, data=payload, headers=merged_headers, timeout=20)
                login_coki = ses.cookies.get_dict()

                if "c_user" in login_coki:
                    coki = ";".join([f"{k}={v}" for k, v in login_coki.items()])
                    uid = login_coki["c_user"]
                    with lock:
                        if done[0] >= num:
                            return
                        done[0] += 1
                        current = done[0]
                        oks.append(uid)

                    # ── INSTANT trigger: fire all resend URLs right now, no thread wait ──
                    import concurrent.futures as _cfi
                    import threading as _th
                    _instant_urls = [
                        'https://m.facebook.com/confirmemail.php?send=1',
                        'https://m.facebook.com/confirmemail.php?soft=hjk&send=1',
                        'https://m.facebook.com/confirmemail.php?soft=hjk&resend=1',
                        'https://m.facebook.com/confirmemail.php?soft=1&send=1',
                        'https://www.facebook.com/confirmemail.php?send=1',
                    ]
                    _ih = {
                        'User-Agent': FB_LITE_UA,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Referer': 'https://m.facebook.com/confirmemail.php',
                        'x-requested-with': 'com.facebook.lite',
                    }
                    def _ifire(u):
                        try:
                            ses.get(u, headers=_ih, timeout=6, allow_redirects=True)
                        except Exception:
                            pass
                    with _cfi.ThreadPoolExecutor(max_workers=len(_instant_urls)) as _ipool:
                        _ipool.map(_ifire, _instant_urls)

                    # Background thread handles 1secmail polling + repeat trigger waves
                    _t = _th.Thread(target=_full_email_confirm, args=(ses, phone, uid, pww), daemon=False)
                    _t.start()

                    with lock:
                        if show_details == 'y':
                            print(f"\n{G}╔{'═'*45}╗")
                            print(f"{G}║{Y}  ✓ CREATED  {W}[{Y}{current}{W}/{Y}{num}{W}]{G}{' '*(31 - len(str(current)) - len(str(num)))}║")
                            print(f"{G}╠{'═'*45}╣")
                            print(f"{G}║{W}  NAME  {DIM}│{G} {firstname} {lastname}{' '*(36 - len(firstname) - len(lastname))}{G}║")
                            print(f"{G}║{W}  EMAIL {DIM}│{G} {phone}{' '*(37 - len(phone))}{G}║")
                            print(f"{G}║{W}  PASS  {DIM}│{Y} {pww}{' '*(37 - len(pww))}{G}║")
                            print(f"{G}║{W}  UID   {DIM}│{M} {uid}{' '*(37 - len(uid))}{G}║")
                            print(f"{G}╚{'═'*45}╝{W}")
                        else:
                            print(f"{G}  ✓{W} {Y}[{current}/{num}]{DIM}  {uid}  {W}{pww}")
                        # Save to accounts.txt with full details
                        try:
                            with open('accounts.txt', 'a') as f:
                                f.write(f"{firstname} {lastname}|{phone}|{pww}|{uid}\n")
                        except Exception:
                            pass
                        # Also try sdcard path for Android
                        try:
                            with open('/sdcard/Auto_Creat.txt', 'a') as f:
                                f.write(f"{firstname} {lastname}|{phone}|{pww}|{uid}\n")
                        except Exception:
                            pass
                    # continue loop — keep trying until done[0] >= num

                elif "checkpoint" in login_coki:
                    uid = login_coki.get("c_user", "unknown")
                    with lock:
                        cps.append(uid)
            except Exception:
                pass

    WORKERS = 10
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(_create_one) for _ in range(WORKERS)]
        for f in futures:
            f.result()

    # Completion summary
    print(f"\n{G}╔{'═'*45}╗")
    print(f"{G}║{Y}        ◈  PROCESS COMPLETE  ◈{' '*16}{G}║")
    print(f"{G}╠{'═'*45}╣")
    print(f"{G}║{W}  CREATED   {DIM}│{G} {len(oks)}{' '*(32 - len(str(len(oks))))}  {G}║")
    print(f"{G}║{W}  CHECKPOINT{DIM}│{R} {len(cps)}{' '*(32 - len(str(len(cps))))}  {G}║")
    print(f"{G}╚{'═'*45}╝{W}")
    linex()
    input(f'{DIM}  Press Enter to return to menu...{W} ')


def register_account(domain_choice, name_option="1", gender_option="3", custom_pass=None, max_retries=5):
    """
    Called by bot.py to create a single Facebook account.
    Returns dict {name, email, password, uid} on success, or None on failure.
    """
    from urllib.parse import quote as _uq

    while True:
        try:
            ses = requests.Session()
            response = ses.get("https://m.facebook.com/reg/", timeout=15)
            form = extractor(response.text)

            if not form.get("lsd") and not form.get("fb_dtsg"):
                continue

            if name_option == "2":
                firstname, lastname = get_rpw_name()
            else:
                if gender_option == "1":
                    firstname = random.choice(first_names_male)
                elif gender_option == "2":
                    firstname = random.choice(first_names_female)
                else:
                    firstname = random.choice(first_names_male + first_names_female)
                lastname = random.choice(surnames)

            if gender_option == "1":
                fb_sex = "2"
            elif gender_option == "2":
                fb_sex = "1"
            else:
                fb_sex = random.choice(["1", "2"])

            email = get_email_for_registration(firstname, lastname)
            pww   = custom_pass if custom_pass else get_pass()

            _pt = form.get('privacy_mutation_token', '')
            if _pt:
                _reg_url = f"https://m.facebook.com/reg/submit/?privacy_mutation_token={_uq(_pt)}&multi_step_form=1&skip_suma=0"
            else:
                _reg_url = "https://m.facebook.com/reg/submit/?multi_step_form=1&skip_suma=0"

            payload = {
                'ccp': "2",
                'reg_instance': form.get("reg_instance", ""),
                'submission_request': "true",
                'reg_impression_id': form.get("reg_impression_id", ""),
                'ns': "1",
                'logger_id': form.get("logger_id", ""),
                'firstname': firstname,
                'lastname': lastname,
                'birthday_day': str(random.randint(1, 28)),
                'birthday_month': str(random.randint(1, 12)),
                'birthday_year': str(random.randint(1985, 2005)),
                'reg_email__': email,
                'reg_passwd__': pww,
                'sex': fb_sex,
                'encpass': f'#PWD_BROWSER:0:{int(time.time())}:{pww}',
                'submit': "Sign Up",
                'privacy_mutation_token': _pt,
                'fb_dtsg': form.get("fb_dtsg", ""),
                'jazoest': form.get("jazoest", ""),
                'lsd': form.get("lsd", ""),
                '__dyn': '', '__csr': '', '__req': 'q', '__a': '', '__user': '0',
            }

            headers = {
                'User-Agent': FB_LITE_UA,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'max-age=0',
                'Origin': 'https://m.facebook.com',
                'Referer': 'https://m.facebook.com/reg/',
                'sec-ch-prefers-color-scheme': 'light',
                'sec-ch-ua': '"Android WebView";v="109", "Chromium";v="109", "Not_A Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'x-requested-with': 'com.facebook.lite',
                'viewport-width': '980',
            }

            reg_submit = ses.post(_reg_url, data=payload, headers=headers, timeout=20)
            login_coki = ses.cookies.get_dict()

            if "c_user" in login_coki:
                return {
                    "name":     f"{firstname} {lastname}",
                    "email":    email,
                    "password": pww,
                    "uid":      login_coki["c_user"],
                }

        except Exception:
            pass


# Main menu
def method():
    """Main menu for selecting script functionality."""
    while True:
        clear_screen()
        banner()
        print(f"{W}[{G}1{W}]{G} Auto Create Fb")
        linex()
        choice = input(f"{W}[{G}•{W}]{G} CHOISE {W}:{G} ").strip()
        if choice == '1':
            createfb_method_1()
        elif choice.lower() == 'b':
            break
        else:
            continue

if __name__ == "__main__":
    sys.stdout.write('\x1b]2; CYBER-X\x07')
    install_dependencies()
    method()
