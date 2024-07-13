import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import nltk
from nltk.corpus import stopwords
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from tweetapi import TweetApi

# Inisialisasi TweetApi untuk mengambil data komentar dari tweet tertentu
tw = TweetApi()

# Fungsi untuk mengumpulkan data komentar dari tweet dengan ID tertentu
def TweetCollection(tweet_id, scarp_continue=5):
    data_collection = []  # List untuk menyimpan data komentar
    try:
        data, status = tw.TweetAPIReplies(tweet_id)  # Ambil balasan tweet pertama
        if status == 200:
            # Tambahkan setiap balasan tweet ke dalam data_collection
            for reply in data["replies"]:
                data_collection.append({
                    "text": reply['text'],
                    "username": reply['user']['username']
                })
            continuation_token = data["continuation_token"]  # Token untuk melanjutkan pengambilan data berikutnya
            if scarp_continue > 0:
                # Lanjutkan mengambil data balasan tweet hingga scarp_continue kali
                for x in range(scarp_continue):
                    data, status = tw.TweetAPISearchContinuation(tweet_id, continuation_token)
                    if status == 200:
                        for reply in data["replies"]:
                            data_collection.append({
                                "text": reply['text'],
                                "username": reply['user']['username']
                            })
                        continuation_token = data["continuation_token"]
                    else:
                        print(f"Error on TweetAPISearchContinuation, status code: {status}, loop: {x + 1}")
            return data_collection
        else:
            raise Exception(f"Error on TweetCollection, status code: {status}")
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Meminta pengguna untuk memasukkan Tweet ID
tweet_id = input("Masukkan Tweet ID: ")

# Kumpulkan data komentar dari tweet dengan ID yang diberikan
database_collections = TweetCollection(tweet_id, scarp_continue=5)

# Pastikan untuk mengunduh stopwords jika belum
nltk.download('stopwords')

# Data sample yang diambil dari API
data = database_collections

# Convert data to DataFrame
df = pd.DataFrame(data)

# Fungsi untuk preprocessing teks
def preprocess_text(text):
    text = re.sub(r'http\S+', '', text)  # Hapus URL
    text = re.sub(r'@\w+', '', text)  # Hapus mentions
    text = re.sub(r'#\w+', '', text)  # Hapus hashtags
    text = re.sub(r'[^A-Za-z\s]', '', text)  # Hapus karakter non-alfabet
    text = text.lower().strip()  # Konversi ke huruf kecil dan hapus spasi di awal/akhir
    text = ' '.join([word for word in text.split() if word not in stopwords.words('english')])  # Hapus stopwords
    return text

# Terapkan preprocessing pada teks di kolom 'text'
df['clean_text'] = df['text'].apply(preprocess_text)

# Menggunakan VADER untuk analisis sentimen
analyzer = SentimentIntensityAnalyzer()

def vader_sentiment_analysis(text):
    score = analyzer.polarity_scores(text)
    if score['compound'] >= 0.05:
        return 1  # Positif
    elif score['compound'] <= -0.05:
        return 0  # Negatif
    else:
        return 2  # Netral (opsional, bisa digabung dengan negatif)

# Terapkan analisis sentimen VADER pada teks
df['sentiment'] = df['text'].apply(vader_sentiment_analysis)

# Bagi data menjadi set pelatihan dan pengujian
X_train, X_test, y_train, y_test = train_test_split(df['clean_text'], df['sentiment'], test_size=0.2, random_state=42)

# Konversi teks menjadi fitur menggunakan TF-IDF Vectorizer
vectorizer = TfidfVectorizer(max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Latih model regresi logistik
model = LogisticRegression()
model.fit(X_train_vec, y_train)

# Prediksi dan evaluasi model
y_pred = model.predict(X_test_vec)
print('Accuracy:', accuracy_score(y_test, y_pred))
print('Classification Report:\n', classification_report(y_test, y_pred, zero_division=0))

# Gunakan model untuk data baru
new_comments = [comment['text'] for comment in data]

# Preprocessing pada data baru
new_comments_clean = [preprocess_text(comment) for comment in new_comments]
new_comments_vec = vectorizer.transform(new_comments_clean)
predictions = model.predict(new_comments_vec)

# Buat DataFrame untuk komentar baru dan sentimen yang diprediksi
new_comments_df = pd.DataFrame({
    'comment': new_comments,
    'sentiment': ['Positive' if sentiment == 1 else 'Negative' for sentiment in predictions]
})

# Simpan hasil analisis sentimen ke dalam file CSV di direktori kerja saat ini
new_comments_df.to_csv('sentiment_analysis_results.csv', index=False)

print("Sentiment analysis results saved to 'sentiment_analysis_results.csv'")
