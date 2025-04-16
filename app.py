import streamlit as st
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

# Cache embeddings
@st.cache_data(show_spinner=True)
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

# UI Starts Here
st.title("🗞️ News Recommendation System")

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

# Footer
st.markdown("""
---
👨‍💻 *Built with Streamlit · Sentence Transformers · Scikit-learn · FuzzyWuzzy*  
📚 *Promoting perspective diversity and reducing algorithmic bias.*
""")
