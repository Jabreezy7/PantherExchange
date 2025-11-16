import React from "react";
import { Link } from "react-router-dom";
import logo from "../assets/images/pitt_logo.png";
import "./Header.css";

function Header() {
  return (
    <header className="header-bar">

      <div className="header-left">
        <Link to="/">
          <img src={logo} alt="Pitt Logo" className="header-logo" />
        </Link>
        <div className="header-center">
          <input
            type="text"
            placeholder="Search..."
            className="header-search"
          />
        </div>
      </div>


      <div className="header-right">
        <button className="sign-in-btn">Sign In</button>
        <button className="register-btn">Register</button>
      </div>
    </header>
  );
}

export default Header;
