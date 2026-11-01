# AI-Powered Food Ordering System with Chatbot

A beginner-friendly full-stack web application built using Django, featuring an AI chatbot powered by Natural Language Processing (NLP). Users can browse a food menu, add items to their shopping cart, place orders, and chat with an intelligent assistant to get recommendations and track orders.

## Features
- **User Authentication:** Registration, Login, Logout, and User Profile.
- **Food Menu & Ordering:** Search and filter food by categories, add to cart, and checkout.
- **AI Chatbot (NLP):** Natural Language Processing with `scikit-learn` and `nltk` using TF-IDF for intent recognition. Suggests menu items and helps users navigate.
- **Recommendation Engine:** Suggests popular items on the homepage based on order frequency.
- **Responsive UI:** Clean frontend using Bootstrap 5.

## Technology Stack
- **Backend:** Django 5, Python 3
- **Frontend:** HTML, Vanilla CSS, JS (jQuery for AJAX), Bootstrap 5
- **Database:** SQLite (default)
- **AI/NLP:** NLTK, Scikit-learn (TF-IDF vectorizer and Cosine Similarity)

## Setup Instructions

1. **Clone the project & Navigate to the directory**
   ```bash
   cd "AI-based food ordering"
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Database Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a Superuser (Admin) to manage the food menu**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the Server**
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser.

## Managing Food Menu
Log into the Django Admin Panel at `http://127.0.0.1:8000/admin/` with the superuser account you created. From there, you can add `Categories` (like "Pizza", "Drinks") and `Food Items` to build out the menu.

## Chatbot Logic
The chatbot is pre-trained using a custom JSON dataset located in `chatbot/dataset/intents.json`. It computes the Cosine Similarity over an NLTK-tokenized TF-IDF vector matrix to figure out user intents such as greeting, requesting vegetarian options, or asking for the menu.
