import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
def use_db(
    dbname,
    user,
    password,
    host="localhost",
    port="5432",
    autocommit=False,
    callback=None
):
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        if autocommit:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor()
        if callback:
            callback(cursor, conn)
        if not autocommit:
            conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



def save_company_to_db(cursor, company):
    cursor.execute("SELECT 1 FROM companies WHERE id = %s;", (company.company_id,))
    exists = cursor.fetchone()

    if exists:
        print(f"Duplicate ID skipped: {company.company_id} - {company.name}")

    else:
        cursor.execute("""
        INSERT INTO addresses (address, city, state, postalcode)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, (company.address, company.city, company.state, company.postalCode))
    
        address_id = cursor.fetchone()[0]

        # Step 2: Insert the company
        cursor.execute("""
            INSERT INTO companies (id, name, phone, website, years, description, address_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (
            company.company_id,
            company.name,
            company.phone,  # since phone is a TEXT[] array
            company.websiteUrl,
            company.years,
            company.description,
            address_id
        ))