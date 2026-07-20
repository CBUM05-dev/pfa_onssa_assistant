# ONSSA Server Installation - Groq Test Phase

This guide installs the current Groq test version on the ONSSA Ubuntu server.

The goal is to reproduce the same terminal test you already do locally:

```text
question
-> BGE embedding
-> Qdrant retrieval
-> BGE reranking
-> RAG prompt
-> Groq generation
-> answer with citations
```

Do not use `deployment/compose/docker-compose.prod.yml` for this phase. It starts a local GPU `vllm` service, which is not the current test setup.

## 0. What Must Be Ready

You need:

```text
PuTTY access to the ONSSA Ubuntu server
Internet access from the server
GitHub repo URL
Groq API key
The local data artifacts from your Windows machine
```

The GitHub repository brings the code, but not all data. These folders must be copied separately:

```text
data/corpus/
data/processed/chunks/
data/processed/embeddings/
data/models/base/
```

Why:

- `data/processed/embeddings/` contains vectors to index into Qdrant.
- `data/models/base/` contains BGE model cache used in offline mode.
- `data/corpus/` and `data/processed/chunks/` preserve source traceability and citation context.

Do not copy:

```text
.venv/
.venvPFAONSSA/
__pycache__/
.env
```

## 1. Check Internet / Wi-Fi / Network

First, connect to the server with PuTTY.

Check whether the server already has Internet:

```bash
ip addr
ip route
ping -c 4 8.8.8.8
ping -c 4 google.com
curl -I https://api.groq.com
```

Interpretation:

- `ping 8.8.8.8` works but `ping google.com` fails: DNS problem.
- both fail: no Internet route.
- `curl -I https://api.groq.com` must return an HTTP response such as `404`, `401`, or similar. That is OK; it proves HTTPS access works.

Required outbound access:

```text
download.docker.com
registry-1.docker.io
pypi.org
files.pythonhosted.org
api.groq.com
```

### If The Server Uses Ethernet

Most servers use Ethernet, not Wi-Fi. Check:

```bash
ip link
nmcli device status
```

If you see an interface like `eth0`, `ens18`, `enp0s3`, or similar with status `connected`, continue.

### If The Server Really Needs Wi-Fi

Check whether Wi-Fi exists:

```bash
nmcli radio wifi
nmcli device wifi list
```

If `nmcli` is missing:

```bash
sudo apt update
sudo apt install -y network-manager
sudo systemctl enable --now NetworkManager
```

Connect to Wi-Fi:

```bash
sudo nmcli device wifi connect "WIFI_NAME" password "WIFI_PASSWORD"
```

Then re-test:

```bash
ping -c 4 8.8.8.8
ping -c 4 google.com
curl -I https://api.groq.com
```

If Wi-Fi is not available on the server hardware, use Ethernet or ask the network admin to provide outbound Internet access. For this Groq phase, without Internet the final RAG generation will not work.

## 2. Install System Prerequisites

Run:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git make rsync gnupg lsb-release
```

Why:

- `git` gets the code from GitHub.
- `curl` tests endpoints and installs Docker keys.
- `rsync` is useful for copying artifacts safely.
- `make` is useful for project scripts.
- `ca-certificates` is required for HTTPS.

## 3. Install Docker Engine

Run:

```bash
sudo install -m 0755 -d /etc/apt/keyrings

sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

Verify:

```bash
sudo systemctl status docker
sudo docker run hello-world
docker compose version
```

Allow your user to run Docker without `sudo`:

```bash
sudo usermod -aG docker "$USER"
```

Important: disconnect from PuTTY and reconnect after this command.

Then verify:

```bash
docker version
docker compose version
```

## 4. Create The Server Project Directory

Run:

```bash
sudo mkdir -p /opt/onssa-ai
sudo chown "$USER":"$USER" /opt/onssa-ai
```

Why:

- `/opt/onssa-ai` is a clean server location.
- ownership lets your PuTTY user deploy without using `sudo` for every file.

## 5. Get The Code From GitHub

Replace `<GITHUB_REPO_URL>` with the real repository URL:

```bash
cd /opt
git clone <GITHUB_REPO_URL> onssa-ai
cd /opt/onssa-ai
```

If the directory already exists:

```bash
cd /opt/onssa-ai
git pull
```

Verify required files exist:

```bash
ls
ls deployment/compose
ls configs
```

You must see:

```text
deployment/compose/docker-compose.onssa-groq.yml
.env.onssa-groq.example
pyproject.toml
src/
scripts/
configs/
```

## 6. Copy Data Artifacts From Windows

From Windows PowerShell, copy the required data folders to the server.

Replace:

```text
SERVER_USER
SERVER_IP
```

with the real SSH user and server IP.

Run from Windows PowerShell:

```powershell
scp -r "C:\Users\user\OneDrive\Desktop\india\projects\PFA_LLM__ONSSA_VF\data\corpus" SERVER_USER@SERVER_IP:/opt/onssa-ai/data/

scp -r "C:\Users\user\OneDrive\Desktop\india\projects\PFA_LLM__ONSSA_VF\data\processed\chunks" SERVER_USER@SERVER_IP:/opt/onssa-ai/data/processed/

scp -r "C:\Users\user\OneDrive\Desktop\india\projects\PFA_LLM__ONSSA_VF\data\processed\embeddings" SERVER_USER@SERVER_IP:/opt/onssa-ai/data/processed/

scp -r "C:\Users\user\OneDrive\Desktop\india\projects\PFA_LLM__ONSSA_VF\data\models\base" SERVER_USER@SERVER_IP:/opt/onssa-ai/data/models/
```

Back in PuTTY, verify:

```bash
cd /opt/onssa-ai
ls data/corpus
ls data/processed/chunks
ls data/processed/embeddings
ls data/models/base
```

Important checks:

```bash
test -f data/processed/embeddings/chunk_embeddings.jsonl && echo "embeddings OK"
test -d data/models/base/models--BAAI--bge-m3 && echo "bge-m3 OK"
test -d data/models/base/models--BAAI--bge-reranker-v2-m3 && echo "reranker OK"
```

If one of these checks does not print `OK`, stop and fix the copy before continuing.

## 7. Configure Groq

Create the real `.env`:

```bash
cd /opt/onssa-ai
cp .env.onssa-groq.example .env
nano .env
```

Set:

```bash
ONSSA_CONFIG_DIR=configs
ONSSA_APP_ENV=prod
ONSSA_LOG_LEVEL=INFO

ONSSA_QDRANT_HOST=qdrant
ONSSA_QDRANT_PORT=6333

ONSSA_INFERENCE_BACKEND=groq
ONSSA_GROQ_BASE_URL=https://api.groq.com/openai/v1
ONSSA_GROQ_MODEL=llama-3.1-8b-instant
ONSSA_GROQ_API_KEY=your_real_groq_key_here
```

Save in nano:

```text
Ctrl+O
Enter
Ctrl+X
```

Verify without showing the key:

```bash
grep -v API_KEY .env
```

## 8. Build And Start The Services

Run:

```bash
cd /opt/onssa-ai
docker compose -f deployment/compose/docker-compose.onssa-groq.yml build
docker compose -f deployment/compose/docker-compose.onssa-groq.yml up -d
```

This starts:

```text
api      FastAPI service
qdrant   vector database
nginx    HTTP reverse proxy on port 80
```

Check:

```bash
docker compose -f deployment/compose/docker-compose.onssa-groq.yml ps
docker compose -f deployment/compose/docker-compose.onssa-groq.yml logs --tail=100 api
```

All services should be running.

## 9. Index Qdrant

Run once after first deployment:

```bash
docker compose -f deployment/compose/docker-compose.onssa-groq.yml exec api \
  python scripts/index_qdrant.py \
  --embeddings-config configs/embeddings.yaml \
  --qdrant-config configs/qdrant.yaml
```

Verify report:

```bash
cat data/processed/embeddings/qdrant_index_report.json
```

Expected:

```text
indexed_count > 0
vector_size = 1024
collection_name = onssa_food_safety_regulations
```

## 10. Test The API From PuTTY

Health:

```bash
curl http://localhost/health
```

Expected:

```json
{"status":"ok","service":"onssa-ai-service"}
```

Check runtime config:

```bash
docker compose -f deployment/compose/docker-compose.onssa-groq.yml exec api \
  python -c "from onssa_ai.core.config import get_settings; s=get_settings(); print(s.models.inference_backend, s.groq.base_url, s.groq.model)"
```

Expected:

```text
groq https://api.groq.com/openai/v1 llama-3.1-8b-instant
```

Run a RAG question:

```bash
curl -X POST http://localhost/api/v1/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"Quelle est la base reglementaire de la securite sanitaire des produits alimentaires ?"}'
```

Expected behavior:

- Qdrant retrieves evidence.
- BGE reranker reranks chunks.
- Groq generates the answer.
- Response includes citations.
- If evidence is insufficient, the API refuses instead of inventing.

## 11. Useful Commands

View API logs:

```bash
docker compose -f deployment/compose/docker-compose.onssa-groq.yml logs -f api
```

Restart API:

```bash
docker compose -f deployment/compose/docker-compose.onssa-groq.yml restart api
```

Stop everything:

```bash
docker compose -f deployment/compose/docker-compose.onssa-groq.yml down
```

Rebuild after code changes:

```bash
docker compose -f deployment/compose/docker-compose.onssa-groq.yml build api
docker compose -f deployment/compose/docker-compose.onssa-groq.yml up -d
```

Check Qdrant container logs:

```bash
docker compose -f deployment/compose/docker-compose.onssa-groq.yml logs --tail=100 qdrant
```

## 12. Common Problems

### Docker build cannot download packages

The server has no Internet or outbound access to PyPI.

Test:

```bash
curl -I https://pypi.org
curl -I https://files.pythonhosted.org
```

### Qdrant indexing fails

Check that embeddings exist:

```bash
ls -lh data/processed/embeddings/chunk_embeddings.jsonl
```

### RAG request fails with Groq connection error

Check:

```bash
curl -I https://api.groq.com
grep ONSSA_GROQ_BASE_URL .env
```

Also verify the API key is set:

```bash
grep ONSSA_GROQ_API_KEY .env
```

### BGE model load fails

Check model cache:

```bash
ls data/models/base
ls data/models/base/models--BAAI--bge-m3
ls data/models/base/models--BAAI--bge-reranker-v2-m3
```

If missing, recopy `data/models/base/` from Windows.
