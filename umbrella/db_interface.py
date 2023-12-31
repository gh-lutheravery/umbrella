import datetime
import os
import psycopg2
import psycopg2.sql as sql


def open_conn():
    conn = psycopg2.connect(
        host="localhost",
        database="umbrella_flask",
        user=os.getenv('UMBRELLA_F_DB_USER'),
        password=os.getenv('UMBRELLA_F_DB_PASS'),
        port=5433
    )

    return conn


def run_query(query: str, params=None, field_param=None):
    with open_conn() as conn:
        cursor = conn.cursor()

        if params:
            if field_param:
                formatted_query = sql.SQL(query).format(sql.Identifier(field_param))
                cursor.execute(formatted_query, params)
            else:
                cursor.execute(query, params)
        else:
            cursor.execute(query)

        conn.commit()

        if cursor.description:
            rows = cursor.fetchall()
            return rows

        rows = ()
        return rows


def read_rows(table_name, limit=None, cond=None, use_like=False):
    if cond:
        params = [cond[1]]
        if use_like:
            query = "SELECT * FROM " + table_name + " WHERE {} LIKE %s AND is_deleted = False"
            params = [f'%{cond[1]}%']
        else:
            query = "SELECT * FROM " + table_name + " WHERE {} = %s AND is_deleted = False"

        field_param = cond[0]

        if limit:
            limit_query = get_limited_q(limit, query)
            rows = run_query(limit_query, params, field_param)
        else:
            rows = run_query(query, params, field_param)

    else:
        query = "SELECT * FROM " + table_name + " WHERE is_deleted = False"

        if limit:
            limit_query = get_limited_q(limit, query)
            rows = run_query(limit_query)
        else:
            rows = run_query(query)

    return rows


def get_limited_q(limit, query):
    return query + " LIMIT " + str(limit)


def create_table(table_name, columns: list[tuple]):
    if not columns:
        raise ValueError("Columns list is empty.")

    query = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"

    # Iterate through the columns and add them to the query
    for column in columns:
        column_name, data_type, *modifiers = column

        if modifiers:
            modifiers_str = " ".join(modifiers)
            query += f"\t{column_name} {data_type} {modifiers_str},\n"
        else:
            query += f"\t{column_name} {data_type},\n"

    query = query.rstrip(",\n")

    query += "\n);"
    run_query(query)

def flatten_query_result(jagged_list):
    flat_list = []
    for sub_tuple in jagged_list:
        for sub_item in sub_tuple:
            flat_list.append(sub_item)
    return flat_list


def get_col_values(columns, obj):
    column_values = []
    if 'id' in columns:
        columns.remove('id')

    for col in columns:
        value = getattr(obj, col)
        column_values.append(value)
    return column_values

def get_table_columns(table_name):
    get_columns_query = \
        f"""
        SELECT
            column_name
        FROM
            information_schema.columns
        WHERE
            table_name = '{table_name}';
        """

    table_columns = run_query(get_columns_query)
    table_columns_flat = flatten_query_result(table_columns)
    return table_columns_flat

def insert_table(table_name, form_obj):
    real_columns = get_table_columns(table_name)

    col_values = get_col_values(real_columns, form_obj)

    column_str = ', '.join(real_columns)
    param_str = ('%s,' * len(col_values)).rstrip(',')

    insert_query = "INSERT INTO " + table_name + " (" + column_str + ") VALUES (" + param_str + ");"

    run_query(insert_query, col_values)


def get_obj_attrs(obj):
    attrs = []
    for attr in dir(obj):
        if not callable(getattr(obj, attr)) and not attr.startswith("__"):
            attrs.append(attr)

    return attrs


def update_row_obj(form_obj, table_name, cond_filter: tuple):
    cols = get_table_columns(table_name)
    col_values = get_col_values(cols, form_obj)

    # Build the SET clause for the UPDATE query
    set_clauses = [f"{col} = %s" for col in cols]
    set_clause_str = ", ".join(set_clauses)

    # Define the UPDATE query
    update_query = f"UPDATE {table_name} SET {set_clause_str} WHERE {cond_filter[0]} = %s;"

    col_values.append(cond_filter[1])
    run_query(update_query, col_values)


def update_row(columns: list, values: list, table_name, cond_filter: tuple, default_col=None):
    if len(values) == 0 and default_col == None:
        raise ValueError('No new values given in update_row')

    set_clauses = []
    for col in columns:
        if default_col and default_col == col:
            set_clauses.append(f"{col} = DEFAULT")
            continue
        set_clauses.append(f"{col} = %s")

    set_clause_str = ", ".join(set_clauses)

    update_query = f"UPDATE {table_name} SET {set_clause_str} WHERE {cond_filter[0]} = %s;"

    values.append(cond_filter[1])
    run_query(update_query, values)


def soft_delete(table_name, cond_filter: tuple):
    update_query = f"UPDATE {table_name} SET is_deleted = %s WHERE {cond_filter[0]} = %s;"
    params = [True, cond_filter[1]]

    run_query(update_query, params)


def does_table_exist(table_name):
    query = f'''
    SELECT EXISTS (
        SELECT FROM
            pg_tables
        WHERE
            schemaname = 'public' AND
            tablename  = %s
    );
    '''

    first_query_result = run_query(query, [table_name])[0][0]
    if first_query_result:
        return True
    else:
        return False
