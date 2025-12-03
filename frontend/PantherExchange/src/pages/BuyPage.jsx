import React, { useEffect, useState } from "react";
import Header from "../components/Header";
import "./BuyPage.css";
import { getListings } from "../services/api";


import electronicsIcon from "../assets/images/electronic_icon.png";
import booksIcon from "../assets/images/book_icon.png";
import furnitureIcon from "../assets/images/furniture_icon.png";
import allIcon from "../assets/images/all_icon.png";

const categoryIcons = {
  Electronics: electronicsIcon,
  Books: booksIcon,
  Furniture: furnitureIcon,
  All: allIcon,
};

function BuyPage() {
  const [listings, setListings] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const categories = ["All", "Electronics", "Books", "Furniture"];

  const fetchListings = async (category) => {
    setLoading(true);
    setError(null);
    try {
      const response = await getListings(category);
      setListings(response.data.data);
    } catch (err) {
      console.error("Error fetching listings:", err);
      setError("Failed to load listings. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings(selectedCategory);
  }, [selectedCategory]);

  return (
    <div className="buy-page">
      <Header />

      <div className="buy-page-content">
        <aside className="category-sidebar">
          <h3>Categories</h3>
          <ul>
            {categories.map((cat) => (
              <li
                key={cat}
                className={cat === selectedCategory ? "active" : ""}
                onClick={() => setSelectedCategory(cat)}
              >
                {categoryIcons[cat] && (
                  <img
                    src={categoryIcons[cat]}
                    alt={cat}
                    className="category-icon"
                  />
                )}
                {cat}
              </li>
            ))}
          </ul>
        </aside>

        <main className="listing-section">
          <h1>Available Listings</h1>

          {loading && <p>Loading listings...</p>}
          {error && <p className="error-message">{error}</p>}

          {!loading && !error && (
            <div className="listing-grid">
              {listings.map((item) => (
                <div className="listing-card" key={item.id}>
                  {item.image ? (
                    <img
                      src={item.image}
                      alt={item.title}
                      className="listing-image"
                    />
                  ) : (
                    <div className="placeholder-image">No Image</div>
                  )}

                  <p className="price">{item.price}</p>
                  <h3>{item.title}</h3>
                  <p className="address">{item.address}</p>

                  <button className="buy-btn">Buy</button>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default BuyPage;
