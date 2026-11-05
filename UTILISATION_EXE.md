# Application Windows autonome

Le fichier à transmettre est `dist/App_traction.exe`. Il contient Python,
Streamlit, Plotly et les modules de l'application. Aucun Python ni installation
de dépendances n'est nécessaire sur le poste destinataire (Windows 64 bits).
Un navigateur récent, par exemple Edge, est nécessaire.

1. Copier `App_traction.exe` dans un dossier local du poste destinataire.
2. Double-cliquer dessus. Le premier démarrage peut prendre quelques dizaines
   de secondes, le temps d'extraire les composants dans le dossier temporaire.
3. Le navigateur s'ouvre sur l'application. Si nécessaire, copier l'adresse
   `http://127.0.0.1:...` affichée dans la fenêtre de lancement.
4. Charger les fichiers de mesure depuis le panneau gauche.
5. Pour arrêter l'application, fermer la fenêtre de lancement ou utiliser
   Ctrl+C dans cette fenêtre. Fermer uniquement l'onglet ne coupe pas le serveur.

L'application fonctionne localement ; le serveur écoute uniquement sur le poste.
Les fichiers d'exemple ne sont pas intégrés dans l'exécutable. Les réglages et
les fichiers chargés ne sont pas conservés après l'arrêt.

## Reconstruire après modification du projet

Sur le poste de développement, avec Python et l'environnement `.venv` installé,
exécuter `construire_exe.bat`. Une connexion est nécessaire si les dépendances
de construction ne sont pas déjà disponibles. Le résultat remplace
`dist/App_traction.exe` ; le dossier `build` est seulement intermédiaire.

La construction utilise PyInstaller et `App_traction.spec`. Le script
`validate_exe.py` vérifie le véritable exécutable dans un dossier temporaire,
avec un PATH sans Python : démarrage, import des trois formats d'exemple,
graphique, légende et export PNG. Il utilise Edge en mode sans fenêtre.

Un essai sur un second poste Windows sans Python reste recommandé : la
validation locale ne reproduit pas les politiques de sécurité de chaque poste.

## Validation du 5 novembre 2026

- Exécutable unique généré : 100 276 590 octets (environ 100 Mo).
- Copie isolée de l'exécutable, sans dossier du projet et sans Python dans le PATH : démarrage réussi.
- Import réel des exemples TRA, CSV et TXT : 941, 478 et 6 797 points.
- Affichage des trois courbes, masquage/réaffichage par légende et PNG 1600 × 900 : réussis.
- Suite existante : 27 tests réussis.
