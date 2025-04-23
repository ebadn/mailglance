import React, { useEffect, useState } from "react";
import "../App.css";

const Emails = () => {
  const [emails, setEmails] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5000/emails", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        console.log("API response:", typeof data, data);
        setEmails(data);
      })
      .catch((err) => console.error("Error fetching emails:", err));
  }, []);

  return (
    <div className="App">
      <h2 className="email-heading">Your Summarized Emails</h2>
      {emails.length === 0 ? (
        <p className="email-empty">No emails found.</p>
      ) : (
        <div className="email-list">
          {emails.map((email, index) => (
            <div key={email.id}>
              <div className="email-card">
                <h3>{email.subject || "No Subject"}</h3>
                <p><strong>From:</strong> {email.from}</p>
                <p>{email.summary}</p>
                <a
                  href={`https://mail.google.com/mail/u/0/#inbox/${email.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "inline-block",
                    marginTop: "1rem",
                    color: "#007bff",
                    textDecoration: "none",
                    fontWeight: "bold",
                  }}
                >
                  Open in Gmail →
                </a>
              </div>
              {index !== emails.length - 1 && <hr className="email-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Emails;
