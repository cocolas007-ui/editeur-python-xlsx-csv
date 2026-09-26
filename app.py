import io

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Éditeur Python XLSX/CSV", layout="wide")
st.title("📊 Éditeur Python — fichiers XLSX / CSV")
st.markdown("Chargez un fichier, appliquez un traitement Python, puis téléchargez le résultat.")

# ---------- Chargement ----------
uploaded = st.file_uploader("Charger un fichier (.csv ou .xlsx)", type=["csv", "xlsx"])
if uploaded is None:
    st.info("⬆️ Commencez par charger un fichier CSV ou XLSX.")
    st.stop()

try:
    if uploaded.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded, sep=None, engine="python")
    else:
        df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"Erreur de lecture du fichier : {e}")
    st.stop()

st.success(f"Fichier **{uploaded.name}** chargé : {df.shape[0]} lignes × {df.shape[1]} colonnes.")

# ---------- Aperçu ----------
st.subheader("Aperçu des données")
st.dataframe(df.head(50), use_container_width=True)

with st.expander("Statistiques descriptives"):
    st.dataframe(df.describe(include="all"), use_container_width=True)

# ---------- Traitements prédéfinis ----------
st.subheader("Traitements")
operations = []

mode = st.radio("Mode de traitement", ["Traitements guidés", "Code Python personnalisé"], horizontal=True)
result = df.copy()

if mode == "Traitements guidés":
    if st.checkbox("Supprimer les lignes dupliquées"):
        before = len(result)
        result = result.drop_duplicates()
        operations.append(f"Suppression des doublons : {before - len(result)} lignes supprimées")

    cols_drop = st.multiselect("Supprimer des colonnes", df.columns)
    if cols_drop:
        result = result.drop(columns=cols_drop)
        operations.append(f"Colonnes supprimées : {', '.join(cols_drop)}")

    fill_col = st.selectbox("Remplir les valeurs manquantes d'une colonne (optionnel)", ["—"] + list(df.columns))
    if fill_col != "—":
        fill_value = st.text_input("Valeur de remplacement", "0")
        result[fill_col] = result[fill_col].fillna(fill_value)
        operations.append(f"Valeurs manquantes de '{fill_col}' remplacées par '{fill_value}'")

    num_cols = df.select_dtypes("number").columns.tolist()
    if num_cols:
        filter_col = st.selectbox("Filtrer sur une colonne numérique (optionnel)", ["—"] + num_cols)
        if filter_col != "—":
            op = st.selectbox("Opérateur", ["Supérieur à", "Inférieur à", "Égal à"])
            threshold = st.number_input("Seuil", value=0.0)
            if op == "Supérieur à":
                result = result[result[filter_col] > threshold]
            elif op == "Inférieur à":
                result = result[result[filter_col] < threshold]
            else:
                result = result[result[filter_col] == threshold]
            operations.append(f"Filtre : {filter_col} {op.lower()} {threshold}")
else:
    st.markdown("Écrivez votre code Python. La variable `df` contient vos données ; "
                "assignez le résultat à `result`.")
    default_code = ("# Exemple : créer une colonne et filtrer\n"
                    "# result = df[df['nom_colonne'] > 10]\n"
                    "result = df\n")
    user_code = st.text_area("Code Python (pandas disponible en tant que `pd`)", default_code, height=200)
    if st.button("▶️ Exécuter le code"):
        try:
            namespace = {"df": df.copy(), "pd": pd, "result": None}
            exec(user_code, namespace)  # noqa: S102 — environnement contrôlé de démonstration
            result = namespace["result"]
            operations.append("Code Python personnalisé exécuté")
            st.success("✅ Code exécuté avec succès.")
        except Exception as e:
            st.error(f"Erreur d'exécution : {e}")
            st.stop()

if operations:
    with st.expander("Opérations appliquées"):
        for op in operations:
            st.write(f"- {op}")

# ---------- Résultat et téléchargement ----------
st.subheader("Résultat")
st.dataframe(result, use_container_width=True)

fmt = st.radio("Format de téléchargement", ["CSV", "XLSX"], horizontal=True)
buffer = io.BytesIO()
if fmt == "CSV":
    data = result.to_csv(index=False).encode("utf-8")
    file_name = "resultat.csv"
else:
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        result.to_excel(writer, index=False, sheet_name="Résultat")
    data = buffer.getvalue()
    file_name = "resultat.xlsx"

st.download_button("⬇️ Télécharger le résultat", data=data, file_name=file_name,
                   mime="application/octet-stream")
