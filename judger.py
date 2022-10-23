import argparse
import hashlib
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Optional, TypedDict

import pandas as pd


parser = argparse.ArgumentParser(description='judge')
parser.add_argument('hwid', type=str, help='homework id in playground dir')
args = parser.parse_args()

config = json.load(open("config.json", "r", encoding="utf-8"))

BASE_SUFFIX = config['base_suffix']
COPIED_SUFFIX = config['copied_suffix']
COMMENT_SUFFIX = config['comment_suffix']
TA_USERIDS = config['ta_userids']
SKIP_COMMENTS = config['skip_comments']
SKIP_SPACES = config['skip_spaces']

HW_ID = args.hwid
SRC_DIR = f"./playground/{HW_ID}/"
DST_DIR = f"./playground/{HW_ID}_copied_code/"

class ResultType(TypedDict):
    score: float
    ac_subid: Optional[int]
    name: str


def judge_list(filename_list: list):
    dct = defaultdict(list)
    for filename in filename_list:
        text = open(filename, "r", encoding="utf-8").read()

        if SKIP_COMMENTS:
            # remove all comments from python3 file
            text = re.sub(r"#.*", "", text)
            text = re.sub(r'""".*?"""', "", text, flags=re.DOTALL)
            text = re.sub(r"'''.*?'''", "", text, flags=re.DOTALL)

        if SKIP_SPACES:
            # remove all spaces
            text = re.sub(r"\s+", "", text)

        hash_digest = hashlib.sha512(text.encode("utf-8")).hexdigest()
        dct[hash_digest].append(filename)

    ret = [dct[k] for k in dct if len(dct[k]) > 1]
    # IPython.embed()
    return ret


def main():
    dst_path = Path(DST_DIR)
    if dst_path.exists():
        shutil.rmtree(dst_path)
    dst_path.mkdir(parents=True)

    pattern = r"([0-9]*)_([0-9]*)_([A-Z]*)_([0-9]*)\((.*)\)\.py3"


    xuanke = pd.read_excel('选课名单.xls', dtype=str)

    score_map = {
        'AC' : 2.0,
        'PE' : 1.0,
        'WA' : 1.0,
        'RE' : 0.0,
        'CE' : 0.0,
        'TLE' : 1.0,
        'MLE' : 1.0,
        'WT' : 0.0,
    }

    lst = os.listdir(SRC_DIR)
    dic: dict[str, dict[int, dict[str, list[tuple[int, str]]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    xuehao_to_userid: dict[str, int] = {}
    userid_to_xuehao: dict[int, str] = {}
    for name in lst:
        if name.endswith(".py3"):
            match = re.match(pattern, name)
            if match is None: continue
            subid, probid, status, userid, username = match.groups()
            subid = int(subid)
            userid = int(userid)
            if userid in TA_USERIDS: continue
            dic[probid][userid][status].append((subid, name))
            for xuehao in xuanke['学号']:
                if xuehao in username:
                    xuehao_to_userid[xuehao] = userid
                    userid_to_xuehao[userid] = xuehao
                    break

    results: dict[str, dict[int, ResultType]] = defaultdict(lambda: defaultdict(lambda: ResultType(score=0.0, ac_subid=0, name="")))

    for prob_id, userid_2_status_subid in dic.items():
        for userid, status_2_subid in userid_2_status_subid.items():
            max_score = 0.0
            stat = (None, '')
            for status, subid in status_2_subid.items():
                if status == 'AC': stat = max(subid)
                max_score = max(max_score, score_map[status])
            results[prob_id][userid] = ResultType(score=max_score, ac_subid=stat[0], name=stat[1])

    prob_ids = sorted(results.keys())
    df = pd.DataFrame(columns=[x+y for y in (BASE_SUFFIX, COPIED_SUFFIX, COMMENT_SUFFIX) for x in prob_ids], index=xuanke.index)
    df = xuanke.merge(df, left_index=True, right_index=True)

    prob_to_filelist = defaultdict(list)
    filename_to_commented = {}

    for prob_id, userid_2_info in results.items():
        for userid, info in userid_2_info.items():
            if (info['ac_subid'] is None) or (userid not in userid_to_xuehao): continue
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
                subid, probid, status, userid, username = match.groups()
                userid = int(userid)
                df.loc[df['学号'] == userid_to_xuehao[userid],  prob_id+COPIED_SUFFIX] = "yes-%03d" % i
                
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


    df.to_csv(f'{HW_ID}_result.csv', index=False)


if __name__ == '__main__':
    main()
