from string import punctuation
from nltk.corpus import stopwords
import pandas as pd
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer

from unidecode import unidecode
import nltk
nltk.download('stopwords')


class Model:

    tokenizer = TfidfVectorizer().build_tokenizer()

    stop_words = [unidecode(stopW) for stopW in stopwords.words('english')]
    non_words = list(punctuation)
    non_words.extend(['¿', '¡', '...', '..'])
    stop_words = stop_words + non_words

    def __init__(self, type):
        self.type = type
        self.model = self.loadModel(type)

    def loadModel(self, type):
        if type == 'author':
            path = 'models/model-v10.0.pkl'
        elif type == 'article':
            path = 'models/model-v9.0.pkl'
        else:
            path = "models/model-v10.0.pkl"

        with open(path, "rb") as fp:
            return pickle.load(fp)

    def getModel(self):
        return self.model

    def preprocessTopic(self, topic):
        return [word.lower() for word in self.tokenizer(unidecode(topic)) if word.lower() not in self.stop_words]

    def getMostRelevantDocsByTopic(self, topic, authorSize):
        preprocessedTopic = self.preprocessTopic(topic)

        if all(token in self.model['vocabulary'] for token in preprocessedTopic):
            tokenIds = [self.model['vocabulary'][token]
                        for token in preprocessedTopic]
            data = {}
            for tokenId in tokenIds:
                data[tokenId] = [item[0] for item in self.model['matrix'].getcol(
                    tokenId).sorted_indices().toarray()]
            dfResult = pd.DataFrame(data=data, index=self.model['indexes'])

            if authorSize:
                return dfResult[(dfResult != 0).all(1)].sum(axis=1).sort_values(ascending=False).head(authorSize)
            else:
                return dfResult[(dfResult != 0).all(1)].sum(axis=1).sort_values(ascending=False)
        else:
            return pd.Series()
