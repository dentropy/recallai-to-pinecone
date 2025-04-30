# recallai-to-pinecone

#### Requirements

* Domain Name
* Pinecone API Key saved to `PINECONE_API_KEY` Environment Variable
* [Caddy](https://caddyserver.com/docs/install#debian-ubuntu-raspbian)
* [Python Virtual Environment Dependencies](https://mememaps.net/f56d0381-aed6-47cf-937f-07cc97dc51ad/)

#### To Install

**Dependencies for a Debian VPS**

``` bash
sudo apt -y update
sudo apt -y install vim
sudo apt -y install tmux
sudo apt -y install git
sudo apt -y install jq
```


**Configure Caddyfile**
``` bash
# Configure Caddyfile
vim /etc/caddy/Caddyfile
```

``` Caddyfile
your.domain.name.tld {
        reverse_proxy localhost:5000
}
```

``` bash
sudo systemctl reload caddy
```

**Disable Firewall, I know you probably forgot**
``` bash
sudo ufw allow 443
sudo ufw allow 80
```

**Actually install all the things**
``` bash
# Optional, use tmux
tmux new -s recall

# Clone Github Repo
cd ~
git clone https://github.com/dentropy/recallai-to-pinecone.git
cd recallai-to-pinecone

# Install Python Dependencies
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

export PINECONE_API_KEY=pcsk_ENTROPY

python app.py

```

## Test the Endpoint

``` bash

export YOUR_TLD=your-api-endpoint.com


curl -X POST http://localhost:5001/your-path \
     -H "Content-Type: application/json" \
     -d @docs/data.json

curl -X POST https://$YOUR_TLD/your-path \
     -H "Content-Type: application/json" \
     -d @docs/data.json

```

## Joining a call with recall.ai

``` bash

export RECALLAI_API_KEY="fENTROPY"
export GOOGLE_MEET_URL="https://meet.google.com/bjk-efke-gea"
export YOUR_TLD="test.tld"
envsubst < docs/bot_create.json > docs/bot_create_substituted.json
cat docs/bot_create_substituted.json


# NOTE YOU MAY BE IN DIFFERENT AWS ZONE
curl -X POST https://us-west-2.recall.ai/api/v1/bot \
    -H "Authorization: Token $RECALLAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d @docs/bot_create_substituted.json | jq

```

#### Ollama Config

``` bash
ollama pull nomic-embed-text
export OLLAMA_HOST="http://localhost:11434"

curl $OLLAMA_HOST/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Hello World"
}'

```


``` bash

export PG_CONN_STRING="postgres://postgres:postgres@localhost:5435/postgres"
psql $PG_CONN_STRING


psql $PG_CONN_STRING -f ./schema.sql


curl -X POST http://localhost:5000/your-path \
     -H "Content-Type: application/json" \
     -d @docs/data.json
```