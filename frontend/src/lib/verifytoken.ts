import axios from "axios";
export default async function verifyToken(token) {
    const backendUrl = import.meta.env.BACKEND_URL
    try {
        const response = await axios.post(`${backendUrl}/api/auth/token/verify/`, {
            token
        });
        return true
    } catch (error) {
        return false
    }
}