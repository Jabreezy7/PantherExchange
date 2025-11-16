import React from "react";
import { Link } from "react-router-dom";
import pittLogo from "../assets/images/pitt_logo.png";
import '../App.css';
import saveMoneyIcon from "../assets/images/discount_tag.png";
import easyUseIcon from "../assets/images/minimal_icon.png";
import trustedIcon from "../assets/images/trust_icon.png";


function HomePage() {
  return (
    <div className="App">
      <header className="header">
        <img src={pittLogo} alt="University of Pittsburgh Logo" className="logo" />
        <h1>PantherExchange</h1>
        <p>Buy and sell items with fellow University of Pittsburgh students!</p>
        <nav>
          <Link to="/buy" className="btn">Buy Items</Link>
          <Link to="/sell" className="btn">Sell Items</Link>
        </nav>
      </header>

      <main>
        <section className="section about">
          <h2>About PantherExchange</h2>
          <p>PantherExchange is a student-run marketplace for the University of Pittsburgh community. Safe, simple, and convenient.</p>


          <div className="info-cards">
            <div className="info-card">
              <img src={saveMoneyIcon} alt="Save Money" className="info-card-icon" />
              <h3>Save Money</h3>
              <p>Find affordable textbooks, electronics, and furniture from fellow students.</p>
            </div>

            <div className="info-card">
              <img src={easyUseIcon} alt="Easy to Use" className="info-card-icon" />
              <h3>Easy to Use</h3>
              <p>Simple interface lets you browse, buy, and sell in just a few clicks.</p>
            </div>

            <div className="info-card">
              <img src={trustedIcon} alt="Trusted Community" className="info-card-icon" />
              <h3>Trusted Community</h3>
              <p>Connect directly with other Pitt students for a safe and reliable transaction.</p>
            </div>
          </div>

        </section>
      </main>

      <footer className="footer">
        <p>&copy; 2025 PantherExchange. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default HomePage;
