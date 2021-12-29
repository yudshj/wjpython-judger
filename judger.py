import re
import os
import shutil
from pathlib import Path
import itertools
from collections import defaultdict
import pandas as pd
import argparse
import IPython
import subprocess
from binascii import a2b_hex

parser = argparse.ArgumentParser(description='judge')
parser.add_argument('--hwid', type=str, help='homework id in playground dir', required=True)
args = parser.parse_args()


def judge_list(filename_list: list):
    proc = subprocess.Popen(['parallel', '-x', 'bash ./get_hash.sh {}'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    # proc = subprocess.Popen(['xargs', '-I{}', 'bash ./get_hash.sh {}'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out,err = proc.communicate(input='\n'.join(filename_list).encode())
    res = out.decode().split('\n')
    source_codes = [(a2b_hex(x[:128].strip()), x[128:].strip()) for x in res]
    dct = defaultdict(list)
    for k,v in source_codes:
        dct[k].append(v)
    ret = [dct[k] for k in dct if len(dct[k]) > 1]
    # IPython.embed()
    return ret




HW_ID = args.hwid
SRC_DIR = f"./playground/{HW_ID}/raw_data"
DST_DIR = f"./playground/{HW_ID}/copied_code"
BASE_SUFFIX = "_base"
COPIED_SUFFIX = "_copied"
COMMENT_SUFFIX = "_comment"
TA_USERNAMES = ['Yudong', 'fuqi', 'hjl', 'liumugeng', 'Guo Yaoqi', 'liukb']
TA_USERIDS = [137238,90322,935617,1106922,936531,810106]

pattern = r"([0-9]*)_([0-9]*)_([A-Z]*)_([0-9]*)\((.*)\)\.py3"




xuanke = pd.read_csv('userid_studentid_final.csv',dtype=str)
xuanke.dropna(axis='index', inplace=True)
xuanke['userid'] = xuanke['userid'].astype(int)
xuanke = xuanke.set_index('userid')




score_map = {
    'AC' : 2.0,
    'PE' : 1.0,
    'WA' : 1.0,
    'RE' : 0.0,
    'CE' : 0.0,
    'TLE' : 1.0,
    'MLE' : 0.3,
    'WT' : 0.4,
}




lst = os.listdir(SRC_DIR)
dic = {}
for name in lst:
    if name.endswith(".py3"):
        match = re.match(pattern, name)
        SUBID, PROBID, STATUS, USERID, USERNAME = match.groups()
        USERID = int(USERID)
        if USERID in TA_USERIDS: continue
        if USERID not in xuanke.index: continue
        SUBID = int(SUBID)
        if PROBID not in dic:
            dic[PROBID] = {}
        if USERID not in dic[PROBID]:
            dic[PROBID][USERID] = {}
        if STATUS not in dic[PROBID][USERID]:
            dic[PROBID][USERID][STATUS] = []
        dic[PROBID][USERID][STATUS].append((SUBID, name))




for prob_id, username_2_status_subid in dic.items():
    for username, status_2_subid in username_2_status_subid.items():
        max_score = 0.0
        stat = (-1, '')
        for status, subid in status_2_subid.items():
            if status == 'AC': stat = max(subid)
            max_score = max(max_score, score_map[status])
        dic[prob_id][username] = {'score': max_score, 'stat': stat[0], 'name': stat[1]}




prob_ids = sorted(dic.keys())
prob_ids




df = pd.DataFrame(columns=[x+BASE_SUFFIX for x in prob_ids] + [x+COPIED_SUFFIX for x in prob_ids] + [x+COMMENT_SUFFIX for x in prob_ids], index=xuanke.index)




df = xuanke.merge(df, left_index=True, right_index=True)




prob_to_filelist = defaultdict(list)
filename_to_commented = {}

for prob_id, username_2_info in dic.items():
    for username, info in username_2_info.items():
        if info['stat'] == -1: continue
        src_path = os.path.join(SRC_DIR, info['name'])
        prob_to_filelist[prob_id].append(src_path)
        code = "".join(open(src_path).readlines())
        commented = "'''" in code or "#" in code
        df.loc[username, prob_id+COMMENT_SUFFIX] = 'yes' if commented else 'no'




for prob_id, username_2_info in dic.items():
    for username, info in username_2_info.items():
        df.loc[username,prob_id+BASE_SUFFIX] = info['score']
df




# df.loc[1174596]




for prob_id in prob_ids:
    filename_lst = prob_to_filelist[prob_id]
    # for name in filename_lst:
    #     final_name = name.split('/')[-1]
    #     if final_name == "31033847_05_AC_1177305(Lizihao).py3" or final_name == "31027825_05_AC_1174596(1700013940-郭彬然).py3":
    #         print(final_name)
    same_lst = judge_list(filename_lst)
    print(prob_id)
    prob_dst_dir = os.path.join(DST_DIR, prob_id)
    if os.path.exists(prob_dst_dir):
        shutil.rmtree(prob_dst_dir)
    for i, lst in enumerate(same_lst):
        print(f"  list{i}:")
        for name in lst:
            final_name = name.split('/')[-1]
            match = re.match(pattern, final_name)
            SUBID, PROBID, STATUS, USERID, USERNAME = match.groups()
            df.loc[int(USERID), prob_id+COPIED_SUFFIX] = "yes-%03d" % i
            
            dst_dir = os.path.join(prob_dst_dir, "%03d" % i)
            Path(dst_dir).mkdir(exist_ok=True, parents=True)
            shutil.copy(name, dst_dir)
            print(f"    {final_name}")
# df




for x in prob_ids:
    col = x + COMMENT_SUFFIX
    df[col] = df[col].fillna('N/A')
    
    col = x + COPIED_SUFFIX
    df[col] = df[col].fillna('no')
    
    col = x + BASE_SUFFIX
    df[col] = df[col].fillna(0.0)
df




df.to_csv(f'{HW_ID}_result.csv')






