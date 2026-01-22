import React from "react"
import { Link } from "react-router-dom"
import "./home.css"

export default function Home() {
  return (
    <section id="home">
      <video
        src="/home.mp4"
        autoPlay
        loop
        muted
        playsInline
        className="hero-video"
      />

      <div className="hero-content">
        <h1 className="hero-title">
          Efficient,<br />
          adaptive,<br />
          and <span className="seamless">seamless</span><br />
          execution
        </h1>

        <p className="hero-sub">
          Revolutionizing AI orchestration
        </p>

        <Link to="/login" className="hero-cta">
          Join us
        </Link>
      </div>
    </section>
  )
}
