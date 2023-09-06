import json, os
import argparse
import openai
import time
from tqdm import tqdm
from collections import Counter
from utils import openai_completion

def parse_option():
    parser = argparse.ArgumentParser("command line arguments for recall columns")
    parser.add_argument("--input_recalled_tables_path", type=str)
    parser.add_argument("--self_consistent", type=bool, default=True)
    parser.add_argument("--n", type=int, default=5,
                        help="Size of self-consistent set")
    parser.add_argument("--add_fk", type=bool, default=True)
    parser.add_argument("--output_recalled_columns_path", type=str)

    opt = parser.parse_args()

    return opt


def generate_reply(input, sc_num):
    completions = openai_completion(input, sc_num)
    if completions is None:
        return None

    tabs_cols_all = []
    for i in range(sc_num):
        raw_tab_col = completions.choices[i].message.content
        try:
            raw_tab_col = '{' + raw_tab_col.split('{', 1)[1]
            raw_tab_col = raw_tab_col.rsplit('}', 1)[0] + '}'
            raw_tab_col = json.loads(raw_tab_col)
        except:
            print('list error')
            return None
        tabs_cols_all.append(raw_tab_col)
    return tabs_cols_all


def generate_schema(data):
    schema = ""
    for table in data['db_schema']:
        schema += '# ' + table['table_name_original'] + ' ( '
        for i, column in enumerate(table['column_names_original']):
            schema += column
            schema += ', '
        schema = schema[:-2] + ' )\n'
    return schema


def extract_fks(strings):
    fks = {}

    for string in strings:
        parts = string.split(' = ')
        left_side = parts[0].split('.')
        right_side = parts[1].split('.')

        left_table = left_side[0]
        left_column = left_side[1]

        right_table = right_side[0]
        right_column = right_side[1]

        if left_table not in fks:
            fks[left_table] = []

        fks[left_table].append(left_column)

        if right_table not in fks:
            fks[right_table] = []

        fks[right_table].append(right_column)

    return fks


def column_sc(tabs_cols_all, tabs_cols_ori, fk_ori, add_fk):
    candidates = {}
    results = {}
    for key in tabs_cols_ori:
        candidates[key] = []

    # filter out invalid tables
    for tabs_cols in tabs_cols_all:
        for key, value in tabs_cols.items():
            if key in tabs_cols_ori:
                candidates[key].append(value)

    for tab, cols_all in candidates.items():
        cols_ori = [item.lower() for item in tabs_cols_ori[tab]]
        cols_sc = []
        for cols in cols_all:
            cols_exist = []
            for col in cols:
                if col.lower() in cols_ori:
                    cols_exist.append(col)
                    if len(cols_exist) == 4:
                        break
            if len(cols_exist) > 0:
                cols_sc.append(cols_exist)
        # choose the top-5 columns with the highest frequency
        if len(cols_sc) > 0:
            cols_add = []
            for cols in cols_sc:
                cols_add = cols_add + cols
            counter = Counter(cols_add)
            most_common_cols = counter.most_common(5)
            temp = []
            for value, count in most_common_cols:
                temp.append(value)
            results[tab] = temp
        else:
            results[tab] = []

    if add_fk:
        fk = extract_fks(fk_ori)
        for tab, cols in fk.items():
            if tab in results:
                for col in cols:
                    if col not in results[tab]:
                        results[tab].append(col)
    return results


def info_generate(tabs_cols, data):
    info = {}
    info['db_id'] = data['db_id']
    info['question'] = data['question']
    info['schema'] = tabs_cols
    info['fk'] = data['fk']
    return info


instruction = '''Given the database tables and question, perform the following actions: 
1 - Rank the columns in each table based on the possibility of being used in the SQL, Column that matches more with the question words or the foreign key is highly relevant and must be placed ahead. You should output them in the order of the most relevant to the least relevant.
Explain why you choose each column.
2 - Output a JSON object that contains all the columns in each table according to your explanation. The format should be like: 
{
    "table_1": ["column_1", "column_2", ......], 
    "table_2": ["column_1", "column_2", ......],
    "table_3": ["column_1", "column_2", ......],
     ......
}

'''

def recall_column(input_recalled_tables_path, output_recalled_columns_path, add_fk, sc_num):
    with open(input_recalled_tables_path) as f:
        data_all = json.load(f)
    res = []
    for i, data in enumerate(tqdm(data_all)):
        schema = generate_schema(data)
        prompt = instruction + 'Schema:\n' + schema
        prompt = prompt + 'Foreign keys: \n'
        for fk in data['fk']:
            prompt = prompt + '# ' + fk + '\n'
        prompt += "\nQuestion:\n### " + data["question"]
        # print(prompt)
        tabs_cols_all = generate_reply([{"role": "user", "content": prompt}], sc_num)
        if tabs_cols_all is None:
            pass
        tab_col_ori = {}
        for table in data['db_schema']:
            tab_col_ori[table['table_name_original'].lower()] = table['column_names_original']
        tabs_cols = column_sc(tabs_cols_all, tab_col_ori, data['fk'], add_fk)
        info = info_generate(tabs_cols, data)
        res.append(info)
        # print(res)
        with open(output_recalled_columns_path, 'w') as f:
            json.dump(res, f, indent=2)

if __name__ == "__main__":
    opt = parse_option()
    sc_num = 1
    if opt.self_consistent:
        sc_num = opt.n        
    recall_column(opt.input_recalled_tables_path, opt.output_recalled_columns_path, opt.add_fk, sc_num)

