"""Formulaire des traitements ; les calculs restent dans processing.py."""

import streamlit as st
from processing import Settings


def number_field(label, default, key, **options):
    """Une seule source de valeur, compatible avec les copies de paramètres."""
    st.session_state.setdefault(key, default)
    return st.number_input(label, value=None, key=key, **options)


def reset_treatment(prefix):
    # Callback exécuté AVANT la recréation des widgets au prochain affichage.
    for key in list(st.session_state):
        if key.startswith(prefix):
            del st.session_state[key]


def treatment_controls(identity, count):
    prefix = identity + "_treatment_"
    st.caption("Activez uniquement les opérations nécessaires, puis validez en bas de cette section.")
    st.caption("Ordre : correction de force → précharge → origines → filtre → zone. Les points sont numérotés à partir de 1 dans le fichier source, indépendamment des retours en déplacement.")
    st.button("Réinitialiser les traitements", key=identity + "reset", on_click=reset_treatment, args=(prefix,))
    # Les champs réagissent aux activations ; seul Appliquer valide le brouillon.
    mode = st.selectbox("Correction de force", ["Aucune", "Valeur saisie", "Moyenne d'une zone"], key=prefix + "mode")
    offset = number_field("Force à soustraire (N)", 0.0, key=prefix + "offset", disabled=mode != "Valeur saisie")
    a, b = st.columns(2)
    with a:
        ref_start = number_field("Référence : premier point", 1, min_value=1, max_value=count, key=prefix + "ref_start", disabled=mode != "Moyenne d'une zone")
    with b:
        ref_end = number_field("Référence : dernier point", min(10, count), min_value=1, max_value=count, key=prefix + "ref_end", disabled=mode != "Moyenne d'une zone")
    preload = st.checkbox("Retirer le début avant précharge", key=prefix + "preload")
    a, b = st.columns(2)
    with a:
        threshold = number_field("Seuil de précharge (N, amplitude positive)", 1.0, min_value=0.0, key=prefix + "threshold", disabled=not preload)
    direction = b.selectbox("Sens de précharge", ["Positive", "Négative", "Valeur absolue"], key=prefix + "direction", disabled=not preload)
    st.caption("Premier point atteignant le seuil, inclus ; aucune soustraction automatique du seuil de force.")
    zero_time = st.checkbox("Temps à zéro au début utile", key=prefix + "zero_time")
    zero_displacement = st.checkbox("Déplacement à zéro au début utile", key=prefix + "zero_displacement")
    smoothing = st.checkbox("Filtrer la force", key=prefix + "smoothing")
    window = number_field("Fenêtre de moyenne centrée (points, impaire)", 5, min_value=3, step=2, key=prefix + "window", disabled=not smoothing)
    st.caption("Filtre en points d'acquisition ; les pics peuvent être atténués. Temps et déplacement ne sont pas filtrés.")
    crop = st.checkbox("Limiter à une zone", key=prefix + "crop")
    a, b = st.columns(2)
    with a:
        first = number_field("Zone : premier point", 1, min_value=1, max_value=count, key=prefix + "first", disabled=not crop)
    with b:
        last = number_field("Zone : dernier point", count, min_value=1, max_value=count, key=prefix + "last", disabled=not crop)
    draft = Settings(mode, offset, (ref_start, ref_end), preload, threshold, direction,
                    zero_time, zero_displacement, crop, (first, last), smoothing, window)

    applied_key = prefix + "applied"
    st.session_state.setdefault(applied_key, draft)
    if st.button("Appliquer à cette courbe", key=prefix + "apply", type="primary", icon=":material/check:"):
        st.session_state[applied_key] = draft
        st.success("Réglages validés pour cette courbe. Le graphique est actualisé ; les traitements impossibles sont signalés.")
    applied = st.session_state[applied_key]
    if draft != applied:
        st.info("Modifications non appliquées : cliquez sur « Appliquer à cette courbe » pour actualiser le graphique.")
    if mode == "Aucune":
        st.caption("Correction de force désactivée. Pour soustraire une force, choisir « Valeur saisie ».")
    st.caption(f"Correction de force validée : {applied.offset_mode}"
               + (f" — soustraction de {applied.offset:g} N" if applied.offset_mode == "Valeur saisie" else ""))
    return applied
