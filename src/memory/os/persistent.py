import chromadb
from chromadb.utils import embedding_functions
import os
from datetime import datetime
import uuid

class PersistentMemory:
    def __init__(self, path=None):
        if path is None:
            path = os.path.dirname(os.path.abspath(__file__))
            print(path)

        self.client = chromadb.PersistentClient(path=path)
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="Snowflake/snowflake-arctic-embed-s")
        
    
    def reset(self):
        try:
            self.client.reset()
        except:
            return False
        
        return True
    
    def initialize(self, name='persistent'):
        self.memory = self.client.get_or_create_collection(name=name, embedding_function=self.embedder)


    def stack(self, role, phrase):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            self.memory.add(
                documents=[phrase],
                metadatas=[{
                    'role' : role,
                    'time': current_time,
                }],
                ids=[str(uuid.uuid4())]
            )
        except Exception as e:
            print(f"Exception @ {e}")
            return False
        
        return True
        
    def recall(self, depth=5, roles=['user', 'assistant'], times: list[str] | None = None, queries: list[str] = [], format=False):
        q: dict = self.memory.query(
            query_texts=queries,
            n_results=depth,
            where={
                'role' : {
                    '$in' : roles
                },
            },
            include=['documents', 'metadatas']
        )

        if not format:
            return q
        
        docs = q.get('documents')[0]
        data = q.get('metadatas')[0]
        builder = ''

        for i, doc in enumerate(docs):
            role = data[i].get('role')

            builder += f'{role}: {doc} \n'

        return builder