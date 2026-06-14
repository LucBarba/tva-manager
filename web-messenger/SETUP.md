# Guide de configuration Firebase — pas à pas

Suivez ces étapes dans l'ordre. Comptez ~10 minutes. À la fin, l'application est
pleinement fonctionnelle (création de compte, messages temps réel, médias).

---

## 1. Créer le projet Firebase

1. Allez sur <https://console.firebase.google.com> et connectez-vous.
2. Cliquez **« Ajouter un projet »**, donnez-lui un nom (ex. `duochat`), validez.
   (Vous pouvez désactiver Google Analytics, inutile ici.)

## 2. Activer l'authentification par email

1. Menu de gauche → **Build → Authentication** → **Get started**.
2. Onglet **Sign-in method** → **Email/Password** → **Activer** (le premier
   interrupteur suffit) → **Enregistrer**.

> La vérification d'email est gérée automatiquement par le code (envoi du lien
> à l'inscription). Aucun réglage supplémentaire requis.

## 3. Créer la base Firestore

1. Menu → **Build → Firestore Database** → **Create database**.
2. Choisissez un emplacement (ex. `eur3`), mode **production** → **Activer**.
   (Les règles de sécurité du repo seront déployées à l'étape 8.)

## 4. Activer Storage

1. Menu → **Build → Storage** → **Get started** → acceptez → **Activer**.

## 5. Récupérer la configuration Web

1. Roue dentée ⚙️ (en haut à gauche) → **Paramètres du projet**.
2. Onglet **Général**, section **« Vos applications »** → icône **Web `</>`**.
3. Donnez un surnom (ex. `duochat-web`) → **Enregistrer l'application**.
4. Firebase affiche un objet `firebaseConfig`. Copiez chaque valeur.

## 6. Récupérer la clé VAPID (notifications push)

1. **Paramètres du projet** → onglet **Cloud Messaging**.
2. Section **« Configuration Web »** → **« Certificats push Web »** →
   **Generate key pair**.
3. Copiez la **clé publique** générée.

## 7. Renseigner le fichier `.env`

```bash
cd web-messenger
cp .env.example .env
```

Ouvrez `.env` et collez vos valeurs (depuis les étapes 5 et 6) :

```
VITE_FIREBASE_API_KEY=...                  # apiKey
VITE_FIREBASE_AUTH_DOMAIN=...              # authDomain
VITE_FIREBASE_PROJECT_ID=...               # projectId
VITE_FIREBASE_STORAGE_BUCKET=...           # storageBucket
VITE_FIREBASE_MESSAGING_SENDER_ID=...      # messagingSenderId
VITE_FIREBASE_APP_ID=...                   # appId
VITE_FIREBASE_VAPID_KEY=...                # clé publique VAPID (étape 6)
```

## 8. Déployer les règles de sécurité et les index

```bash
npm install -g firebase-tools
firebase login
# Mettez votre projectId dans .firebaserc (champ "default")

firebase deploy --only firestore:rules,firestore:indexes,storage
```

> Sans cette étape, la création des index peut prendre quelques minutes la
> première fois qu'une requête de messages est exécutée — c'est normal.

## 9. Lancer l'application

```bash
npm install
npm run dev
```

Ouvrez <http://localhost:5174>.

### Tester à deux
1. **Onglet 1** (navigateur normal) : inscrivez le 1er utilisateur, cliquez le
   lien de vérification reçu par email.
2. **Onglet 2** (fenêtre privée / navigation incognito) : inscrivez le 2e
   utilisateur et vérifiez son email.
3. Les deux se voient automatiquement et peuvent discuter en temps réel. 🎉

---

## 10. (Optionnel) Notifications push entre appareils

Les notifications **locales** (onglet ouvert) fonctionnent sans rien de plus.
Pour les notifications **push réelles** lorsque l'app est fermée :

```bash
cd firebase/functions && npm install && cd ../..
firebase deploy --only functions
```

> Le plan **Blaze** (paiement à l'usage, avec quota gratuit) est requis pour
> déployer des Cloud Functions. La fonction `enforceUserLimit` nécessite en plus
> **Identity Platform** (Authentication → Settings → Blocking functions) ; sinon
> commentez son export dans `firebase/functions/index.js`.

---

## Dépannage

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| `auth/operation-not-allowed` | Email/Password non activé | Étape 2 |
| `Missing or insufficient permissions` | Règles non déployées | Étape 8 |
| Les messages n'arrivent pas en temps réel | Index manquant | Attendez la création de l'index (lien dans la console des erreurs) ou étape 8 |
| Upload média échoue | Storage non activé / règles | Étapes 4 et 8 |
| Pas de notification push | VAPID manquante / Functions non déployées | Étapes 6 et 10 |
| « Inscriptions fermées » | 2 comptes existent déjà | Supprimez un utilisateur dans Authentication |
