import argparse
import json
import time
import openai
from sql_post_process import fix_select_column
import re
import os
import sqlite3
from tqdm import tqdm
from utils import openai_completion

chat_prompt = [
    {
        "role": "system",
        "content": "You are now an excellent SQL writer, first I'll give you some tips and examples, and I need you to remember the tips, and do not make same mistakes."
    },
    {
        "role": "user",
        "content": """Tips 1: 
Question: Which A has most number of B?
Gold SQL: select A from B group by A order by count ( * ) desc limit 1;
Notice that the Gold SQL doesn't select COUNT(*) because the question only wants to know the A and the number should be only used in ORDER BY clause, there are many questions asks in this way, and I need you to remember this in the the following questions."""
    },
    {
        "role": "assistant",
        "content": "Thank you for the tip! I'll keep in mind that when the question only asks for a certain field, I should not include the COUNT(*) in the SELECT statement, but instead use it in the ORDER BY clause to sort the results based on the count of that field."
    },
    {
        "role": "user",
        "content": """Tips 2: 
Don't use "IN", "OR", "LEFT JOIN" as it might cause extra results, use "INTERSECT" or "EXCEPT" instead, and remember to use "DISTINCT" or "LIMIT" when necessary.
For example, 
Question: Who are the A who have been nominated for both B award and C award?
Gold SQL should be: select A from X where award = 'B' intersect select A from X where award = 'C';"""
    },
    {
        "role": "assistant",
        "content": "Thank you for the tip! I'll remember to use \"INTERSECT\" or \"EXCEPT\" instead of \"IN\", \"OR\", or \"LEFT JOIN\" when I want to find records that match or don't match across two tables. Additionally, I'll make sure to use \"DISTINCT\" or \"LIMIT\" when necessary to avoid repetitive results or limit the number of results returned."
    }
]


def parse_option():
    parser = argparse.ArgumentParser("command line arguments for generate sqls")
    parser.add_argument("--input_dataset_path", type=str)
    parser.add_argument("--output_dataset_path", type=str)

    opt = parser.parse_args()

    return opt


def generate_reply(messages, n):
    #print("-------messages start--------")
    #print(messages)
    #print("-------messages end--------")
    completions = openai_completion(messages, n)
    if completions is None:
        return None
    # print(completions)
    mes = completions.choices[0].message.content
    all_p_sqls = []
    for i in range(n):
        all_p_sqls.append(completions.choices[i].message.content.replace("\n", " "))
    return all_p_sqls


def replace_cur_year(query: str) -> str:
    return re.sub(
        "YEAR\s*\(\s*CURDATE\s*\(\s*\)\s*\)\s*", "2020", query, flags=re.IGNORECASE
    )


def get_cursor_from_path(sqlite_path: str):
    try:
        if not os.path.exists(sqlite_path):
            print("Openning a new connection %s" % sqlite_path)
        connection = sqlite3.connect(sqlite_path)
    except Exception as e:
        print(sqlite_path)
        raise e
    connection.text_factory = lambda b: b.decode(errors="ignore")
    cursor = connection.cursor()
    return cursor


def exec_on_db_(sqlite_path: str, query: str):
    query = replace_cur_year(query)
    cursor = get_cursor_from_path(sqlite_path)
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        cursor.connection.close()
        return "result", result
    except Exception as e:
        cursor.close()
        cursor.connection.close()
        return "exception", e


def is_valid(sql, db_path):
    flag, _ = exec_on_db_(db_path, sql)
    if flag == "exception":
        return 0
    else:
        return 1

def generate_query(input_dataset_path, output_dataset_path):
    with open(input_dataset_path) as f:
        data = json.load(f)
    results = []
    p_sql_final = []

    for i, item in enumerate(data):
        #print("id", i)
        messages = []
        messages = chat_prompt.copy()
        input = item['input_sequence']
        messages.append({"role": "user", "content": input})
        p_sql = generate_reply(messages, 1)[0]
        p_sql = 'SELECT ' + p_sql
        p_sql = p_sql.replace("SELECT SELECT", "SELECT")
        try:
            p_sql = fix_select_column(p_sql)
        except:
            print(f"fix_select_column err, p_sql: {p_sql}")
            pass
        p_sql = p_sql.replace("> =", ">=").replace("< =", "<=").replace("! =", "!=")
        #print(f'p_sql: {p_sql}')
        p_sql_final.append(p_sql)
    print(p_sql_final)

    with open(output_dataset_path, 'w') as f:
        for sql in p_sql_final:
            print(sql, file=f)
    return p_sql_final

if __name__ == '__main__':
    opt = parse_option()
    generate_query(opt.input_dataset_path, opt.output_dataset_path)
