### Text2SQL
We built this project to convert a question to SQL. The idea for text to SQL conversion is from C3SQL.

### Quick Start
```
pip install -r requirements.txt

export OPENAI_KEY=your_api_key
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

### Run Web Demo
```
python src/main.py
```

### References

C3SQL
https://github.com/bigbigwatermalon/C3SQL