import React from "react";
import bulb from "../bulb.png";

const ReceivedMessage = ({ message }) => {
    return (
        <div className="receiver-container">
            <button className="copy-button">
                <i className="fa fa-clipboard fa-bounce"></i>
            </button>
            <img className="bulb" src={bulb} alt="bulb" />

            <div className="message receiver">
                <p>{message}</p>
            </div>
        </div>
    );
};

export default ReceivedMessage;
