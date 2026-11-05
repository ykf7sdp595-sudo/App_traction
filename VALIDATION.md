# Validation — phase 6

Compte rendu du 3 novembre 2026. Validation automatisée réalisée sur le poste
de développement ; réception métier et graphique encore à compléter.

## Environnement

Windows 11, Python 3.15.2, Streamlit 1.66.1, Plotly 6.9.0.
Deux dépendances directes inchangées. `pip check` : aucune incompatibilité détectée.
Le script `check_startup.py` a lancé un serveur Streamlit isolé, obtenu une réponse
HTTP 200 sur son contrôle de santé puis arrêté ce serveur. Aucune session
utilisateur existante n'a été arrêtée. Cela vérifie le démarrage, pas le rendu web.

## Résultats automatisés

25 tests unitaires et de parcours Streamlit couvrent notamment :

- lecture et nombres de points des trois exports, décimales et encodages ;
- rejet des valeurs manquantes, non finies et structures incorrectes ;
- conservation de l'ordre d'acquisition et des données sources ;
- précharge, zones, origines, filtre, plateaux, pics et rupture non forcée ;
- copie groupée, cibles incompatibles, statistiques connues et exclusions ;
- correction de 10 N, réinitialisation et annotations ;
- évènements libres : association à la courbe, création, masquage et suppression.

Le contrôle de charge ajoute un import mixte (fichier valide, fichier invalide,
fichier à un seul point) : le fichier invalide ne bloque pas les deux autres.
Le point unique est tracé avec un marqueur. Les empreintes SHA-256 des fichiers
source restent identiques après la validation.

Correction apportée : un champ numérique de traitement vidé est maintenant
refusé avec un message explicite au lieu d'entraîner une exception de type Python.
Le script d'installation Windows et le diagnostic du lanceur ont été ajoutés.

## Charge simulée

Copies en mémoire des trois fichiers fournis, sous des noms distincts. Ce ne sont
pas de nouvelles acquisitions ni une validation de représentativité physique.
AppTest exécute l'interface, les traitements et la construction du graphique,
mais ne lance pas de navigateur. Aucun sous-échantillonnage.

| Courbes | Points transmis | Premier affichage Python | Recalcul du titre | Recalcul avec statistiques | JSON graphique |
|---:|---:|---:|---:|---:|---:|
| 15 | 41 080 | 2,122 s | 0,406 s | 0,395 s | 0,997 Mo |
| 30 | 82 160 | 0,835 s | 0,875 s | 0,894 s | 1,987 Mo |
| 60 | 164 320 | 1,766 s | 2,508 s | 2,615 s | 3,965 Mo |

Une seule mesure par scénario, sans seuil contractuel de performance. Le premier
scénario inclut des initialisations ; les suivants bénéficient des imports/cache
déjà chauds. Ces chiffres ne mesurent ni la consommation GPU, ni le zoom, ni le
temps de rendu du navigateur. Ils ne sont pas une limite de capacité garantie.
Les statistiques de chaque campagne ont été vérifiées sur la moyenne attendue
des trois maxima de référence, avec un écart numérique inférieur à 1e-9 N.

## Références et limites métier

Les références vérifiées sont les valeurs numériques présentes dans les exports :
941 points TRA, 478 points CSV, 6 797 points TXT. Pour le TXT : maximum 173,65 N,
déplacement minimum −2,067 mm, temps de 3,839 à 10,635 s.
Elles concordent avec les ordres de grandeur annoncés par l'utilisateur pour sa
macro Excel. Le classeur et les résultats détaillés de la macro n'étant pas
disponibles, l'équivalence avec son traitement n'est pas démontrée.
Les tolérances métier et de détection restent à convenir sur des essais validés.

## Réception à faire dans le navigateur

Les échanges précédents ont confirmé le fonctionnement sur une dizaine de courbes
et le déplacement des étiquettes. Pour clore la réception de cette version :

1. Charger une campagne réelle de 30 à 60 courbes. Tester zoom, survol, masquage,
   changement de lot ; noter les lenteurs éventuelles et le nombre de points.
2. Sur un essai validé, comparer le maximum, son point source et les corrections
   avec la macro Excel. Conserver les paramètres exacts des deux traitements.
3. Sur deux courbes superposées, sélectionner la seconde pour un marqueur libre.
   Vérifier que le clic choisit son point, nommer l'évènement, déplacer son texte.
4. Ajouter un extremum et deux zones nommées. Exporter à 1600 × 900, échelle 1 :
   vérifier dimensions, unités, accents, couleurs et présence des textes.
5. Refaire à l'échelle 2 (3200 × 1800). Vérifier les positions des étiquettes après
   zoom et déplacement, sans chevauchement gênant ni texte rogné.
6. Copier le projet sans `.venv` ni `__pycache__` sur un autre poste Windows.
   Installer Python, exécuter `installer.bat`, puis `lancer.bat`. Charger un export
   et générer un PNG. Cette installation sur un second poste n'a pas encore été faite.

Noter pour chaque contrôle : fichier/campagne, réglages, résultat attendu,
résultat constaté et éventuel écart. La validation automatisée est terminée ;
la réception graphique, la comparaison métier et le second poste restent ouverts.

## Reproduire les contrôles

Depuis le dossier App_traction :

```powershell
.venv/Scripts/python.exe -m unittest -v
.venv/Scripts/python.exe validate_phase6.py
.venv/Scripts/python.exe check_startup.py
python -m pip --python .venv/Scripts/python.exe check
```

`validate_phase6.py` met à jour `validation_results.json` avec les mesures et les
empreintes. `check_startup.py` écrit `startup_validation.log`. Les tests ne créent
pas de fichiers d'essai supplémentaires et ne modifient pas les données originales.
