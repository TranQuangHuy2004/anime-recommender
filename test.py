import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='anime_db',
        user='anime_user',
        password='anime_password'
    )
    print('✅ PostgreSQL connected successfully!')
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
