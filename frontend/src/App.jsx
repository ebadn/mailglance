import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Emails from "./pages/Emails";
import "./App.css";

function App() {
  return (
    <Router>
      <header>
        <div className="nav-container">
          <Link to="/" className="nav-logo">📬 MailGlance</Link>
          <nav className="nav-links">
            <Link to="/">Home</Link>
            <Link to="/emails">Emails</Link>
          </nav>
        </div>
      </header>
      <main className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/emails" element={<Emails />} />
        </Routes>
      </main>
    </Router>
  );
}

export default App;
