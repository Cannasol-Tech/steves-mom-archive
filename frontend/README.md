# Steve's Mom AI Chatbot - Frontend

This is the React/TypeScript frontend for Steve's Mom AI Chatbot, built with Tailwind CSS for styling and React Router for navigation.

## Features

- **Modern React/TypeScript Setup**: Built with Create React App and TypeScript for type safety
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **React Router**: Client-side routing for single-page application navigation
- **Responsive Design**: Mobile-first responsive design that works on all devices
- **Component Architecture**: Well-organized component structure with reusable UI elements

## Project Structure

```
frontend/
├── public/
│   └── index.html          # Main HTML template
├── src/
│   ├── components/
│   │   └── Layout.tsx      # Main layout component with navigation
│   ├── pages/
│   │   ├── ChatPage.tsx    # Main chat interface
│   │   ├── AdminPage.tsx   # Admin panel with feature toggles
│   │   ├── InventoryPage.tsx # Inventory management interface
│   │   └── NotFoundPage.tsx # 404 error page
│   ├── types/
│   │   └── index.ts        # TypeScript type definitions
│   ├── App.tsx             # Main app component with routing
│   ├── index.tsx           # Application entry point
│   └── index.css           # Global styles with Tailwind imports
├── package.json            # Dependencies and scripts
├── tailwind.config.js      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── postcss.config.js       # PostCSS configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Git

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner in interactive watch mode
- `npm run build` - Builds the app for production to the `build` folder
- `npm run eject` - **Note: this is a one-way operation. Don't eject unless necessary!**

## Pages and Features

### Chat Page (`/` or `/chat`)
- Main chat interface with Steve's Mom AI
- Message history with timestamps
- Real-time typing indicators
- Responsive design for mobile and desktop

### Inventory Page (`/inventory`)
- Inventory item listing with search and filtering
- Summary statistics (total items, quantity, value)
- Table view with sorting capabilities
- Placeholder for Phase 6 integration

### Admin Page (`/admin`)
- Feature toggle controls
- System status monitoring
- Performance metrics dashboard
- Quick action buttons

## Styling and Design

The application uses Tailwind CSS with a custom design system:

- **Primary Colors**: Blue palette for main actions and branding
- **Secondary Colors**: Gray palette for text and backgrounds
- **Typography**: Inter font family for clean, modern text
- **Components**: Reusable CSS classes for buttons, cards, and form elements

## Integration Points

This frontend is designed to integrate with:

- **Azure Functions Backend**: API calls will be made to `/api/*` endpoints
- **Azure Static Web Apps**: Configured for deployment to Azure SWA
- **Authentication**: Placeholder for Azure AD integration (Phase 10)
- **Real-time Updates**: WebSocket support for live chat updates (Phase 3.5)

## Development Status

This is the initial UI shell implementation (Task 3.1). Future phases will add:

- **Phase 3.2-3.6**: Enhanced chat features, streaming, error handling
- **Phase 4**: AI model integration and context management
- **Phase 5**: Task generation and approval workflows
- **Phase 6**: Full inventory management integration
- **Phase 10**: Authentication and user management

## Testing

Basic tests are included using React Testing Library. Run tests with:

```bash
npm test
```

More comprehensive testing will be added as features are implemented.

## Deployment

The application is configured for deployment to Azure Static Web Apps with:

- Build output directory: `build`
- API location: Azure Functions backend
- Routing: Client-side routing with fallback to index.html

## Contributing

This project follows the multi-agent collaboration protocol. See `docs/planning/multi-agent-sync.md` for coordination guidelines.
