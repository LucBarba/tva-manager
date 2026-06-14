//
// services/firestoreService.js
// Accès bas niveau à Firestore : références, lectures, écritures, listeners,
// transactions. Les repositories s'appuient sur ce service.
//

import {
  collection,
  doc,
  getDoc,
  getDocs,
  setDoc,
  updateDoc,
  addDoc,
  onSnapshot,
  query,
  orderBy,
  limit,
  where,
  serverTimestamp,
  runTransaction,
  increment,
  writeBatch,
} from 'firebase/firestore'
import { db } from '../firebase/config'

export const firestoreService = {
  db,
  serverTimestamp,
  increment,

  // --- Références ---
  collectionRef(path) {
    return collection(db, path)
  },
  docRef(path, id) {
    return id ? doc(db, path, id) : doc(collection(db, path))
  },
  subCollectionRef(parentPath, parentId, sub) {
    return collection(db, parentPath, parentId, sub)
  },

  // --- Lectures ---
  async getDoc(ref) {
    return getDoc(ref)
  },
  async getDocs(q) {
    return getDocs(q)
  },

  // --- Écritures ---
  async setDoc(ref, data, options = {}) {
    return setDoc(ref, data, options)
  },
  async updateDoc(ref, data) {
    return updateDoc(ref, data)
  },
  async addDoc(ref, data) {
    return addDoc(ref, data)
  },

  // --- Listeners temps réel ---
  listen(refOrQuery, onNext, onError) {
    return onSnapshot(refOrQuery, onNext, onError)
  },

  // --- Helpers de requête (réexportés) ---
  query,
  orderBy,
  limit,
  where,

  // --- Transactions / batch ---
  runTransaction(updateFn) {
    return runTransaction(db, updateFn)
  },
  batch() {
    return writeBatch(db)
  },
}
