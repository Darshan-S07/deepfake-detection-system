import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const analyzeCall = async (data) => {
  try {
    const res = await axios.post(`${API_BASE}/analyze-call`, data);
    return res.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
