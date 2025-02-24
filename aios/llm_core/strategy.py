from enum import Enum
import random
from typing import List, Dict, Optional
import numpy as np
from threading import Lock
from collections import defaultdict
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, PULP_CBC_CMD, value
import json


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

class RouterStrategy(str, Enum):
    SIMPLE = "simple"
    ECCOS_R = "eccos_r"

class SimpleStrategy:
    def __init__(self, models: List):
        self.models = models
    
    def __call__(self, **kwargs):
        return random.choice(self.models)
    
class QueryStore:
    def __init__(self, 
                 model_name: str = "BAAI/bge-small-en-v1.5",
                 persist_directory: str = "db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        
        self.build_database()
            
    def download_data(self, split: str) -> List[Dict]:
        try:
            from gdown import download
            
            output = "query_data.json"
            # url = f"https://drive.google.com/uc?id={file_ids[split]}"
            download(url, output, quiet=False)
            
            with open(output, 'r') as f:
                data = json.load(f)
            return data
            
        except Exception as e:
            raise Exception(f"Failed to download data from Google Drive: {str(e)}")
    
    def build_database(self, data: List[Dict], collection: str = "query_db"):
        queries = []
        metadatas = []
        ids = []
        # Check if collection exists
        try:
            collection = self.client.get_collection(name=collection)
            print(f"Found existing collection: {collection}")
            return
        except:
            collection = self.client.create_collection(
                name=collection,
                embedding_function=self.embedding_function
            )
            print(f"Created new collection: {collection}")

        # Check if local data file exists
        local_file = "query_data.json"
        if os.path.exists(local_file):
            print(f"Found local data file: {local_file}")
            with open(local_file, 'r') as f:
                data = json.load(f)
        else:
            print(f"Downloading data file...")
            data = self.download_data("train")
        
        correct_count = 0
        total_count = 0
        
        for idx, item in enumerate(tqdm(data)):
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
        
        # print(f"Correctness: {correct_count} / {total_count}")
        
        collection.add(
            documents=queries,
            metadatas=metadatas,
            ids = ids
        )
    
    def query_similar(self, query: str | List[str], split: str = "train", n_results: int = 16):
        collection = getattr(self, f"{split}_collection")
        
        results = collection.query(
            query_texts=query if isinstance(query, List) else [query],
            n_results=n_results
        )
        
        return results
    
    def predict(self, query: str | List[str], model_configs: List[Dict], n_similar: int = 16):
        # Get similar results from training data
        similar_results = self.query_similar(query, "query_db", n_results=n_similar)
        # breakpoint()
        # Initialize stats for each model
        
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
        

    def evaluate_retrieval(self, test_data: List[Dict], n_similar: int = 5, max_output_length: int = 1024, num_buckets: int = 10):
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

class EccosRRouter:
    def load_model_configs(self):
        with open("aios/llm_core/llm_cost_map.json", "r") as f:
            model_configs = json.load(f)
            return model_configs

    def __init__(self, 
                #  model_configs: List,
                 performance_requirement: float = 0.7,
                 n_similar: int = 16):
        self.num_buckets = 10
        self.max_output_limit = 1024
        self.n_similar = n_similar
        self.bucket_size = self.max_output_limit / self.num_buckets
        self.performance_requirement = performance_requirement
        
        # print(f"Performance requirement: {self.performance_requirement}")
        self.model_configs = self.load_model_configs()
        self.store = QueryStore()
        # self.model_stats = {
        #     model["name"]: {
        #         "active_requests": 0,
        #         "avg_response_time": 0,
        #         "total_requests": 0
        #     }
        #     for model in model_configs
        # }
        # self.lock = Lock()

    def optimize_model_selection_local(self, perf_scores, cost_scores, current_loads):
        n_models = len(self.model_configs)
    
        # Get models that are available based on current load
        available_models = []
        for i in range(n_models):
            if current_loads[i] < self.max_load:
                available_models.append(i)
        
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

    def optimize_model_selection_global(self, perf_scores, cost_scores, current_loads):
        n_models = len(self.model_configs)
        n_queries = len(perf_scores)
        
        available_workloads = []
        for i in range(n_models):
            available_workloads.append(self.max_load - current_loads[i])
        
        prob = LpProblem("LLM_Scheduling", LpMinimize)
        
        # Decision variables
        x = LpVariable.dicts("assign",
                           ((i, j) for i in range(n_queries) 
                            for j in range(n_models)),
                           cat='Binary')
        
        # Objective function
        prob += lpSum(x[i,j] * cost_scores[i,j] 
                     for i in range(n_queries) 
                     for j in range(n_models))
        
        # Quality constraint
        prob += lpSum(x[i,j] * perf_scores[i,j] 
                     for i in range(n_queries) 
                     for j in range(n_models)) >= self.performance_requirement * n_queries
        
        # Assignment constraints
        for i in range(n_queries):
            prob += lpSum(x[i,j] for j in range(n_models)) == 1
            
        # Load constraints
        # for j in range(n_models):
        #     prob += lpSum(x[i,j] for i in range(n_queries)) <= available_workloads[j]
            
        # Solve
        prob.solve(PULP_CBC_CMD(msg=False))
        
        # Extract solution
        solution = np.zeros((n_queries, n_models))
        for i in range(n_queries):
            for j in range(n_models):
                solution[i,j] = value(x[i,j])
        
        solution = np.argmax(solution, axis=1)
        return solution

    def get_next_models(self, queries: List[str], input_token_lengths: List[int]) -> Dict:
        model_names = [model["name"] for model in self.model_configs]
        
        perf_scores, length_scores = self.store.predict(queries, self.model_configs)
        
        cost_scores = []
        for i in range(len(length_scores)):
            cost_score = []
            
            for j in range(len(length_scores[i])):
                # idx = np.argmax(length_scores[i])
                input_cost = input_token_lengths[i] * self.model_configs[j]["cost_per_input_token"]
                
                pred_output_length = length_scores[i][j]
                output_cost = pred_output_length * self.model_configs[j]["cost_per_output_token"]
                weighted_score = input_cost + output_cost
                cost_score.append(weighted_score)
                
            cost_scores.append(cost_score)

        cost_scores = np.array(cost_scores)
        
        current_loads = np.array([
            self.model_stats[name]["active_requests"]
            for name in model_names
        ])
        
        selected_idxs = self.optimize_model_selection_global(
            perf_scores,
            cost_scores,
            current_loads
        )
        
        selected_configs = []
        for idx in selected_idxs:
            selected_model_name = model_names[idx]
            selected_config = next(
                config for config in self.model_configs 
                if config["name"] == selected_model_name
            )
            selected_configs.append(selected_config)
            
        return selected_configs

class EccosRStrategy:
    def __init__(self, 
                 model_configs: List,
                 performance_requirement: float = 0.7,
                 n_similar: int = 16):
        self.router = EccosRRouter(
            model_configs=model_configs,
            performance_requirement=performance_requirement,
            n_similar=n_similar
        )
    
    def __call__(self, query: List[str], input_token_lengths: List[int]):
        selected_models = self.router.get_next_models(query, input_token_lengths)
        # self.router.occupy_model(selected_model)
        return selected_models
