"""Analyse de force sans dépendances. Tous les indices retournés sont à base zéro."""

from bisect import bisect_left, insort
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Peak:
    index: int
    force: float
    relief: float


def extreme(values, mode):
    """Premier point en cas d'égalité. Aucun positif/négatif : None."""
    if mode == "Maximum positif":
        indices = [i for i, v in enumerate(values) if v > 0]
        return max(indices, key=lambda i: values[i]) if indices else None
    if mode == "Minimum négatif":
        indices = [i for i, v in enumerate(values) if v < 0]
        return min(indices, key=lambda i: values[i]) if indices else None
    return max(range(len(values)), key=lambda i: abs(values[i])) if values else None


def _positive_peaks(values):
    # Compresser les plateaux pour choisir leur premier point de façon déterministe.
    runs = []
    for i, value in enumerate(values):
        if not runs or runs[-1][1] != value:
            runs.append((i, value))
    result = []
    for j in range(1, len(runs) - 1):
        index, height = runs[j]
        if height <= 0 or not (runs[j - 1][1] < height > runs[j + 1][1]):
            continue
        left, right = j - 1, j + 1
        while left > 0 and runs[left - 1][1] < runs[left][1]:
            left -= 1
        while right < len(runs) - 1 and runs[right + 1][1] < runs[right][1]:
            right += 1
        # Relief LOCAL : hauteur au-dessus de la plus haute des deux vallées voisines.
        relief = min(height - runs[left][1], height - runs[right][1])
        result.append((index, relief))
    return result


def detect_peaks(values, polarity="Les deux", relief=0.1, distance=10):
    """Pics intérieurs, relief local en N ; séparation en points d'acquisition.

    Les extrémités ne sont pas des pics. Les candidats les plus marqués sont
    prioritaires pour l'espacement, puis le premier point en cas d'égalité.
    Ce relief local n'est pas la proéminence topographique globale de SciPy.
    """
    if relief < 0 or distance < 1:
        raise ValueError("Relief ≥ 0 et espacement ≥ 1 requis.")
    candidates = []
    if polarity in ("Positifs", "Les deux"):
        candidates += [Peak(i, values[i], r) for i, r in _positive_peaks(values)]
    if polarity in ("Négatifs", "Les deux"):
        candidates += [Peak(i, values[i], r) for i, r in _positive_peaks([-v for v in values])]
    selected, indices = [], []
    for peak in sorted(candidates, key=lambda p: (-p.relief, p.index)):
        if peak.relief < relief:
            continue
        pos = bisect_left(indices, peak.index)
        if pos and peak.index - indices[pos - 1] < distance:
            continue
        if pos < len(indices) and indices[pos] - peak.index < distance:
            continue
        insort(indices, peak.index)
        selected.append(peak)
    return sorted(selected, key=lambda p: p.index)


def rupture_candidate(values, drop=10.0, window=20, minimum=10.0, direction="Positive"):
    """Premier recul d'au moins drop N dans window points, après minimum N.

    Renvoie (sommet avant chute, point de franchissement). La file monotone
    permet un passage O(n). Une décharge n'est PAS une rupture physique prouvée.
    """
    if drop <= 0 or window < 1 or minimum < 0:
        raise ValueError("Chute > 0, fenêtre ≥ 1 et effort minimal ≥ 0 requis.")
    oriented = [abs(v) if direction == "Valeur absolue" else -v if direction == "Négative" else v for v in values]
    previous = deque()
    for i, value in enumerate(oriented):
        while previous and previous[0] < i - window:
            previous.popleft()
        if previous:
            peak = previous[0]
            if oriented[peak] >= minimum and oriented[peak] - value >= drop:
                return peak, i
        while previous and oriented[previous[-1]] < value:
            previous.pop()
        previous.append(i)
    return None
