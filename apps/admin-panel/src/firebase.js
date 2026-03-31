import { initializeApp } from 'firebase/app';
import { getAnalytics } from 'firebase/analytics';

const firebaseConfig = {
  apiKey: "AIzaSyA6D3J58yB0wsbVR5QOJV9ycqnc5yWOERU",
  authDomain: "empathia-491822.firebaseapp.com",
  projectId: "empathia-491822",
  storageBucket: "empathia-491822.firebasestorage.app",
  messagingSenderId: "65044405357",
  appId: "1:65044405357:web:946b5f7b687b78ddb7b364",
  measurementId: "G-2E7X8EQEBG",
};

export const app = initializeApp(firebaseConfig, 'admin');
export const analytics = getAnalytics(app);
