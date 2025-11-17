import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000",
});

export const getListings = (category) => {
  const params = category && category !== "All" ? { category } : {};
  return API.get("/listings", { params });
};

export const addListing = (data) => {
  return API.post("/listings", JSON.stringify(data), {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
