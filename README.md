#  NYC Yellow Taxi - Prédictions des Trajets

Bienvenue dans ce projet de prédiction des trajets de taxis jaunes de New York ! Nous utilisons des modèles de Machine Learning pour prédire deux aspects clés des trajets de taxi :

1. **Prédiction du nombre de passagers** : Estimation du nombre de passagers pour un trajet donné
2. **Prédiction du montant total** : Estimation du coût total du trajet

##  Table des matières
- [Présentation des modèles](#-présentation-des-modèles)
- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [API Endpoints](#-api-endpoints)
- [Technologies utilisées](#-technologies-utilisées)
- [Auteurs](#-auteurs)

##  Présentation des modèles

### 1. Modèle de prédiction du nombre de passagers
- **Type** : Random Forest
- **Entrées** : Heure, jour ouvré, météo, température, catégorie de distance
- **Sortie** : Nombre de passagers (entier arrondi)

### 2. Modèle de prédiction du montant total
- **Type** : Random Forest Regressor
- **Entrées** : Mêmes entrées que le modèle de passagers
- **Sortie** : Montant total en dollars (avec 2 décimales)

##  Architecture

Le projet est structuré en deux composants principaux :

###  Backend (API Flask)
- Héberge les deux modèles de prédiction
- Expose des endpoints REST pour les prédictions
- Gère la validation des entrées et le formatage des sorties

###  Frontend (Streamlit)
- Interface utilisateur intuitive
- Formulaire de saisie des paramètres du trajet
- Affichage clair des prédictions
- Visualisation des résultats

##  Prérequis

-  Docker 20.10+
-  Docker Compose 2.0+
-  Git
- 8 Go de RAM minimum (recommandé pour faire tourner les modèles)

##  Installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/votre-utilisateur/nyc-taxi-prediction.git
   cd nyc-taxi-prediction
   ```

2. **Vérifier la présence des modèles**
   Assurez-vous que les dossiers suivants existent dans `backend/Models/` :
   - `random_forest_model_passengers_count/`
   - `random_forest_model_total_amount/`

3. **Construire les images Docker**
   ```bash
   docker-compose build
   ```

##  Utilisation

1. **Démarrer les services**
   ```bash
   docker-compose up
   ```

2. **Accéder aux services**
   - Frontend : http://localhost:8501
   - Backend : http://localhost:5000

3. **Utiliser l'interface**
   - Remplissez le formulaire avec les paramètres du trajet
   - Cliquez sur "Obtenir les prédictions"
   - Consultez les résultats pour les deux modèles

##  API Endpoints

### `GET /`
Page d'accueil de l'API

### `POST /predict`
Effectue les prédictions pour les deux modèles

**Requête :**
```json
{
  "hour": 14,
  "is_business_day": 1,
  "weather_index": 0,
  "temp_avg": 22.5,
}
```

**Réponse :**
```json
{
  "passenger_count": 2,
  "total_amount": 12.75
}
```

##  Technologies utilisées

### Backend
- Python 3.9
- Flask 2.3.2
- PySpark 3.5.0
- Scikit-learn 1.2.2

### Frontend
- Streamlit 1.26.0
- Folium (pour la carte interactive)

### Infrastructure
- Docker
- Docker Compose

##  Auteurs

- **Ines HAMMOUCH** - Développeuse principale
- **Ousmane BA** - Développeur principal

##  Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

##  Contribuer

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos modifications (`git commit -am 'Ajout d\'une nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créez une Pull Request
