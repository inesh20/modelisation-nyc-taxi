# Utiliser une image de base avec Python et OpenJDK
FROM openjdk:8-jdk-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier Spark dans le conteneur
#COPY spark-3.5.3-bin-hadoop3.tgz /opt/spark-3.5.3-bin-hadoop3.tgz

# Copiez d'abord le fichier Spark
#COPY spark-3.5.3-bin-hadoop3.tgz /opt/

# Extraire Spark et le déplacer dans /opt/spark
#RUN tar -xvzf /opt/spark-3.5.3-bin-hadoop3.tgz -C /opt \
 #   && mv /opt/spark-3.5.3-bin-hadoop3 /opt/spark \
 #  && rm /opt/spark-3.5.3-bin-hadoop3.tgz

# Télécharger et extraire Spark
RUN wget https://archive.apache.org/dist/spark/spark-3.5.3/spark-3.5.3-bin-hadoop3.tgz -P /opt/ \
    && tar -xvzf /opt/spark-3.5.3-bin-hadoop3.tgz -C /opt \
    && mv /opt/spark-3.5.3-bin-hadoop3 /opt/spark \
    && rm /opt/spark-3.5.3-bin-hadoop3.tgz

# Configurer les variables d'environnement pour Spark
ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV PYTHONPATH=$SPARK_HOME/python:$PYTHONPATH
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Créer le répertoire de l'application
WORKDIR /app

# Copier d'abord requirements.txt pour tirer parti du cache Docker
COPY requirements.txt .

# Installer les dépendances Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer les dossiers pour les modèles
RUN mkdir -p /app/Models/random_forest_model_passengers_count \
    && mkdir -p /app/Models/random_forest_model_total_amount

# Exposer le port 5000 pour l'API Flask
EXPOSE 5000

# Commande pour démarrer l'API Flask
CMD ["python3", "backend_api.py"]