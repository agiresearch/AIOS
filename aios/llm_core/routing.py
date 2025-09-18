from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from qdrant_client import QdrantClient, models
from aios.config.config_manager import config as global_config
import json
import numpy as np
from tqdm import tqdm
from collections import defaultdict

import uuid

from threading import Lock

import openai

import os

from pulp import (
    LpProblem,
    LpMinimize,
    LpVariable,
    lpSum,
    PULP_CBC_CMD,
    value
)

import litellm

import tempfile
import gdown

from litellm import token_counter

"""
Load balancing strategies. Each class represents a strategy which returns the
next endpoint that the router should use.

Each strategy must implement the following:
    __init__(self, llm_name: list[str])
    __call__(self)

The llm_name list contains all the endpoints that the router was initialized
with. It is the strategy's job to then calculate which endpoint should be
used whenever the strategy is called in __call__, and then return the name of
the specific LLM endpoint.
"""

class RouterStrategy:
    Sequential = "sequential"
    Smart = "smart"

class SequentialRouting:
    """
    The SequentialRouting class implements a round-robin selection strategy for load-balancing LLM requests.
    It iterates through a list of selected language models and returns their corresponding index based on
    the request count.

    This strategy ensures that multiple models are utilized in sequence, distributing queries evenly across the available configurations.

    Args:
        llm_configs (List[Dict[str, Any]]): A list of LLM configurations, where each dictionary contains model information such as name, backend, and other optional parameters.

    Example:
        ```python
        configs = [
            {"name": "gpt-4o-mini", "backend": "openai"},
            {"name": "qwen2.5-7b", "backend": "ollama"}
        ]

        selected_llms = [
            {"name": "gpt-4o-mini"},
            {"name": "qwen2.5-7b"}
        ]

        strategy = SimpleStrategy(llm_configs=configs)
        model_idxs = strategy.get_model_idxs(selected_llms, n_queries=3)
        ```
    """
    def __init__(self, llm_configs: List[Dict[str, Any]]):
        self.llm_configs = llm_configs
        self.idx = 0 # internal index to track the current model in the round-robin selection.

    # def __call__(self):
    #     return self.get_model()

    def get_model_idxs(self, selected_llm_lists: List[List[Dict[str, Any]]], queries: List[List[Dict[str, Any]]]):
        """
        Selects model indices from the available LLM configurations using a round-robin strategy.

        Args:
            selected_llm_lists (List[List[str]]): A list of selected LLM names from which models will be chosen.
            queries (List[List[Dict[str, Any]]]): A list of queries to distribute among the selected models.

        Returns:
            List[int]: A list of indices corresponding to the selected models in `self.llm_configs`.

        """
        # current  = self.selected_llms[self.idx]
        model_idxs = []

        available_models = [llm.name for llm in self.llm_configs]

        n_queries = len(queries)

        for i in range(n_queries):
            selected_llm_list = selected_llm_lists[i]

            if not selected_llm_list or len(selected_llm_list) == 0:
                model_idxs.append(0)
                continue

            model_idx = -1
            for selected_llm in selected_llm_list:
                if selected_llm["name"] in available_models:
                    model_idx = available_models.index(selected_llm["name"])
                    break

            model_idxs.append(model_idx)

        return model_idxs

def get_cost_per_token(model_name: str) -> tuple[float, float]:
    """Fetch the latest *per‑token* input/output pricing from LiteLLM.

    This pulls the live `model_cost` map which LiteLLM refreshes from
    `api.litellm.ai`, so you always have current pricing information.
    If the model is unknown, graceful fall‑back to zero cost.
    """
    cost_map = litellm.model_cost  # Live dict {model: {input_cost_per_token, output_cost_per_token, ...}}
    info = cost_map.get(model_name, {})
    return info.get("input_cost_per_token", 0.0), info.get("output_cost_per_token", 0.0)

def get_token_lengths(queries: List[List[Dict[str, Any]]]):
    """
    Get the token lengths of a list of queries.
    """
    return [token_counter(model="gpt-4o-mini", messages=query) for query in queries]

def messages_to_query(messages: List[Dict[str, str]],
                     strategy: str = "last_user") -> str:
    """
    Convert OpenAI ChatCompletion-style messages into a single query string.
    strategy:
      - "last_user": last user message only
      - "concat_users": concat all user messages
      - "concat_all": concat role-labelled full history
      - "summarize": use GPT to summarize into a short query
    """
    if strategy == "last_user":
        for msg in reversed(messages):
            if msg["role"] == "user":
                return msg["content"].strip()
        return ""  # fallback

    if strategy == "concat_users":
        return "\n\n".join(m["content"].strip()
                           for m in messages if m["role"] == "user")

    if strategy == "concat_all":
        return "\n\n".join(f'{m["role"].upper()}: {m["content"].strip()}'
                           for m in messages)

    if strategy == "summarize":
        full_text = "\n\n".join(f'{m["role"]}: {m["content"]}'
                                for m in messages)
        rsp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": ("You are a helpful assistant that rewrites a "
                             "dialogue into a concise search query.")},
                {"role": "user", "content": full_text}
            ],
            max_tokens=32,
            temperature=0.2
        )
        return rsp.choices[0].message.content.strip()

    raise ValueError("unknown strategy")

class SmartRouting:
    """Cost‑/performance‑aware LLM router.

    Two **key upgrades** compared with the original version:
    1. **Bootstrap local ChromaDB** automatically on first run by pulling a
       prepared JSONL corpus from Google Drive (uses `gdown`).
    2. **Live pricing**: no more hard‑coded token prices – we call LiteLLM to
       fetch up‑to‑date `input_cost_per_token` / `output_cost_per_token` for
       every model the moment we need them.
    """

    # ---------------------------------------------------------------------
    # Construction helpers
    # ---------------------------------------------------------------------

    class QueryStore:
        """Simple wrapper around ChromaDB persistent collections."""

        def __init__(self,
                    model_name: str = "all-MiniLM-L6-v2",
                    persist_directory: str = "llm_router",
                    bootstrap_url: str | None = None):
            storage_cfg = global_config.get_storage_config() or {}
            backend = (os.environ.get("VECTOR_DB_BACKEND") or storage_cfg.get("vector_db_backend") or "chroma").lower()

            self._persist_root = os.path.join(os.path.dirname(__file__), persist_directory)
            os.makedirs(self._persist_root, exist_ok=True)

            self.backend = backend
            if backend == "qdrant":
                host = storage_cfg.get("qdrant_host", os.environ.get("QDRANT_HOST", "localhost"))
                port = int(storage_cfg.get("qdrant_port", os.environ.get("QDRANT_PORT", 6333)))
                api_key = storage_cfg.get("qdrant_api_key", os.environ.get("QDRANT_API_KEY"))
                self.qdrant = QdrantClient(host=host, port=port, api_key=api_key)
                self.model_name = storage_cfg.get("qdrant_model_name") or os.environ.get("QDRANT_EMBEDDING_MODEL", model_name)
                self.collection_name = "historical_queries"
                self._ensure_qdrant_collection()
                self.client = None
                self.embedding_function = None
                self.collection = None
            else:
                self.client = chromadb.PersistentClient(path=self._persist_root)
                self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
                self.collection = self._get_or_create_collection("historical_queries")
                self.qdrant = None
                self.model_name = model_name
                self.collection_name = "historical_queries"

            # If DB is empty and we have a bootstrap URL – populate it.
            if bootstrap_url:
                if backend == "qdrant":
                    count = self._qdrant_count()
                    if count == 0:
                        self._bootstrap_from_drive(bootstrap_url)
                else:
                    if self.collection and self.collection.count() == 0:
                        self._bootstrap_from_drive(bootstrap_url)

        def _get_or_create_collection(self, name: str):
            if self.backend == "qdrant":
                return None
            if self.client is None:
                return None
            try:
                return self.client.get_collection(name=name, embedding_function=self.embedding_function)
            except Exception:
                return self.client.create_collection(name=name, embedding_function=self.embedding_function)

        def _ensure_qdrant_collection(self):
            if not self.qdrant.collection_exists(self.collection_name):
                dim = self.qdrant.get_embedding_size(self.model_name)
                self.qdrant.create_collection(
                    self.collection_name,
                    vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
                )

        def _qdrant_count(self) -> int:
            try:
                count = self.qdrant.count(self.collection_name).count
                return count
            except Exception:
                return 0

        def _bootstrap_from_drive(self, url_or_id: str):
            print("\n[SmartRouting] Bootstrapping ChromaDB from Google Drive…\n")

            with tempfile.TemporaryDirectory() as tmp:
                # NB: gdown accepts both share links and raw IDs.
                local_path = os.path.join(tmp, "bootstrap.json")

                gdown.download(url_or_id, local_path, quiet=False, fuzzy=True)

                # Expect JSONL with {"query": ..., "split": "train"|"val"|"test", ...}
                # split_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
                with open(local_path, "r") as f:
                    data = json.load(f)

                self.add_data(data)

                print("[SmartRouting] Bootstrap complete – collections populated.\n")

        def add_data(self, data: List[Dict[str, Any]]):
            if self.backend == "qdrant":
                queries, metadatas, ids = [], [], []
            else:
                collection = self.collection
                queries, metadatas, ids = [], [], []

            correct_count = total_count = 0

            for idx, item in enumerate(tqdm(data, desc="Ingesting historical queries")):
                query = item["query"]
                model_metadatas = item["outputs"]
                for model_metadata in model_metadatas:
                    model_metadata.pop("prediction", None)
                meta = {
                    "input_token_length": item["input_token_length"],
                    "models": json.dumps(model_metadatas),  # store raw list
                }
                for output in item["outputs"]:
                    total_count += 1
                    if output["correctness"]:
                        correct_count += 1
                queries.append(query)
                metadatas.append(meta)
                ids.append(f"{idx}")

            if self.backend == "qdrant":
                docs = [models.Document(text=q, model=self.model_name) for q in queries]
                if docs:
                    # Deterministic UUIDv5 ids; store original in payload
                    q_ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, i)) for i in ids]
                    for i, meta in enumerate(metadatas):
                        meta["original_id"] = ids[i]
                    self.qdrant.upload_collection(
                        collection_name=self.collection_name,
                        vectors=docs,
                        ids=q_ids,
                        payload=metadatas,
                    )
            else:
                if queries and metadatas and ids:  # Only add if we have data
                    collection.add(documents=queries, metadatas=metadatas, ids=ids)
                    print(f"[SmartRouting]: {total_count} historical queries ingested.")

        def query_similar(self, query: str | List[str], n_results: int = 16):
            if self.backend == "qdrant":
                qtext = query if isinstance(query, str) else query[0]
                results = self.qdrant.query_points(
                    collection_name=self.collection_name,
                    query=models.Document(text=qtext, model=self.model_name),
                    limit=n_results,
                ).points
                return {
                    "ids": [[(r.payload or {}).get("original_id", str(r.id)) for r in results]],
                    "metadatas": [[(r.payload or {}) for r in results]],
                    "documents": [[""] * len(results)],
                }
            collection = self.collection
            return collection.query(query_texts=query if isinstance(query, list) else [query], n_results=n_results)

        def predict(self, query: str | List[str], model_configs: List[Dict[str, Any]], n_similar: int = 16):
            similar = self.query_similar(query, n_results=n_similar)
            perf_mat, len_mat = [], []
            for meta_group in similar["metadatas"]:
                model_stats: dict[str, dict[str, float]] = defaultdict(lambda: {"total_len": 0, "cnt": 0, "correct": 0})
                for meta in meta_group:
                    for m in json.loads(meta["models"]):
                        s = model_stats[m["model_name"]]
                        s["total_len"] += m["output_token_length"]
                        s["cnt"] += 1
                        s["correct"] += int(m["correctness"])
                perf_row, len_row = [], []
                for cfg in model_configs:
                    stats = model_stats.get(cfg["name"], None)
                    if stats and stats["cnt"]:
                        perf_row.append(stats["correct"] / stats["cnt"])
                        len_row.append(stats["total_len"] / stats["cnt"])
                    else:
                        perf_row.append(0.0)
                        len_row.append(0.0)
                perf_mat.append(perf_row)
                len_mat.append(len_row)
            return np.array(perf_mat), np.array(len_mat)

    # ---------------------------------------------------------------------
    # SmartRouting main methods
    # ---------------------------------------------------------------------

    def __init__(self,
                llm_configs: List[Dict[str, Any]],
                bootstrap_url: str ,
                performance_requirement: float = 0.7,
                n_similar: int = 16,
                ):
        self.llm_configs = llm_configs
        self.available_models = [llm.name for llm in llm_configs]
        self.bootstrap_url = bootstrap_url
        self.performance_requirement = performance_requirement
        self.n_similar = n_similar
        self.lock = Lock()
        self.max_output_limit = 1024
        self.num_buckets = 10
        self.bucket_size = self.max_output_limit / self.num_buckets

        # Initialise query store – will self‑populate if empty
        self.store = self.QueryStore(bootstrap_url=bootstrap_url)

        print(f"[SmartRouting] Ready – performance threshold: {self.performance_requirement}\n")

    # .....................................................................
    # Local (per‑query) optimisation helper
    # .....................................................................

    def _select_model_single(self, model_cfgs: List[Dict[str, Any]], perf: np.ndarray, cost: np.ndarray) -> int | None:
        qualified = [i for i, p in enumerate(perf) if p >= self.performance_requirement]
        if qualified:
            # Pick cheapest among qualified
            return min(qualified, key=lambda i: cost[i])
        # Else, fallback – best performance overall
        return int(np.argmax(perf)) if len(perf) else 0

    # .....................................................................
    # Public API – batch selection
    # .....................................................................

    def get_model_idxs(self, selected_llm_lists: List[List[Dict[str, Any]]], queries: List[str]):
        if len(selected_llm_lists) != len(queries):
            raise ValueError("selected_llm_lists must have same length as queries")

        input_lens = get_token_lengths(queries)
        chosen_indices: list[int] = []

        converted_queries = [messages_to_query(query) for query in queries]

        for q, q_len, candidate_cfgs in zip(converted_queries, input_lens, selected_llm_lists):
            perf, out_len = self.store.predict(q, candidate_cfgs, n_similar=self.n_similar)
            perf, out_len = perf[0], out_len[0]  # unpack single query

            # Dynamic price lookup via LiteLLM
            cost_scores = []
            for cfg, pred_len in zip(candidate_cfgs, out_len):
                in_cost_pt, out_cost_pt = get_cost_per_token(cfg["name"])
                cost_scores.append(q_len * in_cost_pt + pred_len * out_cost_pt)
            cost_scores = np.array(cost_scores)

            sel_local_idx = self._select_model_single(candidate_cfgs, perf, cost_scores)
            if sel_local_idx is None:
                chosen_indices.append(0)  # safe fallback
                continue

            # Map back to global llm_configs index
            sel_name = candidate_cfgs[sel_local_idx]["name"]

            sel_idx = self.available_models.index(sel_name)
            chosen_indices.append(sel_idx)

        return chosen_indices

    # .....................................................................
    # Global optimisation (unchanged except for cost lookup)
    # .....................................................................

    def optimize_model_selection_global(self, perf_scores: np.ndarray, cost_scores: np.ndarray):
        n_queries, n_models = perf_scores.shape
        prob = LpProblem("LLM_Scheduling", LpMinimize)
        x = LpVariable.dicts("assign", ((i, j) for i in range(n_queries) for j in range(n_models)), cat="Binary")
        prob += lpSum(x[i, j] * cost_scores[i, j] for i in range(n_queries) for j in range(n_models))
        prob += lpSum(x[i, j] * perf_scores[i, j] for i in range(n_queries) for j in range(n_models)) >= self.performance_requirement * n_queries
        for i in range(n_queries):
            prob += lpSum(x[i, j] for j in range(n_models)) == 1
        prob.solve(PULP_CBC_CMD(msg=False))
        sol = np.zeros((n_queries, n_models))
        for i in range(n_queries):
            for j in range(n_models):
                sol[i, j] = value(x[i, j])
        return np.argmax(sol, axis=1)
