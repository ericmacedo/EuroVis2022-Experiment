from utils import calculateSample, l2_norm, batch_processing
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from os.path import basename, splitext, isfile
from models.document import infer_doc2vec
from typing import List, Iterable, Dict
from multiprocessing import cpu_count
from sklearn.cluster import KMeans
from sklearn.utils import shuffle
from pathlib import Path
import numpy as np


name = splitext(basename(__file__))[0]


def model_path(dataset: str, id: int) -> str:
    return str(Path(
        f"./data/{dataset}/document/{name}/{id:03}.bin"
    ).resolve())


def load_model(dataset: str, id: int) -> Doc2Vec:
    path = model_path(dataset=dataset, id=id)
    if isfile(path):
        model = Doc2Vec.load(path)
        model.docvecs.init_sims()
        return model
    return None


def save_model(dataset: str, id: int, model: Doc2Vec):
    model.save(model_path(dataset=dataset, id=id))


def train_model(dataset: str, id: int, corpus: Iterable[str]):
    tagged_data = [
        TaggedDocument(
            doc.split(" "),
            tags=[i]
        ) for i, doc in enumerate(corpus)]

    corpus_size = len(corpus)

    model = Doc2Vec(
        dm=1,
        dm_mean=1,
        dbow_words=1,
        dm_concat=0,
        vector_size=100,
        window=8,
        alpha=0.025,
        min_alpha=0.0007,
        hs=0,
        sample=calculateSample(corpus_size),
        negative=15,
        ns_expoent=0.75,
        min_count=5,
        workers=cpu_count(),
        epochs=40)

    model.build_vocab(documents=tagged_data)

    model.train(
        documents=shuffle(tagged_data),
        total_examples=model.corpus_count,
        epochs=40)

    model.docvecs.init_sims()
    save_model(dataset=dataset, id=id, model=model)


def get_vectors(dataset: str, id: int, data: Iterable[str]) -> List[List[float]]:
    model = load_model(dataset=dataset, id=id)

    model.docvecs.init_sims()

    return l2_norm(batch_processing(
        fn=infer_doc2vec,
        data=data,
        model=model)
    ).tolist() if data else model.docvecs.vectors_docs_norm.tolist()


def cluster(dataset: str, id: int,
            seed_paragraphs: Iterable[Dict[str, Iterable]],
            k: int,
            embeddings: List) -> Iterable[int]:
    doc_seeds = get_vectors(
        dataset=dataset,
        id=id,
        data=[" ".join(p["paragraph"]) for p in seed_paragraphs])

    return KMeans(
        n_clusters=k,
        init=np.array(doc_seeds, dtype=np.float32),
        n_init=10,
        tol=1e-5
    ).fit_predict(embeddings)
