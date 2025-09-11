# Imports après set_page_config
import streamlit as st
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Configuration de l'interface Streamlit - DOIT ÊTRE LA PREMIÈRE COMMANDE
st.set_page_config(
    page_title="Prédiction Taxi NYC", 
    page_icon="🚕",
    layout="wide"
)

# Charger les variables d'environnement
load_dotenv()

# Récupérer les variables d'environnement
google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
backend_url = os.getenv("BACKEND_URL", "http://backend:5000")

# Titre de l'application
st.title("NYC Yellow Taxi Riding Prediction")
#st.markdown("### Prédiction des trajets de taxi à New York")

# Initialisation des variables de session
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = 40.7128  # NYC par défaut
    st.session_state.clicked_lng = -74.0060

# Fonction pour afficher la carte Google Maps
# Fonction pour afficher la carte Google Maps
def show_google_maps(lat, lng, api_key):
    # Lire le fichier HTML
    html_file = Path(__file__).parent / "static" / "map.html"
    html_content = html_file.read_text()
    
    # Remplacer la clé API
    html_content = html_content.replace("YOUR_API_KEY", api_key)
    
    # Afficher la carte
    st.components.v1.html(html_content, height=520)
    
    # JavaScript pour mettre à jour les coordonnées
    js_code = f"""
    <script>
    // Mettre à jour la position initiale
    if (window.moveMarker) {{
        window.moveMarker({lat}, {lng});
    }}
    
    // Fonction pour mettre à jour les champs de formulaire
    function updateInputFields(lat, lng) {{
        const latInput = parent.document.querySelector('input[aria-label="Latitude"]');
        const lngInput = parent.document.querySelector('input[aria-label="Longitude"]');
        
        if (latInput && lngInput) {{
            // Mettre à jour les valeurs
            latInput.value = lat;
            lngInput.value = lng;
            
            // Déclencher les événements de changement
            const event = new Event('input', {{ bubbles: true }});
            latInput.dispatchEvent(event);
            lngInput.dispatchEvent(event);
            
            // Déclencher l'événement change pour Streamlit
            const changeEvent = new Event('change');
            latInput.dispatchEvent(changeEvent);
            lngInput.dispatchEvent(changeEvent);
        }}
    }}
    
    // Mettre à jour les champs au chargement initial
    updateInputFields({lat}, {lng});
    
    // Écouter les messages depuis l'iframe
    window.addEventListener('message', function(event) {{
        if (event.data.type === 'mapClick') {{
            updateInputFields(event.data.lat, event.data.lng);
        }}
    }});
    </script>
    """
    st.components.v1.html(js_code, height=0)

# Carte interactive pour sélectionner un emplacement
#st.header("Choisissez un point de départ")
col1, col2 = st.columns([2, 1])

with col1:
    # Afficher la carte Google Maps
    if not google_maps_api_key:
        st.error("""
            Clé API Google Maps manquante. 
            Veuillez configurer la variable d'environnement GOOGLE_MAPS_API_KEY dans le fichier .env
        """)
    else:
        show_google_maps(
            st.session_state.clicked_lat, 
            st.session_state.clicked_lng, 
            google_maps_api_key
        )

# Entrées utilisateur : caractéristiques
with col2:
    with st.container():
        st.subheader("Paramètres du trajet")
        
        # Callbacks pour la mise à jour de l'état
        def update_lat():
            st.session_state.clicked_lat = st.session_state.lat_input
            
        def update_lng():
            st.session_state.clicked_lng = st.session_state.lng_input
        
        # Afficher les coordonnées sélectionnées
        st.markdown("**Coordonnées sélectionnées:**")
        col_lat, col_lng = st.columns(2)
        
        with col_lat:
            lat = st.number_input(
                "Latitude", 
                min_value=-90.0, 
                max_value=90.0, 
                value=st.session_state.clicked_lat,
                step=0.000001,
                format="%.6f",
                key="lat_input",
                on_change=update_lat
            )
            
        with col_lng:
            lng = st.number_input(
                "Longitude", 
                min_value=-180.0, 
                max_value=180.0, 
                value=st.session_state.clicked_lng,
                step=0.000001,
                format="%.6f",
                key="lng_input",
                on_change=update_lng
            )
        
        # Mettre à jour le marqueur si les coordonnées changent via les champs de saisie
        if 'prev_lat' not in st.session_state:
            st.session_state.prev_lat = lat
        if 'prev_lng' not in st.session_state:
            st.session_state.prev_lng = lng

        if (lat != st.session_state.prev_lat or lng != st.session_state.prev_lng):
            st.session_state.prev_lat = lat
            st.session_state.prev_lng = lng
            
            # Mettre à jour le marqueur sur la carte via JavaScript
            js_update_marker = f"""
            <script>
            if (window.moveMarker) {{
                window.moveMarker({lat}, {lng});
            }}
            </script>
            """
            st.components.v1.html(js_update_marker, height=0)

        # Ajoutez ici le reste de vos champs de formulaire
        hour = st.slider(
            "Heure de la journée", 
            0, 23, 12, 1, 
            help="Heure de la journée (0-23)"
        )
        
        is_business_day = st.radio(
            "Type de jour",
            [1, 0],
            format_func=lambda x: "Jour ouvré" if x == 1 else "Weekend/Jour férié",
            horizontal=True,
            index=0
        )
        
        trip_distance = st.number_input(
            "Distance du trajet (miles)",
            min_value=0.1,
            max_value=100.0,
            value=2.5,
            step=0.1,
            help="Distance estimée du trajet en miles"
        )

        # Nouveaux champs ajoutés
        weather = st.radio(
            "Conditions météo",
            [0, 1],
            format_func=lambda x: "☀️ Clair" if x == 0 else "🌧️ Pluvieux",
            horizontal=True,
            index=0
        )

        temperature = st.slider(
            "Température moyenne (°C)",
            min_value=-10.0,
            max_value=40.0,
            value=22.5,
            step=0.5,
            help="Température moyenne en degrés Celsius"
        )

# Bouton de prédiction
if st.button("🚕 Obtenir les prédictions", type="primary", use_container_width=True):
    # Afficher un indicateur de chargement
    with st.spinner('Calcul des prédictions en cours...'):
        # Préparer les données d'entrée avec les coordonnées
        input_data = {
            'pickup_latitude': float(st.session_state.clicked_lat),
            'pickup_longitude': float(st.session_state.clicked_lng),
            'hour': int(hour),
            'is_business_day': int(is_business_day),
            'trip_distance': float(trip_distance),
            'weather_index': int(weather),  # 0 pour clair, 1 pour pluvieux
            'temp_avg': float(temperature),
            'distance_category_index': 1 if float(trip_distance) > 3 else 0  # 0 pour courte distance, 1 pour longue
        }
        
        # Afficher les données envoyées pour débogage
        st.json(input_data)
        
        # Afficher les informations de débogage
        st.sidebar.json(st.session_state.get('debug_info', {}))
        st.sidebar.write(f"URL du backend: {backend_url}")
        
        try:
            st.sidebar.write(f"Tentative de connexion à: {backend_url}/predict")
            st.sidebar.write("Données envoyées:", input_data)
            
            # Préparer les en-têtes
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Faire la requête sans timeout
            response = requests.post(
                f"{backend_url}/predict",
                json=input_data,
                headers=headers
            )
            
            st.sidebar.write(f"Réponse reçue: {response.status_code}")
            st.sidebar.write("En-têtes de la réponse:", dict(response.headers))
            
            if response.status_code != 200:
                st.sidebar.error(f"Erreur du serveur: {response.text}")
            else:
                result = response.json()
                
                # Formatage des résultats
                passenger_count = round(float(result.get('passenger_count', 0)))
                total_amount = result.get('total_amount', 0.0)
                
                # Affichage des résultats dans des colonnes
                st.success("Prédictions obtenues avec succès !")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        label="👥 Nombre de passagers",
                        value=f"{passenger_count}",
                        help="Nombre estimé de passagers pour ce trajet (arrondi à l'entier le plus proche)"
                    )
                
                with col2:
                    st.metric(
                        label="💵 Montant total du trajet",
                        value=f"${float(total_amount):,.2f}".replace(",", " "),
                        help="Montant estimé du trajet en dollars"
                    )
                
                # Affichage des détails de la prédiction
                with st.expander("Détails de la prédiction", expanded=False):
                    st.json(result)
            
        except Exception as e:
            st.error(f"Une erreur s'est produite : {str(e)}")

# Style CSS personnalisé
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-top: 20px;
        padding: 10px;
        font-size: 16px
    }
    .stMetric {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)