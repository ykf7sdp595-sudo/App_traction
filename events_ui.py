"""Marqueurs libres : ancrage au numéro source, jamais à un extremum imposé."""

from html import escape
from uuid import uuid4

import plotly.graph_objects as go
import streamlit as st


def selected_source(selection, identity, first, last):
    """Ne retenir qu'un clic sur la courbe choisie, pas les annotations/bruts."""
    candidates = []
    for point in selection.get("points", []):
        data = point.get("customdata")
        if (isinstance(data, (list, tuple)) and len(data) == 3
                and data[0] == "event" and data[1] == identity
                and isinstance(data[2], int) and first <= data[2] <= last):
            candidates.append(data[2])
    return candidates[0] if len(candidates) == 1 else None


def add_free_event(identity, source):
    """Ajout commun au clic et à la saisie, avec protection contre le double-clic."""
    title = st.session_state.get("event_title", "Évènement").strip() or "Évènement"
    color = st.session_state.get("event_color", "#c62828")
    markers = st.session_state.setdefault("free_events", {}).setdefault(identity, [])
    if any(m["point"] == source and m["title"] == title and m["visible"] for m in markers):
        st.session_state.event_notice = f"« {title} » est déjà placé au point {source}."
        return
    marker = dict(id=uuid4().hex, point=source, title=title, color=color, visible=True)
    markers.append(marker)
    st.session_state.last_added_event = (identity, marker["id"])
    label = st.session_state.get("event_target_label", "la courbe choisie")
    st.session_state.event_notice = f"« {title} » placé au point {source} — {label}."
    st.toast(st.session_state.event_notice, icon=":material/check_circle:")


def undo_last_event():
    last = st.session_state.pop("last_added_event", None)
    if last:
        remove_event(*last)
        st.session_state.event_notice = "Dernier marqueur annulé."


def remove_event(identity, marker_id):
    st.session_state.free_events[identity] = [m for m in st.session_state.free_events.get(identity, []) if m["id"] != marker_id]
    if st.session_state.get("last_added_event") == (identity, marker_id):
        st.session_state.pop("last_added_event", None)


def event_panel(figure, rendered):
    """Appelé après les calculs, avant le graphique ; renvoie le mode clic."""
    st.session_state.setdefault("free_events", {})
    st.session_state.event_click_target = None
    if not rendered:
        return False
    lookup = {item["curve"]["identity"]: item for item in rendered}
    active = False
    with st.expander("Marqueurs d'évènements libres"):
        active = st.checkbox("Placer un évènement sur une courbe", key="event_enabled")
        if active:
            identity = st.selectbox("Courbe à annoter", list(lookup),
                                    format_func=lambda v: lookup[v]["curve"]["label"], key="event_curve")
            if identity is None:
                return False
            item = lookup[identity]
            st.session_state.event_target_label = item["curve"]["label"]
            points = item["points"]
            click = st.checkbox("Sélectionner le point par clic", value=True, key="event_click")
            st.caption("Choisissez le nom et la couleur, puis cliquez sur un point de cette courbe : le marqueur est ajouté immédiatement. Chaque clic place un évènement, sans validation supplémentaire. Décochez la sélection par clic pour utiliser une saisie numérique.")
            if click:
                st.session_state.event_click_target = (identity, points[0], points[-1])
                for trace in figure.data:
                    if trace.uid == identity:
                        trace.mode = "lines+markers" if len(points) > 1 else "markers"
                        trace.marker.size = 5
                        trace.customdata = [["event", identity, p] for p in points]
                        trace.hovertemplate = "Point source %{customdata[2]}<br>X : %{x:.6g}<br>Y : %{y:.6g}<extra>%{fullData.name}</extra>"
                        # Conserver les autres points visibles après sélection.
                        trace.unselected = dict(marker=dict(opacity=1))
            point_key = identity + "_event_point"
            current = st.session_state.get(point_key) or points[0]
            st.session_state[point_key] = min(max(current, points[0]), points[-1])
            source = st.number_input("Point source de l'évènement", min_value=points[0], max_value=points[-1], value=None, key=point_key)
            title = st.text_input("Nom de l'évènement", value="Évènement", key="event_title")
            color = st.color_picker("Couleur du marqueur libre", value="#c62828", key="event_color")
            if source is not None:
                i = source - points[0]
                st.caption(f"Point {source} : X = {item['x'][i]:.6g} ; Y = {item['y'][i]:.6g} (unités des axes).")
            if not click and st.button("Ajouter ce marqueur", disabled=source is None or not title.strip()):
                add_free_event(identity, source)

        for identity, item in lookup.items():
            markers = st.session_state.free_events.get(identity, [])
            if not markers:
                continue
            st.markdown(f"**{escape(item['curve']['label'])} — évènements enregistrés**")
            for marker in markers:
                key = "free_event_" + marker["id"]
                with st.expander(f"{marker['title']} — point {marker['point']}"):
                    marker["title"] = st.text_input("Libellé du marqueur", value=marker["title"], key=key + "title")
                    point = st.number_input("Ancrage (point source)", min_value=1,
                        max_value=len(item["curve"]["data"].rows), value=marker["point"], key=key + "point")
                    if point is not None:
                        marker["point"] = point
                    marker["color"] = st.color_picker("Couleur de l'évènement", value=marker["color"], key=key + "color")
                    marker["visible"] = st.checkbox("Afficher cet évènement", value=marker["visible"], key=key + "visible")
                    st.button("Supprimer cet évènement", key=key + "delete", on_click=remove_event, args=(identity, marker["id"]))
                    if marker["point"] not in range(item["points"][0], item["points"][-1] + 1):
                        st.caption("Point hors de la zone affichée : marqueur conservé mais non dessiné.")
    for identity, item in lookup.items():
        for marker in st.session_state.free_events.get(identity, []):
            if not marker["visible"] or not item["points"][0] <= marker["point"] <= item["points"][-1]:
                continue
            index = marker["point"] - item["points"][0]
            x, y = item["x"][index], item["y"][index]
            figure.add_trace(go.Scattergl(x=[x], y=[y], mode="markers", showlegend=False,
                meta=dict(curve_id=identity),
                name=f"{item['curve']['label']} · {marker['title']}",
                marker=dict(symbol="star", size=12, color=marker["color"]),
                customdata=[marker["point"]], hovertemplate="Point source %{customdata}<br>X : %{x:.6g}<br>Y : %{y:.6g}<extra>%{fullData.name}</extra>"))
            figure.add_annotation(name=identity + "_event_" + marker["id"], x=x, y=y, text=escape(marker["title"]),
                showarrow=True, arrowhead=2, ax=45, ay=-60, axref="pixel", ayref="pixel",
                bgcolor="white", font=dict(color="#202124"), borderpad=4,
                bordercolor=marker["color"], arrowcolor=marker["color"])
    return bool(st.session_state.event_click_target)
