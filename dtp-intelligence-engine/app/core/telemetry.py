from prometheus_client import Summary, Counter

# Track how long tools take (important for voice latency)
TOOL_EXECUTION_TIME = Summary('tool_execution_seconds', 'Time spent executing external tools', ['tool'])

# Track failures
TOOL_ERRORS = Counter('tool_errors_total', 'Total failures in tool execution', ['tool', 'type'])

# Track RAG usage
RAG_REQUESTS = Counter('rag_requests_total', 'Total RAG retrievals', ['status']) # status=hit/miss