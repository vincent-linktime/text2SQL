import re
import json
import argparse

from bridge_content_encoder import get_database_matches
from sql_metadata import Parser
from tqdm import tqdm

sql_keywords = ['select', 'from', 'where', 'group', 'order', 'limit', 'intersect', 'union', \
                'except', 'join', 'on', 'as', 'not', 'between', 'in', 'like', 'is', 'exists', 'max', 'min', \
                'count', 'sum', 'avg', 'and', 'or', 'desc', 'asc']


def parse_option():
    parser = argparse.ArgumentParser("")

    parser.add_argument('--table_path', type=str, default="./data/spider/tables.json")
    parser.add_argument('--input_dataset_path', type=str, default="./data/spider/test.json")
    parser.add_argument('--output_dataset_path', type=str, default="./data/pre-processing/preprocessed_dataset.json",
                        help="the filepath of preprocessed dataset.")
    parser.add_argument('--db_path', type=str, default="./data/spider/database",
                        help="the filepath of database.")
    opt = parser.parse_args()

    return opt


def get_db_contents(question, table_name_original, column_names_original, db_id, db_path):
    matched_contents = []
    # extract matched contents for each column
    for column_name_original in column_names_original:
        matches = get_database_matches(
            question,
            table_name_original,
            column_name_original,
            db_path + "/{}/{}.sqlite".format(db_id, db_id)
        )
        matches = sorted(matches)
        matched_contents.append(matches)

    return matched_contents


def get_db_schemas(all_db_infos):
    db_schemas = {}

    for db in all_db_infos:
        table_names_original = db["table_names_original"]
        table_names = db["table_names"]
        column_names_original = db["column_names_original"]
        column_names = db["column_names"]
        column_types = db["column_types"]

        db_schemas[db["db_id"]] = {}

        primary_keys, foreign_keys = [], []
        # record primary keys
        for pk_column_idx in db["primary_keys"]:
            pk_table_name_original = table_names_original[column_names_original[pk_column_idx][0]]
            pk_column_name_original = column_names_original[pk_column_idx][1]

            primary_keys.append(
                {
                    "table_name_original": pk_table_name_original.lower(),
                    "column_name_original": pk_column_name_original.lower()
                }
            )

        db_schemas[db["db_id"]]["pk"] = primary_keys

        # record foreign keys
        for source_column_idx, target_column_idx in db["foreign_keys"]:
            fk_source_table_name_original = table_names_original[column_names_original[source_column_idx][0]]
            fk_source_column_name_original = column_names_original[source_column_idx][1]

            fk_target_table_name_original = table_names_original[column_names_original[target_column_idx][0]]
            fk_target_column_name_original = column_names_original[target_column_idx][1]

            foreign_keys.append(
                {
                    "source_table_name_original": fk_source_table_name_original.lower(),
                    "source_column_name_original": fk_source_column_name_original.lower(),
                    "target_table_name_original": fk_target_table_name_original.lower(),
                    "target_column_name_original": fk_target_column_name_original.lower(),
                }
            )
        db_schemas[db["db_id"]]["fk"] = foreign_keys

        db_schemas[db["db_id"]]["schema_items"] = []
        for idx, table_name_original in enumerate(table_names_original):
            column_names_original_list = []
            column_names_list = []
            column_types_list = []
            for column_idx, (table_idx, column_name_original) in enumerate(column_names_original):
                if idx == table_idx:
                    column_names_original_list.append(column_name_original.lower())
                    column_names_list.append(column_names[column_idx][1].lower())
                    column_types_list.append(column_types[column_idx])

            db_schemas[db["db_id"]]["schema_items"].append({
                "table_name_original": table_name_original.lower(),
                "table_name": table_names[idx].lower(),
                "column_names": column_names_list,
                "column_names_original": column_names_original_list,
                "column_types": column_types_list
            })

    return db_schemas


def normalization(sql):
    def white_space_fix(s):
        parsed_s = Parser(s)
        s = " ".join([token.value for token in parsed_s.tokens])

        return s

    # convert everything except text between single quotation marks to lower case
    def lower(s):
        in_quotation = False
        out_s = ""
        for char in s:
            if in_quotation:
                out_s += char
            else:
                out_s += char.lower()

            if char == "'":
                if in_quotation:
                    in_quotation = False
                else:
                    in_quotation = True

        return out_s

    # remove ";"
    def remove_semicolon(s):
        if s.endswith(";"):
            s = s[:-1]
        return s

    # double quotation -> single quotation 
    def double2single(s):
        return s.replace("\"", "'")

    def add_asc(s):
        pattern = re.compile(
            r'order by (?:\w+ \( \S+ \)|\w+\.\w+|\w+)(?: (?:\+|\-|\<|\<\=|\>|\>\=) (?:\w+ \( \S+ \)|\w+\.\w+|\w+))*')
        if "order by" in s and "asc" not in s and "desc" not in s:
            for p_str in pattern.findall(s):
                s = s.replace(p_str, p_str + " asc")

        return s

    def remove_table_alias(s):
        tables_aliases = Parser(s).tables_aliases
        new_tables_aliases = {}
        for i in range(1, 11):
            if "t{}".format(i) in tables_aliases.keys():
                new_tables_aliases["t{}".format(i)] = tables_aliases["t{}".format(i)]

        tables_aliases = new_tables_aliases
        for k, v in tables_aliases.items():
            s = s.replace("as " + k + " ", "")
            s = s.replace(k, v)

        return s

    processing_func = lambda x: remove_table_alias(add_asc(lower(white_space_fix(double2single(remove_semicolon(x))))))

    return processing_func(sql)


# extract the skeleton of sql and natsql
def extract_skeleton(sql, db_schema):
    table_names_original, table_dot_column_names_original, column_names_original = [], [], []
    for table in db_schema["schema_items"]:
        table_name_original = table["table_name_original"]
        table_names_original.append(table_name_original)

        for column_name_original in ["*"] + table["column_names_original"]:
            table_dot_column_names_original.append(table_name_original + "." + column_name_original)
            column_names_original.append(column_name_original)

    parsed_sql = Parser(sql)
    new_sql_tokens = []
    for token in parsed_sql.tokens:
        # mask table names
        if token.value in table_names_original:
            new_sql_tokens.append("_")
        # mask column names
        elif token.value in column_names_original \
                or token.value in table_dot_column_names_original:
            new_sql_tokens.append("_")
        # mask string values
        elif token.value.startswith("'") and token.value.endswith("'"):
            new_sql_tokens.append("_")
        # mask positive int number
        elif token.value.isdigit():
            new_sql_tokens.append("_")
        # mask negative int number
        elif isNegativeInt(token.value):
            new_sql_tokens.append("_")
        # mask float number
        elif isFloat(token.value):
            new_sql_tokens.append("_")
        else:
            new_sql_tokens.append(token.value.strip())

    sql_skeleton = " ".join(new_sql_tokens)

    # remove JOIN ON keywords
    sql_skeleton = sql_skeleton.replace("on _ = _ and _ = _", "on _ = _")
    sql_skeleton = sql_skeleton.replace("on _ = _ or _ = _", "on _ = _")
    sql_skeleton = sql_skeleton.replace(" on _ = _", "")
    pattern3 = re.compile("_ (?:join _ ?)+")
    sql_skeleton = re.sub(pattern3, "_ ", sql_skeleton)

    # "_ , _ , ..., _" -> "_"
    while ("_ , _" in sql_skeleton):
        sql_skeleton = sql_skeleton.replace("_ , _", "_")

    # remove clauses in WHERE keywords
    ops = ["=", "!=", ">", ">=", "<", "<="]
    for op in ops:
        if "_ {} _".format(op) in sql_skeleton:
            sql_skeleton = sql_skeleton.replace("_ {} _".format(op), "_")
    while ("where _ and _" in sql_skeleton or "where _ or _" in sql_skeleton):
        if "where _ and _" in sql_skeleton:
            sql_skeleton = sql_skeleton.replace("where _ and _", "where _")
        if "where _ or _" in sql_skeleton:
            sql_skeleton = sql_skeleton.replace("where _ or _", "where _")

    # remove additional spaces in the skeleton
    while "  " in sql_skeleton:
        sql_skeleton = sql_skeleton.replace("  ", " ")

    return sql_skeleton


def isNegativeInt(string):
    if string.startswith("-") and string[1:].isdigit():
        return True
    else:
        return False


def isFloat(string):
    if string.startswith("-"):
        string = string[1:]

    s = string.split(".")
    if len(s) > 2:
        return False
    else:
        for s_i in s:
            if not s_i.isdigit():
                return False
        return True


def preprocess(input_dataset_path, output_dataset_path, table_path, db_path):
    dataset = json.load(open(input_dataset_path))
    all_db_infos = json.load(open(table_path))
    natsql_dataset = [None for _ in range(len(dataset))]
    db_schemas = get_db_schemas(all_db_infos)
    preprocessed_dataset = []

    for natsql_data, data in tqdm(zip(natsql_dataset, dataset)):
        question = data["question"]
        db_id = data["db_id"]

        sql, norm_sql, sql_skeleton = "", "", ""
        sql_tokens = []

        natsql, norm_natsql, natsql_skeleton = "", "", ""
        natsql_used_columns, natsql_tokens = [], []

        preprocessed_data = {}
        preprocessed_data["question"] = question
        preprocessed_data["db_id"] = db_id

        preprocessed_data["sql"] = sql
        preprocessed_data["norm_sql"] = norm_sql
        preprocessed_data["sql_skeleton"] = sql_skeleton

        preprocessed_data["natsql"] = natsql
        preprocessed_data["norm_natsql"] = norm_natsql
        preprocessed_data["natsql_skeleton"] = natsql_skeleton

        preprocessed_data["db_schema"] = []
        preprocessed_data["pk"] = db_schemas[db_id]["pk"]
        preprocessed_data["fk"] = db_schemas[db_id]["fk"]
        preprocessed_data["table_labels"] = []
        preprocessed_data["column_labels"] = []

        # add database information (including table name, column name, ..., table_labels, and column labels)
        for table in db_schemas[db_id]["schema_items"]:
            db_contents = get_db_contents(
                question,
                table["table_name_original"],
                table["column_names_original"],
                db_id,
                db_path
            )

            preprocessed_data["db_schema"].append({
                "table_name_original": table["table_name_original"],
                "table_name": table["table_name"],
                "column_names": table["column_names"],
                "column_names_original": table["column_names_original"],
                "column_types": table["column_types"],
                "db_contents": db_contents
            })

            # extract table and column classification labels
            if table["table_name_original"] in sql_tokens:  # for used tables
                preprocessed_data["table_labels"].append(1)
                column_labels = []
                for column_name_original in table["column_names_original"]:
                    if column_name_original in sql_tokens or \
                            table[
                                "table_name_original"] + "." + column_name_original in sql_tokens:  # for used columns
                        column_labels.append(1)
                    else:
                        column_labels.append(0)
                preprocessed_data["column_labels"].append(column_labels)
            else:  # for unused tables and their columns
                preprocessed_data["table_labels"].append(0)
                preprocessed_data["column_labels"].append([0 for _ in range(len(table["column_names_original"]))])

        preprocessed_dataset.append(preprocessed_data)

    with open(output_dataset_path, "w") as f:
        preprocessed_dataset_str = json.dumps(preprocessed_dataset, indent=2)
        f.write(preprocessed_dataset_str)


if __name__ == "__main__":
    opt = parse_option()
    preprocess(opt.input_dataset_path, opt.output_dataset_path, opt.table_path, opt.db_path)
