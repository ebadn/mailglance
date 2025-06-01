import React, { useEffect, useState } from "react";
import "../App.css";
import filterIcon from '../components/filter.png';

const Emails = () => {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterOpen, setFilterOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedDateFilter, setSelectedDateFilter] = useState('');
  const [selectedLabels, setSelectedLabels] = useState([]);
  const [selectedDetail, setSelectedDetail] = useState('short');
  const [searchQuery, setSearchQuery] = useState("");

  const filteredEmails = emails.filter((email) => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    const searchMatch =
      normalizedQuery === "" ||
      (email.subject && email.subject.toLowerCase().includes(normalizedQuery)) ||
      (email.from && email.from.toLowerCase().includes(normalizedQuery)) ||
      (email.summary && email.summary.toLowerCase().includes(normalizedQuery));

    let dateMatch = true;
    if (selectedDateFilter) {
      const emailDate = new Date(email.date);
      const now = new Date();
      if (selectedDateFilter === "Today") {
        const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        dateMatch = emailDate >= startOfDay;
      } else if (selectedDateFilter === "This Week") {
        const weekAgo = new Date(now);
        weekAgo.setDate(now.getDate() - 7);
        dateMatch = emailDate >= weekAgo;
      } else if (selectedDateFilter === "This Month") {
        const monthAgo = new Date(now);
        monthAgo.setMonth(now.getMonth() - 1);
        dateMatch = emailDate >= monthAgo;
      }
    }

    const labelMatch = selectedLabels.length === 0 || selectedLabels.some(label => email.labels.includes(label));

    return searchMatch && dateMatch && labelMatch;
  });

  const fetchEmails = () => {
    setLoading(true);
    fetch(`http://localhost:5000/emails?detail=${selectedDetail}`, { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        console.log("API response:", typeof data, data);
        setEmails(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching emails:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchEmails();
  }, []);

  return (
    <div className="App">
      <div className="sticky-toolbar">
        <div className="controls-row">
          <input
            type="text"
            placeholder="Search emails by subject, sender, or keyword..."
            className="search-bar"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <div className="dropdown-group">
            {/* Filter Button */}
            <button className="dropdown-btn" onClick={() => setFilterOpen(!filterOpen)}>
              Filter <img src={filterIcon} alt="Filter" className="filter-icon" />
            </button>
            {filterOpen && (
              <div className="dropdown-card">
                <strong>Filter by Date</strong>
                {["Today", "This Week", "This Month"].map((option) => (
                  <label key={option}>
                    <input
                      type="radio"
                      name="dateFilter"
                      value={option}
                      checked={selectedDateFilter === option}
                      // onChange={(e) => setSelectedDateFilter(e.target.value)}
                    />
                    {option}
                  </label>
                ))}

                <strong style={{ marginTop: "1rem" }}>Filter by Label</strong>
                {["Inbox", "Starred", "Important", "Sent"].map((label) => (
                  <label key={label}>
                    <input
                      type="checkbox"
                      value={label}
                      checked={selectedLabels.includes(label)}
                      onChange={(e) => {
                        const { value, checked } = e.target;
                        // setSelectedLabels((prev) =>
                        //   checked ? [...prev, value] : prev.filter((v) => v !== value)
                        // );
                      }}
                    />
                    {label}
                  </label>
                ))}

                <div className="dropdown-footer">
                  <button onClick={() => setFilterOpen(false)}>Apply Filters</button>
                </div>
              </div>
            )}

            {/* Detail Button */}
            <button className="dropdown-btn" onClick={() => setDetailOpen(!detailOpen)}>
              Detail
            </button>
            {detailOpen && (
              <div className="dropdown-card">
                <strong>Summary Length</strong>
                {["Short", "Medium", "Long"].map((option) => (
                  <label key={option}>
                    <input
                      type="radio"
                        name="summaryLength"
                        value={option.toLowerCase()}
                        checked={selectedDetail === option.toLowerCase()}
                        onChange={(e) => setSelectedDetail(e.target.value)}
                    />
                    {option}
                  </label>
                ))}
                <div className="dropdown-footer">
                  <button
                    onClick={() => {
                      setDetailOpen(false);
                      fetchEmails(); 
                    }}
                  >
                    Apply
                  </button>
                </div>
              </div>
            )}
          </div>

          <button className="refresh-btn" onClick={fetchEmails}>
            🔄 Refresh
          </button>
        </div>
      </div>
      

      <h2 className="email-heading">Your Summarized Emails</h2>
      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading emails...</p>
        </div>
      ) : filteredEmails.length === 0 ? (
        <p className="email-empty">No emails found.</p>
      ) : (
        <div className="email-list">
          {filteredEmails.map((email, index) => (
            <div key={email.id}>
              <div className="email-card">
                <h3>{email.subject || "No Subject"}</h3>
                <p>
                  <strong>From:</strong>{' '}
                  {email.from.replace(/<.*>/, '')} {/* Name part only */}
                  <span className="blurred-email">{
                    email.from.match(/<.*>/)?.[0] || ''
                  }</span>
                </p>
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
              {index !== filteredEmails.length - 1 && <hr className="email-divider" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Emails;
