from flask import Flask, jsonify, request, render_template
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps
import os

app = Flask(__name__)
is_development = os.environ.get('FLASK_ENV') == 'development'

# Basic app configuration
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/art-game')
def game():
    return render_template('guess-art.html')

def get_db_connection():
    """Database connection factory"""
    return psycopg2.connect(
        dbname='mtg_db',
        user='oliver',
        password=os.environ.get('DB_PASSWORD'),
        host='localhost'
    )

def db_handler(f):
    """Decorator to handle database connections"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        conn = get_db_connection()
        try:
            result = f(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
    return wrapper

@app.route('/api/cards', methods=['GET'])
@db_handler
def get_cards(conn):
    """Get all cards with optional filtering"""
    name = request.args.get('name', '')
    oracle = request.args.get('oracle', '')
    cmc = request.args.get('cmc', '')
    colors = request.args.get('colors', '')
    colorLogic = request.args.get('colorLogic', '')
    
    # Validate cmc is a number if provided
    if cmc and not cmc.isdigit():
        return jsonify({'error': 'Invalid CMC value'}), 400
        
    # Validate colorLogic is one of the allowed values
    if colorLogic and colorLogic not in ['all', 'exact', 'any']:
        return jsonify({'error': 'Invalid color logic value'}), 400

    # add params to query to filter for desired cards
    query = """
        SELECT * FROM cards WHERE set_type IN ('core', 'expansion', 'masters', 'draft_innovation', 'commander', 'starter')
        AND name NOT LIKE 'A-%%' 
        AND set_name NOT IN ('Mystery Booster 2')
        AND mana_cost <> ''
    """

    params = []
    
    if name:
        query += " AND LOWER(name) LIKE LOWER(%s)"
        params.append(f'%{name}%')
        
    if oracle:
        # if the card has multiple faces, check all faces for the oracle text
        query += " AND (LOWER(oracle_text) LIKE LOWER(%s) OR LOWER(COALESCE(face_oracle_text, '')) LIKE LOWER(%s) OR LOWER(COALESCE(card_faces->1->>'oracle_text', '')) LIKE LOWER(%s))"
        params.extend([f'%{oracle}%', f'%{oracle}%', f'%{oracle}%'])
    
    if cmc:
        query += " AND CAST(cmc AS NUMERIC) = %s"
        params.append(cmc)

    if colors:
        color_identity = colors.split(",")
        if colorLogic == "all":
            query += " AND color_identity @> %s"
        elif colorLogic == "exact":
            query += """
                AND (SELECT array_agg(x ORDER BY x) FROM unnest(color_identity) x)
                = (SELECT array_agg(x ORDER BY x) FROM unnest(%s) x)
            """
        else:
            if 'C' in color_identity:
                query += " AND color_identity && %s OR color_identity = '{}')"
            else:
                query += " AND color_identity && %s"
        params.append(color_identity)

    query += " ORDER BY name ASC LIMIT 100;"
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        cards = cur.fetchall()
    return jsonify(cards)

@app.route('/api/random-card-art', methods=['GET'])
@db_handler
def get_random_card(conn):
    """Get a random card for the guessing game"""
    query = """
        SELECT name, image_uri_art_crop
        FROM cards 
        WHERE image_uri_art_crop IS NOT NULL 
        AND set_type IN ('core', 'expansion', 'masters', 'draft_innovation', 'commander', 'starter') 
        AND name NOT LIKE 'A-%%' 
        AND set_name NOT IN ('Mystery Booster 2')
        AND (type_line LIKE 'Creature%'
        OR type_line LIKE 'Legendary%'
        OR type_line LIKE 'Artifact%'
        OR type_line LIKE 'Enchantment%'
        OR type_line LIKE 'Planeswalker%'
        OR type_line LIKE 'Sorcery%'
        OR type_line LIKE 'Land%'
        OR type_line LIKE 'Instant%')
        ORDER BY RANDOM() 
        LIMIT 1;
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        card = cur.fetchone()
    return jsonify(card)

@app.route('/api/suggestions', methods=['GET'])
@db_handler
def get_suggestions(conn):
    name = request.args.get('name', '')
    query = """
        SELECT name FROM cards 
        WHERE set_type IN ('core', 'expansion', 'masters', 'draft_innovation', 'commander', 'starter') 
        AND name NOT LIKE 'A-%%' 
        AND set_name NOT IN ('Mystery Booster 2')
        AND (type_line LIKE 'Creature%%'
        OR type_line LIKE 'Legendary%%'
        OR type_line LIKE 'Artifact%%'
        OR type_line LIKE 'Enchantment%%'
        OR type_line LIKE 'Planeswalker%%'
        OR type_line LIKE 'Sorcery%%'
        OR type_line LIKE 'Land%%'
        OR type_line LIKE 'Instant%%')
        AND LOWER(name) LIKE LOWER(%s) 
        ORDER BY name ASC LIMIT 7;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (f'{name}%',))
        suggestions = cur.fetchall()
    return jsonify(suggestions)

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
        debug=True  # Always enable debug mode when running app.py directly
    )
