import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5001",
});

export const getListings = (category) => {
  const params = category && category !== "All" ? { category } : {};
  return API.get("/api/listing", { params });
};

export const addListing = (data) => {
  return API.post("/api/listing", data, {
    headers: { "Content-Type": "application/json" },
  });
};
