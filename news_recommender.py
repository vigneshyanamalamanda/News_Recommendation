import streamlit as st
import requests
import re
import sqlite3
from googlesearch import search
from datetime import datetime
from collections import defaultdict
import csv
import os
import pandas as pd
import joblib
from fuzzywuzzy import process
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import numpy as np

# Load data
news = pd.read_json("Data/news.json", lines=True)

# Preprocessing
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return " ".join(text.split())

def load_embeddings():
    return joblib.load('news_embeddings.pkl')

news_embeddings = load_embeddings()

# Load models
try:
    vectorizer = joblib.load('tfidf_vectorizer.pkl')
    nn_model = joblib.load('nearest_neighbors_model.pkl')
    embedding_model = SentenceTransformer('models/all-MiniLM-L6-v2')
except Exception as e:
    st.error(f"Model loading failed: {e}")
    st.stop()

# TF-IDF based recommendation
def recommend_tfidf(title, top_n=5):
    clean_title = preprocess_text(title)
    match = process.extractOne(clean_title, news['headline'].tolist())[0]
    matched_article = news[news['headline'] == match].iloc[0]

    tfidf_vector = vectorizer.transform([match])
    _, indices = nn_model.kneighbors(tfidf_vector, n_neighbors=top_n + 1)
    recommended_articles = news.iloc[indices[0][1:]]
    return matched_article, recommended_articles

# Embedding-based recommendation
def recommend_embedding(title, top_n=5):
    query_vec = embedding_model.encode([title])
    similarities = cosine_similarity(query_vec, news_embeddings)[0]
    top_indices = np.argsort(similarities)[::-1]

    matched_index = top_indices[0]
    matched_article = news.iloc[matched_index]
    recommended_indices = top_indices[1:top_n + 1]
    recommended_articles = news.iloc[recommended_indices]
    return matched_article, recommended_articles

# Diversify by category
def diversify_by_category(matched_article, recommended_articles):
    matched_category = matched_article.get("category", None)
    if matched_category:
        diverse = news[news['category'] != matched_category]
        return diverse.sample(min(3, len(diverse)))  # up to 3 random different-category articles
    return recommended_articles

# Compute diversity score (based on category count)
def compute_diversity_score(df):
    diversity = df['category'].nunique() if 'category' in df else 0
    return diversity / len(df) if len(df) > 0 else 0


# Connect to DB
def connect_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    return conn, cursor

# Create tables
def create_users_table():
    conn, cursor = connect_db()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            email TEXT,
            join_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Register user
def register_user(username, password, email):
    conn, cursor = connect_db()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        return False
    join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, password, email, join_date))
    conn.commit()
    conn.close()
    return True

def save_liked_article(username, title, url):
    with open("liked_articles.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([username, title, url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

def save_favorite_article(username, title, url, description, image_url):
    with open("favorite_articles.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([username, title, url, description, image_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

def load_liked_articles(username):
    liked = set()
    if os.path.exists("liked_articles.csv"):
        with open("liked_articles.csv", mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username:
                    liked.add(row[1])
    return liked

def load_favorite_articles(username):
    favorites = []
    if os.path.exists("favorite_articles.csv"):
        with open("favorite_articles.csv", mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username:
                    favorites.append({
                        "title": row[1],
                        "url": row[2],
                        "description": row[3],
                        "image_url": row[4]
                    })
    return favorites

def check_credentials(username, password):
    conn, cursor = connect_db()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def get_user_details(username):
    conn, cursor = connect_db()
    cursor.execute("SELECT username, email, join_date FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_recommended_articles(all_articles, keyword_profile):
    recommendations = []
    for article in all_articles:
        title = article.get("title", "")
        description = article.get("description", "")
        article_text = title + " " + description
        score = sum(keyword_profile[word] for word in extract_keywords(article_text) if word in keyword_profile)
        if score > 0:
            recommendations.append((score, article))
    recommendations.sort(reverse=True, key=lambda x: x[0])
    return [article for score, article in recommendations]

def profile_page():
    st.title("👤 Your Profile")
    user = get_user_details(st.session_state.username)
    if user:
        st.write("### Username:", user[0])
        st.write("### Email:", user[1])
        st.write("### Joined On:", user[2])
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

def login_page():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_credentials(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.liked = load_liked_articles(username)
            st.session_state.favorites = load_favorite_articles(username)
            st.session_state.disliked = set()
            st.rerun()
        else:
            st.error("Invalid credentials")

def registration_page():
    st.title("📝 Register")
    username = st.text_input("Choose a Username")
    email = st.text_input("Your Email")
    password = st.text_input("Choose a Password", type="password")
    if st.button("Register"):
        if register_user(username, password, email):
            st.success("Registration successful! Please log in.")
            st.session_state.registered = True
            st.rerun()
        else:
            st.error("Username already taken")

def generate_safe_id(text):
    return re.sub(r'\W+', '_', text.lower())

def fetch_articles(category):
    API_KEY = "a7e38c01cbbf4a24a2ec91fa62417823"
    URL = "https://newsapi.org/v2/top-headlines"
    params = {"country": "us", "category": category.lower(), "apiKey": API_KEY, "pageSize": 10}
    res = requests.get(URL, params=params)
    return res.json().get("articles", []) if res.status_code == 200 else []

def extract_keywords(title):
    return set(re.findall(r'\b\w{5,}\b', title.lower()))

def is_similar(title1, title2):
    return len(extract_keywords(title1) & extract_keywords(title2)) > 1

def search_similar_articles(title):
    query = "+".join(title.split())
    url = f"https://www.bing.com/search?q={query}+site:news"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        links = re.findall(r'href="(https://[^"]+)"', res.text)
        return [link for link in links if "bing.com" not in link][:5]
    except Exception:
        return []

def news_page():
    st.title("📰 Personalized News Recommender")

    title_input = st.text_input("🔍 Enter a news headline:")
    method = st.radio("Choose recommendation method:", ["TF-IDF", "Sentence Embedding"])
    challenge_mode = st.checkbox("🎯 Challenge my perspective (show opposing views)")
    show_diversity = st.checkbox("📊 Show diversity score")
    explore_mode = st.checkbox("🌍 Surprise me with something different")

    if title_input:
        with st.spinner("Fetching recommendations..."):
            if method == "TF-IDF":
                matched_article, recommended_articles = recommend_tfidf(title_input)
            else:
                matched_article, recommended_articles = recommend_embedding(title_input)
                
            # Optionally diversify 
            if challenge_mode:
                recommended_articles = diversify_by_category(matched_article, recommended_articles)

            # Diversity score
            diversity_score = compute_diversity_score(recommended_articles)

        st.subheader("📰 Matched Article")
        st.markdown(f"**Headline:** {matched_article['headline']}")
        st.markdown(f"**Description:** {matched_article['short_description']}")   
        if 'category' in matched_article:
            st.markdown(f"**Category:** {matched_article['category']}")
        if 'source' in matched_article:
            st.markdown(f"**Source:** {matched_article['source']}")
        
        st.subheader("🔁 Recommended Articles")
        if show_diversity:   
            st.markdown(f"📊 **Diversity Score:** `{diversity_score:.2f}`")

        for idx, row in recommended_articles.iterrows():
            st.markdown(f"### {row['headline']}")
            if 'image' in row and pd.notnull(row['image']):
                st.image(row['image'], width=600)
            if 'short_description' in row and pd.notnull(row['short_description']):
                st.write(row['short_description'])
            if 'category' in row and pd.notnull(row['category']):
                st.markdown(f"*Category: {row['category']}*")
            if 'source' in row and pd.notnull(row['source']):
                st.markdown(f"*Source: {row['source']}*")
            if 'link' in row and pd.notnull(row['link']):
                st.markdown(f"[🔗 Read full article]({row['link']})", unsafe_allow_html=True)
            st.markdown("---")

    # Out-of-bubble explorer
    if explore_mode:
        st.subheader("🌐 Explore Outside Your Bubble")
        explore_article = news.sample(1).iloc[0]
        st.markdown(f"### {explore_article['headline']}")
        st.write(explore_article.get('short_description', ''))
        if 'image' in explore_article and pd.notnull(explore_article['image']):
            st.image(explore_article['image'], width=600)
        if 'link' in explore_article and pd.notnull(explore_article['link']):
            st.markdown(f"[🔗 Read full article]({explore_article['link']})", unsafe_allow_html=True)
                                               
    categories = ["Technology", "Sports", "Business", "Entertainment", "Health", "Science", "General"]
    selected = st.multiselect("Choose categories:", categories, default=["Technology"])
    show_favorites = st.checkbox("⭐ Show Favorites")
    show_similar = st.checkbox("🔍 Show Similar Articles")
    
    if show_favorites and st.session_state.favorites:
        st.subheader("⭐ Your Favorites")
        for fav in st.session_state.favorites:
            st.markdown(f"### [{fav['title']}]({fav['url']})")
            if fav.get("image_url"):
                st.image(fav["image_url"], width=600)
            st.markdown(f"_{fav['description']}_")
            if show_similar:
                links = search_similar_articles(fav["title"])
                st.markdown("**Related:**")
                for l in links:
                    st.markdown(f"- [{l}]({l})")
            st.markdown("---")

    for category in selected:
        for article in fetch_articles(category):
            title = article["title"]
            if title in st.session_state.disliked:
                continue

            safe_id = generate_safe_id(title)
            st.markdown(f"## {title}")
            if article.get("urlToImage"):
                st.image(article["urlToImage"], width=600)
            st.markdown(f"_{article.get('description', '')}_")
            st.markdown(f"[Read more ➡️]({article['url']})")

            col1, col2 = st.columns(2)
            with col1:
                liked = title in st.session_state.liked
                if st.button(f"{'❤️' if liked else '🤍'} Like", key=f"like_{safe_id}"):
                    if liked:
                        st.session_state.liked.remove(title)
                    else:
                        st.session_state.liked.add(title)
                        save_liked_article(st.session_state.username, title, article["url"])
            with col2:
                if st.button("⭐ Favorite", key=f"fav_{safe_id}"):
                    if not any(f["title"] == title for f in st.session_state.favorites):
                        fav_obj = {
                            "title": title,
                            "url": article["url"],
                            "description": article.get("description", ""),
                            "image_url": article.get("urlToImage", "")
                        }
                        st.session_state.favorites.append(fav_obj)
                        save_favorite_article(st.session_state.username, **fav_obj)
                        st.success("Added to favorites")
            st.markdown("---")

# Main App Logic
def main():
    st.set_page_config(page_title="Smart News", layout="wide")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.liked = set()
        st.session_state.favorites = []
        st.session_state.disliked = set()

    create_users_table()

    if not st.session_state.logged_in:
        choice = st.sidebar.selectbox("Choose an option", ["Login", "Register"])
        if choice == "Login":
            login_page()
        else:
            registration_page()
    else:
        st.sidebar.title(f"Welcome, {st.session_state.username}")
        page = st.sidebar.radio("Navigate", ["News Feed", "Profile"])
        if page == "News Feed":
            news_page()
        else:
            profile_page()

if __name__ == "__main__":
    main()
