import pandas as pd
import json
import argparse
from pathlib import Path
from dataLoading import load_wallet_data, extract_wallet_features, classify_wallet
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login
from visualization import generate_html_report


class WalletPersonaGenerator:
    def __init__(self, hf_token=None):
        """Initialize with the Mistral-7B-Instruct-v0.2 model
        
        Args:
            hf_token: Hugging Face API token for authentication (optional for this model)
        """
        if hf_token:
            login(token=hf_token, write_permission=False)

        try:
            print("Loading Mistral model pipeline...")
            model_id = "mistralai/Mistral-7B-Instruct-v0.2"
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="auto",
                torch_dtype="auto"
            )
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def generate_persona(self, wallet_data, detailed=True):
        """Generate a persona using Mistral-7B model."""
        classifications = wallet_data.get('classifications', [])
        short_addr = f"{wallet_data['address'][:6]}...{wallet_data['address'][-4:]}"
        
        if detailed:
            content = (
                f"Generate a detailed persona profile for crypto wallet {short_addr} based on the following on-chain data:\n"
                f"- Total networth: ${wallet_data.get('total_networth', 0):,.2f}\n"
                f"- Native balance: {wallet_data.get('native_balance', 0):,.2f}\n"
                f"- Token balance: ${wallet_data.get('token_balance_usd', 0):,.2f}\n"
                f"- Chain: {wallet_data.get('chain', 'unknown')}\n"
                f"- Wallet Health Score: {wallet_data.get('wallet_health_score', 0)} / 100\n"
                f"- Risk Score: {wallet_data.get('risk_score', 0)} / 100 (higher means riskier)\n"
                f"- Activity Score: {wallet_data.get('activity_score', 0)} (aggregate transaction count)\n"
                f"- Token Count: {wallet_data.get('token_count', 0)} tokens held\n"
                f"- Top Tokens: {', '.join(wallet_data.get('top_tokens', [])) or 'None'}\n"
                f"- DeFi Protocols: {wallet_data.get('defi_protocols', 0)} engaged\n"
                f"- Total DeFi USD: ${wallet_data.get('total_defi_usd', 0):,.2f}\n"
                f"- NFT Collections: {wallet_data.get('unique_nft_collections', 0)}\n"
                f"- Classifications: {', '.join(classifications) if classifications else 'None'}\n"
                f"- Social Handle: {wallet_data.get('social_handle', 'N/A')}\n"
                f"\nFictional Persona Journey:\n{wallet_data.get('persona_journey', '')}\n\n"
                f"Based on these, create a rich, fictional persona including:\n"
                f"1. Crypto Identity: Who they are in the crypto ecosystem\n"
                f"2. Trading Style: Their approach, time horizon, transaction patterns\n"
                f"3. Risk Profile: Their comfort with different types of risk\n"
                f"4. Blockchain Preferences: Why they choose this chain\n"
                f"5. Personalized Recommendations: 3-4 specific products or strategies\n\n"
                f"Format your response as a well-structured markdown document with headers for each section."
            )
        else:
            content = (
                f"Create a brief crypto persona for wallet {short_addr} with "
                f"${wallet_data.get('total_networth', 0):,.2f} total worth on {wallet_data.get('chain', 'unknown')} chain. "
                f"Include identity type, risk profile, and 1-2 recommendations."
            )

        messages = [{"role": "user", "content": content}]
        print("Generating response with Mistral model...")

        max_new_tokens = 800 if detailed else 300

        input_ids = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt"
        ).to(self.model.device)

        generated_ids = self.model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

        generated_text = self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        user_content = messages[-1]["content"]

        if user_content in generated_text:
            response_start = generated_text.find(user_content) + len(user_content)
            response_text = generated_text[response_start:].strip()
            response_text = response_text.replace("[/INST]", "").strip()
        else:
            response_text = generated_text.strip()

        return response_text


def main():
    parser = argparse.ArgumentParser(description="Generate crypto wallet personas")
    parser.add_argument("--wallet", type=str, required=True, help="Wallet address to analyze")
    parser.add_argument("--data-dir", type=str, default="web3_kgenX_new", help="Directory with wallet data")
    parser.add_argument("--hf-token", type=str, help="Hugging Face access token (optional)")
    parser.add_argument("--simple", action="store_true", help="Generate simple persona instead of detailed")
    parser.add_argument("--json-output", action="store_true", help="Save persona data as JSON as well")
    parser.add_argument("--html-output", action="store_true", help="Generate interactive HTML report")
    args = parser.parse_args()

    print(f"Loading data from {args.data_dir}...")
    data_dict = load_wallet_data(args.data_dir)

    print(f"Analyzing wallet {args.wallet}...")
    features = extract_wallet_features(args.wallet, data_dict)

    if not features:
        print(f"No data found for wallet {args.wallet}")
        return

    features['classifications'] = classify_wallet(features)

    generator = WalletPersonaGenerator(hf_token=args.hf_token)
    print("Generating persona...")
    persona_md = generator.generate_persona(features, detailed=not args.simple)

    print("\n" + "=" * 50)
    print("WALLET PERSONA")
    print("=" * 50)
    print(persona_md)
    print("=" * 50)

    output_md_file = f"persona_{args.wallet[:8]}.md"
    with open(output_md_file, "w") as f:
        f.write(f"# Wallet Persona for {args.wallet}\n\n")
        f.write(persona_md)
    print(f"Persona saved to {output_md_file}")

    if args.json_output:
        output_json_file = f"persona_{args.wallet[:8]}.json"
        with open(output_json_file, "w") as f:
            json.dump(features, f, indent=2)
        print(f"Raw persona data saved to {output_json_file}")

    if args.html_output:
        output_html_file = f"persona_report_{args.wallet[:8]}.html"
        generate_html_report(features, persona_md, output_html_file)

if __name__ == "__main__":
    main()
