### Text2SQL
 This project optimized the code of [C3SQL](https://github.com/bigbigwatermalon/C3SQL) by incorporating a web-based user interface for demonstrations. 

### Quick Start
Prepare two files:<br>
1. data/tables.json: database and table schemas
2. data/test.json: questions
```
pip install -r requirements.txt

export OPENAI_KEY=your_api_key
export TOKENIZERS_PARALLELISM=false
bash batch_process.sh
```

### Run evaluation
#### Prepare Spider Data
Download [spider data](https://drive.google.com/uc?export=download&id=1TqleXec_OykOYFREKKtschzY29dUcVAQ) and database and then unzip them:
```
unzip spider.zip 
mv spider/database . 
rm -rf spider.zip
rm -rf spider
```

#### Clone evaluation scripts
```
mkdir third_party
cd third_party
git clone https://github.com/taoyds/test-suite-sql-eval
cd ..

python third_party/test-suite-sql-eval/evaluation.py --gold data/test_gold.sql --pred generate_datasets/predicted_sql.txt --db database --table data/tables.json --etype exec 
```
You can replace test_gold.sql, predicted_sql.txt, tables.json with your own files.<br>
Note: The format of each line in test_gold.sql is "sql_statement \t database_name".

### Run Web Demo
```
python src/main.py
```

### Knowledge Base
To optimize the web-based text-to-SQL process, incorporate a knowledge base featuring validated question-SQL pairs adhering to the format in data/QA_SQL.json. When a user poses a question, the system will search this knowledge base for similar questions, based on a 90% similarity threshold, and return the corresponding SQL query from the most closely matching question.

The web-based process additionally produces a knowledge base file, which archives historical question-SQL pairs in generate_datasets/QA_SQL.json.

### References
[C3SQLC3: Zero-shot Text-to-SQL with ChatGPT](https://arxiv.org/pdf/2307.07306.pdf)
