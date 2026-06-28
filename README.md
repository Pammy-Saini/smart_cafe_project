Cozy Cafe 🌸 - Next-Gen AI & ML Specialty Tech-Cafe




Cozy Cafe is a responsive, aesthetically stunning Flask web application designed for a modern, tech-forward cafe experience. Blending premium specialty coffee vibes with state-of-the-art Artificial Intelligence and Machine Learning, the platform is tailored for Gen Z and tech lovers.

🚀 Key Features
🤖 VibeCheck AI Drink Portal: An intelligent, Hinglish/Hindi-supported chatbot powered by the Google Gemini API that analyzes customer mood and preferences to recommend custom signature drinks with matching background aesthetics.
🔮 ML Occupancy Prediction: A dynamic Machine Learning model that predicts Friday occupancy rates and weekly customer volume trends based on historical bookings, weekends, and local festivals.
💬 Gen Z Community Vibe Wall: A Pinterest-inspired anonymous post-it wall supporting full image/photo uploads where customers can pin their cafe memories.
🎧 Spotify DJ Request Queue: An interactive jukebox queue allowing customers to request songs which populate a live speaker feed and database queue.
📅 Tech-Slot Table Reservation: A slot booking engine with a built-in search logs utility where customers can instantly verify booking confirmations via phone number.
📊 Owner Analytics Dashboard: A robust admin panel providing live metrics on occupancy, bookings, orders, and moderation utilities to delete vibe notes or clear requested songs.
🎟️ Weekly Giveaway System: An automated lucky draw module that picks winners from couple bookings for special cafe promotions.
🛠️ Technology Stack
Backend: Python 3.x, Flask Web Framework
Database: MySQL Server (MySQLdb / PyMySQL)
Artificial Intelligence: Google Generative AI (Gemini Flash Model)
Machine Learning: Scikit-Learn (Linear Regression / Random Forest), Pandas, NumPy, Pickle
Frontend: HTML5, CSS3, Tailwind CSS, Javascript, Chart.js
💻 Setup & Installation Instructions
1. Prerequisite Configuration
Ensure you have MySQL server running locally. Create the database:

sql

CREATE DATABASE smart_cafe_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
2. Clone and Setup Environment
Navigate to the project root and create a virtual environment:

bash

python -m venv .venv
Activate the environment:

Windows (Powershell): .venv\Scripts\Activate.ps1
Windows (CMD): .venv\Scripts\activate.bat
3. Install Dependencies
bash

pip install -r requirements.txt
4. Run the Application
Start the Flask development server:

bash

python app.py
The application will automatically verify tables, execute any missing database schema migrations, train the ML model on startup, and host locally at http://127.0.0.1:5000/.
