import React from 'react';

const SentMessage = ({ message }) => {
  return (
    <div className="message sender">
        <p>{message}</p>
    </div>
  );
};

export default SentMessage;
