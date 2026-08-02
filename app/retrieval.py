import json
import re
from dataclasses import dataclass,asdict
from pathlib import Path
import numpy as np
from rank_bm25 import BM25Okapi
from app.config import settings

try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
except Exception:
    _SentenceTransformer=None

class _FallbackEmbeddingModel:
    def encode(self,texts,normalize_embeddings=True):
        if isinstance(texts,str): texts=[texts]
        vectors=np.zeros((len(texts),384),dtype='float32')
        for i,text in enumerate(texts):
            tokens=re.findall(r'\w+',text.lower())
            for token in tokens:
                vectors[i,hash(token)%384]+=1.0
            if normalize_embeddings and vectors[i].sum()>0:
                vectors[i]/=np.linalg.norm(vectors[i])
        return vectors

@dataclass
class Chunk:
    source_id:str; title:str; text:str; page:int|None=None; section:str|None=None
class HybridRetriever:
    def __init__(self):
        self.dir=Path('data/index'); self.dir.mkdir(parents=True,exist_ok=True)
        self.model=self._build_model()
        self.chunks=[]; self.vectors=np.empty((0,384),dtype='float32'); self.bm25=None; self.load()

    def reset(self):
        self.chunks=[]
        self.vectors=np.empty((0,384),dtype='float32')
        self.bm25=None
        for path in [self.dir/'chunks.json', self.dir/'vectors.npy']:
            if path.exists():
                path.unlink(missing_ok=True)

    def _build_model(self):
        if not _SentenceTransformer:
            return _FallbackEmbeddingModel()
        try:
            return _SentenceTransformer(settings().embedding_model)
        except Exception:
            return _FallbackEmbeddingModel()
    def load(self):
        if (self.dir/'chunks.json').exists(): self.chunks=[Chunk(**x) for x in json.loads((self.dir/'chunks.json').read_text('utf-8'))]
        if (self.dir/'vectors.npy').exists(): self.vectors=np.load(self.dir/'vectors.npy')
        if self.chunks: self.bm25=BM25Okapi([c.text.lower().split() for c in self.chunks])
    def add(self,chunks):
        if not chunks:return
        v=self.model.encode([c.text for c in chunks],normalize_embeddings=True).astype('float32')
        self.chunks+=chunks; self.vectors=np.vstack([self.vectors,v]) if len(self.vectors) else v
        self.bm25=BM25Okapi([c.text.lower().split() for c in self.chunks])
        (self.dir/'chunks.json').write_text(json.dumps([asdict(c) for c in self.chunks]),'utf-8'); np.save(self.dir/'vectors.npy',self.vectors)
    def search(self,q,k=8):
        if not self.chunks:return []
        qv=self.model.encode([q],normalize_embeddings=True).astype('float32')[0]
        dense=self.vectors@qv; sparse=np.array(self.bm25.get_scores(q.lower().split()),dtype='float32')
        if sparse.max()>0:sparse/=sparse.max()
        scores=.65*dense+.35*sparse; ids=np.argsort(scores)[::-1][:k]
        return [(self.chunks[i],float(scores[i])) for i in ids]
retriever=HybridRetriever()
