# Reconforge

Reconforge est une toolbox de pentest avec interface web, API FastAPI, historique d'execution et generation de rapports `JSON` / `PDF`.

L'objectif de ce README est simple : permettre a n'importe quelle personne qui clone le depot depuis GitHub de :

- comprendre a quoi sert le projet ;
- l'installer ;
- le configurer ;
- le lancer ;
- le tester rapidement ;
- savoir ou regarder si quelque chose ne fonctionne pas.

## 0. Demarrage express

Si vous voulez juste lancer le projet le plus vite possible :

```bash
git clone https://github.com/RathureDEVOPS/M1_Toolbox.git
cd M1_Toolbox
cp .env.example .env
docker compose --profile lab up --build -d
```

Sous Windows PowerShell, remplacez la ligne `cp .env.example .env` par :

```powershell
Copy-Item .env.example .env
```

Ensuite, ouvrez :

- [http://localhost:8000](http://localhost:8000) pour Reconforge ;
- [http://localhost:3000](http://localhost:3000) pour Juice Shop.

Premier test recommande dans l'interface :

- cible : `http://host.docker.internal:3000`
- modules : `whatweb` + `nikto`

## 1. Ce que fait le projet

Reconforge centralise plusieurs outils de reconnaissance et d'audit dans une seule interface web.

Depuis l'application, on peut :

- saisir une cible ;
- selectionner un ou plusieurs modules ;
- lancer une session d'execution ;
- suivre les sorties en temps reel ;
- consulter l'historique ;
- telecharger les resultats au format `JSON` et `PDF`.

Le projet peut fonctionner de deux manieres :

- `local` : les commandes s'executent dans l'environnement du conteneur Docker ;
- `ssh` : l'interface reste dans Docker, mais les outils peuvent etre lances sur une machine Kali Linux accessible en SSH.

## 2. Ce que contient le depot

Le depot GitHub est pense pour etre autonome. Une fois clone, on retrouve tout ce qu'il faut pour comprendre et reutiliser le projet :

- `app/` : code source de l'application FastAPI, routes web, API, templates et services ;
- `docker-compose.yml` : orchestration des services Docker ;
- `Dockerfile` : image principale de l'application ;
- `.env.example` : exemple complet de configuration ;
- `storage/` : emplacement des rapports, logs et donnees locales ;
- `scripts/` : scripts utilitaires et scripts de generation documentaire ;
- `README.md` : guide d'installation, configuration et utilisation ;
- fichiers DAT et livrables a la racine : documentation de projet.

Important :

- le depot GitHub ne contient pas de VM Kali preconfiguree ;
- aucun export de machine virtuelle n'est fourni dans le repository ;
- le projet peut etre teste sans VM, en mode `local`, avec ou sans Juice Shop ;
- le mode `ssh` vers Kali est une option d'usage avancee pour une demonstration plus complete.

## 3. Fonctionnalites principales

- interface web locale ;
- API documentee via Swagger ;
- execution multi-outils dans une session unique ;
- console temps reel ;
- historique des scans ;
- export `JSON` et `PDF` ;
- authentification locale optionnelle ;
- double facteur TOTP optionnel ;
- mode local ;
- mode SSH vers Kali ;
- services complementaires prevus dans la stack : PostgreSQL, Redis, MinIO, worker Celery optionnel.

## 4. Modules disponibles

Les modules visibles dans l'interface a ce stade sont :

- `nmap` : reconnaissance reseau ;
- `wireshark` / `tshark` : capture reseau courte ;
- `hydra` : tests d'authentification SSH ;
- `whatweb` : fingerprint web ;
- `theHarvester` : OSINT sur domaine ;
- `gobuster` : enumeration web ;
- `sqlmap` : tests SQLi ;
- `nikto` : audit web ;
- `sslyze` : analyse TLS ;
- `auth-audit` : verification d'un endpoint d'authentification web.

Important :

- tous les modules peuvent apparaitre dans l'interface ;
- leur efficacite depend du mode d'execution et des binaires reellement disponibles ;
- le mode `ssh` vers Kali est le mode le plus realiste pour une demonstration complete.

## 5. Architecture Docker

Le `docker-compose.yml` declare les services suivants :

- `web` : application Reconforge ;
- `postgres` : base PostgreSQL ;
- `redis` : broker / cache ;
- `minio` : stockage objet ;
- `worker` : worker Celery optionnel, active via le profil `worker` ;
- `juice-shop` : cible de demonstration, active via le profil `lab`.

Ports utilises par defaut :

- `8000` : interface web et API Reconforge ;
- `3000` : Juice Shop ;
- `5432` : PostgreSQL ;
- `6379` : Redis ;
- `9000` : API MinIO ;
- `9001` : console MinIO.

## 6. Prerequis

Pour utiliser le projet depuis GitHub, il faut au minimum :

- Git ;
- Docker Desktop ou Docker Engine ;
- Docker Compose ;
- une connexion Internet pour le premier build Docker.

Recommande pour une utilisation complete :

- une machine Kali Linux accessible en SSH si vous souhaitez utiliser le mode `ssh` ;
- les outils installes sur Kali si vous utilisez le mode `ssh` ;
- des wordlists disponibles sur Kali pour `hydra` et `gobuster`.

Important :

- la VM Kali n'est pas fournie dans le depot GitHub ;
- si vous voulez utiliser le mode `ssh`, vous devez preparer votre propre machine Kali ou un environnement equivalent ;
- si vous ne disposez pas de Kali, vous pouvez tout de meme lancer et tester le projet en mode `local`.

Verification rapide :

```bash
git --version
docker version
docker compose version
```

Si Docker Desktop n'est pas demarre, aucune commande `docker compose` ne fonctionnera.

## 7. Installation depuis GitHub

### 7.1 Cloner le depot

```bash
git clone https://github.com/RathureDEVOPS/M1_Toolbox.git
cd M1_Toolbox
```

Exemple :

```bash
git clone https://github.com/RathureDEVOPS/M1_Toolbox.git
cd M1_Toolbox
```

Si vous avez telecharge un ZIP GitHub au lieu de cloner le depot, decompressez-le puis ouvrez un terminal dans le dossier racine du projet.

### 7.2 Creer le fichier `.env`

Sous Windows PowerShell :

```powershell
Copy-Item .env.example .env
```

Sous Linux / macOS :

```bash
cp .env.example .env
```

### 7.3 Verifier la presence des fichiers importants

Avant de lancer le projet, verifiez que vous avez bien :

- `docker-compose.yml`
- `Dockerfile`
- `.env`
- `.env.example`
- `README.md`
- `app/`
- `storage/`

## 8. Demarrage rapide recommande

Si vous voulez seulement verifier que le projet se lance correctement, utilisez ce parcours.

### 8.1 Configuration minimale

Dans `.env`, gardez au minimum :

```env
APP_NAME=Reconforge
APP_HOST=0.0.0.0
APP_PORT=8000
TOOLBOX_AUTH_ENABLED=false
EXECUTION_MODE=local
JUICE_SHOP_TARGET=http://host.docker.internal:3000
```

### 8.2 Lancer l'application

```bash
docker compose up --build -d
```

Cette commande demarre :

- l'application web ;
- PostgreSQL ;
- Redis ;
- MinIO.

### 8.3 Ouvrir l'application

Une fois les conteneurs demarres :

- application : [http://localhost:8000](http://localhost:8000)
- Swagger : [http://localhost:8000/docs](http://localhost:8000/docs)
- healthcheck : [http://localhost:8000/health](http://localhost:8000/health)

### 8.4 Verifier les conteneurs

```bash
docker compose ps
```

### 8.5 Suivre les logs si besoin

```bash
docker compose logs -f
```

## 9. Lancer aussi Juice Shop pour une demo web

Pour avoir une cible web locale simple a tester :

```bash
docker compose --profile lab up --build -d
```

Puis ouvrez :

- Reconforge : [http://localhost:8000](http://localhost:8000)
- Juice Shop : [http://localhost:3000](http://localhost:3000)

Dans Reconforge, vous pouvez utiliser par exemple :

- `http://host.docker.internal:3000`

Pourquoi `host.docker.internal` ?

- parce que `localhost` dans le navigateur de votre machine n'est pas la meme chose que `localhost` a l'interieur du conteneur ;
- depuis le conteneur, `host.docker.internal` permet de viser la machine hote Docker.

## 10. Parcours de test le plus simple

Si vous voulez juste verifier que l'outil fonctionne apres clonage du depot :

1. clonez le projet ;
2. creez `.env` a partir de `.env.example` ;
3. lancez `docker compose --profile lab up --build -d` ;
4. ouvrez [http://localhost:8000](http://localhost:8000) ;
5. saisissez `http://host.docker.internal:3000` comme cible ;
6. cochez `whatweb` et `nikto` ;
7. lancez la session ;
8. regardez la sortie dans la console ;
9. verifiez l'historique a droite ;
10. telechargez les artefacts `JSON` et `PDF`.

Ce parcours est celui a privilegier pour une premiere validation rapide du projet.

Il ne necessite pas de VM Kali.

## 11. Utilisation de l'interface

Une fois sur la page principale :

1. entrez une cible ;
2. cochez un ou plusieurs modules ;
3. remplissez les options affichees pour les modules concernes ;
4. lancez la session ;
5. suivez les sorties dans la console web ;
6. consultez l'historique ;
7. telechargez les rapports.

Conseils de saisie :

- pour les outils web, utilisez de preference une URL complete ;
- pour `theHarvester`, entrez de preference un domaine ou une URL contenant un domaine exploitable ;
- pour `sslyze`, utilisez plutot une cible du type `example.com:443` ;
- pour `hydra`, verifiez le port cible, le mode utilisateur et les wordlists selectionnees.

## 12. Configuration du fichier `.env`

Toute la configuration passe par `.env`.

### 12.1 Variables essentielles

| Variable | Description |
| --- | --- |
| `APP_NAME` | nom affiche de l'application |
| `APP_HOST` | host d'ecoute |
| `APP_PORT` | port d'ecoute |
| `TOOLBOX_AUTH_ENABLED` | active ou non l'authentification |
| `TOOLBOX_AUTH_USERNAME` | identifiant local |
| `TOOLBOX_AUTH_PASSWORD` | mot de passe local |
| `TOOLBOX_AUTH_TOTP_SECRET` | secret TOTP |
| `TOOLBOX_AUTH_TOTP_ISSUER` | nom affiche dans l'application OTP |
| `AUTH_SESSION_SECRET` | secret de session |
| `EXECUTION_MODE` | `local` ou `ssh` |
| `KALI_SSH_HOST` | IP ou nom d'hote de la machine Kali |
| `KALI_SSH_PORT` | port SSH |
| `KALI_SSH_USERNAME` | utilisateur SSH |
| `KALI_SSH_PASSWORD` | mot de passe SSH |
| `KALI_SSH_KEY_PATH` | cle SSH eventuelle |
| `JUICE_SHOP_TARGET` | cible de demonstration suggeree |

### 12.2 Configuration minimale locale

```env
TOOLBOX_AUTH_ENABLED=false
EXECUTION_MODE=local
JUICE_SHOP_TARGET=http://host.docker.internal:3000
```

### 12.3 Configuration avec authentification et double facteur

```env
TOOLBOX_AUTH_ENABLED=true
TOOLBOX_AUTH_USERNAME=admin
TOOLBOX_AUTH_PASSWORD=ChangeMe123!
TOOLBOX_AUTH_TOTP_SECRET=JBSWY3DPEHPK3PXP
TOOLBOX_AUTH_TOTP_ISSUER=Reconforge
AUTH_SESSION_SECRET=change-this-session-secret
```

Bonnes pratiques :

- changez le mot de passe par defaut ;
- changez le secret de session ;
- gardez un secret TOTP stable si vous voulez conserver la meme configuration 2FA ;
- ne versionnez pas un `.env` contenant de vrais secrets.

### 12.4 Configuration du mode SSH vers Kali

Cette section est optionnelle.

Le depot GitHub ne fournit pas la machine Kali. Vous devez donc preparer vous-meme :

- une VM Kali ;
- ou une machine Linux contenant les outils attendus et accessible en SSH ;
- ou tout autre environnement compatible avec les binaires appeles par Reconforge.

```env
EXECUTION_MODE=ssh
KALI_SSH_HOST=192.168.56.10
KALI_SSH_PORT=22
KALI_SSH_USERNAME=kali
KALI_SSH_PASSWORD=changeme
KALI_SSH_ALLOW_UNKNOWN_HOST=true
```

Variables utiles si les binaires sont installes sur Kali :

```env
NMAP_BINARY=nmap
NIKTO_BINARY=nikto
SQLMAP_BINARY=sqlmap
SSLYZE_BINARY=sslyze
WHATWEB_BINARY=whatweb
THEHARVESTER_BINARY=theHarvester
GOBUSTER_BINARY=gobuster
HYDRA_BINARY=hydra
WIRESHARK_BINARY=tshark
```

Exemples de wordlists Kali :

```env
HYDRA_USERNAME_LIST_SHORT=/usr/share/seclists/Usernames/top-usernames-shortlist.txt
HYDRA_USERNAME_LIST_COMMON=/usr/share/seclists/Usernames/Names/names.txt
HYDRA_PASSWORD_LIST_SMALL=/usr/share/seclists/Passwords/Common-Credentials/500-worst-passwords.txt
HYDRA_PASSWORD_LIST_COMMON=/usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt
HYDRA_PASSWORD_LIST_ROCKYOU=/usr/share/wordlists/rockyou.txt
GOBUSTER_WORDLIST=/usr/share/wordlists/dirb/common.txt
WIRESHARK_DEFAULT_INTERFACE=eth0
```

Le mode `ssh` permet :

- de conserver l'application dans Docker ;
- d'executer les outils sur un environnement Kali plus riche ;
- d'utiliser les binaires et wordlists de Kali ;
- d'avoir une demonstration plus realiste.

Si vous n'avez pas de machine Kali :

- laissez `EXECUTION_MODE=local` ;
- utilisez le profil `lab` avec Juice Shop ;
- testez d'abord les modules web et les parcours de reporting.

## 13. Authentification et double facteur

Si `TOOLBOX_AUTH_ENABLED=true`, le parcours utilisateur devient :

1. ouverture de `/login` ;
2. validation identifiant / mot de passe ;
3. si le TOTP n'est pas encore enrole, redirection vers `/setup-2fa` ;
4. affichage du QR code ;
5. enrolement dans une application OTP ;
6. saisie du code OTP ;
7. connexions suivantes via `/verify-2fa`.

Les donnees locales liees a l'authentification sont stockees dans :

- `storage/auth/`

## 14. API utile

L'application expose notamment :

- `GET /health` : verifier que l'application repond ;
- `GET /docs` : documentation Swagger ;
- `GET /api/modules` : liste des modules ;
- `POST /api/scans/session` : creation d'une session multi-modules ;
- `GET /api/scans/history` : historique ;
- `GET /api/scans/{scan_id}/artifacts/json` : rapport JSON ;
- `GET /api/scans/{scan_id}/artifacts/pdf` : rapport PDF.

Si vous voulez explorer l'API sans passer par l'interface, utilisez directement Swagger :

- [http://localhost:8000/docs](http://localhost:8000/docs)

## 15. Fichiers generes par l'application

Reconforge ecrit principalement dans `storage/` :

- `storage/reports/` : rapports `JSON` et `PDF` ;
- `storage/logs/audit.log` : journal d'audit ;
- `storage/auth/` : informations locales de session / TOTP.

Important :

- si vous supprimez `storage/`, vous perdez l'historique et les artefacts locaux ;
- si vous voulez repartir de zero pour une demo, sauvegardez d'abord ce dossier si besoin.

## 16. Commandes Docker utiles

Demarrer la stack standard :

```bash
docker compose up --build -d
```

Demarrer avec Juice Shop :

```bash
docker compose --profile lab up --build -d
```

Demarrer avec le worker :

```bash
docker compose --profile worker up --build -d
```

Demarrer avec worker + Juice Shop :

```bash
docker compose --profile worker --profile lab up --build -d
```

Voir l'etat des conteneurs :

```bash
docker compose ps
```

Voir les logs :

```bash
docker compose logs -f
```

Arreter les conteneurs :

```bash
docker compose down
```

Reconstruire l'image :

```bash
docker compose up --build -d
```

## 17. Depannage

### 17.1 Docker Desktop n'est pas demarre

Symptome possible :

```text
failed to connect to the docker API
```

Correction :

- demarrer Docker Desktop ;
- attendre que Docker soit bien operationnel ;
- relancer la commande `docker compose`.

### 17.2 Le build Docker ne telecharge pas les images

Symptome possible :

```text
failed to resolve source metadata
lookup registry-1.docker.io: no such host
```

Cause probable :

- probleme reseau ;
- DNS indisponible ;
- proxy Docker non configure ;
- machine sans acces Internet.

Correction :

- verifier que la machine a acces a Internet ;
- verifier que Docker Desktop a bien acces au reseau ;
- verifier les reglages proxy / DNS de Docker Desktop ;
- retester avec :

```bash
docker compose build --no-cache
```

### 17.3 `theHarvester` retourne `Invalid source`

Cause frequente :

- une source non supportee a ete ajoutee dans `.env`.

Exemple de configuration compatible a utiliser :

```env
THEHARVESTER_SOURCES=crtsh,rapiddns,urlscan
```

Si vous utilisez `anubis`, l'outil peut refuser la source selon la version embarquee.

### 17.4 La cible web ne repond pas depuis le conteneur

Cause frequente :

- vous avez saisi `http://localhost:3000` alors que le scan est execute depuis Docker.

Correction :

- utilisez `http://host.docker.internal:3000` pour cibler une application exposee sur votre machine hote ;
- ou utilisez directement l'IP reelle de la machine / VM cible.

### 17.5 Le mode SSH vers Kali ne fonctionne pas

Verifier :

- l'adresse IP de Kali ;
- le port SSH ;
- l'utilisateur et le mot de passe ;
- la disponibilite des binaires sur Kali ;
- les chemins des wordlists ;
- la connectivite reseau entre Docker et Kali.

### 17.6 L'interface s'ouvre mais certains modules echouent

C'est possible si :

- le module a besoin d'un binaire absent ;
- la cible n'est pas adaptee ;
- le mode `local` est trop limite pour ce test ;
- le timeout du module est trop court ;
- la machine cible ne repond pas.

Dans ce cas :

- regarder la console dans l'interface ;
- regarder `docker compose logs -f` ;
- tester d'abord avec `whatweb`, `nikto` ou `nmap` ;
- passer en mode `ssh` pour les outils les plus dependants de Kali.

## 18. Structure du projet

Structure simplifiee :

```text
.
|-- app/
|   |-- core/
|   |-- routers/
|   |-- services/
|   |-- static/
|   |-- templates/
|   `-- main.py
|-- scripts/
|-- storage/
|-- .env.example
|-- docker-compose.yml
|-- Dockerfile
|-- pyproject.toml
`-- README.md
```

## 19. Reutilisation sur un autre poste

Pour reutiliser le projet sur une autre machine depuis GitHub :

1. cloner le depot ;
2. creer `.env` a partir de `.env.example` ;
3. verifier Docker Desktop ;
4. lancer `docker compose up --build -d` ;
5. ouvrir `http://localhost:8000` ;
6. tester un premier scan ;
7. ajuster ensuite le mode `ssh` si vous voulez une demo plus complete.

Le projet a ete pense pour pouvoir etre redeploye de cette maniere sans devoir reconstruire manuellement toute l'architecture.

La VM Kali ne fait pas partie du depot et doit etre geree a part si vous souhaitez utiliser le mode `ssh`.

## 20. Cadre d'usage

Reconforge doit etre utilise dans un cadre legal et autorise uniquement :

- environnement de TP ;
- lab local ;
- machine de demonstration ;
- cible appartenant a l'equipe projet ;
- infrastructure pour laquelle vous avez une autorisation explicite.

Ne lancez pas d'audits ou de scans sur une cible reelle sans autorisation.
