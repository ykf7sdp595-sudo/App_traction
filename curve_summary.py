"""Résumé des seules courbes visibles et statistiques par colonne, sans dépendance."""

from statistics import mean, stdev


def build_summary(rendered, events, hidden, y_label):
    rows, columns = [], {}
    for item in rendered:
        curve = item["curve"]
        if hidden.get(curve["identity"], False):
            continue
        row = {"Courbe": curve["label"], f"Minimum — {y_label}": min(item["y"]),
               f"Maximum — {y_label}": max(item["y"])}
        occurrences = {}
        for marker in events.get(curve["identity"], []):
            if not marker["visible"] or not item["points"][0] <= marker["point"] <= item["points"][-1]:
                continue
            title = marker["title"].strip() or "Évènement"
            occurrences[title] = occurrences.get(title, 0) + 1
            key = (title, occurrences[title])
            if key not in columns:
                name = f"Évènement — {title}" + (f" [{key[1]}]" if key[1] > 1 else "") + " (N)"
                while name in columns.values():
                    name += " *"
                columns[key] = name
            force = item["signals"].get("force")
            row[columns[key]] = force[marker["point"] - item["points"][0]] if force is not None else None
        rows.append(row)
    if not rows:
        return [], []
    numeric = [k for k in rows[0] if k != "Courbe" and not k.startswith("Évènement — ")] + list(columns.values())
    for row in rows:
        for column in numeric:
            row.setdefault(column, None)
    stats = [{"Statistique": label} for label in ("Moyenne", "Minimum", "Maximum", "Écart-type (échantillon)")]
    for column in numeric:
        values = [row[column] for row in rows if row[column] is not None]
        results = (mean(values) if values else None, min(values) if values else None,
                   max(values) if values else None, stdev(values) if len(values) > 1 else None)
        for row, value in zip(stats, results):
            row[column] = value
    return rows, stats
