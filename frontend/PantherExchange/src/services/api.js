import axios from "axios";

const API_BASE = "http://localhost:5001";

export const getListings = async (category) => {
  if(category !== "All") {
    return axios.get(`${API_BASE}/items/?category=${encodeURIComponent(category)}`);
  }
  return axios.get(`${API_BASE}/items/`);
};

export const addListing = (listingData) => {
  return axios.post(`${API_BASE}/items/`, listingData)
}
