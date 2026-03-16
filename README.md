# Rogne

Petit outil Python pour rogner une image, ou une série d'images, en carré via une interface graphique simple.

Le script affiche chaque image dans une fenêtre de prévisualisation. Il suffit de déplacer la souris pour positionner le carré, puis de cliquer pour valider le cadrage.

## Fonctionnalités

- rognage carré image par image
- traitement d'une image unique ou d'un dossier complet
- prévisualisation interactive avant enregistrement
- sortie automatique dans un dossier dédié
- prise en charge des formats JPG, JPEG, PNG, BMP, WEBP, TIF et TIFF

## Prérequis

- Python 3.10 ou plus récent
- Tkinter disponible dans l'installation Python

## Installation

1. Cloner le dépôt.
2. Installer les dépendances.

```bash
pip install -r requirements.txt
```

## Lancement

### Mode interface graphique

Le mode graphique s'ouvre par défaut si aucun argument n'est fourni.

```bash
python rogne_images.py
```

Vous pouvez aussi le forcer explicitement :

```bash
python rogne_images.py --gui
```

### Mode ligne de commande

Le script accepte en entrée soit une image, soit un dossier.

```bash
python rogne_images.py "chemin/vers/image.jpg"
```

```bash
python rogne_images.py "chemin/vers/dossier" -o "sortie"
```

## Aide disponible

```bash
python rogne_images.py --help
```

Options disponibles :

- `source` : chemin vers une image ou un dossier contenant des images
- `-o`, `--output` : dossier de sortie, par défaut `./sortie`
- `--gui` : ouvre l'interface graphique

## Utilisation de la fenêtre de rognage

- déplacer la souris pour positionner le carré
- clic gauche pour valider
- Entrée pour utiliser un cadrage centré
- Échap pour ignorer l'image en cours

Le carré de rognage prend automatiquement la plus grande taille possible à partir de l'image source, afin de produire une image carrée sans déformation.

## Fichiers générés

Les images rognées sont enregistrées dans le dossier de sortie avec le suffixe `_carre`.

Exemple :

- `photo.jpg` devient `photo_carre.jpg`

## Structure du projet

```text
.
|- rogne_images.py
|- requirements.txt
|- sortie/
```

## Remarques

- si un dossier est sélectionné, seules les images présentes à sa racine sont traitées
- si une image est annulée dans la fenêtre de sélection, elle est ignorée sans arrêter le reste du traitement
- le dossier de sortie est créé automatiquement s'il n'existe pas

## Dépendances

- Pillow

## Auteur

Projet créé par Christen Dijoux.

Portfolio : [https://christendijoux.com/](https://christendijoux.com/)
