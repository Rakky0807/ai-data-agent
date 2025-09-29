import axios from 'axios';

// Point this to your FastAPI backend
const API_URL = 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  // ❌ Don't force Content-Type globally.
  // Axios will set the correct one automatically:
  // - application/json for normal requests
  // - multipart/form-data for FormData uploads
});

export default apiClient;
