import json
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search
import numpy as np


model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

class Knowledge_Base:

    def __init__(self):
        self.qa_embeddings = []
        self.data = []

    def load_data(self, data_file):
        """
        Load data from a json file that contains a list into the knowledge base.

        Args:
            data_file (str): The path to the data file.
        """
        with open(data_file, 'r') as file:
            self.data = json.load(file)

        texts = []
        for item in self.data:
            question = item["question"]
            texts.append(question)
        self.qa_embeddings = model.encode(texts)

    def insert_data(self, question, db_id, sql):
        """
        Insert data into the knowledge base.
        """
        texts = [question]
        embeddings = model.encode(texts)
        self.qa_embeddings = np.concatenate((self.qa_embeddings, embeddings))
        self.data.append({"question": question, "db_id": db_id, "sql": sql})

    def search_data(self, question, db_id, threshold):
        """
        Search for data in the knowledge base.
        """
        input_embeddings = model.encode([question])
        hits = semantic_search(input_embeddings, self.qa_embeddings, top_k=5)

        rtn_sql = None
        for i in range(len(hits[0])):
            if hits[0][i]['score'] > threshold:
                qa_db_id = self.data[hits[0][i]['corpus_id']]["db_id"]
                sql = self.data[hits[0][i]['corpus_id']]["sql"]
                if qa_db_id == db_id:
                    rtn_sql = sql
                    break
        return rtn_sql

    def dump_data(self, data_file):
        """
        Dump the data into a JSON file.
        """
        with open(data_file, 'w') as file:
            json.dump(self.data, file, indent=4)

