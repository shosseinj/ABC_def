import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

def load_iris_splits(seed=42, test_size=0.2, val_size=0.2):
    data = load_iris()
    X, y = data.data, data.target
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )
    rel_val = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval, test_size=rel_val,
        random_state=seed, stratify=y_trainval
    )
    scaler = MinMaxScaler(clip=True)
    X_train = np.clip(scaler.fit_transform(X_train), 0.0, 1.0)
    X_val = np.clip(scaler.transform(X_val), 0.0, 1.0)
    X_test = np.clip(scaler.transform(X_test), 0.0, 1.0)
    return X_train, X_val, X_test, y_train, y_val, y_test, scaler


def load_iris_split_indices(seed=42, test_size=0.2, val_size=0.2):
    data = load_iris()
    indices = np.arange(len(data.target))
    trainval_indices, test_indices, y_trainval, _ = train_test_split(
        indices, data.target, test_size=test_size, random_state=seed,
        stratify=data.target,
    )
    rel_val = val_size / (1.0 - test_size)
    train_indices, val_indices = train_test_split(
        trainval_indices, test_size=rel_val, random_state=seed,
        stratify=y_trainval,
    )
    return train_indices, val_indices, test_indices


def load_iris_train_validation(seed=42, test_size=0.2, val_size=0.2):
    """Return train/validation data without transforming or returning held-out data."""
    data = load_iris()
    indices = np.arange(len(data.target))
    trainval_indices, _, y_trainval, _ = train_test_split(
        indices, data.target, test_size=test_size, random_state=seed,
        stratify=data.target,
    )
    rel_val = val_size / (1.0 - test_size)
    train_indices, val_indices, y_train, y_val = train_test_split(
        trainval_indices, y_trainval, test_size=rel_val, random_state=seed,
        stratify=y_trainval,
    )
    scaler = MinMaxScaler(clip=True)
    X_train = np.clip(scaler.fit_transform(data.data[train_indices]), 0.0, 1.0)
    X_val = np.clip(scaler.transform(data.data[val_indices]), 0.0, 1.0)
    return X_train, X_val, y_train, y_val, scaler, train_indices, val_indices
