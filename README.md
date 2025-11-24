# Pak News Journal Archive

## Overview

A comprehensive AI-powered transcription system designed to preserve Pakistan's broadcast history through automated Urdu language transcription. The system converts video and audio files into accurate, timestamped text transcriptions using OpenAI's Whisper AI model.

## Features

- **AI-Powered Transcription**: Utilizes OpenAI Whisper for accurate Urdu language transcription
- **Real-time Processing**: Live feedback during transcription process
- **User Authentication**: Secure JWT-based authentication system
- **Database Storage**: PostgreSQL for storing videos, transcriptions, and user data
- **Audio Processing**: Advanced audio preprocessing with noise reduction
- **Modern UI**: Glassmorphic interface with cyberpunk aesthetics
- **3D Visualization**: Interactive globe component for geographical context

## Tech Stack

### Backend
- **Python Flask**: REST API server
- **OpenAI Whisper**: AI transcription model
- **PostgreSQL**: Database
- **FFmpeg**: Audio/video processing
- **JWT**: Authentication
- **Flask-CORS**: Cross-origin support

### Frontend
- **React**: UI framework
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **Framer Motion**: Animations
- **Three.js**: 3D graphics
- **React Router**: Navigation

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL
- FFmpeg

### Backend Setup
1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Configure database connection and JWT secret

5. Initialize database:
   ```bash
   python database/setup_db.py
   ```

### Frontend Setup
1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

## Usage

1. Start the backend server:
   ```bash
   cd backend
   python app.py
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Access the application at `http://localhost:5173`

## API Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/transcribe` - Upload and transcribe video/audio
- `GET /api/transcriptions` - Get user's transcriptions

## Project Structure

```
pak-news-journal-archive/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── database/
│   ├── routes/
│   ├── utils/
│   └── logs/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── contexts/
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.