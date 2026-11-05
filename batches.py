"""Calcul des statistiques de lots, indépendant de l'interface."""

from dataclasses import replace
from statistics import mean, median, stdev

from analysis import extreme
from processing import process
from readers import column_values


def curve_signals(curve):
    if not curve["valid"]:
        raise ValueError("Association des colonnes invalide")
    return {q: column_values(curve["data"], col, q, curve["units"][q])
            for q, col in curve["mapping"].items() if col is not None}


def lot_statistics(curves, mode="Maximum positif", filtered=False):
    """Un résultat par courbe, après traitements ; les lots ne sont jamais mélangés.

    Le maximum absolu est une amplitude positive ; le minimum négatif conserve
    son signe. Une courbe sans valeur du signe demandé est exclue explicitement.
    La sélection statistique est indépendante de la visibilité du graphique.
    """
    details, groups = [], {}
    for curve in curves:
        lot = curve["lot"]
        groups.setdefault(lot, [])
        row = {"Lot": lot, "Courbe": curve["label"], "Fichier": curve["name"],
               "Valeur (N)": None, "Point source": None, "Statut": "Incluse"}
        try:
            if not curve["include_stats"]:
                raise ValueError("Exclusion manuelle")
            signals = curve_signals(curve)
            if "force" not in signals:
                raise ValueError("Force absente")
            settings = curve["settings"] if filtered else replace(curve["settings"], smoothing=False)
            data, points, notes = process(signals, settings)
            index = extreme(data["force"], mode)
            if index is None:
                raise ValueError("Aucune force du signe demandé")
            value = data["force"][index]
            if mode == "Maximum absolu":
                value = abs(value)
            row.update({"Valeur (N)": value, "Point source": points[index],
                        "Traitements": "; ".join(notes) or "Aucun"})
            groups[lot].append(value)
        except ValueError as error:
            row["Statut"] = str(error)
        details.append(row)
    summary = []
    for lot, values in groups.items():
        total = sum(row["Lot"] == lot for row in details)
        summary.append({"Lot": lot, "Courbes": total, "Retenues": len(values),
                        "Exclues": total - len(values),
                        "Moyenne (N)": mean(values) if values else None,
                        "Médiane (N)": median(values) if values else None,
                        "Écart-type échantillon (N)": stdev(values) if len(values) > 1 else None,
                        "Minimum (N)": min(values) if values else None,
                        "Maximum (N)": max(values) if values else None})
    return details, summary
