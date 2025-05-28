'''
oliver lee

create database tables, updates with current sets each time it is run
'''

import os
import psycopg2
from psycopg2 import sql
import json
import requests

def create_cards_table(conn):
    """
    Creates the table of all cards from a stored json file.
    """
    with conn.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS cards CASCADE")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                mana_cost VARCHAR(255),
                cmc VARCHAR(255),
                type_line VARCHAR(255),
                oracle_text TEXT,
                rarity VARCHAR(100),
                set_name VARCHAR(255),
                set_type VARCHAR(255),
                set_id INT REFERENCES sets(set_id),
                image_uri_normal TEXT,
                image_uri_large TEXT,
                image_uri_art_crop TEXT,
                card_faces JSONB,
                face_oracle_text TEXT,
                face_image_uri_normal TEXT,
                face_image_uri_large TEXT,
                face_image_uri_art_crop TEXT,
                color_identity TEXT[]
            )
        """)
        conn.commit()

def create_set_table(conn):
    """
    Creates the table of all sets from Scryfall API.
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sets (
                set_id SERIAL PRIMARY KEY,
                code VARCHAR(10),
                set_name VARCHAR(255),
                set_type VARCHAR(255),
                block VARCHAR(255)
            )
        """)

def fetch_card_data():
    """
    Fetches a json file of all cards i have stored somewhere else (its too big).
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_dir, '/Users/oliver/Documents/big_files/all_cards.json')

    with open(json_file_path, 'r') as file:
        data = json.load(file)
    return data

def insert_card_data(conn, card):
    """
    Populates each column of the cards table.
    """
    with conn.cursor() as cursor:
        # First, look up the set_id and set_type using the card's set code
        cursor.execute("""
            SELECT set_id, set_type FROM sets WHERE code = %s
        """, (card.get('set'),))  # 'set' is the code field in card data
        set_info = cursor.fetchone()

        # Get image URIs, handling cases where they might not exist
        image_uris = card.get('image_uris', {})
        
        # Handle card faces
        card_faces = card.get('card_faces', [])
        face_oracle_text = None
        face_image_uri_normal = None
        face_image_uri_large = None
        face_image_uri_art_crop = None

        if card_faces:
            # Assuming you want to store the first face's details
            first_face = card_faces[0]
            face_oracle_text = first_face.get('oracle_text')
            face_image_uris = first_face.get('image_uris', {})
            face_image_uri_normal = face_image_uris.get('normal')
            face_image_uri_large = face_image_uris.get('large')
            face_image_uri_art_crop = face_image_uris.get('art_crop')

        insert_query = sql.SQL("""
            INSERT INTO cards (
                name, mana_cost, cmc, type_line, oracle_text, rarity, 
                set_name, set_type, set_id, image_uri_normal, image_uri_large, image_uri_art_crop,
                card_faces, face_oracle_text, face_image_uri_normal, face_image_uri_large, face_image_uri_art_crop,
                color_identity
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """)
        cursor.execute(insert_query, (
            card.get('name'),
            card.get('mana_cost'),
            card.get('cmc'),
            card.get('type_line'),
            card.get('oracle_text'),
            card.get('rarity'),
            card.get('set_name'),
            set_info[1] if set_info else None,  # set_type
            set_info[0] if set_info else None,  # set_id
            image_uris.get('normal'),
            image_uris.get('large'),
            image_uris.get('art_crop'),
            json.dumps(card_faces) if card_faces else None,
            face_oracle_text,
            face_image_uri_normal,
            face_image_uri_large,
            face_image_uri_art_crop,
            card.get('color_identity', [])
        ))
    conn.commit()

def insert_set_data(conn, set):
    """
    Populates the sets table.
    """
    with conn.cursor() as cursor:
        insert_query = sql.SQL("""
            INSERT INTO sets (code, set_name, set_type, block)
            VALUES (%s, %s, %s, %s)
        """)
        cursor.execute(insert_query, (
            set.get('code'),
            set.get('name'),
            set.get('set_type'),
            set.get('block')
        ))
    conn.commit()  

def main():
    # connect to database
    conn = psycopg2.connect(
        dbname='mtg_db',
        user='oliver',
        password=os.environ.get('DB_PASSWORD'),
        host='localhost'
    )

    if conn:
        create_set_table(conn)
        # fetch set data
        url = 'https://api.scryfall.com/sets'
        response = requests.get(url)

        if response.status_code == 200:
            sets_data = response.json()

            for set in sets_data['data']:
                insert_set_data(conn, set)
        else:
            print(f"Error: {response.status_code}")

        create_cards_table(conn)
        # fetch card data
        card_data = fetch_card_data()
        for card in card_data:
            insert_card_data(conn, card)

        conn.close()
        print("Data inserted successfully!")

if __name__ == '__main__':
    main()
