import { createContext, useState } from "react";
import product1 from "../assets/images/used_textbook.jpg"
import product2 from "../assets/images/desk_chair.jpg"
import product3 from "../assets/images/laptop_charger.jpg"
import product4 from "../assets/images/headphones.jpeg"



export const ListingsContext = createContext();

export function ListingsProvider({ children }) {
  const [listings, setListings] = useState([
    {
      id: 1,
      title: "Used Operating Systems Textbook",
      description: "A great intro CS book.",
      price: "$50",
      address: "Sennot Square",
      category: "Books",
      image: product1
    },
    {
      id: 2,
      title: "Premium Desk Chair",
      description: "A reliable chair",
      price: "$100",
      address: "Cathedral of Learning",
      category: "Furniture",
      image: product2
    },
    {
      id: 3,
      title: "Laptop Charger",
      description: "Used laptop charger",
      price: "$15",
      address: "Alumni Hall",
      category: "Electronics",
      image: product3
    },
    {
      id: 4,
      title: "Bluetooth Headphones",
      description: "Just purchased, but were not for me",
      price: "$60",
      address: "Benedum Hall",
      category: "Electronic",
      image: product4
    }

  ]);

  const addListing = (listing) => {
    setListings((prev) => [
      ...prev,
      { id: prev.length + 1, ...listing }
    ]);
  };

  return (
    <ListingsContext.Provider value={{ listings, addListing }}>
      {children}
    </ListingsContext.Provider>
  );
}
