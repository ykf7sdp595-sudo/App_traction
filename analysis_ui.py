"""Réglages d'analyse et annotations Plotly ; calculs dans analysis.py."""

from dataclasses import replace
from hashlib import sha256
from html import escape

import plotly.graph_objects as go
import streamlit as st

from analysis import detect_peaks, extreme, rupture_candidate
from processing import process


def add_analysis(figure, curve, raw, displayed, points, x_quantity, y_quantity):
    prefix = curve["identity"] + "_analysis_"
    with st.expander("Analyse et annotations", icon=":material/analytics:"):
        enabled = st.checkbox("Activer l'analyse et les annotations", key=prefix + "enabled")
        if not enabled:
            return
        st.caption("Ces réglages s'appliquent immédiatement. Les numéros de points sont ceux du fichier source. Les zones explicatives ne changent pas les calculs.")
        filtered = st.checkbox("Analyser le signal filtré", value=False, disabled=not curve["settings"].smoothing, key=prefix + "filtered")
        if filtered and curve["settings"].smoothing:
            signals = displayed
        else:
            signals, _, _ = process(raw, replace(curve["settings"], smoothing=False))
        st.caption("Base de calcul : " + ("signal filtré" if filtered and curve["settings"].smoothing else "signal sans filtrage") + ", après corrections, précharge et sélection de zone.")
        labels = st.checkbox("Afficher les textes des marqueurs", value=True, key=prefix + "labels")
        force = signals.get("force")
        markers = []
        if force is None:
            st.info("Associer une force pour calculer maxima, pics et rupture. Les zones restent disponibles.")
        else:
            mode = st.selectbox("Extrême de force", ["Masqué", "Maximum positif", "Minimum négatif", "Maximum absolu"], key=prefix + "extreme")
            if mode != "Masqué":
                index = extreme(force, mode)
                if index is None:
                    st.info("Aucune force du signe demandé dans la zone analysée.")
                else:
                    markers.append((index, mode, "diamond"))
            if st.checkbox("Détecter les pics", key=prefix + "peaks"):
                polarity = st.selectbox("Signe des pics", ["Les deux", "Positifs", "Négatifs"], key=prefix + "polarity")
                a, b = st.columns(2)
                relief = a.number_input("Relief local minimal (N)", min_value=0.0, value=0.1, key=prefix + "relief")
                distance = b.number_input("Espacement minimal (points)", min_value=1, value=10, key=prefix + "distance")
                st.caption("Relief = différence avec la plus haute des deux vallées voisines (signe inversé pour les pics négatifs). Les extrémités sont exclues ; premier point d'un plateau retenu.")
                peaks = detect_peaks(force, polarity, relief, distance)
                if not peaks:
                    st.info("Aucun pic détecté avec ces réglages.")
                else:
                    st.dataframe([{"Point source": points[p.index], "Force (N)": p.force, "Relief (N)": p.relief} for p in peaks], hide_index=True)
                    lookup = {points[p.index]: p.index for p in peaks}
                    selection = st.multiselect("Pics à afficher", list(lookup), default=list(lookup)[:10], key=prefix + "selected_peaks")
                    st.caption("Au premier affichage, seuls les dix premiers pics sont sélectionnés. Ajuster cette sélection pour alléger le PNG.")
                    markers.extend((lookup[p], "Pic détecté", "circle") for p in selection if p in lookup)
                manual = st.text_input("Pics manuels : points source séparés par des virgules", key=prefix + "manual_peaks", help="Pour corriger un pic, désélectionner le pic détecté et saisir ici le point souhaité.")
                try:
                    manual_points = sorted(set(int(p.strip()) for p in manual.split(",") if p.strip()))
                    if any(p < points[0] or p > points[-1] for p in manual_points):
                        raise ValueError
                    markers.extend((p - points[0], "Pic manuel", "circle-open") for p in manual_points)
                except ValueError:
                    st.warning("Pics manuels ignorés : utiliser des entiers compris dans la zone analysée.")
            if st.checkbox("Rechercher une rupture candidate", key=prefix + "rupture"):
                direction = st.selectbox("Sens de l'effort pour la rupture", ["Positive", "Négative", "Valeur absolue"], key=prefix + "direction")
                a, b, c = st.columns(3)
                drop = a.number_input("Chute minimale (N)", min_value=0.001, value=10.0, key=prefix + "drop")
                window = b.number_input("Chute sur au plus (points)", min_value=1, value=20, key=prefix + "window")
                minimum = c.number_input("Effort préalable minimal (N)", min_value=0.0, value=10.0, key=prefix + "minimum")
                candidate = rupture_candidate(force, drop, window, minimum, direction)
                if candidate:
                    peak, crossing = candidate
                    st.info(f"Candidat : point {points[peak]} avant chute ; seuil franchi au point {points[crossing]}. À confirmer selon l'évènement physique.")
                else:
                    st.info("Aucune rupture candidate détectée. La fin du fichier n'est pas une rupture par défaut.")
                # Une validation devient caduque dès que les données ou critères changent.
                signature = sha256(repr((force, points, direction, drop, window, minimum)).encode()).hexdigest()[:12]
                manual = st.checkbox("Choisir manuellement le point de rupture", key=prefix + "manual_rupture")
                index = candidate[0] if candidate else None
                if manual:
                    source = st.number_input("Point source de rupture", points[0], points[-1], points[index] if index is not None else points[0], key=prefix + "rupture_point_" + signature)
                    index = source - points[0]
                if index is not None:
                    confirmed = st.checkbox("Confirmer l'évènement comme rupture", key=prefix + f"confirm_{signature}_{points[index]}_{manual}")
                    if st.checkbox("Afficher le marqueur de rupture", value=True, key=prefix + "show_rupture"):
                        markers.append((index, "Rupture confirmée" if confirmed else "Rupture candidate", "x"))
                st.caption("Détection : premier recul de force atteignant la chute demandée dans la fenêtre ; marqueur sur le sommet précédent. Une décharge peut donner le même signal.")

        if markers:
            st.dataframe([{"Évènement": name, "Point source": points[i], "Force (N)": force[i]} for i, name, _ in markers], hide_index=True)
            for marker_number, (index, name, symbol) in enumerate(markers):
                text = f"{name} : {force[index]:.4g} N"
                figure.add_trace(go.Scattergl(x=[signals[x_quantity][index]], y=[signals[y_quantity][index]],
                    mode="markers", name=f"{curve['label']} · {name}", showlegend=False,
                    marker=dict(color=curve["color"], size=10, symbol=symbol),
                    customdata=[[points[index], force[index]]],
                    hovertemplate="Point source %{customdata[0]}<br>Force : %{customdata[1]:.6g} N<extra>%{fullData.name}</extra>"))
                if labels:
                    # Les textes de trace ne sont pas déplaçables : utiliser des
                    # annotations dont seule la queue de flèche peut être déplacée.
                    figure.add_annotation(
                        name=f"{prefix}marker_{name}_{points[index]}",
                        x=signals[x_quantity][index], y=signals[y_quantity][index],
                        text=escape(text), showarrow=True, arrowhead=2,
                        ax=40 if marker_number % 2 == 0 else -40,
                        ay=-45 - 20 * (marker_number % 3), axref="pixel", ayref="pixel",
                        bgcolor="white", borderpad=4, bordercolor=curve["color"],
                        arrowcolor=curve["color"], font=dict(color=curve["color"]))

        st.markdown("**Zones physiques**")
        st.caption("Une zone colore un segment de la courbe affichée, dans l'ordre d'acquisition : l'aller et le retour restent distincts. Zones définies sur le fichier source ; seule leur intersection avec la courbe affichée est dessinée.")
        count = st.number_input("Nombre de zones", min_value=0, max_value=20, value=0, key=prefix + "zones")
        for number in range(count):
            zone_key = prefix + f"zone_{number}_"
            with st.container(border=True):
                st.caption(f"Zone {number + 1}")
                title = st.text_input("Évènement physique", value=f"Phase {number + 1}", key=zone_key + "title")
                a, b, c = st.columns(3)
                first = a.number_input("Début (point source)", 1, len(curve["data"].rows), 1, key=zone_key + "first")
                last = b.number_input("Fin (point source)", 1, len(curve["data"].rows), len(curve["data"].rows), key=zone_key + "last")
                color = c.color_picker("Couleur de zone", ["#ee9b00", "#9b5de5", "#00a896"][number % 3], key=zone_key + "color")
                visible = st.checkbox("Afficher cette zone", value=True, key=zone_key + "visible")
                text_visible = st.checkbox("Afficher le nom de zone", value=True, key=zone_key + "text")
                if first > last:
                    st.warning("Zone ignorée : le début doit précéder la fin.")
                    continue
                begin, end = max(first, points[0]), min(last, points[-1])
                if begin > end:
                    st.caption("Zone hors de la portion affichée.")
                    continue
                if not visible:
                    continue
                begin, end = begin - points[0], end - points[0] + 1
                figure.add_trace(go.Scattergl(x=displayed[x_quantity][begin:end], y=displayed[y_quantity][begin:end],
                    mode="lines" if end - begin > 1 else "markers", line=dict(color=color, width=7),
                    marker=dict(color=color, size=10), opacity=0.45, showlegend=False,
                    name=f"{curve['label']} · {title}", hoverinfo="name"))
                if text_visible:
                    middle = (begin + end - 1) // 2
                    figure.add_annotation(name=zone_key, x=displayed[x_quantity][middle], y=displayed[y_quantity][middle],
                        text=escape(title), showarrow=True, arrowhead=2, ax=30, ay=-45,
                        axref="pixel", ayref="pixel", borderpad=4,
                        bgcolor="white", bordercolor=color, arrowcolor=color, font=dict(color=color))
