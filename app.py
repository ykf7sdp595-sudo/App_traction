"""Interface : import, traitements par courbe, comparaison et export PNG."""

from hashlib import sha256

import plotly.graph_objects as go
import streamlit as st

from readers import ImportErrorDetail, UNITS, column_values, read_measurement
from processing import process
from treatment_ui import treatment_controls
from analysis_ui import add_analysis
from batch_ui import batch_panel
from events_ui import event_panel
from chart_ui import draw_chart, reset_legend_visibility
from curve_summary import build_summary


st.set_page_config(page_title="Courbes de traction", layout="wide")


@st.cache_data(max_entries=100, show_spinner=False)
def cached_read(content: bytes):
    # Un changement de présentation ne doit pas relire les fichiers.
    return read_measurement(content)


COLORS = ["#1769aa", "#d1495b", "#25845b", "#8956a6", "#c27613", "#00838f", "#795548"]
AXES = {"Force / déplacement": ("displacement", "force"),
        "Force / temps": ("time", "force"),
        "Déplacement / temps": ("time", "displacement")}
LABELS = {"force": "Force (N)", "displacement": "Déplacement (mm)", "time": "Temps (s)"}


def axis_range(label: str, key: str):
    """La saisie explicite des bornes est facultative ; le zoom reste disponible."""
    if not st.checkbox(f"Fixer les limites {label}", key=key):
        return None
    left, right = st.columns(2)
    low = left.number_input(f"Minimum {label}", value=0.0, key=key + "min")
    high = right.number_input(f"Maximum {label}", value=10.0, key=key + "max")
    if low >= high:
        st.error(f"Limites {label} : le minimum doit être inférieur au maximum.")
        st.stop()
    return [low, high]


def main():
    st.title("Courbes de traction")
    st.caption("Chargez vos essais, comparez les courbes et préparez vos graphiques de rapport.")
    with st.expander("Premiers pas", icon=":material/help:"):
        st.markdown("1. **Charger** vos fichiers dans le panneau gauche.\n2. **Ajuster** une courbe dans son onglet : présentation, traitements, analyse.\n3. **Comparer** sur le graphique et ajouter vos évènements si nécessaire.\n4. **Exporter** avec l'appareil photo du graphique, après avoir placé les étiquettes.")
        st.caption("Présentation et analyse : effet immédiat. Traitements : cliquer sur « Appliquer à cette courbe ». Les données originales sont conservées ; les réglages ne sont pas sauvegardés entre sessions.")
    with st.sidebar:
        st.header("Fichiers")
        uploaded = st.file_uploader("CSV, ASCII ou TXT", type=["csv", "tra", "txt"], accept_multiple_files=True)
        st.header("Graphique")
        view = st.selectbox("Axes", list(AXES))
        title = st.text_input("Titre", "Comparaison des essais")
        legend = st.checkbox("Afficher la légende", value=True)
        compare = st.checkbox("Comparer au signal brut", value=False)
        move_labels = st.checkbox("Déplacer les étiquettes à la souris", value=True)
        st.session_state.setdefault("label_position_revision", 0)
        if st.button("Réinitialiser la position des étiquettes"):
            st.session_state.label_position_revision += 1
        with st.expander("Cadrage et dimensions"):
            height = st.slider("Hauteur à l'écran (px)", 400, 1000, 600, 50)
            x_range = axis_range("X", "xrange")
            y_range = axis_range("Y", "yrange")
        with st.expander("Exporter une image PNG", icon=":material/download:"):
            filename = st.text_input("Nom du PNG (sans extension)", "courbes_traction")
            png_width = st.number_input("Largeur (px)", 600, 4000, 1600, 100)
            png_height = st.number_input("Hauteur (px)", 400, 3000, 900, 100)
            scale = st.selectbox("Échelle de résolution", [1, 2, 3], index=0)
            st.caption(f"Image exportée : {png_width * scale} × {png_height * scale} pixels. Utiliser l'icône appareil photo du graphique.")

    sources = [(f.name, f.getvalue()) for f in uploaded]
    if not sources:
        st.info("Chargez vos fichiers dans le panneau de gauche pour afficher les courbes.")
        return

    st.subheader("Comparaison des courbes")
    # Réserver la vue en haut pour garder le résultat proche des réglages.
    chart_area = st.container()
    st.subheader("Réglages par courbe")
    curves = []
    # Dédupliquer les fichiers avant de créer les onglets.
    unique_sources = {}
    for name, content in sources:
        identity = sha256(name.encode() + b"\0" + content).hexdigest()
        if identity in unique_sources:
            st.caption(f"Doublon ignoré : {name}")
        unique_sources[identity] = (name, content)
    sources = list(unique_sources.values())
    st.caption("Choisissez une courbe puis ouvrez la section utile. Les lots et les marqueurs libres se règlent sous les onglets.")
    curve_tabs = st.tabs([name for name, _ in sources])
    seen = set()
    with st.container():
        for index, (name, content) in enumerate(sources):
            # Identité stable : les réglages restent associés au fichier même si l'ordre change.
            identity = sha256(name.encode() + b"\0" + content).hexdigest()
            if identity in seen:
                st.caption(f"Doublon ignoré : {name}")
                continue
            seen.add(identity)
            try:
                measurement = cached_read(content)
            except ImportErrorDetail as error:
                curve_tabs[index].error(f"{name} — {error}")
                continue
            with curve_tabs[index]:
                with st.expander("Présentation et données", icon=":material/table_chart:"):
                    st.caption(f"{len(measurement.rows):,} points")
                    st.caption(f"{measurement.profile} · encodage {measurement.encoding}")
                    for warning in measurement.warnings:
                        st.caption(warning)
                    a, b, c = st.columns([1, 3, 1])
                    visible = a.checkbox("Afficher", True, key=identity + "visible",
                                         on_change=reset_legend_visibility, args=(identity,))
                    label = b.text_input("Légende", name, key=identity + "label")
                    color = c.color_picker("Couleur", COLORS[index % len(COLORS)], key=identity + "color")
                    st.session_state.setdefault(identity + "lot", "Lot 1")
                    lot = st.text_input("Lot", key=identity + "lot").strip() or "Sans lot"
                    include_stats = st.checkbox("Inclure dans les statistiques", value=True, key=identity + "include_stats")
                    has_time = len(measurement.headers) == 6
                    defaults = {"force": 2 if has_time else 1, "displacement": 1 if has_time else 0, "time": 0 if has_time else None}
                    mapping, units = {}, {}
                    for container, quantity in zip(st.columns(3), ("force", "displacement", "time")):
                        with container:
                            options = [None] + list(range(len(measurement.headers)))
                            mapping[quantity] = st.selectbox(
                                LABELS[quantity].split(" (")[0] + " : colonne",
                                options, index=options.index(defaults[quantity]),
                                format_func=lambda v, headers=measurement.headers: "Absente" if v is None else f"{v + 1} — {headers[v]}",
                                key=identity + quantity + "column")
                            units[quantity] = st.selectbox("Unité source", list(UNITS[quantity]), key=identity + quantity + "unit")
                    chosen = [v for v in mapping.values() if v is not None]
                    valid = len(chosen) == len(set(chosen))
                    if not valid:
                        st.error("Une colonne ne peut pas représenter plusieurs grandeurs. Corrigez l'association pour afficher cette courbe.")
                    st.caption("Aperçu des 20 premiers points, dans les unités sources. Toutes les colonnes sont conservées.")
                    st.dataframe({f"{i + 1} — {h}": [r[i] for r in measurement.rows[:20]] for i, h in enumerate(measurement.headers)}, hide_index=True)
                with st.expander("Traitements de la courbe", icon=":material/tune:"):
                    settings = treatment_controls(identity, len(measurement.rows))
            curves.append(dict(name=name, identity=identity, data=measurement, label=label,
                               color=color, visible=visible and valid, mapping=mapping, units=units, settings=settings,
                               valid=valid, lot=lot, include_stats=include_stats, tab_index=index))

    curves = batch_panel(curves)
    x_quantity, y_quantity = AXES[view]
    figure = go.Figure()
    rendered = []
    for curve in curves:
        mapping = curve["mapping"]
        if not curve["visible"]:
            curve_tabs[curve["tab_index"]].caption("Courbe masquée ou association invalide : vérifier Présentation et données pour rétablir l'affichage et l'analyse.")
            continue
        if mapping[x_quantity] is None or mapping[y_quantity] is None:
            st.info(f"{curve['name']} : non affiché pour ces axes (grandeur absente).")
            continue
        raw = {q: column_values(curve["data"], col, q, curve["units"][q])
               for q, col in mapping.items() if col is not None}
        try:
            processed, point_numbers, notes = process(raw, curve["settings"])
        except ValueError as error:
            st.error(f"{curve['label']} — traitement non appliqué : {error} Corrigez les réglages ou réinitialisez cette courbe.")
            continue
        x, y = processed[x_quantity], processed[y_quantity]
        curve_tabs[curve["tab_index"]].caption(" ; ".join(notes) if notes else "Signal brut, aucun traitement.")
        if compare and notes:
            figure.add_trace(go.Scattergl(x=raw[x_quantity], y=raw[y_quantity],
                             name=curve["label"] + " · brut", uid=curve["identity"] + "raw",
                             meta=dict(curve_id=curve["identity"]),
                             mode="lines" if len(raw[x_quantity]) > 1 else "markers",
                             line=dict(color=curve["color"], width=1, dash="dot"), opacity=0.45,
                             customdata=list(range(1, len(raw[x_quantity]) + 1)),
                             hovertemplate="Point source %{customdata}<br>X : %{x:.6g}<br>Y : %{y:.6g}<extra>%{fullData.name}</extra>"))
        figure.add_trace(go.Scattergl(x=x, y=y, name=curve["label"] + (" · traité" if notes else ""), uid=curve["identity"],
                         meta=dict(curve_id=curve["identity"]),
                         mode="lines" if len(x) > 1 else "markers", line=dict(color=curve["color"], width=2),
                         marker=dict(color=curve["color"]), customdata=point_numbers,
                         hovertemplate="Point source %{customdata}<br>X : %{x:.6g}<br>Y : %{y:.6g}<extra>%{fullData.name}</extra>"))
        with curve_tabs[curve["tab_index"]]:
            add_analysis(figure, curve, raw, processed, point_numbers, x_quantity, y_quantity)
        rendered.append(dict(curve=curve, points=point_numbers, x=x, y=y, signals=processed))
    event_click = event_panel(figure, rendered)
    if not rendered:
        chart_area.info("Aucune courbe compatible sélectionnée. Vérifiez le lot choisi, la case Afficher et les axes disponibles.")
        return
    # Conserver les déplacements côté navigateur tant que les annotations restent
    # identiques. Une nouvelle sélection/position de point remet les textes à zéro
    # pour éviter d'attribuer un ancien déplacement à une autre annotation.
    annotation_signature = sha256(repr([
        (a.name, a.x, a.y, a.text) for a in figure.select_annotations()
    ]).encode()).hexdigest()
    figure.update_layout(template="plotly_white", title=dict(text=title, x=0.02),
                         paper_bgcolor="white", plot_bgcolor="white",
                         font=dict(color="#202124"),
                         clickmode="event+select" if event_click else "event",
                         editrevision=f"{view}:{annotation_signature}:{st.session_state.label_position_revision}",
                         height=height, showlegend=legend, hovermode="closest",
                         legend=dict(orientation="h", y=-0.2, bgcolor="white", font=dict(color="#202124")), margin=dict(l=70, r=30, t=70, b=100),
                         # Conserve le zoom lors des changements de couleur ou de titre.
                         uirevision=f"{view}:{x_range}:{y_range}:{[(c['settings'], c['units'], c['mapping']) for c in curves]}")
    figure.update_xaxes(title_text=LABELS[x_quantity], range=x_range, autorange=x_range is None)
    figure.update_yaxes(title_text=LABELS[y_quantity], range=y_range, autorange=y_range is None)
    # Style explicite commun à l'écran et au PNG, indépendant du thème Streamlit.
    figure.update_xaxes(color="#202124", gridcolor="#e5e7eb", zerolinecolor="#9ca3af")
    figure.update_yaxes(color="#202124", gridcolor="#e5e7eb", zerolinecolor="#9ca3af")
    figure.update_annotations(bgcolor="white", font=dict(color="#202124"))
    with chart_area:
        hidden = st.session_state.get("legend_hidden", {})
        shown = [item for item in rendered if not hidden.get(item["curve"]["identity"], False)]
        st.caption(f"{len(shown)} courbe(s) affichée(s) · {sum(len(item['points']) for item in shown):,} points")
        draw_chart(figure, point_click=event_click,
                   config={"displaylogo": False, "displayModeBar": True, "scrollZoom": True,
                                "editable": False,
                                "edits": {"annotationTail": move_labels, "annotationPosition": False, "annotationText": False},
                                "toImageButtonOptions": {"format": "png", "filename": filename or "courbes_traction",
                                                         "width": png_width, "height": png_height, "scale": scale}})
        st.caption("Glisser pour zoomer ; double-cliquer pour rétablir la vue. Cliquer sur une légende pour masquer une courbe. L'appareil photo exporte la vue courante, y compris le zoom et les courbes visibles.")
        st.caption("Étiquettes : saisir le texte et le glisser pour le déplacer ; la pointe de flèche reste sur la mesure. Le PNG reprend ce placement. Les positions sont temporaires dans le navigateur et sont réinitialisées si les annotations ou les axes changent.")
    with st.expander("Résumé des courbes sélectionnées"):
        summary, statistics = build_summary(rendered, st.session_state.get("free_events", {}),
                                            st.session_state.get("legend_hidden", {}), LABELS[y_quantity])
        st.caption("Uniquement les courbes affichées, après traitements et sélection de zone. Les colonnes d'évènements contiennent la force en N au point marqué. Un même nom d'évènement partage une colonne entre courbes.")
        if summary:
            st.dataframe(summary, hide_index=True, key="curve_summary")
            st.markdown("**Statistiques des courbes affichées**")
            st.dataframe(statistics, hide_index=True, key="curve_summary_stats")
            st.caption("Les cellules vides sont ignorées. Écart-type d'échantillon (n − 1), vide lorsqu'il y a moins de deux valeurs. Les zooms ne modifient pas les calculs.")
        else:
            st.info("Toutes les courbes sont masquées. Cliquez sur une légende pour en réafficher une.")


if __name__ == "__main__":
    main()
