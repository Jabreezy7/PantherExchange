import React, { useState } from "react";
import Header from "../components/Header";
import { addListing as addListingAPI } from "../services/api";
import "./SellPage.css";

function SellPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [address, setAddress] = useState("");
  const [image, setImage] = useState(null);
  const [category, setCategory] = useState("Electronics");
  const [showSuccess, setShowSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {

      let imageData = null;

      if (image) {
        imageData = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target.result);
          reader.readAsDataURL(image);
        });
      }

      const formData = {
        title,
        description,
        price: Number(price),
        address,
        category,
        image: imageData,
      };

      await addListingAPI(formData);

      setTitle("");
      setDescription("");
      setPrice("");
      setAddress("");
      setImage(null);
      setCategory("Electronics");

      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error(error);
      setErrorMessage("Failed to submit listing. Please try again.");
      setTimeout(() => setErrorMessage(""), 3000);
    }
  };

  return (
    <div className="sell-page">
      <Header />

      <div className="sell-page-content">
        <h1 className="sell-header">Create a Listing</h1>

        <form className="sell-form" onSubmit={handleSubmit}>
          <label>
            Product Title:
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>

          <label>
            Description:
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} required />
          </label>

          <label>
            Price ($):
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              required
            />
          </label>

          <label>
            Address:
            <input value={address} onChange={(e) => setAddress(e.target.value)} required />
          </label>

          <label>
            Image:
            <input type="file" onChange={(e) => setImage(e.target.files[0])} />
          </label>

          <label>
            Category:
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option>Electronics</option>
              <option>Books</option>
              <option>Furniture</option>
              <option>Clothing</option>
              <option>Other</option>
            </select>
          </label>

          <button className="submit-btn" type="submit">Submit Listing</button>
        </form>

        {showSuccess && (
          <div className="popup-message">
            You have successfully created a listing!
          </div>
        )}

        {errorMessage && (
          <div className="popup-message" style={{ backgroundColor: "#d9534f" }}>
            {errorMessage}
          </div>
        )}
      </div>
    </div>
  );
}

export default SellPage;
