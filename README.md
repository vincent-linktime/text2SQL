### Text2SQL
We built this project to convert a question to SQL. The idea for text to SQL conversion is from C3SQL.

### Quick Start
Add your openai key in the src/utils.py file.
openai.api_key = "your_api_key"
```
pip install -r requirements.txt
bash run.sh
```
### Run evaluation
Clone evaluation scripts (test-suite-sql-eval:https://github.com/taoyds/test-suite-sql-eval):

```
mkdir third_party
cd third_party
git clone https://github.com/taoyds/test-suite-sql-eval
cd ..

python third_party/test-suite-sql-eval/evaluation.py --gold data/spider/test_gold.sql --pred generate_datasets/predicted_sql.txt --db database --table data/spider/tables.json --etype exec 
```

### References

C3SQL
https://github.com/bigbigwatermalon/C3SQL