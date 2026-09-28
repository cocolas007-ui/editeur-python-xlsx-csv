import streamlit as st
import pandas as pd
import io
import unicodedata

st.set_page_config(page_title="Éditeur Python XLSX/CSV", layout="wide")
st.title("📊 Éditeur de fichiers XLSX / CSV avec traitements Python")

DEFAULT_CODE = '''import pandas as pd

def traiter(df):
    # Exemple de traitement : votre code ici
    # df = df.dropna(how="all")
    return df
'''

# ---------------- Fonctions de nettoyage ----------------

def enlever_accents(texte):
    if not isinstance(texte, str):
        return texte
    nfkd = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def remplacer_tirets_apostrophes(texte):
    if not isinstance(texte, str):
        return texte
    return texte.replace("-", " ").replace("'", " ").replace("’", " ")

# ---------------- Upload du fichier principal ----------------
st.header("1️⃣ Charger le fichier principal")
fichier = st.file_uploader("Fichier XLSX ou CSV", type=["xlsx", "xls", "csv"], key="principal")

df = None
if fichier is not None:
    try:
        if fichier.name.lower().endswith(".csv"):
            df = pd.read_csv(fichier, sep=None, engine="python")
        else:
            df = pd.read_excel(fichier)
        st.success(f"Fichier chargé : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")

if df is not None:
    st.subheader("Aperçu du fichier")
    st.dataframe(df.head(20))

    # ---------------- Traitements automatiques ----------------
    st.header("2️⃣ Traitements")
    opt_maj = st.checkbox("Mettre les noms de colonnes en majuscules")
    opt_vides = st.checkbox("Supprimer les lignes entièrement vides")
    opt_accents = st.checkbox("Enlever tous les accents (remplacés par la lettre correspondante)")
    opt_tirets = st.checkbox("Enlever les tirets et apostrophes (remplacés par un espace)")

    # ---------------- Ville de rattachement ----------------
    st.header("3️⃣ Colonne 'Ville de rattachement'")
    opt_rattach = st.checkbox("Ajouter une colonne 'Ville de rattachement' après 'Ville de départ'")

    df_agences = None
    if opt_rattach:
        fichier_ag = st.file_uploader("Fichier CSV des agences (colonnes : 'agence de rattachement' et 'ville')", type=["csv"], key="agences")
        if fichier_ag is not None:
            try:
                df_agences = pd.read_csv(fichier_ag, sep=None, engine="python")
                colonnes_basse = [c.strip().lower() for c in df_agences.columns]
                col_agence = df_agences.columns[colonnes_basse.index("agence de rattachement")]
                col_ville = df_agences.columns[colonnes_basse.index("ville")]
                df_agences = df_agences[[col_agence, col_ville]].copy()
                df_agences.columns = ["agence", "ville"]
                # Clé de rapprochement normalisée
                def cle(v):
                    v = enlever_accents(str(v)).lower().strip()
                    v = remplacer_tirets_apostrophes(v)
                    return " ".join(v.split())
                df_agences["_cle"] = df_agences["agence"].apply(cle)
                mapping = dict(zip(df_agences["_cle"], df_agences["ville"]))

                # Trouver la colonne 'Ville de départ'
                col_depart = None
                for c in df.columns:
                    if cle(c) == "ville de depart":
                        col_depart = c
                        break
                if col_depart is None:
                    st.error("Colonne 'Ville de départ' introuvable dans le fichier principal.")
                else:
                    pos = df.columns.get_loc(col_depart) + 1
                    valeurs = df[col_depart].apply(cle).map(mapping).fillna("")
                    df.insert(pos, "Ville de rattachement", valeurs)
                    st.success("Colonne 'Ville de rattachement' ajoutée.")
            except Exception as e:
                st.error(f"Erreur lors du rapprochement : {e}")

    # ---------------- Éditeur de code Python ----------------
    st.header("4️⃣ Traitement Python personnalisé")
    code = st.text_area("Votre code Python (fonction traiter(df) -> df)", DEFAULT_CODE, height=250)

    df_final = df.copy()
    if opt_maj:
        df_final.columns = [str(c).upper() for c in df_final.columns]
    if opt_vides:
        df_final = df_final.dropna(how="all")
    if opt_accents:
        df_final = df_final.applymap(enlever_accents)
        df_final.columns = [enlever_accents(str(c)) for c in df_final.columns]
    if opt_tirets:
        df_final = df_final.applymap(remplacer_tirets_apostrophes)
        df_final.columns = [remplacer_tirets_apostrophes(str(c)) for c in df_final.columns]

    if st.button("▶️ Exécuter le traitement"):
        try:
            exec(code, {"pd": pd, "df": df_final})
            if callable(eval("traiter")):
                df_final = eval("traiter")(df_final)
            st.session_state["resultat"] = df_final
            st.success("Traitement exécuté.")
        except Exception as e:
            st.error(f"Erreur dans le code Python : {e}")

    if "resultat" in st.session_state:
        df_res = st.session_state["resultat"]
        st.subheader("Aperçu du résultat")
        st.dataframe(df_res.head(50))

        # ---------------- Téléchargements ----------------
        st.header("5️⃣ Télécharger le résultat")
        csv_buf = io.StringIO()
        df_res.to_csv(csv_buf, index=False)
        st.download_button("⬇️ Télécharger en CSV", csv_buf.getvalue(), "resultat.csv", "text/csv")

        xlsx_buf = io.BytesIO()
        with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
            df_res.to_excel(writer, index=False, sheet_name="Résultat")
        st.download_button("⬇️ Télécharger en XLSX", xlsx_buf.getvalue(), "resultat.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
