from knowledge_base import Knowledge_Base

kb = Knowledge_Base()
kb.load_data('./data/QA_SQL.json')  # Load data from a JSON file
#result = kb.search_data('List the average, minimum, and maximum age of all singers from France', 'concert_singer', 0.9)  # Search for existing data
#print(result)
kb.insert_data("qa12", "db1", "sql1")
kb.dump_data("./generate_datasets/QA_SQL.json")