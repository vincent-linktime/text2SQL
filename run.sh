set -e

tables="./data/spider/tables.json"
dataset_path="./data/spider/test.json"
db_dir="database"
output_dataset_path="./generate_datasets/predicted_sql.txt"

processed_dataset_path="./generate_datasets/text2sql.json"

# preprocess data
bash scripts/prepare_dataset.sh $tables $dataset_path $db_dir $processed_dataset_path
# run prediction
python src/generate_sqls_by_gpt3.5.py --input_dataset_path $processed_dataset_path  --output_dataset_path $output_dataset_path --db_dir $db_dir

