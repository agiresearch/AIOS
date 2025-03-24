from enum import Enum
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
import json
import numpy as np
from typing import List, Dict, Any
from tqdm import tqdm
from collections import defaultdict

import json

from threading import Lock

import os

from pulp import (
    LpProblem,
    LpMinimize,
    LpVariable,
    lpSum,
    PULP_CBC_CMD,
    value
)

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

class RouterStrategy(Enum):
    Sequential = 0,

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

    def get_model_idxs(self, selected_llms: List[str], n_queries: int=1):
        """
        Selects model indices from the available LLM configurations using a round-robin strategy.

        Args:
            selected_llms (List[str]): A list of selected LLM names from which models will be chosen.
            n_queries (int): The number of queries to distribute among the selected models. Defaults to 1.

        Returns:
            List[int]: A list of indices corresponding to the selected models in `self.llm_configs`.

        """
        # current  = self.selected_llms[self.idx]
        model_idxs = []
        
        # breakpoint()
        
        for _ in range(n_queries):
            current = selected_llms[self.idx]
            for i, llm_config in enumerate(self.llm_configs):
                # breakpoint()
                if llm_config["name"] == current["name"]:
                    model_idxs.append(i)
                    break
            self.idx = (self.idx + 1) % len(selected_llms)
            
        # breakpoint()
        
        return model_idxs
        
        bucket_size = max_output_length / num_buckets
        
        total_queries = len(test_data)
        model_metrics = defaultdict(lambda: {
            "correct_predictions": 0,
            "total_predictions": 0,
            "correct_length_predictions": 0,
            "total_length_predictions": 0,
            "correct_bucket_predictions": 0,
        })
        
        # Initialize metrics for each model
        model_metrics = defaultdict(lambda: {
            "correct_predictions": 0,
            "total_predictions": 0,
            "correct_length_predictions": 0, 
            "total_length_predictions": 0,
            "correct_bucket_predictions": 0
        })
        
        for test_item in tqdm(test_data, desc="Evaluating"):
            similar_results = self.query_similar(
                test_item["query"], 
                "train", 
                n_results=n_similar
            )
            
            model_stats = defaultdict(lambda: {
                "total_length": 0,
                "count": 0,
                "correct_count": 0
            })
            
            
            for metadata in similar_results["metadatas"][0]:
                for model_info in json.loads(metadata["models"]):
                    model_name = model_info["model_name"]
                    stats = model_stats[model_name]
                    stats["total_length"] += model_info["output_token_length"]
                    stats["count"] += 1
                    stats["correct_count"] += int(model_info["correctness"])
            
            for model_output in test_item["outputs"]:
                model_name = model_output["model_name"]
                if model_name in model_stats:
                    stats = model_stats[model_name]
                    
                    if stats["count"] > 0:
                        predicted_correctness = stats["correct_count"] / stats["count"] >= 0.5
                        actual_correctness = model_output["correctness"]
                        
                        if predicted_correctness == actual_correctness:
                            model_metrics[model_name]["correct_predictions"] += 1
                        
                        predicted_length = stats["total_length"] / stats["count"]
                        
                        predicted_bucket = min(int(predicted_length / bucket_size), num_buckets - 1)
                        
                        actual_length = model_output["output_token_length"]
                        
                        # length_error = abs(predicted_length - actual_length)
                        actual_bucket = min(int(actual_length / bucket_size), num_buckets - 1)
                        
                        if predicted_bucket == actual_bucket:
                            model_metrics[model_name]["correct_length_predictions"] += 1
                            
                        if abs(predicted_bucket - actual_bucket) <= 1:
                            model_metrics[model_name]["correct_bucket_predictions"] += 1
                        
                        model_metrics[model_name]["total_predictions"] += 1
                        model_metrics[model_name]["total_length_predictions"] += 1
        
        results = {}
        
        # Calculate overall accuracy across all models
        total_correct_predictions = sum(metrics["correct_predictions"] for metrics in model_metrics.values())
        total_correct_length_predictions = sum(metrics["correct_length_predictions"] for metrics in model_metrics.values())
        total_correct_bucket_predictions = sum(metrics["correct_bucket_predictions"] for metrics in model_metrics.values())
        total_predictions = sum(metrics["total_predictions"] for metrics in model_metrics.values())
        
        if total_predictions > 0:
            results["overall"] = {
                "performance_accuracy": total_correct_predictions / total_predictions,
                "length_accuracy": total_correct_length_predictions / total_predictions,
                "bucket_accuracy": total_correct_bucket_predictions / total_predictions
            }
        for model_name, metrics in model_metrics.items():
            total = metrics["total_predictions"]
            if total > 0:
                results[model_name] = {
                    "performance_accuracy": metrics["correct_predictions"] / total,
                    "length_accuracy": metrics["correct_length_predictions"] / total,
                    "bucket_accuracy": metrics["correct_bucket_predictions"] / total
                }
        results["overall"] = {
            "performance_accuracy": total_correct_predictions / total_predictions,
            "length_accuracy": total_correct_length_predictions / total_predictions,
            "bucket_accuracy": total_correct_bucket_predictions / total_predictions
        }
        
        return results

class SmartRouting:
    """
    The SmartRouting class implements a cost-performance optimized selection strategy for LLM requests.
    It uses historical performance data to predict which models will perform best for a given query
    while minimizing cost.

    This strategy ensures that models are selected based on their predicted performance and cost,
    optimizing for both quality and efficiency.

    Args:
        llm_configs (List[Dict[str, Any]]): A list of LLM configurations, where each dictionary contains 
                                           model information such as name, backend, cost parameters, etc.
        performance_requirement (float): The minimum performance score required (default: 0.7)
        n_similar (int): Number of similar queries to retrieve for prediction (default: 16)
    """
    def __init__(self, llm_configs: List[Dict[str, Any]], performance_requirement: float=0.7, n_similar: int=16):
        self.num_buckets = 10
        self.max_output_limit = 1024
        self.n_similar = n_similar
        self.bucket_size = self.max_output_limit / self.num_buckets
        self.performance_requirement = performance_requirement
        
        print(f"Performance requirement: {self.performance_requirement}")
        
        self.llm_configs = llm_configs
        self.store = self.QueryStore()
        self.lock = Lock()
        
    class QueryStore:
        """
        Internal class for storing and retrieving query embeddings and related model performance data.
        Uses ChromaDB for vector similarity search.
        """
        def __init__(self, 
                    model_name: str = "BAAI/bge-small-en-v1.5",
                    persist_directory: str = "llm_router"):
            
            file_path = os.path.join(os.path.dirname(__file__), persist_directory)
            self.client = chromadb.PersistentClient(path=file_path)
            
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model_name
            )
            
            try:
                self.train_collection = self.client.get_collection(
                    name="train_queries",
                    embedding_function=self.embedding_function
                )
            except:
                self.train_collection = self.client.create_collection(
                    name="train_queries",
                    embedding_function=self.embedding_function
                )
            
            try:
                self.val_collection = self.client.get_collection(
                    name="val_queries",
                    embedding_function=self.embedding_function
                )
            except:
                self.val_collection = self.client.create_collection(
                    name="val_queries",
                    embedding_function=self.embedding_function
                )
            
            try:
                self.test_collection = self.client.get_collection(
                    name="test_queries",
                    embedding_function=self.embedding_function
                )
            except:
                self.test_collection = self.client.create_collection(
                    name="test_queries",
                    embedding_function=self.embedding_function
                )
        
        def add_data(self, data: List[Dict], split: str = "train"):
            """
            Add query data to the appropriate collection.
            
            Args:
                data (List[Dict]): List of query data items
                split (str): Data split ("train", "val", or "test")
            """
            collection = getattr(self, f"{split}_collection")
            queries = []
            metadatas = []
            ids = []
            
            correct_count = 0
            total_count = 0
            
            for idx, item in enumerate(tqdm(data, desc=f"Adding {split} data")):
                query = item["query"]
                
                metadata = {
                    "input_token_length": item["input_token_length"],
                    "models": []
                }
                
                for output in item["outputs"]:
                    model_info = {
                        "model_name": output["model_name"],
                        "correctness": output["correctness"],
                        "output_token_length": output["output_token_length"]
                    }
                    if output["correctness"]:
                        correct_count += 1
                    total_count += 1
                    metadata["models"].append(model_info)
                    
                metadata["models"] = json.dumps(metadata["models"])
                
                queries.append(query)
                metadatas.append(metadata)
                ids.append("id"+str(idx))
            
            print(f"Correctness: {correct_count} / {total_count}")
            
            collection.add(
                documents=queries,
                metadatas=metadatas,
                ids = ids
            )
        
        def query_similar(self, query: str | List[str], split: str = "train", n_results: int = 16):
            """
            Find similar queries in the database.
            
            Args:
                query (str|List[str]): Query or list of queries to find similar items for
                split (str): Data split to search in
                n_results (int): Number of similar results to return
                
            Returns:
                Dict: Results from ChromaDB query
            """
            collection = getattr(self, f"{split}_collection")
            
            results = collection.query(
                query_texts=query if isinstance(query, List) else [query],
                n_results=n_results
            )
            
            return results
        
        def predict(self, query: str | List[str], model_configs: List[Dict], n_similar: int = 16):
            """
            Predict performance and output length for models on the given query.
            
            Args:
                query (str|List[str]): Query or list of queries
                model_configs (List[Dict]): List of model configurations
                n_similar (int): Number of similar queries to use for prediction
                
            Returns:
                Tuple[np.array, np.array]: Performance scores and length scores
            """
            # Get similar results from training data
            similar_results = self.query_similar(query, "train", n_results=n_similar)
            
            total_performance_scores = []
            total_length_scores = []
            # Aggregate stats from similar results
            for i in range(len(similar_results["metadatas"])):
                model_stats = defaultdict(lambda: {
                    "total_length": 0,
                    "count": 0,
                    "correct_count": 0
                })
                metadatas = similar_results["metadatas"][i]
                for metadata in metadatas:
                    for model_info in json.loads(metadata["models"]):
                        model_name = model_info["model_name"]
                        stats = model_stats[model_name]
                        stats["total_length"] += model_info["output_token_length"]
                        stats["count"] += 1
                        stats["correct_count"] += int(model_info["correctness"])
            
                # Calculate performance and length scores for each model
                performance_scores = []
                length_scores = []
                
                for model in model_configs:
                    model_name = model["name"]
                    if model_name in model_stats and model_stats[model_name]["count"] > 0:
                        stats = model_stats[model_name]
                        # Calculate performance score as accuracy
                        perf_score = stats["correct_count"] / stats["count"]
                        # Calculate average length
                        avg_length = stats["total_length"] / stats["count"]
                        
                        performance_scores.append(perf_score)
                        length_scores.append(avg_length)
                    else:
                        # If no data for model, use default scores
                        performance_scores.append(0.0)
                        length_scores.append(0.0)
                
                total_performance_scores.append(performance_scores)
                total_length_scores.append(length_scores)
                    
            return np.array(total_performance_scores), np.array(total_length_scores)
    
    def optimize_model_selection_local(self, model_configs, perf_scores, cost_scores):
        """
        Optimize model selection for a single query based on performance and cost.
        
        Args:
            model_configs (List[Dict]): List of model configurations
            perf_scores (np.array): Performance scores for each model
            cost_scores (np.array): Cost scores for each model
            
        Returns:
            int: Index of the selected model
        """
        n_models = len(model_configs)
    
        # Get all available models
        available_models = list(range(n_models))
        
        if not available_models:
            return None
            
        # Find models that meet performance requirement
        qualified_models = []
        for i in available_models:
            if perf_scores[i] >= self.performance_requirement:
                qualified_models.append(i)
        
        if qualified_models:
            # If there are models meeting performance requirement,
            # select the one with lowest cost
            min_cost = float('inf')
            selected_model = None
            for i in qualified_models:
                if cost_scores[i] < min_cost:
                    min_cost = cost_scores[i]
                    selected_model = i
            return selected_model
        else:
            # If no model meets performance requirement,
            # select available model with highest performance
            max_perf = float('-inf')
            selected_model = None
            for i in available_models:
                if perf_scores[i] > max_perf:
                    max_perf = perf_scores[i]
                    selected_model = i
            return selected_model
    
    def get_model_idxs(self, selected_llms: List[Dict[str, Any]], queries: List[str]=None, input_token_lengths: List[int]=None):
        """
        Selects model indices from the available LLM configurations based on predicted performance and cost.
        
        Args:
            selected_llms (List[Dict]): A list of selected LLM configurations from which models will be chosen.
            n_queries (int): The number of queries to process. Defaults to 1.
            queries (List[str], optional): List of query strings. If provided, will be used for model selection.
            input_token_lengths (List[int], optional): List of input token lengths. Required if queries is provided.
            
        Returns:
            List[int]: A list of indices corresponding to the selected models in `self.llm_configs`.
        """
        model_idxs = []
            
        # Ensure we have matching number of queries and token lengths
        if len(queries) != len(input_token_lengths):
            raise ValueError("Number of queries must match number of input token lengths")
            
        # Process each query
        for i in range(len(queries)):
            query = queries[i]
            input_token_length = input_token_lengths[i]
            
            # Get performance and length predictions
            perf_scores, length_scores = self.store.predict(query, selected_llms, n_similar=self.n_similar)
            perf_scores = perf_scores[0]  # First query's scores
            length_scores = length_scores[0]  # First query's length predictions
            
            # Calculate cost scores
            cost_scores = []
            for j in range(len(selected_llms)):
                pred_output_length = length_scores[j]
                input_cost = input_token_length * selected_llms[j].get("cost_per_input_token", 0)
                output_cost = pred_output_length * selected_llms[j].get("cost_per_output_token", 0)
                weighted_score = input_cost + output_cost
                cost_scores.append(weighted_score)
            
            cost_scores = np.array(cost_scores)
            
            # Select optimal model
            selected_idx = self.optimize_model_selection_local(
                selected_llms,
                perf_scores,
                cost_scores
            )
            
            # Find the index in the original llm_configs
            for idx, config in enumerate(self.llm_configs):
                if config["name"] == selected_llms[selected_idx]["name"]:
                    model_idxs.append(idx)
                    break
            else:
                # If not found, use the first model as fallback
                model_idxs.append(0)
        
        return model_idxs
    
    def optimize_model_selection_global(self, perf_scores, cost_scores):
        """
        Globally optimize model selection for multiple queries using linear programming.
        
        Args:
            perf_scores (np.array): Performance scores matrix [queries × models]
            cost_scores (np.array): Cost scores matrix [queries × models]
            
        Returns:
            np.array: Array of selected model indices for each query
        """
        n_models = len(self.llm_configs)
        n_queries = len(perf_scores)
        
        prob = LpProblem("LLM_Scheduling", LpMinimize)
        
        # Decision variables
        x = LpVariable.dicts("assign",
                           ((i, j) for i in range(n_queries) 
                            for j in range(n_models)),
                           cat='Binary')
        
        # Objective function: minimize total cost
        prob += lpSum(x[i,j] * cost_scores[i,j] 
                     for i in range(n_queries) 
                     for j in range(n_models))
        
        # Quality constraint: ensure overall performance meets requirement
        prob += lpSum(x[i,j] * perf_scores[i,j] 
                     for i in range(n_queries) 
                     for j in range(n_models)) >= self.performance_requirement * n_queries
        
        # Assignment constraints: each query must be assigned to exactly one model
        for i in range(n_queries):
            prob += lpSum(x[i,j] for j in range(n_models)) == 1
            
        # Solve
        prob.solve(PULP_CBC_CMD(msg=False))
        
        # Extract solution
        solution = np.zeros((n_queries, n_models))
        for i in range(n_queries):
            for j in range(n_models):
                solution[i,j] = value(x[i,j])
        
        solution = np.argmax(solution, axis=1)
        return solution
