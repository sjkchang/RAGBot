import React from "react";
import ChatBox from "./ChatBox"
import "./ChatContainer.css"; // Import the CSS file for styling
import gpt from "../gpt.png"

const ChatContainer = () => {
    return (
        <div className="chat-container">
            <div className="chat-heading">
                Economic and Sustainability of Marginalized and Highly
                Vulnerable communities
                <img className="gpt-logo" src={gpt} alt="gpt" />
            </div>
            <center>
                <h1>Budget Prompt</h1>
            </center>
            <ChatBox />
            
        </div>
    );
};

export default ChatContainer;
