from flask import Flask, request, jsonify
from flask_cors import CORS
from pyspark.sql import SparkSession
from pyspark.ml.regression import RandomForestRegressionModel
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.types import StructType, StructField, IntegerType, DoubleType
import os
import logging
from typing import Dict, Any, Tuple

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de Flask
app = Flask(__name__)
CORS(app)

# Configuration des chemins des modèles
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'Models')
PASSENGER_MODEL_PATH = os.path.join(MODELS_DIR, 'random_forest_model_passengers_count')
TOTAL_AMOUNT_MODEL_PATH = os.path.join(MODELS_DIR, 'random_forest_model_total_amount')

# Variables globales pour les modèles
passenger_model = None
total_amount_model = None
spark = None
feature_assembler = None

def load_model(model_path):
    """
    Charge un modèle RandomForestRegressionModel.
    
    Args:
        model_path: Chemin vers le modèle
        
    Returns:
        Modèle chargé
    """
    try:
        logger.info(f"Chargement du modèle depuis {model_path}...")
        return RandomForestRegressionModel.load(model_path)
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle {model_path}: {str(e)}")
        raise

def initialize_models() -> Tuple[bool, str]:
    """
    Initialise la session Spark et charge les modèles.
    
    Returns:
        Tuple[bool, str]: (succès, message)
    """
    global spark, passenger_model, total_amount_model, feature_assembler
    
    try:
        # Configuration de Spark pour utiliser moins de mémoire
        spark_config = {
            "spark.driver.memory": "1g",
            "spark.executor.memory": "1g",
            "spark.memory.fraction": "0.6",
            "spark.memory.storageFraction": "0.2",
            "spark.sql.shuffle.partitions": "1",
            "spark.default.parallelism": "1",
            "spark.driver.maxResultSize": "1g",
            "spark.memory.offHeap.enabled": "false"
        }
        
        # Création de la session Spark
        spark = SparkSession.builder \
            .appName("NYCTaxiPrediction") \
            .config("spark.driver.memory", "1g") \
            .config("spark.executor.memory", "1g") \
            .config("spark.memory.fraction", "0.6") \
            .config("spark.memory.storageFraction", "0.2") \
            .config("spark.sql.shuffle.partitions", "1") \
            .config("spark.default.parallelism", "1") \
            .config("spark.driver.maxResultSize", "1g") \
            .config("spark.memory.offHeap.enabled", "false") \
            .getOrCreate()
        
        # Vérification de l'existence des dossiers de modèles
        if not os.path.exists(PASSENGER_MODEL_PATH):
            return False, f"Dossier du modèle passager introuvable: {PASSENGER_MODEL_PATH}"
            
        if not os.path.exists(TOTAL_AMOUNT_MODEL_PATH):
            return False, f"Dossier du modèle montant total introuvable: {TOTAL_AMOUNT_MODEL_PATH}"
        
        # Chargement des modèles
        logger.info("Chargement du modèle de prédiction du nombre de passagers...")
        passenger_model = load_model(PASSENGER_MODEL_PATH)
        
        logger.info("Chargement du modèle de prédiction du montant total...")
        total_amount_model = load_model(TOTAL_AMOUNT_MODEL_PATH)
        
        # Initialisation du VectorAssembler pour préparer les features
        feature_columns = ['hour', 'is_business_day', 'weather_index', 'temp_avg', 'distance_category_index']
        feature_assembler = VectorAssembler(
            inputCols=feature_columns,
            outputCol="features"
        )
        
        logger.info("Modèles chargés avec succès!")
        return True, "Initialisation réussie"
        
    except Exception as e:
        error_msg = f"Erreur lors de l'initialisation des modèles: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

# Initialisation au démarrage
init_success, init_message = initialize_models()
if not init_success:
    logger.error(f"Échec de l'initialisation: {init_message}")

# Route de base
@app.route('/', methods=['GET'])
def home():
    return f"""
    <h1>API de prédiction des trajets de taxi NYC</h1>
    <p>Utilisez le point de terminaison /predict pour effectuer des prédictions.</p>
    <p>Format attendu (POST JSON):</p>
    <pre>
    {{
        "hour": 14,
        "is_business_day": 1,
        "weather_index": 0,
        "temp_avg": 22.5,
        "distance_category_index": 0
    }}
    </pre>
    <p>Statut: {'Prêt' if init_success else f'Erreur: {init_message}'}</p>
    """

def validate_input(data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Valide et formate les données d'entrée.
    
    Args:
        data: Données d'entrée brutes
        
    Returns:
        Tuple[bool, str, Dict]: (succès, message, données formatées)
    """
    try:
        # Vérification des champs obligatoires
        required_fields = {
            'hour': (int, lambda x: 0 <= x <= 23, "doit être entre 0 et 23"),
            'is_business_day': (int, lambda x: x in (0, 1), "doit être 0 ou 1"),
            'weather_index': (int, lambda x: x in (0, 1), "doit être 0 (clair) ou 1 (pluvieux)"),
            'temp_avg': (float, lambda x: -50 <= x <= 50, "doit être une température valide"),
            'distance_category_index': (int, lambda x: x in (0, 1), "doit être 0 (courte) ou 1 (longue)")
        }
        
        formatted_data = {}
        
        for field, (field_type, validator, error_msg) in required_fields.items():
            if field not in data:
                return False, f"Champ manquant: {field}", None
                
            try:
                value = field_type(data[field])
                if not validator(value):
                    return False, f"Valeur invalide pour {field}: {error_msg}", None
                formatted_data[field] = value
            except (ValueError, TypeError):
                return False, f"Type invalide pour {field}: doit être {field_type.__name__}", None
        
        return True, "Données valides", formatted_data
        
    except Exception as e:
        return False, f"Erreur de validation: {str(e)}", None

# Endpoint pour effectuer des prédictions
@app.route('/predict', methods=['POST'])
def predict():
    if not init_success:
        return jsonify({
            'error': 'Service non disponible',
            'details': f'Erreur d\'initialisation: {init_message}'
        }), 503
    
    try:
        # Récupération et validation des données
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Aucune donnée fournie'}), 400
            
        is_valid, message, validated_data = validate_input(data)
        if not is_valid:
            return jsonify({'error': 'Données invalides', 'details': message}), 400
        
        # Création du schéma pour le DataFrame
        schema = StructType([
            StructField("hour", IntegerType(), False),
            StructField("is_business_day", IntegerType(), False),
            StructField("weather_index", IntegerType(), False),
            StructField("temp_avg", DoubleType(), False),
            StructField("distance_category_index", IntegerType(), False)
        ])
        
        # Création du DataFrame Spark avec les données validées
        input_data = [(
            validated_data['hour'],
            validated_data['is_business_day'],
            validated_data['weather_index'],
            float(validated_data['temp_avg']),  # S'assurer que c'est un float
            validated_data['distance_category_index']
        )]
        
        df = spark.createDataFrame(input_data, schema)
        
        # Préparation des features
        df_with_features = feature_assembler.transform(df)
        
        # Effectuer les prédictions
        passenger_pred = float(passenger_model.transform(df_with_features).select("prediction").collect()[0][0])
        total_amount_pred = float(total_amount_model.transform(df_with_features).select("prediction").collect()[0][0])
        
        # Formater les résultats
        result = {
            'passenger_count': max(1, round(passenger_pred)),  # Au moins 1 passager, arrondi à l'entier
            'total_amount': max(0, round(total_amount_pred, 2))  # Pas de montant négatif, 2 décimales
        }
        
        logger.info(f"Prédiction effectuée: {result}")
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Erreur lors de la prédiction: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'error': 'Erreur lors du traitement de la requête',
            'details': str(e)
        }), 500

# Point d'entrée pour l'exécution directe
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)