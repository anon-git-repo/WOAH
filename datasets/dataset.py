from abc import ABC, abstractmethod
from hashlib import sha256
from . import helpers
import pandas as pd
import os
import csv
import json
import ast

import logging

class Dataset(ABC):

    @staticmethod
    @property
    @abstractmethod
    def name():
        pass

    @staticmethod
    @property
    @abstractmethod
    def url():
        pass

    @staticmethod
    @property
    def license():
        return []

    @staticmethod
    @property
    def hash():
        return ""

    @staticmethod
    @property
    def files():
        return []

    @classmethod
    def download(cls, temp_folder):
        return helpers.download_from(cls.url, temp_folder)

    @classmethod
    def process(cls, tmp_file_path, dataset_folder, temp_folder):
        pass

    @classmethod
    def valid_hash(cls, file):
        hash = sha256()

        with open(file, 'rb') as file:
            while True:
                chunk = file.read(hash.block_size)
                if not chunk:
                    break
                hash.update(chunk)
        hash_value = hash.hexdigest()
        if cls.hash == hash_value:
            return True
        else:
            logging.warning(cls.name + ": Expected Dataset hash to be " + cls.hash + " but was " + hash_value)
            return False

    @classmethod
    def unify_row(cls, row):
        return row

    @classmethod
    def translate_row(cls, row, translation):
        translated_labels = []
        if type(row["labels"]) == str:
            row["labels"] = ast.literal_eval(row["labels"])
        for i in row["labels"]:
            translated_labels.extend(translation.get(i, [i]))
        row["labels"] = translated_labels
        return row

    @classmethod
    def unify(cls, dataset_folder, translate_labels):
        if (os.path.isfile("config.json")):
            with open("config.json", "r") as f:
                config = json.load(f)
        for file in cls.files:
            df = pd.read_csv(os.path.join(dataset_folder, file["name"]))
            df = cls.unify_format(df)
            if (translate_labels and config and file["name"] in config["datasets"]):
                df = cls.translate_labels(df, config["datasets"][file["name"]]["translation"])
            df.to_csv(os.path.join(dataset_folder, file["name"]), index_label="id", quoting=csv.QUOTE_NONNUMERIC, sep="\t")

    @classmethod
    def translate_labels(cls, df, translation):
        return df.apply(cls.translate_row, axis=1, args=(translation,))

    @classmethod
    def unify_format(cls, df):
        return df.apply(cls.unify_row, axis=1) 