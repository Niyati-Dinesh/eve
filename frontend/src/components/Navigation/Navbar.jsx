import "./navbar.css";
import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { TextAlignJustify } from "lucide-react";

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const active = location.pathname;

  const links = [
    { label: "Home", id: "/home" },
    { label: "About", id: "/about" },
    { label: "Get Started", id: "/login" }
  ];

  return (
    <div id="navbar" className={menuOpen ? "expanded" : ""}>
      <div className="brand">
        <div className="brand-name">
          <h1>E.v.e</h1>
        </div>

        <div className={`brand-links ${menuOpen ? "open" : ""}`}>
          {links.map((link) => (
            <Link
              to={link.id}
              key={link.id}
              className={`nav-link ${active === link.id ? "active" : ""}`}
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <button
          className="navbar-toggler"
          onClick={() => setMenuOpen((prev) => !prev)}
        >
          <TextAlignJustify />
        </button>
      </div>
    </div>
  );
}
