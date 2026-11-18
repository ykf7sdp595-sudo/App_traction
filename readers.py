"""Lecture des exports machine, sans dépendance externe ni modification des sources."""

from dataclasses import dataclass
import math


class ImportErrorDetail(ValueError):
    """Erreur de fichier présentable directement à l'utilisateur."""


@dataclass(frozen=True)
class Measurement:
    headers: tuple[str, ...]
    rows: tuple[tuple[float, ...], ...]
    profile: str
    encoding: str
    warnings: tuple[str, ...]


def read_measurement(content: bytes) -> Measurement:
    """Reconnaît les deux structures validées. Refuse les lignes malformées.

    Un refus explicite évite de relier artificiellement des points de part et
    d'autre d'une donnée manquante. Les lignes vides seules sont ignorées.
    """
    if not content:
        raise ImportErrorDetail("Fichier vide.")
    encodings = ("utf-16",) if content.startswith((b"\xff\xfe", b"\xfe\xff")) else ("utf-8-sig", "cp1252")
    for encoding in encodings:
        try:
            source = content.decode(encoding)
            break
        except UnicodeError:
            continue
    else:
        raise ImportErrorDetail("Encodage illisible : utiliser UTF-8 ou Windows-1252.")
    lines = [(i, line.strip()) for i, line in enumerate(source.splitlines(), 1) if line.strip()]
    if not lines:
        raise ImportErrorDetail("Le fichier ne contient aucune donnée.")
    first = lines[0][1]
    if [v.strip().casefold() for v in first.split(";")] == ["allongement", "force standard"]:
        profile = "Allongement / Force standard"
        headers = ("Allongement", "Force standard")
        data_lines = lines[1:]
        width = 2
    elif len(first.split("\t")) == 2 and all(len(g.split(";")) == 3 for g in first.split("\t")):
        profile = "TXT à deux groupes (association provisoire)"
        headers = ("Temps", "Déplacement", "Force", "Colonne 4", "Colonne 5", "Colonne 6")
        data_lines = lines
        width = 6
    else:
        raise ImportErrorDetail("Format inconnu. Attendu : Allongement;Force standard ou deux groupes temps;déplacement;force séparés par une tabulation.")
    rows = []
    errors = []
    for number, line in data_lines:
        groups = line.split("\t")
        cells = line.replace("\t", ";").split(";")
        try:
            if len(cells) != width or (width == 6 and (len(groups) != 2 or any(len(g.split(";")) != 3 for g in groups))):
                raise ValueError("nombre de colonnes incorrect")
            values = tuple(float(v.strip().replace(",", ".")) for v in cells)
            if not all(math.isfinite(v) for v in values):
                raise ValueError("valeur non finie")
            rows.append(values)
        except ValueError:
            errors.append(number)
    if errors:
        sample = ", ".join(map(str, errors[:8]))
        raise ImportErrorDetail(f"{len(errors)} ligne(s) invalide(s), dont : {sample}. Corriger les valeurs manquantes, non numériques ou les colonnes ; aucun point n'a été supprimé.")
    if not rows:
        raise ImportErrorDetail("En-tête présent, mais aucune mesure.")
    warnings = ["Unités absentes du fichier : N, mm et s appliqués par défaut, modifiables ci-dessous."]
    if len(rows) == 1:
        warnings.append("Un seul point : affichage par marqueur.")
    if width == 6:
        warnings.append("Colonnes 1–3 sélectionnées par défaut. La signification des colonnes 4–6 reste à confirmer ; elles sont conservées dans l'aperçu.")
    return Measurement(headers, tuple(rows), profile, encoding, tuple(warnings))


# Les facteurs convertissent vers les unités communes du graphique.
UNITS = {"force": {"N": 1.0, "kN": 1000.0, "mN": 0.001},
         "displacement": {"mm": 1.0, "m": 1000.0, "µm": 0.001},
         "time": {"s": 1.0, "ms": 0.001, "min": 60.0}}


def column_values(measurement: Measurement, column: int, quantity: str, unit: str) -> list[float]:
    factor = UNITS[quantity][unit]
    return [row[column] * factor for row in measurement.rows]
