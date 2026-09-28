import streamlit as st
import pandas as pd
import unicodedata
import io

st.set_page_config(page_title="Éditeur Python XLSX/CSV", layout="wide")
st.title("📊 Éditeur Python — fichiers XLSX / CSV")

@st.cache_data
def charger_fichier(fichier):
    if fichier.name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(fichier)
    else:
        for sep in [",", ";", "\t"]:
            try:
                return pd.read_csv(fichier, sep=sep)
            except Exception:
                continue
        raise ValueError("Impossible de lire le fichier CSV")

def enlever_espaces_df(df):
    return df.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))

def enlever_accents(x):
    if isinstance(x, str):
        return "".join(c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c))
    return x

def enlever_accents_df(df):
    return df.apply(lambda col: col.map(enlever_accents))

def remplacer_tirets_apostrophes(x):
    if isinstance(x, str):
        return x.replace("-", " ").replace("'", " ").replace("\u2019", " ")
    return x

def remplacer_tirets_apostrophes_df(df):
    return df.apply(lambda col: col.map(remplacer_tirets_apostrophes))

def majuscules_colonnes(df):
    df = df.copy()
    df.columns = [str(c).upper() for c in df.columns]
    return df

def supprimer_lignes_vides(df):
    return df.dropna(how="all").reset_index(drop=True)

# ---- Chargement du fichier principal ----
fichier = st.file_uploader("Chargez un fichier XLSX ou CSV", type=["xlsx", "xls", "csv"])

if fichier is not None:
    df = charger_fichier(fichier)
    st.subheader("Aperçu du fichier")
    st.dataframe(df.head(20))

    st.sidebar.header("Traitements")
    opts = {}
    opts["espaces"] = st.sidebar.checkbox("Enlever les espaces en début/fin")
    opts["accents"] = st.sidebar.checkbox("Enlever tous les accents (remplacer par la lettre correspondante)")
    opts["tirets"] = st.sidebar.checkbox("Enlever les tirets et apostrophes (remplacer par un espace)")
    opts["majuscules"] = st.sidebar.checkbox("Noms de colonnes en majuscules")
    opts["lignes_vides"] = st.sidebar.checkbox("Supprimer les lignes vides")

    # ---- Option ville de rattachement ----
    opts["rattachement"] = st.sidebar.checkbox("Ajouter la colonne 'Ville de rattachement' (après 'Ville de départ')")
    fichier_agences = None
    if opts["rattachement"]:
        fichier_agences = st.sidebar.file_uploader(
            "Fichier de correspondance (agences) CSV/XLSX avec colonnes 'agence de rattachement' et 'ville'",
            type=["xlsx", "xls", "csv"], key="agences")

    # ---- Éditeur de code personnalisé ----
    st.subheader("Traitement Python personnalisé (optionnel)")
    code_defaut = "# df est le DataFrame\n# Exemple :\n# df = df.drop_duplicates()\n"
    code = st.text_area("Code Python à exécuter sur le DataFrame (df)", value=code_defaut, height=200)

    if st.button("▶️ Exécuter le traitement"):
        df_final = df.copy()
        try:
            if opts["espaces"]:
                df_final = enlever_espaces_df(df_final)
            if opts["accents"]:
                df_final = enlever_accents_df(df_final)
            if opts["tirets"]:
                df_final = remplacer_tirets_apostrophes_df(df_final)
            if opts["majuscules"]:
                df_final = majuscules_colonnes(df_final)
            if opts["lignes_vides"]:
                df_final = supprimer_lignes_vides(df_final)

            # Ville de rattachement
            if opts["rattachement"]:
                if fichier_agences is None:
                    st.warning("Veuillez charger le fichier de correspondance des agences.")
                else:
                    df_ag = charger_fichier(fichier_agences)
                    df_ag.columns = [str(c).strip().lower() for c in df_ag.columns]
                    col_agence = [c for c in df_ag.columns if "agence" in c][0]
                    col_ville = [c for c in df_ag.columns if c == "ville" or "ville" in c][0]

                    def normaliser(v):
                        v = enlever_accents(str(v)).lower()
                        for ch in ["-", "'", "\u2019"]:
                            v = v.replace(ch, " ")
                        return " ".join(v.split())

                    table = {normaliser(a): str(v).strip() for a, v in zip(df_ag[col_agence], df_ag[col_ville])}

                    col_vd = None
                    for c in df_final.columns:
                        if "ville" in str(c).lower() and "départ" in str(c).lower():
                            col_vd = c
                            break
                    if col_vd is None:
                        for c in df_final.columns:
                            if "depart" in normaliser(c) or "départ" in str(c).lower():
                                col_vd = c
                                break
                    if col_vd is None:
                        st.error("Colonne 'Ville de départ' introuvable dans le fichier principal.")
                    else:
                        pos = list(df_final.columns).index(col_vd) + 1
                        valeurs = df_final[col_vd].map(lambda v: table.get(normaliser(v), "") if pd.notna(v) else "")
                        df_final.insert(pos, "Ville de rattachement", valeurs)

            # Code personnalisé
            if code.strip() and not code.startswith("# df"):
                exec(code, {"df": df_final, "pd": pd})

            st.subheader("Résultat")
            st.dataframe(df_final.head(50))
            st.session_state["df_final"] = df_final
        except Exception as e:
            st.error(f"Erreur pendant le traitement : {e}")

    # ---- Téléchargements ----
    if "df_final" in st.session_state:
        df_final = st.session_state["df_final"]
        st.subheader("Téléchargement")
        csv_buf = io.StringIO()
        df_final.to_csv(csv_buf, index=False, sep=";")
        st.download_button("⬇️ Télécharger en CSV", csv_buf.getvalue(), "resultat.csv", "text/csv")
        xlsx_buf = io.BytesIO()
        with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as w:
            df_final.to_excel(w, index=False)
        st.download_button("⬇️ Télécharger en XLSX", xlsx_buf.getvalue(), "resultat.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
