import React, { useState, useEffect } from "react";
import SentMessage from "./SentMessage";
import RecievedMessage from "./RecievedMessage";

const ChatBox = () => {
    const [messages, setMessages] = useState([]);
    const [query, setQuery] = useState("");

    const handleSend = () => {
        let requestBody = {
            query: query,
        };
        setMessages((prevMessages) => [
            ...prevMessages,
            {
                content: query,
                role: "user",
            },
        ]);
        fetch("http://localhost:5000/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(requestBody),
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(data.response);
                setMessages((prevMessages) => [
                    ...prevMessages,
                    {
                        role: "assistant",
                        content: data.response,
                    },
                ]);
            })
            .catch((error) => {
                console.error("Error:", error);
            });

        setQuery("");
    };

    const renderMessages = () => {
        return messages.map((message, i) => {
            if (message.role === "user") {
                return <SentMessage key={i} message={message.content} />;
            } else {
                return <RecievedMessage key={i} message={message.content} />;
            }
        });
    };

    return (
        <div>
            {renderMessages()}
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
            />
            <button
                onClick={handleSend}
                disabled={query.length > 0 ? false : true}
            >
                Send
            </button>
        </div>
    );
};

export default ChatBox;
