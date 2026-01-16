## README



Clean Up My Download is a script that automates the cleanup of the downloads directory.

The downloads directory usually contains files and folders that are used only **once**, often **duplicated**, and which accumulate over time.

This leads to **storage space saturation** or important files being lost in an ocean of files. Cleaning it up is **inevitable** but very **time-consuming** because of the pre-filtering process.  


### When to use ?

This script is designed to be **executed at each operating system startup** in order to take into account the user's file usage, determine the importance level of files and archives them rather than delete them.

The script can also be **executed manually**, but if it is mainly used this way, the importance level of files **cannot be properly taken into account.** 

### How to use ? 

#### Requirements

- Python 3.14
- `Send2Trash==2.1.0`

#### Algorithm (in french)

```
Parcourir l'ensemble des fichiers
Vérifier leur date de création
Vérifier leur dernière utilisation 
Stocker dans un tableau [chemin du fichier, date création, date dernière utilisation, compteur utilisation]
Si date dernière utilisation > TEMPS  
	Si fichier utilisé +LIMITE fois 
		Stocker le fichier dans une archive
	Sinon 
		Déplacer le fichier dans la corbeille
Sinon
	Ajouter les nouvelles instances dans le CSV
	Supprimer les instances obsolètes (déplacer dans la corbeille) dans le CSV
	Mettre à jour les instances existantes dans le CSV
```


#### On Windows



#### On Linux


### Limites


*Constraints*
- Require daily execution at each operating system startup
- There is a risk of loss of important data
- By default, only files that have been used more than three times are considered important and are archived rather than deleted

*Mitigations*
- By default, files that are used at least three times are archived and moved out of the downloads directory
- Files that are used less than three times and are concidered deprecated are moved to filesystem's trash, which adds an additional 30 days delay before permanent loss

