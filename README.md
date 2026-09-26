# Éditeur Python — fichiers XLSX / CSV

Application web (Streamlit + pandas) qui permet de :

- 📤 **Charger** un fichier **CSV** ou **XLSX**
- 🔎 Aperçu des données et statistiques descriptives
- ⚙️ **Traiter** les données soit via des traitements guidés (doublons, colonnes, valeurs manquantes, filtres numériques), soit via du **code Python personnalisé** exécuté à la volée
- ⬇️ **Télécharger** le résultat au format **CSV** ou **XLSX**

## Installation

```bash
git clone https://github.com/cocolas007-ui/editeur-python-xlsx-csv.git
cd editeur-python-xlsx-csv
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501.

## Déploiement

L'application peut être déployée gratuitement sur [Streamlit Community Cloud](https://streamlit.io/cloud) ou Hugging Face Spaces : il suffit de pointer vers `app.py`.
