

# VoiceSaas

**VoiceSaas** is a comprehensive, production-ready platform designed to build and scale Voice AI applications. Whether you are building an AI voice assistant, an automated transcription service, or a voice-over generator, this repository provides the foundation for handling voice processing, LLM orchestration, and user management.

##  Features

- **Real-time Voice Processing**: High-fidelity speech-to-text (STT) and text-to-speech (TTS) integration.
- **AI Orchestration**: Intelligent dialogue management powered by OpenAI GPT-4 / Claude 3.5.
- **Multiple Voice Providers**: Seamless integration with ElevenLabs, Deepgram, and OpenAI TTS.
- **User Authentication**: Secure sign-in and session management (powered by Clerk/NextAuth).
- **Subscription Management**: Full Stripe integration for recurring billing and credit usage.
- **Dashboard Analytics**: Track usage, costs, and voice interactions in a clean UI.
- **Optimized Latency**: Low-latency WebSocket connections for real-time voice interactions.

##  Tech Stack

- **Frontend**: [Next.js](https://nextjs.org/) (React), Tailwind CSS, Lucide Icons
- **Backend**: Next.js API Routes / Node.js
- **Database**: PostgreSQL with [Prisma ORM](https://www.prisma.io/) or [Drizzle](https://orm.drizzle.team/)
- **Voice APIs**: ElevenLabs (TTS), Deepgram (STT), Whisper (STT)
- **AI Logic**: LangChain / Vercel AI SDK
- **Payments**: [Stripe](https://stripe.com/)
- **Auth**: [Clerk](https://clerk.dev/) or [Auth0](https://auth0.com/)

##  Getting Started

### Prerequisites

- Node.js 18.x or higher
- A package manager (npm, yarn, or pnpm)
- API keys for OpenAI, ElevenLabs, and Stripe

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rameshramaswamy/VoiceSaas.git
   cd VoiceSaas
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   Create a `.env.local` file in the root directory and add the following:
   ```env
   # App
   NEXT_PUBLIC_APP_URL=http://localhost:3000

   # Database
   DATABASE_URL="your-postgresql-url"

   # AI Providers
   OPENAI_API_KEY="your-openai-api-key"
   ELEVENLABS_API_KEY="your-elevenlabs-api-key"
   DEEPGRAM_API_KEY="your-deepgram-api-key"

   # Auth (Clerk Example)
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
   CLERK_SECRET_KEY=

   # Billing (Stripe)
   STRIPE_API_KEY=
   STRIPE_WEBHOOK_SECRET=
   ```

4. **Initialize the database:**
   ```bash
   npx prisma db push
   ```

5. **Run the development server:**
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) to see the result.

##  Architecture

The project follows a modular architecture:
- `/app`: Next.js App Router components and pages.
- `/components`: Reusable UI components (shadcn/ui).
- `/lib`: Utility functions, API clients, and shared logic.
- `/hooks`: Custom React hooks for voice recording and playback.
- `/api`: Server-side routes for handling sensitive operations and webhooks.

##  Contributing

Contributions are welcome! Please follow these steps:
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

##  License

Distributed under the MIT License. See `LICENSE` for more information.
