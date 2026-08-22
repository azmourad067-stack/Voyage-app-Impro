# 🧳 ComparoVoyage

Application Streamlit qui compare et recommande les meilleures combinaisons
**transport (bus, train, avion) + hébergement (hôtel, Airbnb)** à partir
d'une ville de départ, d'une destination et d'un budget.

---

## ✨ Fonctionnalités

**Formulaire de recherche**
- Ville de départ / destination
- Budget cible avec marge de tolérance ajustable (±€)
- Rayon de recherche (km) autour de la destination pour l'hébergement
- Type d'hébergement : Hôtel, Airbnb, ou les deux
- Filtre par nombre d'étoiles (actif uniquement si "Hôtel" est sélectionné)
- Nombre de voyageurs et de nuits sur place

**Différenciation par rapport aux comparateurs classiques**

| Fonctionnalité | Pourquoi c'est utile |
|---|---|
| **Score de rapport qualité/prix personnalisable** | L'utilisateur pondère lui-même l'importance du prix, de la rapidité, du confort et de l'écologie : la recommandation "meilleur choix" s'adapte à ses priorités réelles, plutôt qu'un algorithme figé identique pour tout le monde. |
| **Temps de trajet porte-à-porte** | Additionne le transport, les correspondances et le trajet gare/aéroport → hébergement. Beaucoup de comparateurs n'affichent que le temps de transport pur, ce qui sous-estime la durée réelle du voyage. |
| **Empreinte carbone estimée (CO2)** | Critère de plus en plus déterminant pour les voyageurs, quasiment absent des comparateurs low-cost classiques. |
| **Résultats cliquables (accordéons)** | Chaque combinaison s'affiche d'abord sous forme de résumé (mode, prix, score). Un clic déploie tous les détails : transport (opérateur, horaires, durée, CO2), hébergement (note, équipements, distance), et le détail complet du budget. |
| **Repli intelligent si budget trop restrictif** | Plutôt qu'un message d'échec sec, l'application propose les 3 options les plus proches du budget et explique comment ajuster la recherche. |
| **Badges de recommandation** (💰 Meilleur prix, ⚡ Plus rapide, 🌿 Plus écologique, ⭐ Meilleur choix) | Lecture immédiate des meilleurs compromis sans avoir à éplucher un tableau. |
| **Transparence des données** | Chaque carte de résultat indique clairement "Données simulées" tant que les vraies API ne sont pas branchées — aucune ambiguïté pour l'utilisateur. |

---

## 🏗️ Architecture du projet

```
voyage-app/
├── app.py                     # Point d'entrée Streamlit (UI uniquement)
├── requirements.txt
├── .streamlit/
│   ├── config.toml            # Thème visuel
│   └── secrets.toml.example   # Modèle pour les futures clés API réelles
├── core/                       # Logique métier (aucun import streamlit sauf secrets)
│   ├── config.py               # Constantes métier + emplacements des clés API
│   ├── geocoding.py             # Géocodage (API réelle + repli hors-ligne)
│   ├── transport.py             # Recherche des offres de transport
│   ├── accommodation.py         # Recherche des hébergements
│   ├── scoring.py                # Constitution des packages + calcul des scores
│   └── search_engine.py          # Orchestrateur + gestion des erreurs
└── ui/                          # Interface utilisateur (aucune logique métier)
    ├── sidebar_form.py           # Formulaire de recherche
    ├── results_view.py            # Affichage des résultats (cartes, graphique)
    └── styles.py                  # CSS personnalisé
```

Séparation stricte : `core/` ne dépend jamais de `streamlit` pour son
fonctionnement (sauf lecture optionnelle des secrets), ce qui le rend
testable indépendamment de l'interface.

---

## 🔌 Données réelles vs données simulées

| Donnée | Source actuelle | Pour passer en données réelles |
|---|---|---|
| Géolocalisation des villes | **API réelle** : [Nominatim / OpenStreetMap](https://nominatim.org/) (gratuite, sans clé) avec repli automatique sur une base locale hors-ligne si l'API est indisponible | Déjà fonctionnel |
| Offres de train/bus/avion | Simulées (formules réalistes basées sur la distance) | Voir `core/transport.py` : brancher SNCF Connect / navitia.io (train), FlixBus Distribution API (bus), Amadeus Flight Offers Search (avion) |
| Hôtels | Simulés | Voir `core/accommodation.py` : brancher Amadeus Hotel Search API ou Booking.com via RapidAPI |
| Airbnb | Simulé | Airbnb ne propose pas d'API publique officielle ; envisager un partenariat direct ou un agrégateur tiers de locations courte durée |

Les clés API se déclarent dans `core/config.py` (via `st.secrets` ou
variables d'environnement) — copiez `.streamlit/secrets.toml.example` en
`.streamlit/secrets.toml` en local, ou renseignez-les dans **Manage app >
Settings > Secrets** sur Streamlit Community Cloud.

---

## 🚀 Lancer en local

```bash
git clone <url-du-repo>
cd voyage-app
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre automatiquement sur `http://localhost:8501`.

---

## ☁️ Déployer sur Streamlit Community Cloud (via GitHub)

1. **Créer un dépôt GitHub** contenant l'ensemble de ces fichiers (en
   conservant la structure de dossiers telle quelle), et le pousser :
   ```bash
   git init
   git add .
   git commit -m "Première version de ComparoVoyage"
   git branch -M main
   git remote add origin https://github.com/<votre-compte>/<votre-repo>.git
   git push -u origin main
   ```
2. Aller sur **[share.streamlit.io](https://share.streamlit.io)** et se
   connecter avec le compte GitHub.
3. Cliquer sur **"New app"**, sélectionner le dépôt, la branche `main`, et
   indiquer `app.py` comme fichier principal.
4. (Optionnel) Dans **Advanced settings**, ajouter les clés API réelles
   dans la section **Secrets** au format TOML (voir
   `.streamlit/secrets.toml.example`).
5. Cliquer sur **"Deploy"**. L'application est en ligne en quelques minutes,
   et se redéploie automatiquement à chaque `git push` sur `main`.

---

## ⚠️ Gestion des erreurs prévue

- Champ de départ ou de destination vide → message explicite.
- Départ = destination → message explicite.
- Ville introuvable (orthographe) → message explicite, avec tolérance aux
  fautes de frappe sur la base de secours hors-ligne.
- Aucun hébergement dans le rayon/étoiles demandés → suggestion d'élargir
  le rayon ou de réduire le nombre d'étoiles minimum.
- Budget trop restrictif (aucune combinaison dans la tolérance) → les 3
  options les plus proches du budget sont proposées à la place d'un échec sec.

---

## 🔭 Pistes d'évolution

- Ajout de dates de retour flexibles et comparaison multi-dates.
- Carte interactive des hébergements dans le rayon sélectionné.
- Historique des recherches et alertes de prix.
- Authentification utilisateur pour sauvegarder des favoris.
- Vraie intégration des API listées ci-dessus (train, bus, avion, hôtels).

---

## 🧪 Note technique

Les données simulées sont générées de façon déterministe par trajet (même
ville de départ + destination ⇒ mêmes offres de base au sein d'une même
exécution du serveur), afin que les résultats restent cohérents pendant
une session de démonstration.
