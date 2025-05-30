import pandas as pd
import numpy as np
from pathlib import Path
from moralis import evm_api
import os
from dotenv import load_dotenv

load_dotenv()

MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
if not MORALIS_API_KEY:
    raise ValueError("MORALIS_API_KEY not found in environment variables. Please create a .env file with your API key.")


def fetch_wallet_data_from_api(wallet_address):
    """Fetch wallet data from Moralis API for a single wallet."""
    try:
        api_key = MORALIS_API_KEY
        data = {}

        # Get token balances
        token_params = {
            "chain": "eth",
            "address": wallet_address
        }
        token_result = evm_api.wallets.get_wallet_token_balances_price(
            api_key=api_key,
            params=token_params,
        )
        data["tokens"] = pd.DataFrame(token_result.get("result", []))

        # Get net worth
        networth_params = {
            "exclude_spam": True,
            "exclude_unverified_contracts": True,
            "max_token_inactivity": 1,
            "min_pair_side_liquidity_usd": 1000,
            "address": wallet_address
        }
        networth_result = evm_api.wallets.get_wallet_net_worth(
            api_key=api_key,
            params=networth_params,
        )
        networth_data = []
        total_usd = networth_result.get("total_networth_usd", 0)
        for chain_data in networth_result.get("chains", []):
            networth_data.append({
                "wallet": wallet_address,
                "chain": chain_data.get("chain"),
                "native_balance": chain_data.get("native_balance_formatted"),
                "native_balance_usd": chain_data.get("native_balance_usd"),
                "token_balance_usd": chain_data.get("token_balance_usd"),
                "chain_networth_usd": chain_data.get("networth_usd"),
                "total_networth_usd": total_usd
            })
        data["networth"] = pd.DataFrame(networth_data)

        # Get wallet stats
        stats_params = {
            "chain": "eth",
            "address": wallet_address
        }
        stats_result = evm_api.wallets.get_wallet_stats(
            api_key=api_key,
            params=stats_params,
        )
        stats_data = [{
            "wallet": wallet_address,
            "nfts": stats_result.get("nfts", ""),
            "collections": stats_result.get("collections", ""),
            "transactions_total": stats_result.get("transactions", {}).get("total", ""),
            "nft_transfers_total": stats_result.get("nft_transfers", {}).get("total", ""),
            "token_transfers_total": stats_result.get("token_transfers", {}).get("total", ""),
        }]
        data["stats"] = pd.DataFrame(stats_data)

        # Get NFT collections
        nft_params = {
            "chain": "eth",
            "address": wallet_address
        }
        nft_result = evm_api.nft.get_wallet_nft_collections(
            api_key=api_key,
            params=nft_params
        )
        collections = nft_result.get("result", [])
        if isinstance(collections, dict):
            collections = [collections]
        nft_data = []
        for col in collections:
            nft_data.append({
                "wallet_address": wallet_address,
                "token_address": col.get("token_address", ""),
                "contract_type": col.get("contract_type", ""),
                "name": col.get("name", ""),
                "verified_collection": col.get("verified_collection", ""),
                "count": col.get("count", 0)
            })
        data["nfts"] = pd.DataFrame(nft_data)

        return data

    except Exception as e:
        print(f"Error fetching data from Moralis API: {e}")
        return None

def load_wallet_data(data_dir="web3_kgenX_new"):
    """Load and combine wallet data from CSV files."""
    base_path = Path(data_dir)

    def safe_load(filename):
        path = base_path / filename
        if path.exists():
            df = pd.read_csv(path)
            return df.fillna(np.nan)
        return pd.DataFrame()

    data = {
        "networth": safe_load("wallet_networth_all_chains.csv"),
        "tokens": safe_load("token_balances.csv"),
        "defi": safe_load("defi_positions.csv"),
        "nfts": safe_load("nft_collections_cleaned.csv"),
        "stats": safe_load("wallet_stats.csv")
    }
    
    return data

def extract_wallet_features(wallet_address, data_dict):
    """Extract features from wallet data, fetching from API if not found locally."""
    features = {"address": wallet_address}
    
    # Check if wallet exists in local data
    networth_df = data_dict.get("networth", pd.DataFrame())
    wallet_exists = False if networth_df.empty else wallet_address in networth_df["wallet"].values
    
    # If wallet not found in local data, try fetching from API
    if not wallet_exists:
        print(f"Wallet {wallet_address} not found in local data. Fetching from Moralis API...")
        api_data = fetch_wallet_data_from_api(wallet_address)
        if api_data:
            data_dict = api_data
            print("Successfully fetched wallet data from API")
        else:
            print("Failed to fetch data from API")
            return None

    if not networth_df.empty:
        row = networth_df[networth_df["wallet"] == wallet_address]
        if not row.empty:
            row = row.iloc[0]
            features.update({
                "total_networth": float(row.get("total_networth_usd", 0) or 0),
                "native_balance": float(row.get("native_balance", 0) or 0),
                "token_balance_usd": float(row.get("token_balance_usd", 0) or 0),
                "chain": row.get("chain", "unknown") or "unknown",
                "token_ratio": float(row.get("token_balance_usd", 0) or 0) / max(float(row.get("total_networth_usd", 1) or 1), 1)
            })
        else:
            features.update({
                "total_networth": 0,
                "native_balance": 0,
                "token_balance_usd": 0,
                "chain": "unknown",
                "token_ratio": 0
            })
    else:
        features.update({
            "total_networth": 0,
            "native_balance": 0,
            "token_balance_usd": 0,
            "chain": "unknown",
            "token_ratio": 0
        })

    # Wallet Stats
    stats_df = data_dict.get("stats", pd.DataFrame())
    if not stats_df.empty:
        row = stats_df[stats_df["wallet"] == wallet_address]
        if not row.empty:
            row = row.iloc[0]
            features.update({
                "transactions_total": int(row.get("transactions_total", 0) or 0),
                "nft_transfers_total": int(row.get("nft_transfers_total", 0) or 0),
                "token_transfers_total": int(row.get("token_transfers_total", 0) or 0),
                "nft_count": int(row.get("nfts", 0) or 0),
                "nft_collections": int(row.get("collections", 0) or 0)
            })
        else:
            features.update({
                "transactions_total": 0,
                "nft_transfers_total": 0,
                "token_transfers_total": 0,
                "nft_count": 0,
                "nft_collections": 0
            })
    else:
        features.update({
            "transactions_total": 0,
            "nft_transfers_total": 0,
            "token_transfers_total": 0,
            "nft_count": 0,
            "nft_collections": 0
        })

    # Token Balances
    token_df = data_dict.get("tokens", pd.DataFrame())
    if not token_df.empty:
        user_tokens = token_df[token_df["wallet"] == wallet_address]
        features.update({
            "token_count": user_tokens["token_symbol"].nunique(),
            "top_tokens": user_tokens.sort_values("usd_value", ascending=False)
                                        .head(3)["token_symbol"].tolist()
        })
    else:
        features.update({
            "token_count": 0,
            "top_tokens": []
        })

    # DeFi Positions
    defi_df = data_dict.get("defi", pd.DataFrame())
    if not defi_df.empty:
        user_defi = defi_df[defi_df["wallet"] == wallet_address]
        features.update({
            "defi_protocols": user_defi["protocol_name"].nunique() if not user_defi.empty else 0,
            "total_defi_usd": user_defi["usd_value"].sum() if not user_defi.empty else 0.0
        })
    else:
        features.update({
            "defi_protocols": 0,
            "total_defi_usd": 0.0
        })

    # NFT Collections
    # Note: nft_collections_cleaned.csv lacks wallet info; relying on stats data
    features["unique_nft_collections"] = features.get("nft_collections", 0)

    # Derived Scores
    features["activity_score"] = (
        features.get("transactions_total", 0) +
        features.get("nft_transfers_total", 0) +
        features.get("token_transfers_total", 0)
    )

    # Wallet Health Score (0-100)
    activity_norm = min(features["activity_score"] / 100, 1.0)
    networth_norm = min(features["total_networth"] / 10_000, 1.0)
    defi_norm = min(features["total_defi_usd"] / 5_000, 1.0)
    wallet_health = (0.4 * activity_norm + 0.4 * networth_norm + 0.2 * defi_norm) * 100
    features["wallet_health_score"] = round(wallet_health, 1)

    # Risk score example: simplified - high networth + DeFi + activity lowers risk
    risk_raw = (1 - networth_norm) * 0.5 + (1 - activity_norm) * 0.3 + (1 - defi_norm) * 0.2
    features["risk_score"] = round(risk_raw * 100, 1)  # Higher means riskier

    # Generate simple AI social handle (just a placeholder using wallet prefix + classification)
    features["social_handle"] = generate_social_handle(wallet_address)

    # Generate dApp/NFT recommendations based on wallet profile (simplified)
    # We will assign classifications later, so skip referencing them here
    

    classifications = classify_wallet(features)
    features["recommendations"] = generate_recommendations(features, classifications)
    features["persona_profile"] = generate_persona_profile(features, classifications)

    return features


def classify_wallet(features):
    """Assign persona categories based on extracted features."""
    classification = []

    networth = features.get("total_networth", 0)
    if networth > 1_000_000:
        classification.append("whale")
    elif networth > 100_000:
        classification.append("large_holder")

    if features.get("token_ratio", 0) > 0.7:
        classification.append("token_diversified")
    if features.get("token_count", 0) > 25:
        classification.append("token_explorer")

    if features.get("unique_nft_collections", 0) > 20:
        classification.append("nft_whale")
    elif features.get("nft_count", 0) > 10:
        classification.append("nft_collector")

    if features.get("nft_transfers_total", 0) > 200:
        classification.append("nft_trader")

    if features.get("defi_protocols", 0) > 5:
        classification.append("defi_power_user")
    if features.get("total_defi_usd", 0) > 100_000:
        classification.append("defi_whale")

    if features.get("transactions_total", 0) > 100_000:
        classification.append("power_user")
    if features.get("token_transfers_total", 0) > 100_000:
        classification.append("high_volume_trader")

    if not classification:
        classification.append("retail_user")

    return classification


# Helper functions for added features:

def generate_social_handle(wallet_address):
    """Generate a fun social handle based on wallet prefix and random words."""
    prefix = wallet_address[:6]
    suffix = wallet_address[-4:]
    # Example: "CryptoWolf_0x1234_ab56"
    return f"CryptoWolf_{prefix}_{suffix}"


def generate_recommendations(features, classifications):
    """Return a list of dApps/NFT or strategies to recommend based on features."""
    recs = []
    if features.get("wallet_health_score", 0) > 70:
        recs.append("Explore DeFi yield farming protocols")
    if features.get("risk_score", 100) < 50:
        recs.append("Consider long-term staking opportunities")
    if "nft_whale" in classifications:
        recs.append("Check out exclusive NFT drops on OpenSea")
    if features.get("token_count", 0) > 20:
        recs.append("Diversify portfolio with Layer 2 tokens")
    if not recs:
        recs.append("Start exploring popular dApps like Uniswap and Aave")
    return recs


def generate_persona_profile(features, classifications):
    """Generate a detailed persona profile text based on features and classifications."""

    handle = features.get("social_handle", "CryptoUser")
    networth = features.get("total_networth", 0)
    activity = features.get("activity_score", 0)
    risk = features.get("risk_score", 50)
    defi_count = features.get("defi_protocols", 0)
    nft_count = features.get("unique_nft_collections", 0)
    token_count = features.get("token_count", 0)
    chain = features.get("chain", "Ethereum")

    # Crypto Identity
    identity_parts = []
    if "whale" in classifications:
        identity_parts.append("whale")
    elif "large_holder" in classifications:
        identity_parts.append("large holder")
    else:
        identity_parts.append("retail user")

    if "token_explorer" in classifications:
        identity_parts.append("token explorer")
    if "nft_whale" in classifications:
        identity_parts.append("NFT whale")
    elif "nft_collector" in classifications:
        identity_parts.append("NFT collector")
    if "defi_power_user" in classifications:
        identity_parts.append("DeFi power user")

    crypto_identity = ", ".join(identity_parts) if identity_parts else "crypto enthusiast"

    # Trading Style
    if activity > 500:
        trading_style = "an active trader with frequent transactions and portfolio adjustments"
    elif activity > 100:
        trading_style = "a moderately active investor balancing exploration and holding"
    else:
        trading_style = "a long-term investor with a low trading frequency"

    # Risk Profile
    if risk < 30:
        risk_profile = "low risk tolerance, preferring stable and secure investments"
    elif risk < 70:
        risk_profile = "moderate risk appetite, open to some experimental opportunities"
    else:
        risk_profile = "high risk tolerance, often engaging in speculative or high-volatility assets"

    # Blockchain Preferences
    blockchain_pref = f"Primarily active on the {chain} blockchain, leveraging its ecosystem for opportunities."

    # Recommendations (build dynamically from generate_recommendations)
    recs = generate_recommendations(features, classifications)
    recs_text = "\n".join([f"- {r}" for r in recs])

    # Compose markdown persona profile
    persona_md = f"""
# Persona Profile: {handle}

## 1. Crypto Identity
This persona is identified as a **{crypto_identity}**, with a net worth of approximately **${networth:,.2f}**. They hold **{token_count}** tokens and are involved in **{nft_count}** unique NFT collections.

## 2. Trading Style
{handle} is {trading_style}, showing consistent engagement in the crypto markets.

## 3. Risk Profile
Their risk profile indicates a **{risk_profile}**, with a risk score of {risk} out of 100.

## 4. Blockchain Preferences
{blockchain_pref}

## 5. Personalized Recommendations
Based on their profile, the following recommendations may suit their interests and investment style:

{recs_text}
    """

    return persona_md.strip()

