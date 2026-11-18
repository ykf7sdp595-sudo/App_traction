"""Traitements purs : listes en N/mm/s, sans dépendance ni mutation des sources."""

from dataclasses import dataclass
from math import fsum, isfinite


@dataclass(frozen=True)
class Settings:
    offset_mode: str = "Aucune"
    offset: float = 0.0
    reference: tuple[int, int] = (1, 1)
    preload: bool = False
    threshold: float = 0.0
    direction: str = "Positive"
    zero_time: bool = False
    zero_displacement: bool = False
    crop: bool = False
    interval: tuple[int, int] = (1, 1)
    smoothing: bool = False
    window: int = 5


def check_interval(interval, length):
    first, last = interval
    if not all(isinstance(v, int) for v in interval) or not 1 <= first <= last <= length:
        raise ValueError(f"La plage doit respecter 1 ≤ début ≤ fin ≤ {length}.")
    return first - 1, last  # Interface numérotée à partir de 1, bornes incluses.


def moving_average(values, window):
    """Moyenne centrée O(n), bords calculés sur les seuls points disponibles.

    La fenêtre est exprimée en points d'acquisition, pas en secondes/mm.
    Elle peut atténuer les pics : comparer systématiquement au brut.
    """
    if not isinstance(window, int) or window < 3 or window % 2 == 0 or window > len(values):
        raise ValueError("La fenêtre doit être impaire, ≥ 3 et ≤ au nombre de points retenus.")
    half = window // 2
    left, right = 0, half + 1
    total = fsum(values[left:right])
    result = []
    for i in range(len(values)):
        target_left, target_right = max(0, i - half), min(len(values), i + half + 1)
        while right < target_right:
            total += values[right]
            right += 1
        while left < target_left:
            total -= values[left]
            left += 1
        result.append(total / (right - left))
    return result


def process(signals: dict[str, list[float]], settings: Settings):
    """Offset → précharge → origines → filtre → zone (indices source).

    Retourne les signaux, numéros source et description des opérations.
    Les origines sont au premier point conservé après précharge, même si une
    zone ultérieure masque ce point. Le filtre précède la découpe de zone.
    """
    if not signals:
        raise ValueError("Aucune grandeur associée.")
    length = len(next(iter(signals.values())))
    if not length or any(len(v) != length for v in signals.values()):
        raise ValueError("Signaux vides ou de longueurs différentes.")
    data = {k: list(v) for k, v in signals.items()}
    notes = []
    force_required = settings.offset_mode != "Aucune" or settings.preload or settings.smoothing
    if force_required and "force" not in data:
        raise ValueError("Associer une colonne de force pour ce traitement.")
    if settings.offset_mode != "Aucune":
        if settings.offset_mode == "Moyenne d'une zone":
            a, b = check_interval(settings.reference, length)
            offset = fsum(data["force"][a:b]) / (b - a)
        elif settings.offset_mode == "Valeur saisie":
            offset = settings.offset
        else:
            raise ValueError("Mode de correction de force inconnu.")
        if not isinstance(offset, (int, float)) or not isfinite(offset):
            raise ValueError("La correction de force doit être finie.")
        data["force"] = [v - offset for v in data["force"]]
        notes.append(f"Force − ({offset:.6g} N)")
    start = 0
    if settings.preload:
        if not isinstance(settings.threshold, (int, float)) or not isfinite(settings.threshold) or settings.threshold <= 0:
            raise ValueError("Le seuil de précharge doit être strictement positif et fini.")
        transform = {"Positive": lambda v: v, "Négative": lambda v: -v, "Valeur absolue": abs}[settings.direction]
        start = next((i for i, v in enumerate(data["force"]) if transform(v) >= settings.threshold), None)
        if start is None:
            raise ValueError("Seuil de précharge jamais atteint après correction de force.")
        notes.append(f"Précharge {settings.direction.lower()} {settings.threshold:g} N : début au point {start + 1}")
    data = {k: v[start:] for k, v in data.items()}
    for quantity, enabled in (("time", settings.zero_time), ("displacement", settings.zero_displacement)):
        if enabled:
            if quantity not in data:
                raise ValueError(f"Grandeur absente pour la remise à zéro : {quantity}.")
            origin = data[quantity][0]
            data[quantity] = [v - origin for v in data[quantity]]
            notes.append(f"Origine {'temps' if quantity == 'time' else 'déplacement'} au point {start + 1}")
    if settings.smoothing:
        data["force"] = moving_average(data["force"], settings.window)
        notes.append(f"Force filtrée : moyenne centrée sur {settings.window} points (bords réduits)")
    end = length
    if settings.crop:
        first, end = check_interval(settings.interval, length)
        first = max(first, start)
        if first >= end:
            raise ValueError("La zone sélectionnée est entièrement avant le début de précharge.")
        data = {k: v[first - start:end - start] for k, v in data.items()}
        start = first
        notes.append(f"Zone source : points {start + 1} à {end}")
    if any(not isfinite(v) for values in data.values() for v in values):
        raise ValueError("Valeur non finie après traitement ; vérifier les unités et paramètres.")
    return data, list(range(start + 1, end + 1)), notes
