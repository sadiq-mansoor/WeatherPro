// API base URL. Empty in dev (uses CRA proxy in package.json).
// In production (Vercel), set REACT_APP_API_URL to your deployed backend URL.
const API_BASE = process.env.REACT_APP_API_URL || "";

export default API_BASE;
