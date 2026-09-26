import io
import unicodedata

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Éditeur de fichiers XLSX / CSV", page_icon="📝", layout="wide")

st.title("📝 Éditeur de fichiers XLSX / CSV")

# ---------- Confidentialité ----------
with st.expander("🔒 Confidentialité"):
    st.info(
        "Les fichiers que vous chargez sont traités **uniquement en mémoire**, pendant votre session. "
        "Ils ne sont ni stockés sur un serveur, ni visibles par les autres utilisateurs, "
        "et les fichiers téléchargés sont générés à la volée sur votre machine."
    )

# ---------- Utilitaires ----------

def normaliser(texte):
    """Minuscules, sans accents, espaces trimmés — pour les rapprochements."""
    if pd.isna(texte):
        return ""
    texte = str(texte).strip().lower()
    texte = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in texte if not unicodedata.combining(c))


def enlever_accents(texte):
    if pd.isna(texte):
        return texte
    texte = str(texte)
    decomp = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in decomp if not unicodedata.combining(c))


def enlever_tirets_apostrophes(texte):
    if pd.isna(texte):
        return texte
    texte = str(texte)
    for ch in ("-", "–", "—", "'", "’"):
        texte = texte.replace(ch, " ")
    return texte


def appliquer_traitements(df, opts):
    """Applique les traitements choisis sur les colonnes de texte."""
    df = df.copy()
    colonnes_texte = [c for c in df.columns if df[c].dtype == object]
    for col in colonnes_texte:
        if opts["accents"]:
            df[col] = df[col].map(enlever_accents)
        if opts["tirets"]:
            df[col] = df[col].map(enlever_tirets_apostrophes)
    return df


def ajouter_ville_rattachement(df, df_agences):
    """Ajoute la colonne 'Ville de rattachement' juste après 'Ville de départ'.

    Rapproche la valeur de 'Ville de départ' du champ 'agence de rattachement'
    du fichier de correspondance et y associe la 'ville' correspondante.
    """
    df = df.copy()
    agences = df_agences.copy()

    # Recherche insensible à la casse / aux accents des colonnes
    col_depart = next((c for c in df.columns if normaliser(c) == "ville de depart"), None)
    col_agence = next((c for c in agences.columns if normaliser(c) == "agence de rattachement"), None)
    col_ville = next((c for c in agences.columns if normaliser(c) == "ville"), None)

    if not col_depart:
        st.warning("Colonne 'Ville de départ' introuvable dans le fichier principal.")
        return df
    if not col_agence or not col_ville:
        st.warning("Colonnes 'agence de rattachement' et/ou 'ville' introuvables dans le fichier de correspondance.")
        return df

    # Table de correspondance : agence (normalisée) -> ville (valeur d'origine)
    mapping = (
        agences[[col_agence, col_ville]]
        .dropna(subset=[col_agence])
        .drop_duplicates(subset=[col_agence].__class__([col_agence])[0])
    )
    mapping = dict(
        zip(normaliser_series(agences[col_agence]), agences[col_ville])
    )

    # Nouvelle colonne remplie par correspondance
    valeurs = normaliser_series(df[col_depart]).map(mapping)
    df["Ville de rattachement"] = valeurs

    # Réordonner : insérer juste après 'Ville de départ'
    colonnes = list(df.columns)
    colonnes.remove("Ville de rattachement")
    idx = colonnes.index(col_depart) + 1
    colonnes.insert(idx, "Ville de rattachement")
    return df[colonnes]


def normaliser_series(serie):
    return serie.map(normaliser)

# ---------- Chargement ----------
st.header("1. Charger un fichier")
fichier = st.file_uploader("Fichier XLSX ou CSV", type=["xlsx", "xls", "csv"])

if fichier is None:
    st.stop()

if fichier.name.lower().endswith(".csv"):
    df = pd.read_csv(fichier, dtype=str, keep_default_na=False)
else:
    df = pd.read_excel(fichier, dtype=str)

st.success(f"Fichier chargé : **{fichier.name}** — {len(df)} lignes, {len(df.columns)} colonnes.")

# ---------- Traitements ----------
st.header("2. Traitements")
opts = {
    "accents": st.checkbox("Enlever tous les accents (remplacés par la lettre correspondante)"),
    "tirets": st.checkbox("Enlever les tirets et apostrophes (remplacés par un espace)"),
}

# Option Ville de rattachement
if st.checkbox("Ajouter une colonne 'Ville de rattachement' (rapprochement avec fichier agences/villes)"):
    st.markdown(
        "Chargez un CSV contenant les colonnes **agence de rattachement** et **ville**. "
        "La valeur de la colonne **Ville de départ** est rapprochée du champ *agence de rattachement* "
        "pour récupérer la ville correspondante."
    )
    fichier_agences = st.file_uploader("Fichier de correspondance (CSV)", type=["csv"], key="agences")
    if fichier_agences is not None:
        try:
            df_agences = pd.read_csv(fichier_agences, dtype=str, keep_default_na=False)
            df = ajouter_ville_rattachement(df, df_agences)
            st.success("Colonne 'Ville de rattachement' ajoutée.")
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier de correspondance : {e}")

df = appliquer_traitements(df, opts)

# ---------- Aperçu ----------
st.header("3. Aperçu")
st.dataframe(df, use_container_width=True)

# ---------- Téléchargement ----------
st.header("4. Téléchargement")

col1, col2 = st.columns(2)
with col1:
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Télécharger en CSV", csv_data, "resultat.csv", "text/csv")
with col2:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button("⬇️ Télécharger en XLSX", buffer.getvalue(), "resultat.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
