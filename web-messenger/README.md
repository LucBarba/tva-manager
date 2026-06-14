# DuoChat — Messagerie privée temps réel (React + Vite + Firebase)

Application **web** de messagerie privée inspirée de WhatsApp, **limitée à deux
utilisateurs**, en temps réel. Construite en **React 18 + Vite**, avec
**Firebase Authentication, Firestore, Storage et Cloud Messaging (FCM)**.

> Remarque : votre cahier des charges initial mentionnait SwiftUI/iOS, puis vous
> avez demandé une **app web React/Vue**. Ce projet est donc la version **web React**,
> qui couvre l'intégralité des fonctionnalités demandées (auth, conversation
> unique, images, vidéos, notifications, présence, indicateurs de lecture, etc.).

---

## ✨ Fonctionnalités

- **Authentification** : inscription, connexion, déconnexion, réinitialisation
  de mot de passe, **vérification d'email** obligatoire.
- **2 utilisateurs maximum** : garde-fou côté client, règles Firestore, et
  fonction bloquante Cloud Functions.
- **Conversation unique** temps réel entre les deux utilisateurs.
- **Messages texte** horodatés, bulles alignées (droite = vous, gauche = contact).
- **Images** : galerie ou caméra, upload Storage, affichage + **zoom plein écran**.
- **Vidéos** : galerie ou caméra, upload Storage, vignette + **lecture plein écran**.
- **Notifications push FCM** (message / photo / vidéo) via Cloud Function, plus
  notifications locales au premier plan.
- **Présence** : en ligne / hors ligne / dernière connexion.
- **Indicateurs de remise** (coches WhatsApp) : envoyé ✓, reçu ✓✓, lu ✓✓ (bleu).
- **Interface moderne** : thèmes **clair & sombre**, animations fluides.

---

## 🗂 Arborescence du projet

```
web-messenger/
├── index.html                     # Point d'entrée HTML
├── package.json                   # Dépendances & scripts npm
├── vite.config.js                 # Configuration Vite (port 5174)
├── eslint.config.js               # Configuration ESLint (flat config)
├── .env.example                   # Modèle de configuration Firebase
├── .firebaserc                    # Projet Firebase par défaut
├── firebase.json                  # Hosting + Firestore + Storage + Functions
│
├── public/
│   ├── favicon.svg
│   └── firebase-messaging-sw.js   # Service Worker FCM (notifications en arrière-plan)
│
├── firebase/
│   ├── firestore.rules            # Règles de sécurité Firestore
│   ├── firestore.indexes.json     # Index composites
│   ├── storage.rules              # Règles de sécurité Storage
│   └── functions/
│       ├── package.json
│       └── index.js               # Push FCM + limite de 2 utilisateurs
│
└── src/
    ├── main.jsx                   # Bootstrap React (Router + AuthProvider)
    ├── App.jsx                    # Routage + garde d'authentification
    │
    ├── firebase/
    │   └── config.js              # Initialisation du SDK Firebase
    │
    ├── models/                    # Schémas & (dé)sérialisation des documents
    │   ├── User.js
    │   ├── Message.js
    │   └── Conversation.js
    │
    ├── services/                  # Accès bas niveau aux services Firebase
    │   ├── authService.js
    │   ├── firestoreService.js
    │   ├── storageService.js
    │   └── notificationService.js
    │
    ├── repositories/              # Logique métier au-dessus des services
    │   ├── userRepository.js
    │   ├── conversationRepository.js
    │   └── messageRepository.js
    │
    ├── hooks/                     # "ViewModels" (état + actions des écrans)
    │   ├── useAuthViewModel.js
    │   ├── useChatViewModel.js
    │   ├── useProfileViewModel.js
    │   └── useTheme.js
    │
    ├── context/
    │   └── AuthContext.jsx        # État d'authentification global
    │
    ├── components/                # Composants UI réutilisables
    │   ├── Avatar.jsx
    │   ├── Ticks.jsx
    │   ├── MessageBubble.jsx
    │   ├── MessageList.jsx
    │   ├── Composer.jsx
    │   ├── MediaViewer.jsx
    │   └── Spinner.jsx
    │
    ├── pages/                     # Écrans (vues)
    │   ├── SplashScreen.jsx
    │   ├── Login.jsx
    │   ├── Register.jsx
    │   ├── ResetPassword.jsx
    │   ├── VerifyEmail.jsx
    │   ├── ConversationPage.jsx
    │   └── ProfilePage.jsx
    │
    ├── utils/
    │   ├── constants.js
    │   ├── errors.js
    │   ├── validators.js
    │   ├── format.js
    │   └── media.js
    │
    └── styles/
        └── index.css              # Thèmes clair/sombre + composants
```

---

## 🏗 Architecture (inspirée MVVM)

La structure respecte la séparation demandée, transposée à React :

| Couche         | Dossier          | Rôle |
|----------------|------------------|------|
| **Models**     | `models/`        | Schémas des documents Firestore + helpers de (dé)sérialisation. |
| **Views**      | `pages/`, `components/` | Affichage pur, sans logique d'accès aux données. |
| **ViewModels** | `hooks/`         | État réactif + actions exposées aux vues (équivalent `@Observable`). |
| **Services**   | `services/`      | Accès bas niveau aux SDK Firebase (Auth, Firestore, Storage, Messaging). |
| **Repositories** | `repositories/` | Règles métier, requêtes, transactions, agrégations. |
| **Utilities**  | `utils/`         | Constantes, validation, erreurs, formatage, traitement média. |

**Flux de données** : `View → Hook (ViewModel) → Repository → Service → Firebase`.
Les listeners Firestore (`onSnapshot`) assurent le **temps réel** : tout message
écrit par un utilisateur apparaît instantanément chez l'autre.

---

## 🔥 Structure Firestore

### `users/{userId}`  (userId = UID Firebase Auth)

| Champ         | Type      | Description |
|---------------|-----------|-------------|
| `displayName` | string    | Nom affiché |
| `email`       | string    | Adresse email |
| `photoURL`    | string?   | URL Storage de la photo de profil |
| `isOnline`    | boolean   | Statut de présence |
| `lastSeen`    | timestamp | Dernière activité |
| `fcmToken`    | string?   | Jeton FCM pour les notifications |
| `createdAt`   | timestamp | Date de création du compte |

### `conversations/{conversationId}`  (id = `uidA_uidB` triés)

| Champ                 | Type             | Description |
|-----------------------|------------------|-------------|
| `participants`        | string[2]        | Les deux UID |
| `lastMessageText`     | string?          | Aperçu du dernier message |
| `lastMessageSenderId` | string?          | UID de l'expéditeur du dernier message |
| `lastMessageType`     | string?          | `text` / `image` / `video` |
| `lastMessageAt`       | timestamp        | Date du dernier message |
| `unreadCounts`        | map<string,int>  | Non-lus par UID, ex. `{uidA:0, uidB:3}` |
| `createdAt`           | timestamp        | Date de création |

### `conversations/{conversationId}/messages/{messageId}`

| Champ          | Type      | Description |
|----------------|-----------|-------------|
| `senderId`     | string    | UID de l'expéditeur |
| `type`         | string    | `text` / `image` / `video` |
| `text`         | string?   | Contenu texte / légende |
| `mediaURL`     | string?   | URL Storage du média |
| `thumbnailURL` | string?   | URL de la vignette (vidéos) |
| `mediaWidth`   | number?   | Largeur du média (px) |
| `mediaHeight`  | number?   | Hauteur du média (px) |
| `status`       | string    | `sending` / `sent` / `delivered` / `read` |
| `timestamp`    | timestamp | Date d'envoi (serveur) |

---

## ⚙️ Installation

### 1. Prérequis
- Node.js 20+
- Un projet Firebase (console : <https://console.firebase.google.com>)

### 2. Configurer Firebase (console)
1. **Authentication** → activer **Email/Password** et **vérification d'email**.
2. **Firestore Database** → créer la base (mode production).
3. **Storage** → activer.
4. **Cloud Messaging** → générer un certificat **Web Push (clé VAPID)**.
5. **Project settings → Vos applications → Web** → copier la config.

### 3. Variables d'environnement
```bash
cd web-messenger
cp .env.example .env
# Renseignez toutes les valeurs VITE_FIREBASE_* et VITE_FIREBASE_VAPID_KEY
```
⚠️ Reportez **les mêmes valeurs** de config dans `public/firebase-messaging-sw.js`
(le Service Worker n'a pas accès aux variables Vite).

### 4. Installer et lancer
```bash
npm install
npm run dev
# Ouvre http://localhost:5174
```

---

## 🚀 Déploiement

### Déployer les règles, index et fonctions
```bash
# Depuis web-messenger/
npm install -g firebase-tools
firebase login
# Mettez votre projectId dans .firebaserc

firebase deploy --only firestore:rules,firestore:indexes,storage
cd firebase/functions && npm install && cd ../..
firebase deploy --only functions
```
> La fonction bloquante `enforceUserLimit` nécessite **Identity Platform**
> (Authentication → Settings → Blocking functions). Si vous ne l'activez pas,
> la limite reste appliquée côté client + règles.

### Déployer le site (Firebase Hosting)
```bash
npm run build
firebase deploy --only hosting
```

Alternative : tout déployer d'un coup
```bash
npm run build
firebase deploy
```

---

## 🔐 Sécurité

- **Validation des entrées** : `utils/validators.js` (email, mot de passe fort,
  nom, taille des médias) — appliquée avant tout appel Firebase.
- **Règles Firestore** (`firebase/firestore.rules`) : authentification requise,
  écriture limitée à son propre profil, conversation/messages réservés aux
  participants, email vérifié exigé pour discuter.
- **Règles Storage** (`firebase/storage.rules`) : accès média réservé aux
  participants de la conversation, contrôle du type MIME et de la taille (≤ 50 Mo).
- **Limite de 2 utilisateurs** : triple protection (client, règles, Cloud Function).
- **Gestion d'erreurs** centralisée : `utils/errors.js` traduit les codes Firebase
  en messages clairs pour l'utilisateur.

---

## 🧭 Écrans

1. **Splash** — initialisation de la session.
2. **Login** — connexion.
3. **Register** — inscription (+ envoi de l'email de vérification).
4. **VerifyEmail** — attente de vérification (rafraîchissement automatique).
5. **Conversation** — discussion temps réel (texte, images, vidéos, coches).
6. **Profil** — photo, nom, email, statut, dernière connexion, déconnexion.
7. **Visionneuse** — photo plein écran avec zoom / lecture vidéo plein écran.

---

## 📌 Notes

- Sur le web, le statut « hors ligne » à la fermeture de l'onglet est *best-effort*
  (limites des navigateurs). La présence « en ligne » est fiable à l'ouverture.
- Les notifications push web requièrent **HTTPS** (ou `localhost`) et l'autorisation
  de l'utilisateur. En production, servez le site via Firebase Hosting (HTTPS).
```
