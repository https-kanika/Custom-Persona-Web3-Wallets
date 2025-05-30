from flask import Flask, request, jsonify, send_file
from threading import Lock
from dataLoading import (
    load_wallet_data,
    extract_wallet_features,
    classify_wallet,
    fetch_wallet_data_from_api
)
from test import WalletPersonaGenerator
from visualization import generate_html_report

app = Flask(__name__)

class ModelManager:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance.generator = None
                cls._instance.data_dict = None
            return cls._instance
    
    def load_model(self, hf_token=None):
        """Initialize the model if not already loaded"""
        with self._lock:
            if self.generator is None:
                print("Initializing WalletPersonaGenerator...")
                self.generator = WalletPersonaGenerator(hf_token=hf_token)
                print("Model initialized successfully")
    
    def load_data(self, data_dir="web3_kgenX_new"):
        """Load wallet data if not already loaded"""
        with self._lock:
            if self.data_dict is None:
                self.data_dict = load_wallet_data(data_dir)
                print(f"Data loaded from {data_dir}")

model_manager = ModelManager()

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model_manager.generator is not None,
        "data_loaded": model_manager.data_dict is not None
    })

@app.route('/api/wallet/analyze', methods=['POST'])
def analyze_wallet():
    """Analyze a wallet and generate a persona"""
    try:
        data = request.json
        if not data or 'wallet_address' not in data:
            return jsonify({"error": "Missing wallet_address parameter"}), 400
            
        wallet_address = data['wallet_address']
        detailed = data.get('detailed', True)
        
        if model_manager.generator is None:
            model_manager.load_model(hf_token=data.get('hf_token'))
        
        if model_manager.data_dict is None:
            model_manager.load_data(data.get('data_dir', 'web3_kgenX_new'))
        
        print(f"Analyzing wallet {wallet_address}...")
        features = extract_wallet_features(wallet_address, model_manager.data_dict)
        
        if not features:
            return jsonify({
                "error": "No data found for wallet",
                "wallet_address": wallet_address
            }), 404
            
        features['address'] = wallet_address
        features['classifications'] = classify_wallet(features)
        
        print("Generating persona...")
        persona = model_manager.generator.generate_persona(features, detailed=detailed)
        
        response = {
            "wallet_address": wallet_address,
            "persona": persona,
            "classifications": features['classifications'],
            "stats": {
                "total_networth": features.get('total_networth', 0),
                "native_balance": features.get('native_balance', 0),
                "token_balance_usd": features.get('token_balance_usd', 0),
                "chain": features.get('chain', 'unknown'),
                "wallet_health_score": features.get('wallet_health_score', 0),
                "risk_score": features.get('risk_score', 0),
                "activity_score": features.get('activity_score', 0)
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while processing the request"
        }), 500

@app.route('/api/wallet/stats', methods=['GET'])
def get_wallet_stats():
    """Get statistics for a wallet"""
    try:
        wallet_address = request.args.get('wallet_address')
        if not wallet_address:
            return jsonify({"error": "Missing wallet_address parameter"}), 400
        
        if model_manager.data_dict is None:
            model_manager.load_data(request.args.get('data_dir', 'web3_kgenX_new'))
        
        features = extract_wallet_features(wallet_address, model_manager.data_dict)
        
        if not features:
            return jsonify({
                "error": "No data found for wallet",
                "wallet_address": wallet_address
            }), 404
            
        features['classifications'] = classify_wallet(features)
    
        response = {
            "wallet_address": wallet_address,
            "stats": {
                "total_networth": features.get('total_networth', 0),
                "native_balance": features.get('native_balance', 0),
                "token_balance_usd": features.get('token_balance_usd', 0),
                "chain": features.get('chain', 'unknown'),
                "token_count": features.get('token_count', 0),
                "top_tokens": features.get('top_tokens', []),
                "defi_protocols": features.get('defi_protocols', 0),
                "total_defi_usd": features.get('total_defi_usd', 0),
                "nft_count": features.get('nft_count', 0),
                "nft_collections": features.get('unique_nft_collections', 0),
                "transactions_total": features.get('transactions_total', 0),
                "wallet_health_score": features.get('wallet_health_score', 0),
                "risk_score": features.get('risk_score', 0),
                "activity_score": features.get('activity_score', 0)
            },
            "classifications": features['classifications']
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while processing the request"
        }), 500

@app.route('/api/wallet/report', methods=['POST'])
def generate_report():
    """Generate an HTML report for a wallet"""
    try:
        data = request.json
        if not data or 'wallet_address' not in data:
            return jsonify({"error": "Missing wallet_address parameter"}), 400
            
        wallet_address = data['wallet_address']
        detailed = data.get('detailed', True)

        if model_manager.generator is None:
            model_manager.load_model(hf_token=data.get('hf_token'))
        
        if model_manager.data_dict is None:
            model_manager.load_data(data.get('data_dir', 'web3_kgenX_new'))
        
        features = extract_wallet_features(wallet_address, model_manager.data_dict)
        
        if not features:
            return jsonify({
                "error": "No data found for wallet",
                "wallet_address": wallet_address
            }), 404
            
        features['address'] = wallet_address
        features['classifications'] = classify_wallet(features)
        
        persona = model_manager.generator.generate_persona(features, detailed=detailed)
        
        output_file = f"persona_{wallet_address[:8]}.html"
        generate_html_report(features, persona, output_file)
        
        return send_file(output_file, mimetype='text/html')
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while processing the request"
        }), 500

@app.route('/api/wallet/fetch', methods=['POST'])
def fetch_wallet():
    """Fetch wallet data directly from API"""
    try:
        data = request.json
        if not data or 'wallet_address' not in data:
            return jsonify({"error": "Missing wallet_address parameter"}), 400
            
        wallet_address = data['wallet_address']
        
        api_data = fetch_wallet_data_from_api(wallet_address)
        
        if not api_data:
            return jsonify({
                "error": "Failed to fetch wallet data from API",
                "wallet_address": wallet_address
            }), 500
            
        features = extract_wallet_features(wallet_address, api_data)
        features['classifications'] = classify_wallet(features)
        
        response = {
            "wallet_address": wallet_address,
            "stats": {
                "total_networth": features.get('total_networth', 0),
                "native_balance": features.get('native_balance', 0),
                "token_balance_usd": features.get('token_balance_usd', 0),
                "chain": features.get('chain', 'unknown')
            },
            "tokens": api_data.get("tokens").to_dict(orient='records') if "tokens" in api_data else [],
            "classifications": features['classifications']
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while processing the request"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)