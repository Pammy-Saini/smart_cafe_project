# ☕ Cozy Cafe 🌸 — Next-Gen AI & ML Specialty Tech Cafe

Cozy Cafe is a modern, AI-powered cafe management web application built using **Flask, Machine Learning, MySQL, and Google Gemini AI**.  
It delivers a premium digital cafe experience by combining specialty coffee culture with Artificial Intelligence, smart analytics, and an aesthetic Gen-Z inspired interface.

Designed for **tech lovers, cafe owners, and modern customers**, this platform provides intelligent drink recommendations, ML-based occupancy prediction, live order management, and an interactive community experience.

---

## ✨ Project Highlights

- Responsive and modern UI  
- AI-powered drink recommendation system  
- Machine Learning occupancy forecasting  
- Live customer interaction modules  
- Admin dashboard with analytics  
- Full database integration using MySQL  

---

# 🚀 Key Features

## 🤖 VibeCheck AI Drink Portal
An intelligent chatbot powered by **Google Gemini AI**.

Features:
- Understands customer mood and drink preference  
- Supports **English, Hinglish, and Hindi**
- Recommends signature drinks instantly  
- Explains why the drink matches customer mood  
- Shows matching drink visuals  

Example:
> “Mujhe kuch cold aur sweet chahiye”  
→ AI recommends **Chocolate Frappe** 🍫

---

## 🔮 ML Occupancy Prediction
A Machine Learning model predicts cafe crowd levels using historical data.

Prediction factors:
- Day of week  
- Month  
- Weekend status  
- Festival season  
- Previous occupancy  
- Average booking slots  

Helps cafe owners with:
- Staff planning  
- Inventory management  
- Peak-hour optimization  

---

## 📅 Tech-Slot Table Reservation
Customers can reserve cafe tables using smart booking slots.

Features:
- Slot-based booking  
- Guest count tracking  
- Booking confirmation  
- Phone-based booking history search  

---

## 🛒 Smart Cart & Order System
Customers can add food/drinks to cart and place orders.

Features:
- Add to cart  
- Quantity management  
- Price calculation  
- Order confirmation  
- Admin order tracking  

---

## 📊 Owner Analytics Dashboard
A powerful admin dashboard for cafe management.

Includes:
- Total bookings  
- Order records  
- Customer queries  
- ML prediction charts  
- Occupancy statistics  
- Weekly analytics  

---

## 💬 Gen Z Community Vibe Wall
A modern Pinterest-style community wall.

Customers can:
- Upload selfies  
- Share cafe memories  
- Post coffee moments  
- Upload aesthetic images  

Example:
> “My cold coffee moment ☕✨”

---

## 🎧 Spotify DJ Request Queue
Interactive music request system.

Customers can:
- Request songs  
- Add mood music  
- Update live speaker queue  

Creates a premium cafe vibe.

---

## 🎟️ Weekly Giveaway System
Automatic lucky draw system.

Features:
- Selects winners from couple bookings  
- Generates promotional winners  
- Useful for cafe offers & events  

---

# 🛠 Tech Stack

## Backend
- Python 3.x
- Flask

## Database
- MySQL
- Flask-MySQLdb

## Artificial Intelligence
- Google Generative AI
- Gemini Flash Model

## Machine Learning
- Scikit-Learn
- Pandas
- NumPy
- Pickle

## Frontend
- HTML5
- CSS3
- Tailwind CSS
- JavaScript
- Chart.js
- Jinja2 Templates

---

# 📂 Project Modules

Main modules included:

- Customer Interface  
- Admin Dashboard  
- AI Chat Assistant  
- Reservation System  
- Order Management  
- ML Prediction Engine  
- Community Upload System  

---

# 💻 Installation Guide

## 1) Clone Repository

```bash
git clone <your-repo-link>
cd smart_cafe_project
```

## 2) Create Virtual Environment

```bash
python -m venv .venv
```

Activate:

### Windows PowerShell
```bash
.venv\Scripts\Activate.ps1
```

### Windows CMD
```bash
.venv\Scripts\activate.bat
```

---

## 3) Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4) Configure MySQL Database

Create database:

```sql
CREATE DATABASE smart_cafe_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Update database configuration in `app.py`:

```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'smart_cafe_db'
```

---

## 5) Configure Environment Variables

Create `.env` file:

```env
GENAI_API_KEY=your_api_key_here
```

⚠️ Never push API keys to GitHub.

---

## 6) Run Application

```bash
python app.py
```

Server runs at:

```text
http://127.0.0.1:5000/
```

---

# 🧠 Machine Learning Workflow

1. Collect booking history  
2. Clean historical data  
3. Train prediction model  
4. Save trained model using Pickle  
5. Predict future occupancy  

---

# 📸 Screens Included
Project contains:

- Homepage UI  
- AI Chat Portal  
- Menu Section  
- Cart Page  
- Booking Interface  
- Analytics Dashboard  

---

# 🎯 Future Improvements

Planned upgrades:

- Online payment gateway  
- Live order notifications  
- Recommendation engine for food combos  
- User authentication with password hashing  
- Sales forecasting using advanced ML  
- Deployment on cloud  

---

# 👩‍💻 Developer

**Pammy Saini**  
Python Developer | AI/ML Enthusiast | Flask Developer  

Built with ❤️ using AI + ML + Coffee
