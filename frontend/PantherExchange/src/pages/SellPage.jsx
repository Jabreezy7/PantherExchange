import React, { useState, useContext } from "react";
import Header from "../components/Header";
import { ListingsContext } from "../context/ListingsContext";
import "./SellPage.css";

function SellPage() {
  const { addListing } = useContext(ListingsContext);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [address, setAddress] = useState("");
  const [image, setImage] = useState(null);
  const [category, setCategory] = useState("Electronics");
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();

    const newListing = {
      title,
      description,
      price: "$" + price,
      address,
      category,
      image: image ? URL.createObjectURL(image) : null
    };

    addListing(newListing);

    setTitle("");
    setDescription("");
    setPrice("");
    setAddress("");
    setImage(null);
    setCategory("Electronics");

    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  return (
    <div className="sell-page">
      <Header />

      <h1>Sell an Item</h1>

      <form className="sell-form" onSubmit={handleSubmit}>

        <label>Product Title:
          <input value={title} onChange={e => setTitle(e.target.value)} required />
        </label>

        <label>Description:
          <textarea value={description} onChange={e => setDescription(e.target.value)} required />
        </label>

        <label>Price ($):
          <input
            type="number"
            value={price}
            onChange={e => setPrice(e.target.value)}
            required
          />
        </label>

        <label>Address:
          <input value={address} onChange={e => setAddress(e.target.value)} required />
        </label>

        <label>Image:
          <input type="file" onChange={e => setImage(e.target.files[0])} required />
        </label>

        <label>Category:
          <select value={category} onChange={e => setCategory(e.target.value)}>
            <option>Electronics</option>
            <option>Books</option>
            <option>Furniture</option>
            <option>Clothing</option>
            <option>Other</option>
          </select>
        </label>

        <button className="btn" type="submit">Submit Listing</button>
      </form>

      {showSuccess && (
        <div className="popup-message">
          🎉 You have successfully created a listing!
        </div>
      )}
    </div>
  );
}

export default SellPage;
