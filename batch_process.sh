set -e

tables="./data/tables.json"
dataset_path="./data/test.json"
output_dataset_path="./generate_datasets/predicted_sql.txt"

processed_dataset_path="./generate_datasets/text2sql.json"

# preprocess data
bash scripts/prepare_dataset.sh $tables $dataset_path $processed_dataset_path
# run prediction
python src/generate_sqls_by_gpt.py --input_dataset_path $processed_dataset_path  --output_dataset_path $output_dataset_path

