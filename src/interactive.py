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

def create_dataset(output_question_path):
    question = input("Enter your question: ")
    db = input("Enter the database: ")
    entry = [{"db_id":db, "question": question}]
    with open(output_question_path, "w") as outfile:
        outfile.write(json.dumps(entry, indent=4))

if __name__ == "__main__":
    opt = parse_option()
    all_db_infos = json.load(open(opt.table_path))
    db_schemas = get_db_schemas(all_db_infos)
    #print("------- Database information ---------")
    #print(json.dumps(db_schemas, indent=4))

    output_question_path = "./data/spider/test.json"
    output_dataset_path = "./generate_datasets/preprocessed_data.json"
    output_recalled_tables_path = "./generate_datasets/table_recall.json"
    output_recalled_columns_path = "./generate_datasets/column_recall.json"
    processed_dataset_path="./generate_datasets/text2sql.json"
    output_query_path="./generate_datasets/predicted_sql.txt"

    start_time = time.time()
    create_dataset(output_question_path)
    print("------- preprocessing ---------")
    preprocess(output_question_path, output_dataset_path, opt.table_path, opt.db_path)
    print("------- recall tables... ---------")
    recall_table(output_dataset_path, output_recalled_tables_path, 5)
    print("------- recall columns... ---------")
    recall_column(output_recalled_tables_path, output_recalled_columns_path, True, 5)
    print("------- generate prompt... ---------")
    generate_prompt(output_recalled_columns_path, processed_dataset_path)
    print("------- generate SQL... ---------")
    generate_query(processed_dataset_path, output_query_path, 10, opt.db_path, False)
    print("--- processing time: %s seconds ---" % (time.time() - start_time))
    
    
    
