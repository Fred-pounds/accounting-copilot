# AI Accounting Copilot - Frontend

React-based frontend application for the AI Accounting Copilot system.

## Features

- **Authentication**: AWS Cognito integration with JWT token management and automatic session timeout (15 minutes)
- **Dashboard**: Real-time financial summaries with charts for profit trends and expense categories
- **Document Upload**: Drag-and-drop file upload with S3 pre-signed URLs and progress tracking
- **Transactions**: List, filter, sort, and manage transactions with approval workflow
- **Financial Assistant**: Chat interface for asking business questions with AI-powered responses
- **Audit Trail**: Complete history of all AI and human actions with CSV export
- **Approvals**: Review and approve pending items (new vendors, large transactions, bulk changes)

## Tech Stack

- **React 18** with TypeScript
- **React Router** for navigation
- **Recharts** for data visualization
- **Axios** with auth interceptors for API calls
- **Amazon Cognito Identity JS** for authentication
- **Vite** for fast development and building

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- AWS Cognito User Pool configured
- API Gateway endpoint deployed

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your AWS configuration:
```
VITE_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
VITE_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_COGNITO_REGION=us-east-1
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Building for Production

Build the application:
```bash
npm run build
```

The built files will be in the `dist/` directory, ready to deploy to S3.

Preview the production build:
```bash
npm run preview
```

### Type Checking

Run TypeScript type checking:
```bash
npm run type-check
```

### Linting

Run ESLint:
```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── Layout.tsx       # Main layout with navigation
│   │   ├── ProtectedRoute.tsx
│   │   └── TransactionDetailModal.tsx
│   ├── context/             # React context providers
│   │   └── AuthContext.tsx  # Authentication state management
│   ├── pages/               # Page components
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Transactions.tsx
│   │   ├── DocumentUpload.tsx
│   │   ├── Assistant.tsx
│   │   ├── AuditTrail.tsx
│   │   └── Approvals.tsx
│   ├── services/            # API and service layer
│   │   ├── api.ts           # API client with interceptors
│   │   └── auth.ts          # Authentication service
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx              # Main app component with routing
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Key Features Implementation

### Authentication & Session Management

- JWT token storage and automatic refresh
- Session timeout after 15 minutes of inactivity
- Activity tracking (mouse, keyboard, scroll, touch events)
- Automatic redirect to login on session expiration

### API Integration

- Axios interceptors for automatic token injection
- Automatic token refresh on 401 responses
- Error handling and retry logic
- Type-safe API client

### Dashboard Performance

- Auto-refresh every 60 seconds
- Optimized data loading (target: < 3 seconds)
- Responsive charts with Recharts
- Real-time pending approvals badge

### Document Upload

- Drag-and-drop interface with react-dropzone
- File validation (type, size)
- S3 pre-signed URL upload
- Progress tracking and error handling

### Transaction Management

- Advanced filtering (type, category, status, date range)
- Sorting by date or amount
- Inline approval actions
- Detailed transaction modal with AI reasoning display

### Financial Assistant

- Real-time chat interface
- Message history persistence
- Clickable citations linking to transactions
- Loading indicators for AI responses (target: < 5 seconds)

### Audit Trail

- Comprehensive filtering (date, action type, transaction)
- CSV export functionality
- Detailed entry modal
- 7-year retention compliance

### Approvals Workflow

- Pending approvals list with type badges
- Detailed approval information
- Approve/reject actions
- History tracking

## Responsive Design

The application is fully responsive and works on:
- Desktop (1400px+)
- Tablet (768px - 1399px)
- Mobile (< 768px)

## Security Features

- HTTPS-only communication
- JWT token-based authentication
- Automatic session timeout
- Protected routes
- CORS configuration

## Performance Optimization

- Code splitting with React Router
- Lazy loading of components
- Optimized bundle size with Vite
- Efficient re-rendering with React hooks
- API response caching where appropriate

## Deployment

The frontend is deployed to AWS S3 + CloudFront for global CDN delivery with HTTPS.

### Quick Start

See [DEPLOYMENT_QUICKSTART.md](./DEPLOYMENT_QUICKSTART.md) for a condensed 3-step deployment guide.

### Detailed Guide

See [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive deployment instructions including:
- Infrastructure setup (S3 bucket and CloudFront distribution)
- Environment configuration
- Deployment automation
- SSL/TLS configuration
- Troubleshooting
- CI/CD integration
- Cost considerations
- Monitoring and rollback procedures

### Deployment Scripts

- `setup-infrastructure.sh` - Creates AWS infrastructure (one-time setup)
- `deploy.sh` - Builds and deploys the application
- `deploy-cloudformation.sh` - Alternative CloudFormation-based setup
- `cloudformation-template.yaml` - Infrastructure as Code template

### Quick Deploy

```bash
# One-time setup
./setup-infrastructure.sh

# Configure environment
cp .env.example .env
# Edit .env with your values

# Deploy
source deploy.env
./deploy.sh
```

### Environment-Specific Builds

For different environments, create separate `.env` files:
- `.env.development`
- `.env.staging`
- `.env.production`

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Accessibility

- Semantic HTML
- ARIA labels where appropriate
- Keyboard navigation support
- Focus indicators
- Screen reader friendly

## Contributing

1. Follow TypeScript best practices
2. Use functional components with hooks
3. Maintain type safety
4. Write descriptive component and function names
5. Keep components focused and reusable

## License

Proprietary - AI Accounting Copilot
