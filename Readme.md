# CMPE 273 Hackathon (RAGBot)

## Project Architecture

![Architecture](HackathonArchitecture.jpg)

## Demo Screenshots
![No Prompt](screenshots/Empty.png)
![One Prompt](screenshots/Sustainability-Statements.png)
![Two Prompt](screenshots/SocialSustainability.png)


## Getting Started
### Prerequisites: 
NodeJS & NPM - Install Guides can be found [official Node.js website](https://nodejs.org/)

Docker - Install Guides can be found [official Docker website](https://www.docker.com/get-started/)

An OpenAI API Key

### Start Backend
Add your OPEN AI API key to the docker compose file, then run
```
docker compose up
```

### Start Frontend
```
cd chat-frontend
npm install
npm start
```
