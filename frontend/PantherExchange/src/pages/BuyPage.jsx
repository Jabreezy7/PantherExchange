import React, { useContext, useState } from "react";
import Header from "../components/Header";
import { ListingsContext } from "../context/ListingsContext";
import "./BuyPage.css";


import electronicsIcon from "../assets/images/electronic_icon.png";
import booksIcon from "../assets/images/book_icon.jpg";
import furnitureIcon from "../assets/images/furniture_icon.jpg";
import allIcon from "../assets/images/all_icon.png";

const categoryIcons = {
  Electronics: electronicsIcon,
  Books: booksIcon,
  Furniture: furnitureIcon,
  All: allIcon
};

function BuyPage() {
  const { listings } = useContext(ListingsContext);
  const [selectedCategory, setSelectedCategory] = useState("All");

  const filteredListings =
    selectedCategory === "All"
      ? listings
      : listings.filter(item => item.category === selectedCategory);

  const categories = ["All", "Electronics", "Books", "Furniture"];

  return (
    <div className="buy-page">
      <Header />

      <div className="buy-page-content">
        <aside className="category-sidebar">
          <h3>Categories</h3>
          <ul>
            {categories.map((cat, index) => (
              <li
                key={index}
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
          <div className="listing-grid">
            {filteredListings.map(item => (
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
                <p className="address"> {item.address}</p>

                <button className="buy-btn">Buy</button>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}

export default BuyPage;
