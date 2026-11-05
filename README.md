# Courbes de traction — phases 1 à 5, validation phase 6

Application locale Streamlit : import CSV/TRA/TXT, superposition, aperçu,
unités, couleurs, légendes, limites d'axes et export PNG.
Corrections, précharge, sélection de zone et filtre sont disponibles par courbe.
Maxima, pics, rupture candidate et annotations physiques sont disponibles.
Les lots, traitements groupés et statistiques de forces sont disponibles.

## Sauvegarde GitHub de la version testée

Ce dépôt sauvegarde les sources de la version testée le 5 novembre 2026.
Les fichiers de mesure, captures, résultats générés et exécutables ne sont pas
publiés. L'exécutable peut être reconstruit avec `construire_exe.bat`.
Les tests utilisant les exemples TRA/CSV/TXT nécessitent ces fichiers locaux,
absents du dépôt ; les résultats de validation documentés ont été obtenus sur
le poste de développement avec ces exemples.

## Version Windows sans Python

Double-cliquer sur **`dist/App_traction.exe`**. Ce fichier peut être copié seul
sur un poste Windows 64 bits : Python et les dépendances sont embarqués.
L'application s'ouvre dans le navigateur. Fermer la fenêtre de lancement pour
l'arrêter. Voir [le mode d'emploi de l'exécutable](UTILISATION_EXE.md).

Pour reconstruire après une modification, lancer `construire_exe.bat` sur le
poste de développement.

## Installation sous Windows avec Python (sources)

Sur un nouveau poste, copier le dossier **sans `.venv` ni `__pycache__`** :
un environnement virtuel ne doit pas être déplacé entre postes. Installer Python
(version vérifiée ici : 3.15.2), puis lancer `installer.bat`. Une connexion réseau
est nécessaire pour l'installation ; les analyses fonctionnent ensuite localement.
L'installation sur un second poste reste à vérifier.

Équivalent dans un terminal ouvert dans ce dossier :

```powershell
python -m venv .venv
python -m pip --python .venv/Scripts/python.exe install -r requirements.txt
.venv/Scripts/python.exe -m streamlit run app.py --server.address localhost --browser.gatherUsageStats false
```

Après installation, double-cliquer sur `lancer.bat`. Fermer le terminal arrête
l'application. Les fichiers chargés et les réglages ne sont pas sauvegardés entre sessions.
Les fichiers source ne sont jamais écrits. L'ancien fichier vide `App_traction`
est conservé ; le point d'entrée exécutable est désormais `app.py`.

## Utilisation

1. Charger vos fichiers CSV, ASCII ou TXT dans le panneau gauche (extensions `.csv`, `.TRA`, `.txt`).
2. Choisir l'onglet de la courbe : il regroupe sa présentation, ses données,
   ses traitements et son analyse dans trois sections repliables : « Présentation
   et données », « Traitements de la courbe » et « Analyse et annotations ».
   Le graphique commun apparaît au-dessus des onglets, avec le nombre de courbes
   et de points affichés. Les lots et les évènements libres restent sous les onglets.
3. Choisir les axes dans le panneau gauche. Une courbe sans temps ne peut pas
   apparaître sur un graphique temporel : aucune fréquence n'est inventée.
4. Régler les titres et limites, puis zoomer si nécessaire.
5. Choisir les dimensions PNG et cliquer sur l'appareil photo en haut du graphique.
   L'image reprend le zoom et la visibilité courants. L'échelle 2 double les
   dimensions en pixels ; aucun DPI d'impression particulier n'est imposé.

Le graphique et les PNG utilisent systématiquement un fond blanc (zone de tracé,
marges, légende et étiquettes), avec des textes et axes sombres, quel que soit
le thème de l'interface. Les courbes, marqueurs, flèches et bordures gardent leurs couleurs.

« Premiers pas » présente le parcours général. Dans le panneau gauche, les
sections « Cadrage et dimensions » et « Exporter une image PNG » se déplient
uniquement lorsque ces réglages sont utiles. Le bouton principal « Appliquer à
cette courbe » valide les traitements ; un message signale les modifications
encore en attente. Replier une section conserve ses réglages.

Le résumé suit les cases « Afficher », le lot choisi **et les clics sur la légende**.
Un clic masque ou réaffiche la courbe entière, avec ses annotations ; le double-clic
n'isole plus une courbe. Recocher « Afficher » rétablit également sa visibilité.
Les extrêmes du tableau sont ceux du signal après traitements et sélection de
zone, indépendamment du zoom.

Le résumé contient le nom de la courbe, le minimum et le maximum de la grandeur Y.
Les anciennes colonnes Signal, Points, X min et X max ont été supprimées.
Les évènements libres visibles ajoutent chacun une colonne de **force en N**, même
si le graphique représente le déplacement en fonction du temps. La force est prise
sur le signal affiché, avec ses corrections et son éventuel filtrage, au point source
du marqueur. Un marqueur masqué ou hors de la zone retenue n'entre pas dans le tableau.

Un même libellé d'évènement partage une colonne entre courbes. Deux marqueurs de
même nom sur une courbe sont distingués par leur ordre de création ([2], [3]…).
Nommer les évènements de façon cohérente pour comparer la même phase physique.
Les cellules restent vides lorsque la courbe n'a pas ce marqueur. Une colonne
disparaît si aucune courbe visible ne porte l'évènement correspondant.

Sous le résumé, moyenne, minimum, maximum et écart-type d'échantillon sont calculés
pour chaque colonne numérique sur les seules cellules renseignées. Avec une seule
valeur, l'écart-type reste vide. Ces statistiques de visibilité sont distinctes des
statistiques par lot, dont la case « Inclure dans les statistiques » conserve son rôle.

## Traitements (phase 3)

Dans les réglages de chaque fichier, renseigner le formulaire puis cliquer sur
« Appliquer à cette courbe ». Aucun traitement n'est activé par défaut.
Choisir d'abord le mode ou cocher le traitement pour activer ses champs.
Par exemple : « Correction de force » → « Valeur saisie », saisir 10 N,
puis « Appliquer à cette courbe ». Les réglages en cours de saisie sont distincts
des réglages validés : le graphique reste inchangé jusqu'au clic sur Appliquer.
Les champs des traitements désactivés sont grisés.
Les réglages s'appliquent uniquement à cette courbe, dans cet ordre :

1. Correction de force : soustraction d'une valeur en N ou de la moyenne d'une
   plage de points source, avant toute autre opération.
2. Précharge : conserver à partir du premier point atteignant le seuil sur la
   force corrigée. Sens positif, négatif ou valeur absolue. Le point est inclus ;
   le seuil n'est jamais soustrait de la force. Aucun filtrage préalable du seuil.
3. Origines : temps et/ou déplacement à zéro au début utile (après précharge).
4. Filtre de force : moyenne centrée à fenêtre impaire en points d'acquisition,
   calculée en temps linéaire. Aux bords, moyenne des points disponibles. Les
   autres grandeurs restent intactes. Ce filtre peut atténuer les pics ; pour des
   pas de temps irréguliers il ne correspond pas à une fenêtre temporelle fixe.
5. Zone : bornes inclusives exprimées en numéros de points source (à partir de 1).
   L'intersection avec la précharge est conservée ; une intersection vide est
   refusée. Les origines et le filtre ne sont pas recalculés sur cette zone.

Le numéro du point source apparaît au survol pour repérer les bornes à saisir,
y compris sur une branche retour. La sélection se fait par les champs numériques,
pas par le rectangle de zoom. La comparaison au brut, activable dans le panneau
gauche, affiche le signal original complet en pointillés et le signal traité en
trait plein : le brut conserve ses origines et n'est pas réaligné artificiellement.

Un résumé des opérations est affiché au-dessus du graphique. Un réglage invalide
exclut explicitement cette courbe du graphique jusqu'à correction ou réinitialisation,
sans bloquer les autres. « Réinitialiser les traitements » restaure les données brutes
et les paramètres par défaut tout en conservant nom, couleur, unités et colonnes.

Les changements d'unités et de colonnes réappliquent les réglages existants ; les
valeurs de correction et précharge restent exprimées en N. Vérifier ces réglages
après un changement d'association. Les traitements restent temporaires à la session.

## Analyse et annotations (phase 4)

Dans l'onglet de la courbe, descendre à « Analyse et annotations »
et cocher « Activer l'analyse et les annotations ». Ces réglages réagissent
immédiatement, sans bouton Appliquer supplémentaire. Ils concernent uniquement
les courbes visibles, compatibles avec les axes et dont les traitements sont valides.

La base de calcul est par défaut le signal **sans filtrage**, avec les corrections,
la précharge et la zone déjà appliquées. « Analyser le signal filtré » permet
explicitement de changer cette base si un filtre est actif. Les marqueurs portent
les valeurs du signal analysé : ils peuvent s'écarter de la ligne filtrée affichée.
Le tableau récapitulatif général conserve les extrêmes du signal affiché ; les
tableaux d'analyse indiquent ceux de la base choisie. Tout reste dans les unités N/mm/s.

- **Extrême** : maximum strictement positif, minimum strictement négatif ou
  maximum en valeur absolue (la force signée reste indiquée). Le premier point
  est retenu en cas d'égalité, y compris un plateau. Les extrémités sont admissibles.
- **Pics** : extrema intérieurs, positifs, négatifs ou les deux. Un plateau donne
  son premier point. Le relief local minimal est exprimé en N ; il mesure la
  différence avec la plus haute des deux vallées adjacentes, après inversion de
  signe pour les pics négatifs. Ce n'est pas une proéminence topographique globale.
  L'espacement est en points d'acquisition, les candidats de plus grand relief
  étant prioritaires. Les deux signes partagent le même espacement.
- Tous les pics détectés apparaissent dans le tableau. Choisir ceux à dessiner
  dans « Pics à afficher » (dix premiers sélectionnés initialement). Pour corriger
  un pic, le désélectionner puis saisir le point voulu dans « Pics manuels ».
  Les marqueurs manuels sont explicitement identifiés et ne sont pas requalifiés
  comme extrema automatiquement détectés.
- **Rupture candidate** : première baisse de force d'au moins la chute demandée,
  sur au plus la fenêtre choisie, depuis un effort atteignant le minimum préalable.
  Le marqueur désigne le sommet avant la chute, pas le point de franchissement.
  Une décharge ou un désaccouplement peut satisfaire ces critères : l'interprétation
  physique nécessite la case « Confirmer l'évènement comme rupture ».
  Un point manuel peut être choisi, même en l'absence de candidat automatique.
  Toute modification des données analysées, critères ou point choisi invalide
  la confirmation précédente. Aucun point final n'est assimilé automatiquement à
  une rupture. La détection n'utilise pas encore de critère de maintien de la chute.
- **Zones physiques** : ajouter de 0 à 20 zones, nommer l'évènement, saisir les
  points source de début/fin et choisir une couleur. La portion de courbe est
  surlignée, ce qui distingue l'aller et le retour, même aux mêmes abscisses.
  Les zones n'affectent ni les traitements ni les détections. Elles sont coupées
  à la portion actuellement visible ; une zone entièrement hors de cette portion
  est signalée. Les zones peuvent se chevaucher.

Les textes des marqueurs et les zones sont masquables pour préparer l'export.
Les étiquettes d'extrema, pics, rupture et zones se déplacent en glissant leur
texte à la souris. La flèche reste ancrée à la mesure : le déplacement ne modifie
aucune valeur. L'option « Déplacer les étiquettes à la souris » permet de verrouiller
le placement. « Réinitialiser la position des étiquettes » restaure les positions
initiales. Les textes ont un fond blanc et une bordure pour rester lisibles.
Le placement reste dans le navigateur, sans sauvegarde entre sessions ; il est
réinitialisé quand la liste des annotations, leur texte, leurs points ou les axes
changent. Terminer les réglages d'analyse avant le placement final pour le PNG.
Il s'agit d'un placement manuel, sans algorithme d'évitement des chevauchements.
L'appareil photo inclut les marqueurs, segments colorés et noms de zone affichés.
Les annotations restent limitées à la session ; masquer une courbe ou désactiver
l'analyse peut réinitialiser ses widgets d'analyse à leur prochaine apparition.
« Réinitialiser les traitements » ne supprime pas les zones physiques.

## Marqueurs d'évènements libres

Ouvrir « Marqueurs d'évènements libres », activer le placement et choisir une
courbe. Avec « Sélectionner le point par clic », de petits points apparaissent
sur cette courbe. Choisir le nom et la couleur, puis cliquer sur un point :
le marqueur apparaît immédiatement, sans validation. Un message au-dessus du
graphique confirme le placement et un bouton permet d'annuler le dernier ajout.
Un nouveau clic au même point avec le même nom ne crée pas de doublon.
Pour saisir le numéro source directement, désactiver la sélection par clic,
puis utiliser « Ajouter ce marqueur ».
Le clic sur une autre courbe, un signal brut de comparaison ou une annotation
est ignoré. Zoomer aide à distinguer les courbes qui se superposent.

Les évènements libres n'ont aucune condition d'extremum. Ils sont dessinés en
étoile avec une étiquette déplaçable et sont inclus dans le PNG. Sous « évènements
enregistrés », modifier le libellé, le point source, la couleur, la visibilité
ou supprimer un marqueur. Désactiver le mode placement conserve les marqueurs.

Ils restent attachés au point source et suivent les traitements de la courbe
affichée. Si une précharge ou une zone exclut ce point, le marqueur reste mémorisé
mais n'est pas dessiné ; il réapparaît lorsque le point est de nouveau visible.
Le passage à un autre lot ou le masquage de la courbe ne supprime pas les évènements.
Ils sont conservés pendant la session uniquement, sans modifier les calculs.

## Lots et statistiques (phase 5)

Chaque fichier appartient par défaut à « Lot 1 ». Le champ « Lot » permet de
renommer son groupe ; une valeur vide devient « Sans lot ». Pour une affectation
collective, ouvrir « Lots, traitements groupés et statistiques », sélectionner les
courbes cibles, saisir le nom du lot puis cliquer sur « Affecter le lot ».
Le sélecteur « Lot à afficher et analyser » limite le graphique et les tableaux
au groupe choisi. « Tous les lots » affiche les courbes ensemble, mais calcule
toujours une synthèse statistique distincte pour chaque lot.

Pour traiter une campagne :

1. Régler et **appliquer** les traitements d'une courbe modèle.
2. Choisir cette courbe dans « Courbe modèle pour les traitements ».
3. Sélectionner les courbes cibles (elles peuvent appartenir à plusieurs lots).
4. Cliquer sur « Appliquer les traitements aux courbes cibles ».
5. Lire le compte rendu par fichier. Une cible incompatible conserve ses anciens
   paramètres : aucune adaptation ni suppression silencieuse n'est effectuée.

Les paramètres copiés concernent uniquement les traitements : pas les colonnes,
unités, couleurs ou annotations. Les plages en points sont copiées telles quelles
lorsqu'elles sont actives ; il faut donc comparer des acquisitions compatibles.
Les champs inactifs sont adaptés à la longueur du fichier sans changer le traitement.
Chaque courbe reste modifiable individuellement après la copie.

Cocher « Afficher les statistiques des forces », puis choisir une convention
commune : maximum positif, minimum négatif (valeur signée) ou maximum absolu
(amplitude positive). Un fichier contribue une seule valeur, même si le TXT
contient deux groupes de colonnes. La base est sans filtrage par défaut, après
correction, précharge et sélection de zone ; l'utilisation des filtres validés est
une option explicite. Les réglages individuels restent autorisés et sont indiqués
dans le détail pour vérifier la comparabilité des essais.

La synthèse indique l'effectif total, retenu et exclu, la moyenne, médiane,
l'écart-type d'échantillon (diviseur n − 1), et les extrêmes. Pour une seule courbe,
l'écart-type reste vide ; pour un lot sans résultat valide, les statistiques sont
vides et les exclusions explicites. Une courbe sans force du signe demandé,
sans colonne force ou avec traitement impossible n'entre pas dans les calculs.

« Inclure dans les statistiques » est indépendant de « Afficher » et du masquage
dans la légende. Changer les axes du graphique n'exclut pas une force valide.
Les fichiers refusés à l'import restent signalés à l'import ; ils n'appartiennent
pas aux lots chargés et ne figurent pas dans leur effectif. Les statistiques sont
consultables dans l'interface ; elles ne sont pas ajoutées au PNG du graphique.

## Formats et choix de lecture

- TRA/CSV : en-tête `Allongement;Force standard`, nombres scientifiques,
  décimales point ou virgule. Pas de temps disponible.
- TXT : deux triplets séparés par une tabulation. Par défaut, colonnes 1/2/3 =
  temps/déplacement/force. Les six colonnes restent consultables et sélectionnables.
  L'interprétation des colonnes 4/5/6 comme données brutes reste provisoire.
- N, mm, s par défaut. Conversion possible depuis kN, mN, m, µm, ms et min.
- Aucun tri ni traitement automatique ; les transformations sont activées explicitement.
- Les lignes vides sont ignorées ; les lignes invalides provoquent un refus du
  fichier avec leurs numéros, sans bloquer les autres fichiers.
- Formats inconnus refusés explicitement : ce n'est pas un importeur CSV universel.

## Comprendre et maintenir le code

- `readers.py` : modèle `Measurement`, reconnaissance des deux structures,
  validation des nombres et conversion des unités. Aucune dépendance externe.
- `app.py` : interface et graphique. `cached_read` évite de relire les données
  lors d'un changement de présentation. Les paramètres sont associés au nom et
  au contenu du fichier pour rester stables lors d'un ajout ou retrait.
- `test_readers.py` : cas de référence et erreurs de lecture, via `unittest`.
- `processing.py` : paramètres immuables et calculs purs, sans Streamlit.
- `treatment_ui.py` : formulaire et réinitialisation des paramètres par courbe.
- `test_processing.py` : ordre des traitements, seuils, filtre et absence de mutation.
- `analysis.py` : extrema, pics à relief local et rupture candidate, sans dépendances.
- `analysis_ui.py` : paramètres d'analyse, choix des marqueurs et zones Plotly.
- `test_analysis.py` : plateaux, signes, espacement, chute et absence de rupture.
- `batches.py` : statistiques des forces par lot, sans dépendance externe.
- `batch_ui.py` : affectation des lots et copie contrôlée des paramètres.
- `events_ui.py` : sélection par clic, marqueurs libres et édition par courbe.
- `chart_ui.py` : graphique Plotly local avec remontée des clics de légende à Streamlit.
- `curve_summary.py` : résumé des courbes visibles et statistiques par colonne.
- `test_batches.py` : valeurs statistiques de référence, exclusions et conventions.
- `test_interface.py` : parcours Streamlit avec les exemples, les trois vues
  et les paramètres PNG, sans navigateur.
- `requirements.txt` : seulement Streamlit et Plotly en dépendances directes
  (ils installent leurs propres dépendances transitives).

Pour ajouter un format, ajouter sa reconnaissance dans `read_measurement`,
retourner un `Measurement`, adapter les associations par défaut dans `app.py`
et ajouter un cas de test. Les points restent dans l'ordre d'acquisition.

Plotly utilise WebGL pour les courbes et le navigateur pour exporter le PNG :
pas de Kaleido, Chrome supplémentaire, SciPy ou traitement pandas dans notre code.
Tous les points sont transmis, sans sous-échantillonnage. La capacité réelle
dépend de la mémoire et du navigateur ; valider les grosses campagnes sur le poste cible.

## Vérification

```powershell
.venv/Scripts/python.exe -m unittest -v
```

Références : 941 points TRA, 478 points CSV, 6 797 points TXT.
TXT : maximum 173,65 N, déplacement minimum −2,067 mm,
temps 3,839 à 10,635 s (durée enregistrée 6,796 s).

Contrôle manuel : charger les exemples, changer les trois vues, masquer et renommer
une courbe, modifier une unité puis revenir à l'unité initiale, zoomer et exporter
un PNG. Contrôler ses dimensions, sa légende et son cadrage.

Documentation de l'export navigateur : https://plotly.com/python/configuration-options/

## Validation et prise en main

Le bilan, les limites et le parcours de réception sont dans [VALIDATION.md](VALIDATION.md).
Les mesures de charge reproductibles sont dans `validation_results.json`.
`validate_phase6.py` vérifie 15, 30 et 60 courbes simulées ; `check_startup.py`
teste le lancement sur un port isolé puis arrête son propre serveur.

Pour commencer : charger vos fichiers, sélectionner les axes, appliquer les
traitements sur une courbe, puis éventuellement les copier vers un lot. Vérifier
les valeurs et exclusions avant d'ajouter les annotations. Régler les dimensions
du PNG, placer les étiquettes en dernier, puis utiliser l'appareil photo.

En cas de problème de lancement :

- Environnement absent ou modules manquants : exécuter `installer.bat`.
- Python introuvable : installer Python et rouvrir le terminal.
- Échec réseau lors de l'installation : vérifier la connexion/proxy de l'entreprise.
- Port occupé : garder l'application déjà ouverte ou lancer avec `--server.port 8502`.
- Pour arrêter l'application : Ctrl+C dans son terminal. Ne pas compter sur la
  fermeture du navigateur pour conserver la session ; aucun enregistrement de
  session n'est disponible à ce stade.
