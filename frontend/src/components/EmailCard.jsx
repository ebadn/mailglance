import React from 'react';

const EmailCard = ({ subject, from, summary, messageId }) => {
  const gmailLink = `https://mail.google.com/mail/u/0/#inbox/${messageId}`;

  return (
    <div className="bg-white shadow-md rounded-2xl p-4 mb-4 transition-all duration-200 hover:shadow-lg">
      <h2 className="text-xl font-bold text-gray-800 mb-1">
        {subject && subject.trim() !== "" ? subject : "No Subject"}
      </h2>
      <p className="text-sm text-gray-600 mb-2">From: {from}</p>
      <p className="text-base text-gray-700 mb-4">{summary}</p>
      <a
        href={gmailLink}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
      >
        Open in Gmail
      </a>
    </div>
  );
};

export default EmailCard;
