import argparse, json, time
from preprocessing import get_db_schemas, preprocess
from table_recall import recall_table
from column_recall import recall_column
from prompt_generate import generate_prompt
from generate_sqls_by_gpt import generate_query

def parse_option():
    parser = argparse.ArgumentParser("")

    parser.add_argument('--table_path', type=str, default="./data/spider/tables.json")
    parser.add_argument('--db_path', type=str, default="./database",
                        help="the filepath of database.")
    opt = parser.parse_args()

    return opt

def create_dataset(question, db, output_question_path):
    entry = [{"db_id":db, "question": question}]
    with open(output_question_path, "w") as outfile:
        outfile.write(json.dumps(entry, indent=4))

def text2sql(question, db, table_path, db_path):
    all_db_infos = json.load(open(table_path))
    db_schemas = get_db_schemas(all_db_infos)

    output_question_path = "./data/spider/test.json"
    output_dataset_path = "./generate_datasets/preprocessed_data.json"
    output_recalled_tables_path = "./generate_datasets/table_recall.json"
    output_recalled_columns_path = "./generate_datasets/column_recall.json"
    processed_dataset_path="./generate_datasets/text2sql.json"
    output_query_path="./generate_datasets/predicted_sql.txt"

    start_time = time.time()
    create_dataset(question, db, output_question_path)
    
    msg = "------- preprocessing ---------"
    print(msg)
    preprocess(output_question_path, output_dataset_path, table_path, db_path)

    msg = "------- recall tables... ---------"
    print(msg)
    recall_table(output_dataset_path, output_recalled_tables_path, 5)
    
    msg = "------- recall columns... ---------"
    print(msg)
    recall_column(output_recalled_tables_path, output_recalled_columns_path, True, 5)

    msg = "------- generate prompt... ---------"
    print(msg)
    generate_prompt(output_recalled_columns_path, processed_dataset_path)

    msg = "------- generate SQL... ---------"
    print(msg)
    rtn_list = generate_query(processed_dataset_path, output_query_path, 10, db_path, False)

    msg = "--- processing time: %s seconds ---" % (time.time() - start_time)
    print(msg)

    return rtn_list

if __name__ == "__main__":
    opt = parse_option()
    question = input("Enter your question: ")
    db = input("Enter the database: ")
    text2sql(question, db, opt.table_path, opt.db_path)
