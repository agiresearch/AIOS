import uuid
import logging

from typing import (
    Optional,
    List,
    Dict,
    Any, Union
)

from autogen.logger.logger_utils import get_current_ts
from autogen.oai.client import LEGACY_DEFAULT_CACHE_SEED, LEGACY_CACHE_DIR, PlaceHolderClient
from autogen.oai.openai_utils import get_key
from autogen.runtime_logging import logging_enabled, log_new_wrapper, log_chat_completion
from openai import APITimeoutError, APIError

from aios.hooks.syscall import useSysCall
from cerebrum.llm.communication import LLMQuery

try:
    from autogen import (
        ModelClient,
        Cache
    )
except ImportError:
    raise ImportError(
        "Could not import autogen python package. "
        "Please install it with `pip install pyautogen`."
    )

logger = logging.getLogger(__name__)

send_request, _ = useSysCall()


def adapter_autogen_client_init(self, *,
                                config_list: Optional[List[Dict[str, Any]]] = None,
                                agent_name: Optional[str],
                                **base_config: Any):
    if agent_name:
        self.agent_name = agent_name

    if logging_enabled():
        log_new_wrapper(self, locals())
    _, extra_kwargs = self._separate_openai_config(base_config)
    # It's OK if "model" is not provided in base_config or config_list
    # Because one can provide "model" at `create` time.

    self._clients: List[ModelClient] = []
    self._config_list: List[Dict[str, Any]] = []

    self._config_list = [extra_kwargs]
    self.wrapper_id = id(self)


def adapter_client_create(self, **config: Any) -> ModelClient.ModelClientResponseProtocol:
    # if ERROR:
    #     raise ERROR
    invocation_id = str(uuid.uuid4())
    last = len(self._clients) - 1
    # Check if all configs in config list are activated
    non_activated = [
        client.config["model_client_cls"] for client in self._clients if isinstance(client, PlaceHolderClient)
    ]
    if non_activated:
        raise RuntimeError(
            f"Model client(s) {non_activated} are not activated. Please register the custom model clients using "
            f"`register_model_client` or filter them out form the config list."
        )
    for i, client in enumerate([None]):
        # merge the input config with the i-th config in the config list
        full_config = {**config, **self._config_list[i]}
        # separate the config into create_config and extra_kwargs
        create_config, extra_kwargs = self._separate_create_config(full_config)
        api_type = extra_kwargs.get("api_type")
        if api_type and api_type.startswith("azure") and "model" in create_config:
            create_config["model"] = create_config["model"].replace(".", "")
        # construct the create params
        params = self._construct_create_params(create_config, extra_kwargs)
        # get the cache_seed, filter_func and context
        cache_seed = extra_kwargs.get("cache_seed", LEGACY_DEFAULT_CACHE_SEED)
        cache = extra_kwargs.get("cache")
        filter_func = extra_kwargs.get("filter_func")
        context = extra_kwargs.get("context")
        agent = extra_kwargs.get("agent")
        price = extra_kwargs.get("price", None)
        if isinstance(price, list):
            price = tuple(price)
        elif isinstance(price, float) or isinstance(price, int):
            logger.warning(
                "Input price is a float/int. Using the same price for prompt and completion tokens. Use a list/tuple "
                "if prompt and completion token prices are different."
            )

        cache_client = None
        if cache is not None:
            # Use the cache object if provided.
            cache_client = cache
        elif cache_seed is not None:
            # Legacy cache behavior, if cache_seed is given, use DiskCache.
            cache_client = Cache.disk(cache_seed, LEGACY_CACHE_DIR)

        if cache_client is not None:
            with cache_client as cache:
                # Try to get the response from cache
                key = get_key(params)
                request_ts = get_current_ts()

                response: ModelClient.ModelClientResponseProtocol = cache.get(key, None)

                if response is not None:
                    # response.message_retrieval_function = client.message_retrieval
                    # try:
                    #     response.cost  # type: ignore [attr-defined]
                    # except AttributeError:
                    #     # update attribute if cost is not calculated
                    #     response.cost = client.cost(response)
                    #     cache.set(key, response)
                    # total_usage = client.get_usage(response)

                    if logging_enabled():
                        # Log the cache hit
                        # TODO: log the config_id and pass_filter etc.
                        log_chat_completion(
                            invocation_id=invocation_id,
                            client_id=id(client),
                            wrapper_id=id(self),
                            agent=agent,
                            request=params,
                            response=response,
                            is_cached=1,
                            cost=response.cost,
                            start_time=request_ts,
                        )

                    # check the filter
                    pass_filter = filter_func is None or filter_func(context=context, response=response)
                    if pass_filter or i == last:
                        return response
                    continue  # filter is not passed; try the next config
        try:
            request_ts = get_current_ts()
            response = send_request(
                agent_name="AutoGen",
                query=LLMQuery(
                    messages=params['messages'],
                    tools=(params["tools"] if "tools" in params else None)
                )
            )["response"]
            response = {'content': response.response_message, 'tool_calls': response.tool_calls}
        except APITimeoutError as err:
            logger.debug(f"config {i} timed out", exc_info=True)
            if i == last:
                raise TimeoutError(
                    "OpenAI API call timed out. This could be due to congestion or too small a timeout value. The "
                    "timeout can be specified by setting the 'timeout' value (in seconds) in the llm_config (if you "
                    "are using agents) or the OpenAIWrapper constructor (if you are using the OpenAIWrapper directly)."
                ) from err
        except APIError as err:
            error_code = getattr(err, "code", None)
            if logging_enabled():
                log_chat_completion(
                    invocation_id=invocation_id,
                    client_id=id(client),
                    wrapper_id=id(self),
                    agent=agent,
                    request=params,
                    response=f"error_code:{error_code}, config {i} failed",
                    is_cached=0,
                    cost=0,
                    start_time=request_ts,
                )

            if error_code == "content_filter":
                # raise the error for content_filter
                raise
            logger.debug(f"config {i} failed", exc_info=True)
            if i == last:
                raise
        else:
            if cache_client is not None:
                # Cache the response
                with cache_client as cache:
                    cache.set(key, response)

            if logging_enabled():
                log_chat_completion(
                    invocation_id=invocation_id,
                    client_id=id(client),
                    wrapper_id=id(self),
                    agent=agent,
                    request=params,
                    response=response,
                    is_cached=0,
                    cost=response.cost,
                    start_time=request_ts,
                )

            # response.message_retrieval_function = client.message_retrieval
            # check the filter
            pass_filter = filter_func is None or filter_func(context=context, response=response)
            if pass_filter or i == last:
                return response
            continue  # filter is not passed; try the next config
    raise RuntimeError("Should not reach here.")


def adapter_client_extract_text_or_completion_object(
        cls, response: ModelClient.ModelClientResponseProtocol
) -> Union[List[str], List[ModelClient.ModelClientResponseProtocol.Choice.Message]]:
    """Extract the text or ChatCompletion objects from a completion or chat response.

    Args:
        response (ChatCompletion | Completion): The response from openai.

    Returns:
        A list of text, or a list of ChatCompletion objects if function_call/tool_calls are present.
    """
    return [response]
