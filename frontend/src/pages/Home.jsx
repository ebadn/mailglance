import React from "react";
import "../App.css";

function Home() {
  const handleLogin = () => {
    window.location.href = "http://localhost:5000/authorize";
  };

  return (
    <div className="home-container">
      <p className="home-description">
        <span className="main-line">
          Instantly summarize and browse through your Gmail with ease.
        </span>
        <br />
        <span className="sub-line">
          Fast, minimal, and distraction-free.
        </span>
      </p>

      <button onClick={handleLogin} className="sign-in-btn">
        Sign in with Google
      </button>
    </div>
  );
}

export default Home;
