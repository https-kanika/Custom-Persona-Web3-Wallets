What if your crypto wallet could tell your story? In the pseudonymous world of Web3, understanding user behavior is a challenge. No real names. No bios. Just blockchain data.

Introducing the AI-Powered Web3 Wallet Persona Engine — a tool that transforms raw wallet activity into rich, human-like personas.

The goal of this project is to turn raw on-chain wallet activity into rich, human-like persona profiles. In the world of Web3, users are pseudonymous. That makes it hard to personalize experiences, understand user behavior, or even define a crypto identity. We solve this by building an intelligent backend that ingests wallet data, extracts key behavioral features, and uses a language model to generate detailed persona narratives.

We start by collecting data using the Moralis API. This gives us token balances, net worth, DeFi positions, NFT collections, and transaction history for any Ethereum wallet.

From this data, we extract over a dozen features — things like token diversity, NFT activity, DeFi engagement, transaction frequency, and total net worth. We also compute a wallet health score and a risk score based on normalized financial and behavioral metrics.

Next, we classify wallets using a rule-based system. For example, a wallet with high-value transactions and many tokens is tagged as an investor or large holder. A wallet with many NFTs is tagged as an NFT collector or NFT whale. We also detect DeFi power users, explorers, and airdrop hunters.

Once the wallet is classified, we generate the persona using the Mistral-7B-Instruct model. The prompt includes wallet statistics, tags, and a generated social handle. The model outputs a markdown-formatted bio with five key sections: crypto identity, trading style, risk profile, blockchain preferences, and personalized recommendations.

On the backend, we expose REST APIs to analyze wallets, get stats, and generate reports. The Flask server handles all requests, manages model loading, and streams back persona data. There’s also a frontend built using Streamlit that visualizes the persona, health score, and wallet breakdowns.

Finally, we generate a downloadable HTML report with tags, metrics, and the full persona narrative.

---
## API Endpoints

### Health Check

- **URL:** `/api/health`  
- **Method:** `GET`  
- **Description:** Returns server and model status.

---

### Analyze Wallet

- **URL:** `/api/wallet/analyze`  
- **Method:** `POST`  
- **Request Body:**
  ```json
  {
    "wallet_address": "0x742d35cc6634c0532925a3b844bc454e4438f44e",
    "detailed": true,
    "hf_token": "optional_huggingface_token"
  }
- Returns wallet persona and basic stats

---

### Get Wallet Stats

- **URL:** `/api/wallet/stats`
- **Method:** `GET`
- **Query Parameters:** `- wallet_address`
- Returns detailed wallet statistics

### Generate HTML Report

- **URL:** `/api/wallet/report`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "wallet_address": "0x742d35cc6634c0532925a3b844bc454e4438f44e",
    "detailed": true
    }
- Returns an HTML report for the wallet

---

### Fetch Wallet from API

- **URL:** `/api/wallet/fetch`
- **Method:** `POST`
- **Request Body:**
  ```json
    {
    "wallet_address": "0x742d35cc6634c0532925a3b844bc454e4438f44e"
    }
- Returns wallet data fetched directly from Moralis API
