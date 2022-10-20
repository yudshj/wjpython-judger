import re
import os
import shutil
from pathlib import Path
# import itertools
from collections import defaultdict
import pandas as pd
import argparse
# import IPython
# import subprocess
import hashlib
# from binascii import a2b_hex
from typing import TypedDict, Optional

class ResultType(TypedDict):
    score: float
    ac_subid: int
    name: str


def judge_list(filename_list: list):
    dct = defaultdict(list)
    for filename in filename_list:
        hasher = hashlib.sha512()
        for line in open(filename, 'r'):
            bin = re.sub(r'[ \t\n\r]', '', line).encode()
            hasher.update(bin)
        dct[hasher.digest()].append(filename)
    ret = [dct[k] for k in dct if len(dct[k]) > 1]
    # IPython.embed()
    return ret


def main():
    parser = argparse.ArgumentParser(description='judge')
    parser.add_argument('--hwid', type=str, help='homework id in playground dir', required=True)
    args = parser.parse_args()


    HW_ID = args.hwid
    SRC_DIR = f"./playground/{HW_ID}/"
    DST_DIR = f"./playground/{HW_ID}_copied_code/"
    BASE_SUFFIX = "_base"
    COPIED_SUFFIX = "_copied"
    COMMENT_SUFFIX = "_comment"
    TA_USERIDS = [137238, 90322, 935617, 1106922, 936531, 810106, 1256347, 1145420]

    pattern = r"([0-9]*)_([0-9]*)_([A-Z]*)_([0-9]*)\((.*)\)\.py3"


    xuanke = pd.read_excel('选课名单.xls',dtype=str)

    score_map = {
        'AC' : 2.0,
        'PE' : 1.0,
        'WA' : 0.1,
        'RE' : 0.0,
        'CE' : 0.0,
        'TLE' : 0.1,
        'MLE' : 0.1,
        'WT' : 0.1,
    }

    lst = os.listdir(SRC_DIR)
    dic: dict[str, dict[int, dict[str, list[tuple[int, str]]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    xuehao_to_userid: dict[str, int] = {}
    userid_to_xuehao: dict[int, str] = {}
    for name in lst:
        if name.endswith(".py3"):
            match = re.match(pattern, name)
            if match is None: continue
            SUBID, PROBID, STATUS, USERID, USERNAME = match.groups()
            SUBID = int(SUBID)
            USERID = int(USERID)
            if USERID in TA_USERIDS: continue
            dic[PROBID][USERID][STATUS].append((SUBID, name))
            for xuehao in xuanke['学号']:
                if xuehao in USERNAME:
                    xuehao_to_userid[xuehao] = USERID
                    userid_to_xuehao[USERID] = xuehao
                    break

    results: dict[str, dict[int, ResultType]] = defaultdict(lambda: defaultdict(lambda: ResultType(score=0.0, ac_subid=0, name="")))

    for prob_id, userid_2_status_subid in dic.items():
        for userid, status_2_subid in userid_2_status_subid.items():
            max_score = 0.0
            stat = (-1, '')
            for status, subid in status_2_subid.items():
                if status == 'AC': stat = max(subid)
                max_score = max(max_score, score_map[status])
            results[prob_id][userid] = ResultType(score=max_score, ac_subid=stat[0], name=stat[1])

    prob_ids = sorted(results.keys())
    df = pd.DataFrame(columns=[x+BASE_SUFFIX for x in prob_ids] + [x+COPIED_SUFFIX for x in prob_ids] + [x+COMMENT_SUFFIX for x in prob_ids], index=xuanke.index)
    df = xuanke.merge(df, left_index=True, right_index=True)

    prob_to_filelist = defaultdict(list)
    filename_to_commented = {}

    for prob_id, userid_2_info in results.items():
        for userid, info in userid_2_info.items():
            if info['ac_subid'] == -1: continue
            if userid not in userid_to_xuehao: continue
            src_path = os.path.join(SRC_DIR, info['name'])
            prob_to_filelist[prob_id].append(src_path)
            code = "".join(open(src_path).readlines())
            commented = "'''" in code or "#" in code
            df.loc[df['学号'] == userid_to_xuehao[userid], prob_id+COMMENT_SUFFIX] = 'yes' if commented else 'no'


    for prob_id, userid_2_info in results.items():
        for userid, info in userid_2_info.items():
            if userid not in userid_to_xuehao: continue
            df.loc[df['学号'] == userid_to_xuehao[userid], prob_id+BASE_SUFFIX] = info['score']

    for prob_id in prob_ids:
        filename_lst = prob_to_filelist[prob_id]
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
                if match is None: continue
                SUBID, PROBID, STATUS, USERID, USERNAME = match.groups()
                USERID = int(USERID)
                df.loc[df['学号'] == userid_to_xuehao[USERID],  prob_id+COPIED_SUFFIX] = "yes-%03d" % i
                
                dst_dir = os.path.join(prob_dst_dir, "%03d" % i)
                Path(dst_dir).mkdir(exist_ok=True, parents=True)
                shutil.copy(name, dst_dir)
                print(f"    {final_name}")

    for x in prob_ids:
        col = x + COMMENT_SUFFIX
        df[col] = df[col].fillna('N/A')
        
        col = x + COPIED_SUFFIX
        df[col] = df[col].fillna('no')
        
        col = x + BASE_SUFFIX
        df[col] = df[col].fillna(0.0)


    df.to_csv(f'{HW_ID}_result.csv')


if __name__ == '__main__':
    main()