import streamlit as st
import pandas as pd
import unicodedata
import io

st.set_page_config(page_title="Éditeur Python - XLSX / CSV", page_icon="🐍", layout="wide")

st.title("🐍 Éditeur Python — traitement de fichiers XLSX / CSV")
st.markdown(
    "Chargez un fichier **.xlsx** ou **.csv**, appliquez des traitements "
    "automatiques ou écrivez votre propre code Python, puis téléchargez le résultat."
)

# ── Chargement du fichier ─────────────────────────────────────────────
uploaded = st.file_uploader("📂 Charger un fichier", type=["xlsx", "csv"])

df = None
if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
        st.success(f"Fichier **{uploaded.name}** chargé : {df.shape[0]} lignes × {df.shape[1]} colonnes.")
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")

# ── Traitements automatiques ──────────────────────────────────────────
if df is not None:
    st.header("⚙️ Traitements automatiques")

    trim_spaces = st.checkbox("Supprimer les espaces en début/fin de valeurs")
    remove_accents = st.checkbox(
        "Enlever tous les accents (remplacés par la lettre correspondante)"
    )
    remove_dashes_apostrophes = st.checkbox(
        "Enlever les tirets et apostrophes (remplacés par un espace)"
    )
    upper_cols = st.checkbox("Mettre les noms de colonnes en majuscules")
    drop_empty_rows = st.checkbox("Supprimer les lignes entièrement vides")

    def strip_accents(text):
        """Remplace les caractères accentués par leur équivalent non accentué."""
        return "".join(
            ch
            for ch in unicodedata.normalize("NFKD", str(text))
            if not unicodedata.combining(ch)
        )

    def replace_dashes_apostrophes(text):
        """Remplace tirets (-, –, —) et apostrophes (', ’) par un espace."""
        for ch in ("-", "\u2013", "\u2014", "'", "\u2019"):
            text = text.replace(ch, " ")
        return text

    df_processed = df.copy()
    applied = []

    if trim_spaces:
        for col in df_processed.select_dtypes(include="object").columns:
            df_processed[col] = df_processed[col].apply(
                lambda v: v.strip() if isinstance(v, str) else v
            )
        applied.append("suppression des espaces en début/fin")

    if remove_accents:
        for col in df_processed.select_dtypes(include="object").columns:
            df_processed[col] = df_processed[col].apply(
                lambda v: strip_accents(v) if isinstance(v, str) else v
            )
        applied.append("suppression des accents")

    if remove_dashes_apostrophes:
        for col in df_processed.select_dtypes(include="object").columns:
            df_processed[col] = df_processed[col].apply(
                lambda v: replace_dashes_apostrophes(v) if isinstance(v, str) else v
            )
        applied.append("remplacement des tirets et apostrophes par un espace")

    if upper_cols:
        df_processed.columns = [str(c).upper() for c in df_processed.columns]
        applied.append("noms de colonnes en majuscules")

    if drop_empty_rows:
        before = len(df_processed)
        df_processed = df_processed.dropna(how="all")
        applied.append(f"suppression des lignes vides ({before - len(df_processed)} ligne(s) supprimée(s))")

    if applied:
        st.info("Traitements appliqués : " + ", ".join(applied) + ".")

    st.subheader("Aperçu du résultat")
    st.dataframe(df_processed.head(50), use_container_width=True)

    # ── Téléchargement ────────────────────────────────────────────────
    st.header("⬇️ Téléchargement")
    col1, col2 = st.columns(2)

    with col1:
        csv_buffer = io.StringIO()
        df_processed.to_csv(csv_buffer, index=False)
        st.download_button(
            "Télécharger en CSV",
            data=csv_buffer.getvalue().encode("utf-8-sig"),
            file_name="resultat.csv",
            mime="text/csv",
        )

    with col2:
        xlsx_buffer = io.BytesIO()
        with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
            df_processed.to_excel(writer, index=False, sheet_name="Résultat")
        st.download_button(
            "Télécharger en XLSX",
            data=xlsx_buffer.getvalue(),
            file_name="resultat.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # ── Code Python personnalisé ──────────────────────────────────────
    st.header("✍️ Code Python personnalisé")
    st.markdown(
        "Votre code est exécuté avec le DataFrame chargé dans la variable `df`.\n\n"
        "```python\n"
        "# Exemple :\n"
        "df = df.drop_duplicates()\n"
        "df[\"TOTAL\"] = df[\"QTE\"] * df[\"PRIX\"]\n"
        "```"
    )

    default_code = "# Votre DataFrame est disponible dans la variable 'df'\ndf = df.drop_duplicates()\n"
    user_code = st.text_area("Éditeur de code", value=default_code, height=220)

    if st.button("▶ Exécuter le code"):
        try:
            exec_globals = {"df": df_processed.copy(), "pd": pd}
            exec(user_code, exec_globals)
            df_final = exec_globals["df"]
            st.success("Code exécuté avec succès !")
            st.dataframe(df_final.head(50), use_container_width=True)

            csv_final = io.StringIO()
            df_final.to_csv(csv_final, index=False)
            st.download_button(
                "⬇️ Télécharger le résultat du code (CSV)",
                data=csv_final.getvalue().encode("utf-8-sig"),
                file_name="resultat_code.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Erreur d'exécution : {e}")
else:
    st.info("Chargez un fichier pour commencer.")

st.markdown("---")
st.caption("© 2026 — Éditeur Python XLSX/CSV")
