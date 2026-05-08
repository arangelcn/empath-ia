import { initializeApp } from 'firebase/app';
import { getAnalytics } from 'firebase/analytics';

const firebaseConfig = {
  apiKey: "AIzaSyA6D3J58yB0wsbVR5QOJV9ycqnc5yWOERU",
  authDomain: "empathia-491822.firebaseapp.com",
  projectId: "empathia-491822",
  storageBucket: "empathia-491822.firebasestorage.app",
  messagingSenderId: "65044405357",
  appId: "1:65044405357:web:6cb232056de72dbdb7b364",
  measurementId: "G-Y11CSQ0B28",
};

export const app = initializeApp(firebaseConfig);
export const analytics = getAnalytics(app);
