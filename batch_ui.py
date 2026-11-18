"""Actions collectives exécutées en callback avant de recréer les widgets."""

import streamlit as st
from dataclasses import replace

from batches import curve_signals, lot_statistics
from processing import process


def assign_lot(targets, name):
    name = name.strip()
    if not name:
        st.session_state.batch_report = "Nom de lot vide : aucune affectation."
        return
    for identity in targets:
        st.session_state[identity + "lot"] = name
    st.session_state.batch_report = f"{len(targets)} courbe(s) affectée(s) au lot {name}."


def copy_treatments(curves, source, targets):
    settings = next(c["settings"] for c in curves if c["identity"] == source)
    report = []
    for curve in curves:
        if curve["identity"] not in targets:
            continue
        try:
            process(curve_signals(curve), settings)
        except ValueError as error:
            report.append(f"{curve['label']} : non appliqué ({error}) ; anciens réglages conservés.")
            continue
        # Synchroniser les champs ET les paramètres validés, sans toucher aux
        # unités, couleurs, colonnes, annotations ou données originales.
        n = len(curve["data"].rows)
        values = dict(mode=settings.offset_mode, offset=settings.offset,
                      ref_start=settings.reference[0] if settings.offset_mode == "Moyenne d'une zone" else 1,
                      ref_end=settings.reference[1] if settings.offset_mode == "Moyenne d'une zone" else min(10, n),
                      preload=settings.preload, threshold=settings.threshold, direction=settings.direction,
                      zero_time=settings.zero_time, zero_displacement=settings.zero_displacement,
                      smoothing=settings.smoothing, window=settings.window, crop=settings.crop,
                      first=settings.interval[0] if settings.crop else 1,
                      last=settings.interval[1] if settings.crop else n, applied=settings)
        values["applied"] = replace(settings, reference=(values["ref_start"], values["ref_end"]),
                                    interval=(values["first"], values["last"]))
        for key, value in values.items():
            st.session_state[curve["identity"] + "_treatment_" + key] = value
        report.append(f"{curve['label']} : traitements appliqués.")
    st.session_state.batch_report = "\n".join(report) or "Aucune cible sélectionnée."


def batch_panel(curves):
    if not curves:
        return curves
    with st.expander("Lots, traitements groupés et statistiques"):
        names = {c["identity"]: f"{c['label']} — {c['name']}" for c in curves}
        targets = st.multiselect("Courbes cibles", list(names), format_func=names.get, key="batch_targets")
        lot_name = st.text_input("Nom du lot à affecter", value="Lot 1", key="batch_lot_name")
        st.button("Affecter le lot aux courbes cibles", disabled=not targets,
                  on_click=assign_lot, args=(targets, lot_name))
        source = st.selectbox("Courbe modèle pour les traitements", list(names), format_func=names.get, key="batch_source")
        st.caption("Copie les réglages déjà validés du modèle. Les bornes restent des numéros de points source, sans adaptation automatique. Une cible incompatible conserve ses anciens réglages et est signalée. Chaque courbe reste ajustable individuellement.")
        st.button("Appliquer les traitements aux courbes cibles", disabled=not targets,
                  on_click=copy_treatments, args=(curves, source, targets))
        if st.session_state.get("batch_report"):
            st.text(st.session_state.batch_report)
        lots = sorted({c["lot"] for c in curves})
        selected = st.selectbox("Lot à afficher et analyser", [None] + lots,
                                format_func=lambda value: "Tous les lots (statistiques séparées)" if value is None else value,
                                key="batch_filter")
        selected_curves = [c for c in curves if selected is None or c["lot"] == selected]
        if st.checkbox("Afficher les statistiques des forces", key="batch_stats"):
            mode = st.selectbox("Convention commune des forces", ["Maximum positif", "Minimum négatif", "Maximum absolu"], key="batch_mode")
            filtered = st.checkbox("Utiliser les filtres validés des courbes", key="batch_filtered")
            st.caption("Une valeur par fichier et par courbe. Maximum absolu = amplitude positive ; minimum négatif = valeur signée. Base commune : sans filtrage par défaut, après corrections/précharge/zone. La case « Inclure dans les statistiques » est indépendante du masquage du graphique et des axes disponibles.")
            details, summary = lot_statistics(selected_curves, mode, filtered)
            st.dataframe(summary, hide_index=True, key="lot_summary")
            st.dataframe(details, hide_index=True, key="lot_details")
            st.caption("Écart-type d'échantillon : n − 1 ; non calculable pour moins de deux courbes. Les réglages individuels restent possibles : vérifier la colonne Traitements avant de comparer des essais.")
        return selected_curves
