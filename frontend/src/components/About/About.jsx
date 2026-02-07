import React, { useEffect, useRef } from "react";
import "./About.css";
import aboutVideo1 from "/about_video1.mp4";
import aboutVideo2 from "/about_video2.mp4";

const About = () => {
  const scrollRefs = useRef([]);

  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
        }
      });
    }, observerOptions);

    scrollRefs.current.forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => observer.disconnect();
  }, []);

  const addToRefs = (el) => {
    if (el && !scrollRefs.current.includes(el)) {
      scrollRefs.current.push(el);
    }
  };

  return (
    <div className="about">
      {/* Hero Section */}
      <div className="section hero js_detect-scroll" ref={addToRefs}>
        <div className="bg-video">
          <video src={aboutVideo1} autoPlay playsInline muted loop />
        </div>
        <h1 className="title">
          Intelligent AI
          <br />
          Orchestration
        </h1>
        <div className="text">
          Building a versatile execution engine where AI efficiency meets
          intelligent task distribution
        </div>
      </div>

   

      {/* Why EVE Exists Section */}
      <div className="exists">
        <div className="wrap">
          <div className="text js_detect-scroll" ref={addToRefs}>
            <h2 className="title">
              Why
              <br />
              E.V.E. Exists?
            </h2>
            <div className="descr">
              Current AI systems suffer from inefficient resource utilization
              and lack of task specialization. We're changing this paradigm by
            </div>
          </div>

          <div className="media">
            <video src={aboutVideo2} autoPlay playsInline muted loop />
          </div>

          <ol className="js_detect-scroll" ref={addToRefs}>
            <li>
              Automatic Model Selection AI-driven routing to the most suitable
              worker for each task
            </li>
            <li>
              Hybrid Worker Architecture Efficient mix of generalist and
              specialist AI nodes
            </li>
            <li>
              Zero-Lag Intelligence Synthetic warm-up ensures optimization from
              first interaction
            </li>
            <li>
              Context Continuity Seamless multi-turn interactions with session
              memory
            </li>
            <li>
              Fault-Tolerant Design Master-level failover for uninterrupted
              orchestration
            </li>
            <li>
              Performance Optimization Data-driven decision making through
              historical metrics
            </li>
          </ol>
        </div>
      </div>

      {/* Roadmap Section */}
      <div className="roadmap">
        <div className="wrap js_detect-scroll" ref={addToRefs}>
          <h2 className="title top-title">Roadmap</h2>
          <div className="swiper">
            <ul className="swiper-wrapper">
              <li className="swiper-slide">
                <div className="small">Phase 1</div>
                <h3 className="title">Foundation</h3>
                <div className="descr">
                  <ul>
                    <li>Master-Worker architecture setup</li>
                    <li>Basic routing implementation</li>
                    <li>Initial worker node deployment</li>
                  </ul>
                </div>
              </li>
              <li className="swiper-slide">
                <div className="small">Phase 2</div>
                <h3 className="title">Intelligence</h3>
                <div className="descr">
                  <ul>
                    <li>AI-driven routing optimization</li>
                    <li>Context engine integration</li>
                    <li>Performance metrics tracking</li>
                  </ul>
                </div>
              </li>
              <li className="swiper-slide">
                <div className="small">Phase 3</div>
                <h3 className="title">Scale</h3>
                <div className="descr">
                  <ul>
                    <li>Fault tolerance mechanisms</li>
                    <li>Advanced worker specialization</li>
                    <li>Production deployment</li>
                  </ul>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Join/CTA Section */}
      <div className="join">
        <div className="bg"></div>
        <div className="text js_detect-scroll" ref={addToRefs}>
          <h2 className="title">
            Be A Part Of The 
            <br />
            Future
          </h2>
          <div className="descr">
            Discover how intelligent AI orchestration can transform your
            workflow. Join us in building a more efficient and reliable AI
            execution ecosystem.
          </div>
          <button className="btn btn-secondary">
            <span>Get Started</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default About;
