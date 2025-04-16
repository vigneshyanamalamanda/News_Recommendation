import pandas as pd
from sentence_transformers import SentenceTransformer
import joblib

# Load your news data
news = pd.read_json("Data/news.json", lines=True)

# Load the SentenceTransformer model
embedding_model = SentenceTransformer('models/all-MiniLM-L6-v2')

# Precompute embeddings for news headlines
embeddings = embedding_model.encode(news['headline'].tolist(), show_progress_bar=True)

# Save embeddings to a file
joblib.dump(embeddings, 'news_embeddings.pkl')

print("Embeddings saved successfully!")
