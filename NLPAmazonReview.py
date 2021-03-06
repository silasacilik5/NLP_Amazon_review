

from warnings import filterwarnings
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, GridSearchCV, cross_validate
from sklearn.preprocessing import LabelEncoder
from textblob import Word, TextBlob
from wordcloud import WordCloud


filterwarnings('ignore')
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

##################################################
# 1. Text Preprocessing
##################################################

df = pd.read_csv("datasets/amazon_review.csv", sep=",")
df.head()


###############################
# Normalizing Case Folding
###############################

df['reviewText'] = df['reviewText'].str.lower()

###############################
# Punctuations
###############################

df['reviewText'] = df['reviewText'].str.replace('[^\w\s]', '')

###############################
# Numbers
###############################

df['reviewText'] = df['reviewText'].str.replace('\d', '')

###############################
# Stopwords
###############################
import nltk
nltk.download('stopwords')
sw = stopwords.words('english')
df['reviewText'] = df['reviewText'].apply(lambda x: " ".join(x for x in str(x).split() if x not in sw))
df['reviewText'] .head()
###############################
# Rarewords
###############################

temp_df = pd.Series(' '.join(df['reviewText']).split()).value_counts()

drops = temp_df[temp_df <= 1]

df['reviewText'] = df['reviewText'].apply(lambda x: " ".join(x for x in x.split() if x not in drops))


###############################
# Tokenization
###############################

nltk.download("punkt")
df["reviewText"].apply(lambda x: TextBlob(x).words).head()


###############################
# Lemmatization
###############################

# Kelimeleri k??klerine ay??rma i??lemidir.
nltk.download('wordnet')
df['reviewText'] = df['reviewText'].apply(lambda x: " ".join([Word(word).lemmatize() for word in x.split()]))


##################################################
# 3. Sentiment Analysis
##################################################


df.head()
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

df["polarity_score"] = df["reviewText"].apply(lambda x: sia.polarity_scores(x)["compound"])



##################################################
# 4. Sentiment Modeling
##################################################



df["reviewText"][0:10].apply(lambda x: "pos" if sia.polarity_scores(x)["compound"] > 0 else "neg")

df["sentiment_label"] = df["reviewText"].apply(lambda x: "pos" if sia.polarity_scores(x)["compound"] > 0 else "neg")
df.head(20)

df["sentiment_label"].value_counts()

df.groupby("sentiment_label")["overall"].mean()

df["sentiment_label"] = LabelEncoder().fit_transform(df["sentiment_label"])

X = df["reviewText"]
y = df["sentiment_label"]

###############################
# Count Vectors
###############################


from sklearn.feature_extraction.text import CountVectorizer


# Veriye uygulanmas??:
vectorizer = CountVectorizer()
X_count = vectorizer.fit_transform(X)



###############################
# TF-IDF
###############################

# word tf-idf
from sklearn.feature_extraction.text import TfidfVectorizer



# n-gram tf-idf
from sklearn.feature_extraction.text import TfidfVectorizer



tf_idf_word_vectorizer = TfidfVectorizer()
X_tf_idf_word = tf_idf_word_vectorizer.fit_transform(X)


tf_idf_ngram_vectorizer = TfidfVectorizer(ngram_range=(2, 3))
X_tf_idf_ngram = tf_idf_word_vectorizer.fit_transform(X)


###############################
# 5. Modeling
###############################

###############################
# Logistic Regression
###############################

log_model = LogisticRegression().fit(X_tf_idf_word, y)

cross_val_score(log_model,
                X_tf_idf_word,
                y, scoring="accuracy",
                cv=5).mean()


random_review = pd.Series(df["reviewText"].sample(1).values)
new_review = TfidfVectorizer().fit(X).transform(random_review)
log_model.predict(new_review)


###############################
# Random Forests
###############################

# Count Vectors
rf_model = RandomForestClassifier().fit(X_count, y)
cross_val_score(rf_model, X_count, y, cv=5, n_jobs=-1).mean()

# TF-IDF Word-Level
rf_model = RandomForestClassifier().fit(X_tf_idf_word, y)
cross_val_score(rf_model, X_tf_idf_word, y, cv=5, n_jobs=-1).mean()

# TF-IDF N-GRAM
rf_model = RandomForestClassifier().fit(X_tf_idf_ngram, y)
cross_val_score(rf_model, X_tf_idf_ngram, y, cv=5, n_jobs=-1).mean()



###############################
# Hiperparametre Optimizasyonu
###############################

rf_model = RandomForestClassifier(random_state=17)

rf_params = {"max_depth": [5, 8, None],
             "max_features": [5, 7, "auto"],
             "min_samples_split": [2, 5, 8, 20],
             "n_estimators": [100, 200, 500]}

rf_best_grid = GridSearchCV(rf_model,
                            rf_params,
                            cv=5,
                            n_jobs=-1,
                            verbose=True).fit(X_count, y)

rf_best_grid.best_params_

rf_final = rf_model.set_params(**rf_best_grid.best_params_, random_state=17).fit(X_count, y)

cv_results = cross_validate(rf_final, X_count, y, cv=3, scoring=["accuracy", "f1", "roc_auc"])

cv_results['test_accuracy'].mean()
cv_results['test_f1'].mean()
cv_results['test_roc_auc'].mean()