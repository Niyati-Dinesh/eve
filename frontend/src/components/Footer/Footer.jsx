import React from "react";
import { Mail } from "lucide-react";
import "./footer.css"
export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-bg"></div>

      <div className="footer-inner">
        {/* Top Section */}
        <div className="footer-top">
          <div className="footer-logo-block">
            <img src="logo-transparent.png" alt="EVE Logo" className="footer-logo" />
            <p className="footer-tagline">Execution Versatility Engine</p>
          </div>

          <div className="footer-nav">
            <a href="#home">Home</a>
            <a href="https://naicoits.com/" target="_blank">Company</a>
            <a href="#contact" target="_blank">Contact</a>
          </div>
        </div>

        <div className="footer-divider"></div>

        {/* Bottom Section */}
        <div className="footer-bottom">
          <div className="footer-email-block">
            <a href="mailto:ignite.techteam33@gmail.com" className="footer-email">
              <Mail size={18} />
              <span>ignite.techteam33@gmail.com</span>
            </a>
          </div>

          <div className="footer-links">
            <a href="#">Terms & conditions</a>
            <a href="#">Privacy Policy</a>
            <a href="#">Cookie Policy</a>
            <p>© {new Date().getFullYear()} EVE, All rights reserved</p>
          </div>
        </div>
      </div>

      <div className="footer-bottom-gradient"></div>
    </footer>
  );
}
