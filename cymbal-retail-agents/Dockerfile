# Deploy the Retail Ops MCP server to Cloud Run (Module 6)
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "mcp>=1.9.0"
COPY mcp_server/retail_ops_server.py mcp_server/
COPY setup/seed_database.py setup/
# Seed demo data into the container image (stateless demo DB)
RUN python setup/seed_database.py
EXPOSE 8080
CMD ["python", "mcp_server/retail_ops_server.py", "--transport", "http", "--port", "8080"]
