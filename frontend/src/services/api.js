// import axios from 'axios';

// const API_BASE = 'http://localhost:8000';

// export const analyzeCall = async (data) => {
//   try {
//     const res = await axios.post(`${API_BASE}/analyze-call`, data);
//     return res.data;
//   } catch (error) {
//     console.error('API Error:', error);
//     throw error;
//   }
// };
import axios from "axios";

const API_BASE = "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
});

// attach token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const signup = (username, password) =>
  api.post("/auth/signup", { username, password });

export const login = (username, password) =>
  api.post("/auth/login", { username, password });

export const uploadMedia = (callerId, audioFile, videoFile) => {
  const form = new FormData();
  form.append("caller_id", callerId);
  if (audioFile) form.append("audio", audioFile);
  if (videoFile) form.append("video", videoFile);
  return api.post("/media/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
