"""Plotly local avec remontée des clics de légende et des points à Streamlit.

Le composant v2 utilise le JavaScript déjà fourni par Plotly : aucun CDN ni
nouvelle dépendance. Le résumé reçoit ainsi la même visibilité que le graphique.
"""

import streamlit as st
from streamlit.components.v2 import component
from plotly.offline import get_plotlyjs
from events_ui import selected_source, add_free_event, undo_last_event


JS = r"""
const instances = new WeakMap();
export default function(component) {
  const {parentElement, data, setTriggerValue} = component;
  const plot = parentElement.querySelector('.traction-plot');
  const feedback = parentElement.querySelector('.traction-feedback');
  feedback.textContent = data.feedback || '';
  let state = instances.get(plot);
  if (!state) {
    state = {queue: Promise.resolve(), observer: new ResizeObserver(() => {
      if (plot._fullLayout) window.Plotly.Plots.resize(plot);
    })};
    state.observer.observe(plot);
    instances.set(plot, state);
  }
  state.component = component;
  state.data = data;
  state.queue = state.queue.then(async () => {
    const latest = state.data;
    const figure = JSON.parse(latest.spec);
    await window.Plotly.react(plot, figure.data, figure.layout, latest.config);
    plot.removeAllListeners('plotly_legendclick');
    plot.removeAllListeners('plotly_legenddoubleclick');
    plot.removeAllListeners('plotly_click');
    plot.on('plotly_legendclick', e => {
      const trace = plot.data[e.curveNumber];
      const id = trace.meta?.curve_id;
      if (id) {
        state.component.setTriggerValue('visibility', {id, hidden: trace.visible !== 'legendonly'});
      }
      return false;
    });
    // Un clic = bascule ; désactiver l'isolation implicite du double-clic.
    plot.on('plotly_legenddoubleclick', () => false);
    plot.on('plotly_click', e => {
      if (!state.data.point_click) return;
      const point = e.points?.[0];
      if (point && Array.isArray(point.customdata) && point.customdata[0] === 'event') {
        feedback.textContent = 'Placement du marqueur…';
        state.component.setTriggerValue('point', {customdata: point.customdata});
      }
    });
  }).catch(error => { plot.textContent = 'Erreur du graphique : ' + error.message; });
  return () => { state.observer.disconnect(); window.Plotly.purge(plot); instances.delete(plot); };
}
"""

_CHART = component("traction_plot", html='<div class="traction-feedback" role="status" aria-live="polite" style="color:#14532d;background:#f0fdf4;padding:6px 12px;min-height:32px"></div><div class="traction-plot" style="width:100%;background:white"></div>',
    js=get_plotlyjs() + "\n" + JS, isolate_styles=False)


def reset_legend_visibility(identity):
    st.session_state.setdefault("legend_hidden", {}).pop(identity, None)


def visibility_changed():
    event = st.session_state.get("traction_chart", {}).get("visibility")
    if event and event.get("id") in st.session_state.get("chart_curve_ids", []):
        st.session_state.setdefault("legend_hidden", {})[event["id"]] = bool(event.get("hidden"))


def point_changed():
    target = st.session_state.get("event_click_target")
    event = st.session_state.get("traction_chart", {}).get("point")
    if target and event:
        identity, first, last = target
        point = selected_source({"points": [event]}, identity, first, last)
        if point is not None:
            st.session_state[identity + "_event_point"] = point
            add_free_event(identity, point)


def draw_chart(figure, config, point_click):
    hidden = st.session_state.setdefault("legend_hidden", {})
    ids = set()
    for trace in figure.data:
        owner = (trace.meta or {}).get("curve_id")
        if owner:
            ids.add(owner)
            trace.legendgroup = owner
            if hidden.get(owner, False):
                trace.visible = "legendonly" if trace.uid == owner else False
    for annotation in figure.layout.annotations:
        owner = (annotation.name or "").split("_", 1)[0]
        if hidden.get(owner, False):
            annotation.visible = False
    st.session_state.chart_curve_ids = list(ids)
    # Le payload sert aussi aux contrôles automatisés (le DOM n'est pas simulé).
    feedback = st.session_state.get("event_notice", "")
    if not feedback and point_click:
        feedback = "Placement actif : cliquez sur la courbe choisie pour ajouter un marqueur."
    payload = dict(spec=figure.to_json(), config=config, point_click=point_click, feedback=feedback)
    st.session_state.chart_payload = payload
    _CHART(data=payload, key="traction_chart", height=int(figure.layout.height) + 40,
           on_visibility_change=visibility_changed, on_point_change=point_changed)
    if st.session_state.get("last_added_event"):
        st.button("Annuler le dernier marqueur", on_click=undo_last_event, icon=":material/undo:")
