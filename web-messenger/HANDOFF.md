# DuoChat — Document de passation (handoff)

> À reprendre dans une nouvelle session (cowork). Ce fichier résume le contexte
> complet : demande initiale, décisions, ce qui a été construit, l'état actuel
> et les prochaines étapes.

---

## 1. Contexte du dépôt

- **Repo** : `LucBarba/tva-manager`
- **Branche de travail** : `claude/ios-messaging-app-hl2nda`
- Le dépôt contenait à l'origine une app web **TVA Manager** (React + Vite
  frontend, FastAPI + PostgreSQL backend). **Elle n'a pas été modifiée.**
- La nouvelle application de messagerie a été ajoutée dans un dossier séparé :
  **`web-messenger/`**.

---

## 2. Demande de l'utilisateur (résumé)

Créer une **messagerie privée temps réel inspirée de WhatsApp, limitée à 2
utilisateurs**. Fonctionnalités demandées :

- Auth : inscription, connexion, déconnexion, reset mot de passe, **vérification email**
- Utilisateurs : profil, photo, statut en ligne/hors ligne, dernière connexion
- Conversation unique temps réel, bulles alignées droite/gauche, horodatage
- Images (galerie + caméra), upload, zoom plein écran
- Vidéos (galerie + caméra), upload, lecture plein écran
- Notifications push (FCM) : message / photo / vidéo
- Indicateurs de remise (coches WhatsApp) : envoyé / reçu / lu
- Dark mode + light mode, animations
- Sécurité : règles Firestore + Storage, validation, gestion d'erreurs
- Architecture en couches : Models / Views / ViewModels / Services / Repositories / Utilities

### Évolution de la demande (important)
1. 1er message : formulé pour **iOS/SwiftUI** (Xcode, Swift 6).
2. Puis : **« je veux une app web react / vue »**.
3. Choix confirmé : **React + Vite + Firebase**.
4. Puis : **« je veux une application web fonctionnel »**.
5. Choix confirmé : **garder Firebase + configuration guidée** (plutôt qu'un
   backend autonome sans Firebase).

➡️ **Décision finale : application WEB React + Vite + Firebase.** Il n'y a pas de
projet Xcode/Swift (les fichiers iOS initiaux ont été supprimés).

---

## 3. Stack technique

- **React 18 + Vite** (port dev 5174), **react-router-dom**
- **Firebase** : Authentication, Firestore (temps réel via `onSnapshot`),
  Storage, Cloud Messaging (FCM)
- **Cloud Functions** (Node 20) : push FCM + limite de 2 utilisateurs
- Architecture MVVM transposée à React (hooks = ViewModels)

---

## 4. Ce qui a été construit (état = TERMINÉ et poussé)

Arborescence dans `web-messenger/` :

```
web-messenger/
├── index.html, package.json, vite.config.js, eslint.config.js
├── .env.example, .firebaserc, firebase.json
├── README.md, SETUP.md, HANDOFF.md (ce fichier)
├── public/
│   ├── favicon.svg
│   └── firebase-messaging-sw.js        # SW FCM (config reçue via URL params)
├── firebase/
│   ├── firestore.rules                 # règles Firestore
│   ├── firestore.indexes.json          # index composites (messages)
│   ├── storage.rules                   # règles Storage
│   └── functions/{package.json,index.js}  # push FCM + enforceUserLimit
└── src/
    ├── main.jsx, App.jsx               # bootstrap + routage/garde auth
    ├── firebase/config.js              # init SDK + export firebaseConfig
    ├── models/{User,Message,Conversation}.js
    ├── services/{auth,firestore,storage,notification}Service.js
    ├── repositories/{user,conversation,message}Repository.js
    ├── hooks/{useAuthViewModel,useChatViewModel,useProfileViewModel,useTheme}.js
    ├── context/AuthContext.jsx
    ├── components/{Avatar,Ticks,MessageBubble,MessageList,Composer,MediaViewer,Spinner}.jsx
    ├── pages/{SplashScreen,Login,Register,ResetPassword,VerifyEmail,ConversationPage,ProfilePage}.jsx
    ├── utils/{constants,errors,validators,format,media}.js
    └── styles/index.css                # thèmes clair/sombre
```

### Modèle de données Firestore
- `users/{uid}` : `displayName, email, photoURL?, isOnline, lastSeen, fcmToken?, createdAt`
- `conversations/{cid}` (cid = `uidA_uidB` triés) : `participants[2], lastMessageText?,
  lastMessageSenderId?, lastMessageType?, lastMessageAt, unreadCounts{uid:int}, createdAt`
- `conversations/{cid}/messages/{mid}` : `senderId, type(text|image|video), text?,
  mediaURL?, thumbnailURL?, mediaWidth?, mediaHeight?, status(sending|sent|delivered|read), timestamp`

### Vérifications effectuées
- `npm install` ✅
- `npm run build` ✅ (90 modules, aucune erreur ; warning bénin de taille de
  bundle dû à Firebase)
- ⚠️ **Non testé à l'exécution** : nécessite un projet Firebase réel (voir SETUP.md).

---

## 5. Commits sur la branche `claude/ios-messaging-app-hl2nda`

1. `Add DuoChat: real-time private messaging web app (React + Vite + Firebase)`
2. `Make DuoChat ready-to-run: single-file config + setup guide`
   - Le service worker reçoit la config Firebase via paramètres d'URL → **un seul
     fichier à configurer** (`.env`).
   - Accusés reçu/lu fiabilisés (requêtes par égalité sur l'UID du contact).
   - Ajout de `SETUP.md`.

Tout est **poussé** sur `origin/claude/ios-messaging-app-hl2nda`.
**Aucune Pull Request créée** (en attente de votre feu vert).

---

## 6. Comment lancer (résumé — détails dans SETUP.md)

1. Créer un projet Firebase ; activer **Email/Password**, **Firestore**, **Storage**.
2. Générer la **clé VAPID** (Cloud Messaging → Certificats push Web).
3. `cd web-messenger && cp .env.example .env` puis remplir les 7 valeurs.
4. Mettre le `projectId` dans `.firebaserc`, puis :
   `firebase deploy --only firestore:rules,firestore:indexes,storage`
5. `npm install && npm run dev` → http://localhost:5174
6. Tester à deux : onglet normal + fenêtre navigation privée (1 compte chacun,
   vérifier l'email).

Notifications push entre appareils (app fermée) = déployer les Cloud Functions
(plan Blaze requis).

---

## 7. Limites connues / décisions à valider

- **Pas de version iOS/SwiftUI** (abandonnée au profit du web, sur demande).
- **Statut hors-ligne** à la fermeture de l'onglet = *best-effort* (limite navigateur).
- **Cloud Functions** nécessitent le plan Blaze ; `enforceUserLimit` requiert
  Identity Platform (sinon commenter son export). La limite de 2 users reste
  appliquée côté client + règles Firestore.
- **Warning de taille de bundle** Firebase non traité (code-splitting possible).

---

## 8. Prochaines étapes possibles (TODO)

- [ ] Créer la Pull Request si souhaité.
- [ ] Code-splitting / `manualChunks` pour réduire la taille du bundle Firebase.
- [ ] Tests (Vitest + React Testing Library).
- [ ] Indicateur « en train d'écrire… » (typing indicator).
- [ ] Suppression de messages / médias.
- [ ] PWA installable (manifest + offline).
- [ ] CI (lint + build) via GitHub Actions.

---

## 9. Prompt de reprise suggéré (à coller dans la nouvelle session)

> « Reprends le projet DuoChat dans `web-messenger/` (branche
> `claude/ios-messaging-app-hl2nda`). C'est une messagerie web React + Vite +
> Firebase à 2 utilisateurs, déjà complète et qui build. Lis `HANDOFF.md`,
> `README.md` et `SETUP.md` pour le contexte. Tâche : [décrire ici]. »
