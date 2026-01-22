import "./navbar.css";
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { TextAlignJustify } from "lucide-react";

export default function Navbar() {
  const [active, setActive] = useState("/home");
  const [menuOpen, setMenuOpen] = useState(false);

  const links = [
    { label: "Home", id: "/home" },
    { label: "About", id: "/about" },
    { label: "Contact", id: "/contact" },
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
              onClick={() => {
                setActive(link.id);
                setMenuOpen(false);
              }}
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
