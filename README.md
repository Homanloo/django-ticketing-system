# Django Ticketing System

A comprehensive ticketing system built with Django REST Framework and a modern JavaScript frontend. This system allows users to create and manage support tickets, communicate with staff through messages, and track ticket activities.

## Features

### Backend (Django REST Framework)
- **JWT Authentication**: Secure token-based authentication with HttpOnly refresh tokens
- **User Management**: Registration, login, logout, profile management
- **Ticket Management**: Create, read, update, delete tickets (CRUD operations)
- **Ticket Messaging**: Add messages to tickets for communication
- **File Attachments**: Upload files to ticket messages
- **Activity Tracking**: Complete audit trail of all ticket changes
- **Permission System**: Role-based access (User/Staff)
- **API Documentation**: Auto-generated with drf-spectacular (Swagger/OpenAPI)

### Frontend (Vanilla JavaScript)
- **Modern UI**: Clean, responsive design with CSS variables
- **Authentication**: Login and registration forms
- **Dashboard**: View and filter tickets by status and priority
- **Ticket Creation**: Easy-to-use modal for creating new tickets
- **Ticket Details**: Full ticket view with messages and activity log
- **Real-time Messaging**: Add messages to tickets
- **Auto Token Refresh**: Seamless JWT token refresh
- **Responsive Design**: Works on desktop, tablet, and mobile

## Technology Stack

### Backend
- Python 3.x
- Django 5.2
- Django REST Framework
- PostgreSQL
- Simple JWT for authentication
- drf-spectacular for API documentation

### Frontend
- HTML5
- CSS3 (with CSS Grid & Flexbox)
- Vanilla JavaScript (ES6+)
- No frameworks or build tools required

## Project Structure

```
django-ticketing-system/
├── TicketingSystem/
│   ├── apps/
│   │   ├── Tickets/          # Ticket management app
│   │   │   ├── models.py     # Ticket, Message, Attachment, Activity models
│   │   │   ├── serializers.py
│   │   │   ├── views.py      # API views
│   │   │   └── urls.py
│   │   └── Users/            # User management app
│   │       ├── models.py     # Custom User model
│   │       ├── serializers.py
│   │       ├── views.py      # Auth views
│   │       └── urls.py
│   ├── static/               # Frontend files
│   │   ├── index.html        # Main HTML file
│   │   ├── styles.css        # All styles
│   │   ├── app.js           # JavaScript logic
│   │   └── README.md        # Frontend documentation
│   ├── TicketingSystem/      # Project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── views.py         # Frontend view
│   └── manage.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL (or Docker)
- pip

### Installation

#### Option 1: Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd django-ticketing-system
```

2. Create a `.env` file in the root directory:
```env
DJANGO_SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
POSTGRES_DB=ticketing_db
POSTGRES_USER=ticketing_user
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

4. Run migrations:
```bash
docker-compose exec web python manage.py migrate
```

5. Create a superuser (optional):
```bash
docker-compose exec web python manage.py createsuperuser
```

#### Option 2: Manual Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd django-ticketing-system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL database and create `.env` file (as shown above)

5. Run migrations:
```bash
cd TicketingSystem
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Collect static files:
```bash
python manage.py collectstatic --noinput
```

8. Run the development server:
```bash
python manage.py runserver
```

### Accessing the Application

- **Frontend UI**: http://localhost:8000/
- **API Documentation**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/

## Using the Frontend

1. **Register a New Account**:
   - Navigate to http://localhost:8000/
   - Click "Register" and fill in your details
   - You'll be automatically logged in after registration

2. **Create a Ticket**:
   - Click "+ Create Ticket" button
   - Fill in topic, description, and select priority
   - Click "Create Ticket"

3. **View and Manage Tickets**:
   - See all your tickets in the dashboard
   - Filter by status or priority using the dropdown menus
   - Click on a ticket to view details, add messages, and see activity

4. **Add Messages**:
   - Open a ticket detail modal
   - Type your message at the bottom
   - Click "Send" to add your message

## API Endpoints

### Authentication Endpoints
```
POST   /api/v1/users/auth/register/        - Register new user
POST   /api/v1/users/auth/login/           - User login
POST   /api/v1/users/auth/logout/          - User logout
POST   /api/v1/users/auth/refresh/         - Refresh access token
GET    /api/v1/users/profile/              - Get user profile
PUT    /api/v1/users/profile/              - Update user profile
POST   /api/v1/users/profile/change-password/ - Change password
```

### Ticket Endpoints
```
GET    /api/v1/tickets/                    - List all tickets (staff: all, user: own)
POST   /api/v1/tickets/                    - Create new ticket
GET    /api/v1/tickets/{id}/               - Get ticket details
PUT    /api/v1/tickets/{id}/               - Update ticket
DELETE /api/v1/tickets/{id}/               - Delete ticket (staff only)
GET    /api/v1/my-tickets/                 - Get current user's tickets
GET    /api/v1/assigned-tickets/           - Get assigned tickets (staff only)
```

### Message Endpoints
```
GET    /api/v1/tickets/{id}/messages/      - Get ticket messages
POST   /api/v1/tickets/{id}/messages/      - Add message to ticket
```

### Attachment Endpoints
```
POST   /api/v1/tickets/{id}/attachments/   - Upload attachment
```

### Activity Endpoints
```
GET    /api/v1/tickets/{id}/activities/    - Get ticket activities
```

## API Documentation

The API is fully documented using OpenAPI/Swagger:
- Interactive documentation: http://localhost:8000/api/docs/
- OpenAPI schema: http://localhost:8000/api/schema/

## Database Models

### User
- Custom user model extending Django's AbstractBaseUser
- Fields: username, email, first_name, last_name, is_staff, etc.

### Ticket
- id (UUID)
- user (ForeignKey to User)
- topic (CharField)
- description (TextField)
- status (open, in_progress, resolved, closed)
- priority (low, medium, high, critical)
- assigned_to (ForeignKey to User, nullable)
- created_at, updated_at, resolved_at

### TicketMessage
- id (UUID)
- ticket (ForeignKey to Ticket)
- user (ForeignKey to User)
- message (TextField)
- is_staff_message (Boolean)
- created_at

### TicketAttachment
- id (UUID)
- ticket (ForeignKey to Ticket)
- message (ForeignKey to TicketMessage)
- file (FileField)
- uploaded_by (ForeignKey to User)
- created_at

### TicketActivity
- id (UUID)
- ticket (ForeignKey to Ticket)
- action (CharField)
- performed_by (ForeignKey to User)
- details (TextField)
- created_at

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **HttpOnly Cookies**: Refresh tokens stored in secure cookies
- **Token Rotation**: Refresh tokens are rotated on each refresh
- **Token Blacklisting**: Old tokens are blacklisted after refresh
- **Password Hashing**: Passwords are securely hashed
- **CSRF Protection**: Django's built-in CSRF protection
- **Permission System**: Role-based access control

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating a Staff User

To test staff features, create a staff user:
```bash
python manage.py createsuperuser
```

Or in Django shell:
```python
from apps.Users.models import User
user = User.objects.create_user(
    username='staff',
    email='staff@example.com',
    password='password123',
    is_staff=True
)
```

## Troubleshooting

### Backend Issues

1. **Database Connection Error**:
   - Check PostgreSQL is running
   - Verify `.env` file has correct database credentials
   - Try: `docker-compose down && docker-compose up`

2. **Migration Issues**:
   - Delete migrations folder contents (except `__init__.py`)
   - Drop and recreate database
   - Run `python manage.py makemigrations` and `python manage.py migrate`

3. **Static Files Not Loading**:
   - Run `python manage.py collectstatic`
   - Check `STATIC_URL` and `STATICFILES_DIRS` in settings

### Frontend Issues

1. **Login/Register Not Working**:
   - Check browser console for errors
   - Verify backend is running
   - Check network tab for API responses

2. **Tickets Not Loading**:
   - Ensure you're logged in
   - Check backend logs for errors
   - Verify JWT token is valid

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Contact

For questions or support, please open an issue on the GitHub repository.

## Acknowledgments

- Django and Django REST Framework communities
- drf-spectacular for API documentation
- Simple JWT for authentication
