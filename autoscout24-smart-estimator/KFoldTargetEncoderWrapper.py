from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import KFold
import category_encoders as ce
import pandas as pd
import numpy as np


class KFoldTargetEncoderWrapper(BaseEstimator, TransformerMixin):
    def __init__(self, cols=None, n_splits=5, shuffle=True, random_state=42):
        self.cols = cols
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state
        self.encoders = {}

    def fit(self, X, y):
        self.kf = KFold(n_splits=self.n_splits, shuffle=self.shuffle, random_state=self.random_state)
        self.learned_means = {}
        X = X.reset_index(drop=True)
        y = y.reset_index(drop=True)
        
        self.out_of_fold = pd.DataFrame(index=X.index)
        for col in self.cols:
            self.out_of_fold[col] = np.nan
            for train_idx, val_idx in self.kf.split(X):
                encoder = ce.TargetEncoder(cols=[col])
                encoder.fit(X.loc[train_idx, col], y.loc[train_idx])
                self.out_of_fold.loc[val_idx, col] = encoder.transform(X.loc[val_idx, col])[col].values

            self.learned_means[col] = ce.TargetEncoder(cols=[col]).fit(X[col], y)

        return self

    def transform(self, X):
        X_copy = X.copy()
        for col in self.cols:
            if col in self.learned_means:
                X_copy[col] = self.learned_means[col].transform(X_copy[col])[col].values
        return X_copy
