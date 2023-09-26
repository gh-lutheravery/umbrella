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


def read_rows(table_name, limit=None, cond=None):
    if cond:
        query = "SELECT * FROM " + table_name + " WHERE {} = %s AND is_deleted = False"
        params = [cond[1]]
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

def insert_table(table_name, form_obj):
    get_columns_query = \
    f"""
    SELECT
        column_name
    FROM
        information_schema.columns
    WHERE
        table_name = '{table_name}';
    """

    real_columns = run_query(get_columns_query)
    real_columns_flat = flatten_query_result(real_columns)

    col_values = get_col_values(real_columns_flat, form_obj)

    column_str = ', '.join(real_columns_flat)
    param_str = ('%s,' * len(col_values)).rstrip(',')

    insert_query = "INSERT INTO " + table_name + " (" + column_str + ") VALUES (" + param_str + ");"

    run_query(insert_query, col_values)


def get_obj_attrs(obj):
    attrs = []
    for attr in dir(obj):
        if not callable(getattr(obj, attr)) and not attr.startswith("__"):
            attrs.append(attr)

    return attrs


def update_row_obj(form_obj, table_name, cond_filter: tuple, soft_delete_flag=None):
    if soft_delete_flag:
        update_query = f"UPDATE {table_name} SET is_deleted = %s WHERE {cond_filter[0]} = %s;"

        params = [soft_delete_flag, cond_filter[1]]

        run_query(update_query, params)

    else:
        # Extract attribute names and values from the object
        attributes = get_obj_attrs(form_obj)
        attribute_values = [getattr(form_obj, attr) for attr in attributes]

        # Build the SET clause for the UPDATE query
        set_clauses = [f"{attr} = %s" for attr in attributes]
        set_clause_str = ", ".join(set_clauses)

        # Define the UPDATE query
        update_query = f"UPDATE {table_name} SET {set_clause_str} WHERE {cond_filter[0]} = %s;"

        params = [attribute_values + [getattr(form_obj, cond_filter[1])]]
        run_query(update_query, params)


def update_row(columns: list, values: list, table_name, cond_filter: tuple, soft_delete_flag=None):
    if soft_delete_flag:
        update_query = f"UPDATE {table_name} SET is_deleted = %s WHERE {cond_filter[0]} = %s;"

        params = [soft_delete_flag, cond_filter[1]]

        run_query(update_query, params)

    else:
        # Build the SET clause for the UPDATE query
        set_clauses = [f"{attr} = %s" for attr in columns]
        set_clause_str = ", ".join(set_clauses)

        # Define the UPDATE query
        update_query = f"UPDATE {table_name} SET {set_clause_str} WHERE {cond_filter[0]} = %s;"

        params = [values + cond_filter[1]]
        run_query(update_query, params)


def soft_delete(table_name, cond_filter: tuple):
    update_row(None, table_name, cond_filter, soft_delete_flag=True)


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
