import os
import pickle
import random
import re
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
# Patch MySQLdb with pymysql for easy installation on Windows systems
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
import MySQLdb
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import google.generativeai as genai
# Machine Learning Logic Import (ml_model.py se)
try:
    from ml_model import predict_occupancy, train_demand_model, get_historical_data
except ImportError:
    # Backup default functions
    def predict_occupancy(day_code=6, month=6, weekend=0, festival=0, avg_slot=3, previous_occupancy=25): return 75
    def train_demand_model(): return False
    def get_historical_data(): return []
app = Flask(__name__)
app.secret_key = "smart_cafe_secret_key"
# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'          # Default user
app.config['MYSQL_PASSWORD'] = 'pammysaini'  # User's password
app.config['MYSQL_DB'] = 'smart_cafe_db'
mysql = MySQL(app)
# Google AI Studio API Key Configuration
GENAI_API_KEY = "YOUR_API_KEY"
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
drink_images = {
    "Iced Vanilla Latte": "https://images.unsplash.com/photo-1517701604599-bb29b565090c",
    "Chocolate Frappe": "https://images.unsplash.com/photo-1572490122747-3968b75cc699",
    "Hot Americano": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085",
    "Mint Mojito": "https://images.unsplash.com/photo-1551751299-1b51cab2694c"
}
# Photo Upload Configuration
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure upload directory exists
os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def remove_emojis(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)
def init_db():
    """Verify database and tables exist, run column migrations, and seed menu/gallery data."""
    try:
        conn = MySQLdb.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            passwd=app.config['MYSQL_PASSWORD']
        )
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['MYSQL_DB']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()
        db = MySQLdb.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            passwd=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )
        cur = db.cursor()
        
        # 1. Create tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cafe_photos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                photo_title VARCHAR(250),
                photo_path VARCHAR(250)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cafe_menu (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(100),
                item_category VARCHAR(100),
                item_price DECIMAL(10,2),
                item_image VARCHAR(255)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100),
                phone VARCHAR(20),
                booking_date DATE,
                booking_slot VARCHAR(50),
                guests_count INT,
                status VARCHAR(20) DEFAULT 'Confirmed'
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(50),
                user_message TEXT,
                ai_response TEXT,
                detected_language VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                password VARCHAR(100)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ml_predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                prediction_for_date DATE,
                predicted_occupancy_percent INT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contact_tickets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                phone VARCHAR(150),
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100),
                item_name VARCHAR(100),
                quantity INT,
                total_price DECIMAL(10,2),
                status VARCHAR(20) DEFAULT 'Pending',
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vibe_notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                author VARCHAR(100),
                note TEXT,
                image_path VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS song_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                song_name VARCHAR(150),
                artist VARCHAR(150),
                requested_by VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Database Migrations (Check and alter existing tables if columns are missing)
        # Check order_date in orders
        cur.execute("SHOW COLUMNS FROM orders LIKE 'order_date'")
        if not cur.fetchone():
            print("Migration: Adding 'order_date' column to existing 'orders' table.")
            cur.execute("ALTER TABLE orders ADD COLUMN order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        # Check status in orders
        cur.execute("SHOW COLUMNS FROM orders LIKE 'status'")
        if not cur.fetchone():
            print("Migration: Adding 'status' column to existing 'orders' table.")
            cur.execute("ALTER TABLE orders ADD COLUMN status VARCHAR(20) DEFAULT 'Pending'")
        # Check item_name in orders
        cur.execute("SHOW COLUMNS FROM orders LIKE 'item_name'")
        if not cur.fetchone():
            cur.execute("SHOW COLUMNS FROM orders LIKE 'item_ordered'")
            if cur.fetchone():
                print("Migration: Adding 'item_name' column to existing 'orders' table and copying from 'item_ordered'.")
                cur.execute("ALTER TABLE orders ADD COLUMN item_name VARCHAR(100)")
                cur.execute("UPDATE orders SET item_name = item_ordered WHERE item_name IS NULL")
            else:
                print("Migration: Adding 'item_name' column to existing 'orders' table.")
                cur.execute("ALTER TABLE orders ADD COLUMN item_name VARCHAR(100)")
            
        # Check status in bookings
        cur.execute("SHOW COLUMNS FROM bookings LIKE 'status'")
        if not cur.fetchone():
            print("Migration: Adding 'status' column to existing 'bookings' table.")
            cur.execute("ALTER TABLE bookings ADD COLUMN status VARCHAR(20) DEFAULT 'Confirmed'")
            
        # Migrate contact_tickets phone column length to 150
        print("Migration: Ensuring 'contact_tickets.phone' column accepts up to 150 characters.")
        cur.execute("ALTER TABLE contact_tickets MODIFY COLUMN phone VARCHAR(150)")
        # Migrate vibe_notes table to add image_path column
        cur.execute("SHOW COLUMNS FROM vibe_notes LIKE 'image_path'")
        if not cur.fetchone():
            print("Migration: Adding 'image_path' column to existing 'vibe_notes' table.")
            cur.execute("ALTER TABLE vibe_notes ADD COLUMN image_path VARCHAR(255) DEFAULT NULL")
        
        # 3. Seed Cafe Menu
        cur.execute("SELECT COUNT(*) FROM cafe_menu")
        if cur.fetchone()[0] == 0:
            default_menu = [
                ("Iced Vanilla Latte", "Coffee Bar", 220.00, "https://images.unsplash.com/photo-1517701604599-bb29b565090c"),
                ("Chocolate Frappe", "Beverages", 280.00, "https://images.unsplash.com/photo-1572490122747-3968b75cc699"),
                ("Hot Americano", "Coffee Bar", 180.00, "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085"),
                ("Mint Mojito", "Beverages", 200.00, "https://images.unsplash.com/photo-1551751299-1b51cab2694c"),
                ("Loaded Cheese Pizza", "Pizza Hub", 320.00, "https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=500&auto=format&fit=crop"),
                ("Peri Peri Paneer Pizza", "Pizza Hub", 360.00, "https://images.unsplash.com/photo-1593560708920-61dd98c46a4e?q=80&w=500&auto=format&fit=crop"),
                ("Creamy White Sauce Pasta", "Pastas", 240.00, "https://images.unsplash.com/photo-1645112411341-6c4fd023714a?q=80&w=500&auto=format&fit=crop"),
                ("KitKat Premium Shake", "Beverages", 250.00, "https://images.unsplash.com/photo-1572490122747-3968b75cc699?q=80&w=500&auto=format&fit=crop"),
                ("Crispy Veg Burger", "Snacks", 180.00, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?q=80&w=500&auto=format&fit=crop"),
                ("Classic French Fries", "Quick Bites", 130.00, "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?q=80&w=500&auto=format&fit=crop")
            ]
            cur.executemany("""
                INSERT INTO cafe_menu (item_name, item_category, item_price, item_image)
                VALUES (%s, %s, %s, %s)
            """, default_menu)
            db.commit()
            print("Successfully seeded cafe_menu with default items!")
            
        # 4. Seed Cafe Photos
        cur.execute("SELECT COUNT(*) FROM cafe_photos")
        if cur.fetchone()[0] == 0:
            default_photos = [
                ("Coffee Counter", "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=600&auto=format&fit=crop"),
                ("Cafe Interior", "https://images.unsplash.com/photo-1554118811-1e0d58224f24?q=80&w=600&auto=format&fit=crop")
            ]
            cur.executemany("""
                INSERT INTO cafe_photos (photo_title, photo_path)
                VALUES (%s, %s)
            """, default_photos)
            db.commit()
            print("Successfully seeded cafe_photos with default gallery counters!")
        # 5. Seed Vibe Notes
        cur.execute("SELECT COUNT(*) FROM vibe_notes")
        if cur.fetchone()[0] == 0:
            default_notes = [
                ("Aman", "Love the vibe here! Coffee is super strong. 💻🔥"),
                ("Riya", "KitKat Shake is to die for! Best place for weekend gossips 🌸✨"),
                ("Kabir", "Coders paradise. High speed wifi works like a charm. ⚡💻")
            ]
            cur.executemany("INSERT INTO vibe_notes (author, note) VALUES (%s, %s)", default_notes)
            db.commit()
            print("Successfully seeded vibe_notes!")
        # 6. Seed Song Requests
        cur.execute("SELECT COUNT(*) FROM song_requests")
        if cur.fetchone()[0] == 0:
            default_songs = [
                ("Cruel Summer", "Taylor Swift", "Riya"),
                ("Starboy", "The Weeknd", "Aman"),
                ("Perfect", "Ed Sheeran", "Kabir")
            ]
            cur.executemany("INSERT INTO song_requests (song_name, artist, requested_by) VALUES (%s, %s, %s)", default_songs)
            db.commit()
            print("Successfully seeded song_requests!")
            
        db.close()
        print("Database verification completed.")
    except Exception as e:
        print(f"Warning: DB initialization skipped: {e}")
# ====================================================================
# 🌐 1. HOME PAGE ROUTE (Gen Z Interface & Photo Gallery)
# ====================================================================
@app.before_request
def init_cart():
    if 'cart' not in session or not isinstance(session['cart'], dict):
        session['cart'] = {}
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cafe_photos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            photo_title VARCHAR(250),
            photo_path VARCHAR(250)
        )
    """)
    cur.execute("SELECT * FROM cafe_photos ORDER BY id DESC")
    photos = cur.fetchall()
    
    # MENU ITEMS FETCH
    cur.execute("SELECT * FROM cafe_menu ORDER BY id DESC")
    menu_items = cur.fetchall()
    
    # VIBE NOTES FETCH
    cur.execute("SELECT id, author, note, image_path, DATE_FORMAT(created_at, '%H:%i | %d %b') FROM vibe_notes ORDER BY id DESC")
    vibe_notes = cur.fetchall()
    
    # SONG REQUESTS FETCH
    cur.execute("SELECT * FROM song_requests ORDER BY id DESC LIMIT 10")
    song_requests = cur.fetchall()
    
    cur.close()
    return render_template(
        'index.html',
        photos=photos,
        menu_items=menu_items,
        vibe_notes=vibe_notes,
        song_requests=song_requests
    )
# ====================================================================
# 📜 2. MENU PAGE ROUTE (Customers ke liye)
# ====================================================================
@app.route('/menu')
def menu_page():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cafe_menu ORDER BY id DESC")
    menu_items = cur.fetchall()
    cur.close()
    return render_template('menu.html', menu=menu_items)
# ====================================================================
# 🍔 3. ADD MENU ITEM ROUTE (Owner Dashboard / Home Form se trigger)
# ====================================================================
@app.route('/add-menu-item', methods=['POST'])
def add_menu_item():
    if 'item_image' not in request.files:
        return "No image file part", 400
        
    file = request.files['item_image']
    name = request.form['item_name']
    category = request.form['item_category']
    price = request.form['item_price']
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Save to static/uploads
        file_path = f"uploads/{filename}"
        full_path = os.path.join(app.root_path, "static", file_path)
        file.save(full_path)
        
        # Insert into Database
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO cafe_menu (item_name, item_category, item_price, item_image)
            VALUES (%s, %s, %s, %s)
        """, (name, category, price, file_path))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('index'))
    return "Invalid File Format", 400
# ====================================================================
# 🔒 4. SLOT BOOKING ROUTE (EMAIL COLUMN REMOVED - FIXED 5 ARGUMENTS)
# ====================================================================
@app.route('/book', methods=['POST'])
def book_table():
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        guests = request.form.get('guests')
        date = request.form.get('date')
        slot = request.form.get('slot')
        
        cur = mysql.connection.cursor()
        
        # Bookings Table Check
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100),
                phone VARCHAR(20),
                booking_date DATE,
                booking_slot VARCHAR(50),
                guests_count INT,
                status VARCHAR(20) DEFAULT 'Confirmed'
            )
        """)
        
        # Insert booking row
        cur.execute("""
            INSERT INTO bookings (customer_name, phone, booking_date, booking_slot, guests_count)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, phone, date, slot, guests))
        
        mysql.connection.commit()
        cur.close()
        
        return "<script>alert('🎉 Tech-Slot Booked Successfully! See you there.'); window.location.href='/';</script>"
        
    except Exception as e:
        print(f"Booking Error Traceback: {e}")
        return f"Database Programming Error: {e}", 500
# ====================================================================
# 📸 5. PHOTO UPLOAD ROUTE (For Owner Gallery)
# ====================================================================
@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    if 'cafe_image' not in request.files:
        return "No file part", 400
    file = request.files['cafe_image']
    title = request.form.get('title', 'smart_cafe_vibes')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = f"uploads/{filename}"
        full_path = os.path.join(app.root_path, "static", file_path)
        file.save(full_path)
        
        # Save photo metadata in DB
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO cafe_photos (photo_title, photo_path) VALUES (%s, %s)", (title, file_path))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('index'))
    return "Invalid File Format", 400
# ====================================================================
# 🔍 6. CUSTOMER BOOKING HISTORY SEARCH ROUTE (Via Phone Module)
# ====================================================================
@app.route('/customer-history', methods=['POST'])
def customer_history():
    search_input = request.form.get('search_input')
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT booking_date, booking_slot, guests_count 
        FROM bookings 
        WHERE phone = %s 
        ORDER BY booking_date DESC
    """, (search_input,))
    
    user_bookings = cur.fetchall()
    
    # Fetch initial components to render index
    cur.execute("SELECT * FROM cafe_photos ORDER BY id DESC")
    photos = cur.fetchall()
    cur.execute("SELECT * FROM cafe_menu ORDER BY id DESC")
    menu_items = cur.fetchall()
    
    cur.close()
    
    return render_template(
        'index.html', 
        user_bookings=user_bookings, 
        searched_by=search_input, 
        photos=photos, 
        menu_items=menu_items
    )
# Chat UI Route
@app.route('/chat')
def chat_page():
    return render_template('chat.html')
# ====================================================================
# 🤖 7. AI CHAT PROCESSING ENGINE (GEMINI CORE CODE)
# ====================================================================
@app.route('/api/chat', methods=['POST'])
def ai_chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({"response": "Please say something!"}), 400
        system_instruction = """
        You are Smart Cafe AI Assistant.
        Behave like a premium cafe waiter.
        Rules:
        1. First understand customer mood and preference
        2. Sweet -> Recommend Iced Vanilla Latte or Chocolate Frappe
        3. Cold -> Recommend Mint Mojito
        4. Hot -> Recommend Hot Americano
        5. Strong coffee -> Recommend Hot Americano
        6. Reply in Hinglish if user uses Hindi
        7. Keep answers short, friendly, and stylish
        8. Always explain why that drink matches customer mood
        """
        full_prompt = system_instruction + "\nUser: " + user_message
        response = model.generate_content(full_prompt)
        ai_response_text = response.text
        
        # Emoji remove for DB compatibility
        clean_response = remove_emojis(ai_response_text)
        detected_lang = "hi" if any(
            word in user_message.lower()
            for word in ["mujhe", "kuch", "chaiye", "kya", "batao"]
        ) else "en"
        
        # Drink image selection
        selected_image = ""
        lower_response = ai_response_text.lower()
        if "vanilla latte" in lower_response:
            selected_image = drink_images["Iced Vanilla Latte"]
        elif "frappe" in lower_response:
            selected_image = drink_images["Chocolate Frappe"]
        elif "americano" in lower_response:
            selected_image = drink_images["Hot Americano"]
        elif "mojito" in lower_response:
            selected_image = drink_images["Mint Mojito"]
            
        # Save chat history
        cur = mysql.connection.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(50),
                user_message TEXT,
                ai_response TEXT,
                detected_language VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            INSERT INTO chat_history (session_id, user_message, ai_response, detected_language)
            VALUES (%s, %s, %s, %s)
        """, ("session_123", user_message, clean_response, detected_lang))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            "response": ai_response_text,
            "image": selected_image
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "response": f"REAL ERROR: {str(e)}"
        }), 500
@app.route('/login')
def login_page():
    return render_template('login.html')
@app.route('/signin')
def signin():
    return render_template('signin.html')
@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    cur = mysql.connection.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            password VARCHAR(100)
        )
    """)
    cur.execute("""
        INSERT INTO users (name, email, password)
        VALUES (%s, %s, %s)
    """, (name, email, password))
    mysql.connection.commit()
    cur.close()
    return "<script>alert('SignIn Successful');window.location='/login';</script>"
@app.route('/auth-signin', methods=['POST'])
def auth_signin():
    email = request.form.get('user_email')
    password = request.form.get('user_pass')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cur.fetchone()
    cur.close()
    if user:
        session['user'] = user[1]
        return "<script>alert('Login Successful! Welcome to Cozy Cafe.'); window.location.href='/';</script>"
    else:
        return "<script>alert('Invalid Credentials! Please try again.'); window.location.href='/login';</script>"
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/location')
def location():
    return render_template('location.html')
@app.route('/submit-vibe-note', methods=['POST'])
def submit_vibe_note():
    author = request.form.get('author')
    note = request.form.get('note')
    
    file_path = None
    if 'vibe_image' in request.files:
        file = request.files['vibe_image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"vibe_{random.randint(1000, 9999)}_{filename}"
            file_path = f"uploads/{unique_filename}"
            full_path = os.path.join(app.root_path, "static", file_path)
            file.save(full_path)
            
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO vibe_notes (author, note, image_path) VALUES (%s, %s, %s)", (author, note, file_path))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index') + '#vibe-wall')
@app.route('/submit-song-request', methods=['POST'])
def submit_song_request():
    song_name = request.form.get('song_name')
    artist = request.form.get('artist')
    requested_by = request.form.get('requested_by')
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO song_requests (song_name, artist, requested_by) VALUES (%s, %s, %s)", (song_name, artist, requested_by))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index') + '#music-queue')
@app.route('/admin/delete-vibe-note/<int:note_id>')
def delete_vibe_note(note_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM vibe_notes WHERE id = %s", (note_id,))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print("Error deleting vibe note:", e)
    return redirect(url_for('dashboard'))
@app.route('/admin/delete-song-request/<int:request_id>')
def delete_song_request(request_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM song_requests WHERE id = %s", (request_id,))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print("Error deleting song request:", e)
    return redirect(url_for('dashboard'))
# ====================================================================
# 📊 8. OWNER MASTER ANALYTICS CONTROL PANEL
# ====================================================================
@app.route('/dashboard')
def dashboard():
    cur = mysql.connection.cursor()
    # 1. Bookings
    cur.execute("SELECT * FROM bookings ORDER BY id ASC")
    bookings = cur.fetchall()
    
    # 2. Orders with robust fallback order by clause
    try:
        cur.execute("SELECT id, customer_name, item_name, quantity, total_price, status, order_date FROM orders ORDER BY order_date DESC")
        orders = cur.fetchall()
    except Exception:
        try:
            cur.execute("SELECT id, customer_name, item_name, quantity, total_price, status, order_date FROM orders ORDER BY id DESC")
            orders = cur.fetchall()
        except Exception:
            orders = []
        
    # 3. ML occupancy predictions
    friday_prediction = predict_occupancy(
        day_code=6,
        month=6,
        weekend=1,
        festival=0,
        avg_slot=3,
        previous_occupancy=25
    )
    ml_training_data = get_historical_data()
    
    # 4. Save prediction
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ml_predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                prediction_for_date DATE,
                predicted_occupancy_percent INT
            )
        """)
        # Generate predictions dynamically for each unique booking date if not exists
        for row in ml_training_data:
            b_date = row[0]
            cur.execute("SELECT id FROM ml_predictions WHERE prediction_for_date = %s", (b_date,))
            if not cur.fetchone():
                day_code = int(row[1]) if row[1] is not None else 6
                month_code = int(row[2]) if row[2] is not None else 6
                weekend_code = int(row[3]) if row[3] is not None else 0
                avg_slot_val = int(row[4]) if row[4] is not None else 3
                prev_occ = int(row[5]) if row[5] is not None else 25
                
                try:
                    from ml_model import is_festival
                    fest_val = is_festival(b_date)
                except Exception:
                    fest_val = 0
                
                pred_val = predict_occupancy(
                    day_code=day_code,
                    month=month_code,
                    weekend=weekend_code,
                    festival=fest_val,
                    avg_slot=avg_slot_val,
                    previous_occupancy=prev_occ
                )
                cur.execute("""
                    INSERT INTO ml_predictions (prediction_for_date, predicted_occupancy_percent)
                    VALUES (%s, %s)
                """, (b_date, pred_val))
                
        # Save CURDATE() prediction as backup
        cur.execute("SELECT id FROM ml_predictions WHERE prediction_for_date = CURDATE()")
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO ml_predictions (prediction_for_date, predicted_occupancy_percent)
                VALUES (CURDATE(), %s)
            """, (friday_prediction,))
        mysql.connection.commit()
    except Exception as e:
        print("ML Prediction Generation Error:", e)
        
    # 5. Fetch predictions grouped by date
    cur.execute("""
        SELECT MIN(id) as id, prediction_for_date, MAX(predicted_occupancy_percent) as predicted_occupancy_percent 
        FROM ml_predictions 
        GROUP BY prediction_for_date 
        ORDER BY prediction_for_date DESC
    """)
    prediction_data = cur.fetchall()
    
    # 6. Fetch support tickets
    try:
        cur.execute("SELECT * FROM contact_tickets ORDER BY created_at DESC")
        tickets = cur.fetchall()
    except Exception:
        tickets = []
    # 7. Fetch vibe notes for dashboard management
    try:
        cur.execute("SELECT * FROM vibe_notes ORDER BY id DESC")
        vibe_notes = cur.fetchall()
    except Exception:
        vibe_notes = []
    # 8. Fetch song requests for dashboard management
    try:
        cur.execute("SELECT * FROM song_requests ORDER BY id DESC")
        song_requests = cur.fetchall()
    except Exception:
        song_requests = []
        
    cur.close()
    return render_template(
        "dashboard.html",
        ml_predict=friday_prediction,
        bookings=bookings,
        orders=orders,
        ml_training_data=ml_training_data,
        prediction_data=prediction_data,
        tickets=tickets,
        vibe_notes=vibe_notes,
        song_requests=song_requests
    )
# ====================================================================
# 🎟️ 9. WEEKLY COUPON / WINNER SELECTION SYSTEM
# ====================================================================
@app.route('/weekly-winners')
def weekly_winners():
    cur = mysql.connection.cursor()
    
    # Couple bookings selection (guests_count = 2)
    cur.execute("SELECT customer_name, booking_date FROM bookings WHERE guests_count = 2")
    all_couples = cur.fetchall()
    
    lucky_couples = []
    if len(all_couples) >= 2:
        lucky_couples = random.sample(all_couples, 2)
    elif len(all_couples) > 0:
        lucky_couples = all_couples
    cur.close()
    return render_template('winners.html', winners=lucky_couples)
# ====================================================================
# 📬 10. CONTACT FORM SUPPORT SYSTEM (Direct to MySQL)
# ====================================================================
@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    name = request.form.get('c_name')
    phone = request.form.get('c_phone')
    msg = request.form.get('c_message')
    
    cur = mysql.connection.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contact_tickets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            phone VARCHAR(150),
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("INSERT INTO contact_tickets (name, phone, message) VALUES (%s, %s, %s)", (name, phone, msg))
    mysql.connection.commit()
    cur.close()
    
    return "<script>alert('Message Sent Successfully! Cafe admin team will contact you back.'); window.location.href='/';</script>"
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contact_tickets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    phone VARCHAR(150),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("INSERT INTO contact_tickets (name, phone, message) VALUES (%s, %s, %s)", (name, email, message))
            mysql.connection.commit()
            cur.close()
            return "<script>alert('Message Sent Successfully!'); window.location.href='/';</script>"
        except Exception as e:
            print("Error writing general contact:", e)
            return f"Database Error: {e}", 500
    return render_template("contact.html")
# ====================================================================
# 📬 SUPPORT TICKETS VIEW & RESOLVE (Admin ke liye)
# ====================================================================
@app.route('/admin/support-tickets')
def support_tickets():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM contact_tickets ORDER BY created_at DESC")
    tickets = cur.fetchall()
    cur.close()
    return render_template('support_admin.html', tickets=tickets)
@app.route('/admin/delete-ticket/<int:ticket_id>')
def delete_ticket(ticket_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM contact_tickets WHERE id = %s", (ticket_id,))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print("Error deleting ticket:", e)
    return redirect(url_for('dashboard'))
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    item_name = request.form['item_name']
    price = float(request.form['price'])
    image = request.form.get('image')
    
    cart = session.get('cart', {})
    if item_name in cart:
        cart[item_name]['qty'] += 1
    else:
        cart[item_name] = {
            'price': price,
            'qty': 1,
            'image': image
        }
    session['cart'] = cart
    session.modified = True
    return redirect('/cart')
@app.route('/decrease-cart', methods=['POST'])
def decrease_cart():
    item_name = request.form['item_name']
    cart = session.get('cart', {})
    if item_name in cart:
        cart[item_name]['qty'] -= 1
        if cart[item_name]['qty'] <= 0:
            del cart[item_name]
    session['cart'] = cart
    session.modified = True
    return redirect('/cart')
@app.route('/cart')
def cart():
    cart_data = session.get('cart', {})
    subtotal = 0
    for name, data in cart_data.items():
        subtotal += data['price'] * data['qty']
    handling_fee = 20
    security_fee = 10
    total = subtotal + handling_fee + security_fee
    return render_template(
        'cart.html',
        cart=cart_data,
        subtotal=subtotal,
        handling_fee=handling_fee,
        security_fee=security_fee,
        total=total
    )
@app.route('/confirm-order', methods=['POST'])
def confirm_order():
    name = request.form['customer_name']
    cart = session.get('cart', {})
    cur = mysql.connection.cursor()
    for item_name, data in cart.items():
        total = data['price'] * data['qty']
        cur.execute("""
            INSERT INTO orders (customer_name, item_name, quantity, total_price, status)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            name,
            item_name,
            data['qty'],
            total,
            "Pending"
        ))
    mysql.connection.commit()
    cur.close()
    session['cart'] = {}
    return redirect('/dashboard')
@app.route('/confirm-order/<int:order_id>')
def confirm_order_admin(order_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE orders
        SET status = 'Confirmed'
        WHERE id = %s
    """, (order_id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/dashboard')
@app.route('/place-order')
def place_order():
    cart = session.get('cart', {})
    cur = mysql.connection.cursor()
    for item_name, data in cart.items():
        total = data['price'] * data['qty']
        cur.execute("""
            INSERT INTO orders (customer_name, item_name, quantity, total_price, status)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            "Pammy",   # Default logged in user
            item_name,
            total,
            "Pending"
        ))
    mysql.connection.commit()
    cur.close()
    session['cart'] = {}
    return redirect('/dashboard')
# ====================================================================
# 🚀 12. RUN ENGINE PLATFORM
# ====================================================================
if __name__ == '__main__':
    # Initialize DB Tables on Startup
    init_db()
    
    try:
        print("🔄 Checking & Auto-Retraining ML Model with latest database entries...")
        train_demand_model()
    except Exception as e:
        print(f"ML Startup Training Skipped: {e}")
        
    app.run(debug=True, use_reloader=False)
