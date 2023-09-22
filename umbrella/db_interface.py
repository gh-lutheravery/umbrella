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