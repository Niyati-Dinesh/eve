import React from "react";
import About from "./components/About/About";
import Navbar from "./components/Navigation/Navbar";
import ScrollToTop from "./components/ScrollToTop";
import Footer from "./components/Footer/Footer";
import { Route, Routes } from "react-router-dom";
import Main from "./components/Home/Main";
import AuthComponent from "./components/Auth/AuthComponent";
export default function App() {
  return (
    <div className="app">
      <ScrollToTop/>
      <Navbar />
      <main className="app-main">
        <Routes>
          <Route path="/home" element={<Main />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<AuthComponent />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
