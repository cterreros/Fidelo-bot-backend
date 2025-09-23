# 📄 Software Requirements Specification (SRS) – FideloBot

---

## 1. Introduction

### 1.1 System Purpose

FideloBot is an intelligent loyalty solution for small businesses that enables customers to accumulate points through purchases, check their point balance, and receive automatic bonuses for special events like birthdays, all through a seamless integration between a modern web interface and a Telegram bot.

---

### 1.2 Target Audience

**Primary Users:**
- **Small Business Owners**: Coffee shops, retail stores, restaurants, beauty salons, hardware stores
- **Business Employees**: Staff members registering customer purchases
- **End Customers**: Clients who make purchases and want to track their loyalty points

**Technical Requirements:**
- Business owners: Access to web browser and basic computer literacy
- Customers: Smartphone with Telegram app
- Technical setup: Basic understanding of web applications (or technical support)

---

### 1.3 System Scope (MVP)

**Core Functionality:**
- Multi-business loyalty point management
- Intelligent customer detection and linking
- Web interface for business purchase registration
- Telegram bot for customer interaction
- Automatic point calculation and history tracking
- Birthday bonus system
- Real-time notifications

**Out of Scope (Future Versions):**
- Point redemption system
- Advanced analytics dashboard
- WhatsApp integration
- Mobile applications
- POS system direct integration

---

## 2. System Requirements

### 2.1 Functional Requirements

| ID | Priority | Description |
|----|----------|-------------|
| **FR1** | High | The system must allow businesses to register purchases with customer information |
| **FR2** | High | The system must automatically calculate points based on configurable rates per business |
| **FR3** | High | The system must detect existing customers by phone number across web and bot interfaces |
| **FR4** | High | Customers must be able to view their point balance through the Telegram bot |
| **FR5** | High | Customers must be able to view their complete purchase history through the bot |
| **FR6** | Medium | The system must automatically award birthday bonuses to customers |
| **FR7** | Medium | The system must send automatic notifications for purchases (Telegram only) |
| **FR8** | Medium | The system must support multiple independent businesses |
| **FR9** | Medium | The system must provide business authentication for the web interface |
| **FR10** | Low | Administrators must be able to manage businesses and customers through Django admin |

### 2.2 Business Rules

| ID | Rule Description |
|----|------------------|
| **BR1** | Each customer belongs to one or more businesses (can register in multiple) |
| **BR2** | Phone numbers must be unique per business (same phone can exist across businesses) |
| **BR3** | Points are calculated as: `points = amount * business.points_per_currency` |
| **BR4** | Birthday bonuses are awarded once per year per business |
| **BR5** | Customer phone numbers are used as the primary linking mechanism between web and bot |
| **BR6** | Telegram users are identified by email format: `telegram_{user_id}@fidelo.local` |

### 2.3 User Stories

#### **Business Owner Stories**
```
As a business owner,
I want to register customer purchases through a web form,
So that customers automatically earn loyalty points.

As a business owner,
I want the system to detect returning customers automatically,
So that I don't create duplicate accounts.

As a business owner,
I want to authenticate my business before registering purchases,
So that points are credited to the correct loyalty program.
```

#### **Customer Stories**
```
As a customer,
I want to check my loyalty points through Telegram,
So that I know how many points I have without calling the business.

As a customer,
I want to see my complete purchase history,
So that I can track my spending and points earned.

As a customer,
I want the system to recognize me automatically when I switch between web registration and bot,
So that all my points are consolidated in one account.

As a customer,
I want to receive automatic notifications when I earn points,
So that I'm aware of my loyalty program activity.
```

#### **System Stories**
```
As the system,
I need to link customers registered through the web form with their Telegram accounts,
So that they have a unified experience across both interfaces.

As the system,
I need to prevent duplicate customer accounts,
So that points are not split across multiple profiles.
```

---

## 3. Non-Functional Requirements

### 3.1 Performance Requirements

| ID | Requirement | Target Value |
|----|-------------|--------------|
| **NFR1** | Web response time | < 2 seconds for purchase registration |
| **NFR2** | Bot response time | < 3 seconds for command responses |
| **NFR3** | Concurrent users | Support 100 concurrent web sessions |
| **NFR4** | Database queries | < 500ms for customer lookup operations |
| **NFR5** | Bot availability | 99% uptime during business hours |

### 3.2 Security Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| **SR1** | Data encryption | Customer phone numbers and personal data encrypted at rest |
| **SR2** | Business isolation | Complete data separation between different businesses |
| **SR3** | Session security | Business web sessions expire after 8 hours of inactivity |
| **SR4** | Input validation | All user inputs validated and sanitized |
| **SR5** | API security | CSRF protection for all web forms |

### 3.3 Usability Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| **UR1** | Web interface | Intuitive form with clear validation messages |
| **UR2** | Bot commands | Simple, memorizable command structure |
| **UR3** | Mobile responsiveness | Web interface works on tablets and mobile devices |
| **UR4** | Error handling | Clear error messages in user's language |
| **UR5** | Navigation | Bot provides easy navigation with inline buttons |

### 3.4 Compatibility Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| **CR1** | Browser support | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ |
| **CR2** | Mobile platforms | Telegram available on iOS and Android |
| **CR3** | Database | PostgreSQL 12+ |
| **CR4** | Python version | Python 3.11+ |

---

## 4. System Constraints and Assumptions

### 4.1 Technical Constraints
- **Platform**: Web-based interface for businesses, Telegram for customers
- **Database**: PostgreSQL required for production deployment
- **Hosting**: Requires server capable of running Django applications
- **Internet**: Continuous internet connection required for Telegram bot operation

### 4.2 Business Constraints
- **Payment**: No payment processing integration in MVP
- **Languages**: English interface (Spanish support in future versions)
- **Businesses**: Designed for small to medium businesses (< 10,000 customers per business)
- **Integration**: No direct POS system integration (manual entry required)

### 4.3 Assumptions
- Customers have smartphones with Telegram installed
- Business staff have basic computer literacy
- Phone numbers provided by customers are accurate and accessible
- Customers are willing to use Telegram for loyalty program interaction
- Businesses have reliable internet connection during operating hours

---

## 5. System Interfaces

### 5.1 User Interfaces

#### **Web Interface (Business)**
- **Login Page**: Business selection and authentication
- **Purchase Form**: Customer data entry and purchase registration
- **Confirmation Modal**: Purchase success with customer details and points

#### **Telegram Bot Interface (Customer)**
- **Registration Flow**: Step-by-step business selection and phone entry
- **Main Menu**: Point balance, history, and program information
- **Interactive Navigation**: Inline keyboard buttons for seamless UX

### 5.2 API Interfaces

#### **Internal APIs**
```http
POST /api/purchase-with-client-data/
GET /api/clients/
GET /api/businesses/
GET /api/point-events/
```

#### **Bot Integration**
- Direct Django ORM access for real-time data
- Async/await pattern for non-blocking operations

### 5.3 Database Interfaces
- **PostgreSQL**: Primary data storage
- **Django ORM**: Database abstraction layer
- **Migrations**: Version-controlled schema changes

---

## 6. Data Requirements

### 6.1 Data Entities

#### **Business**
```python
- business_id: UUID (Primary Key)
- name: String (max 160 chars)
- email: Email
- timezone: String (default: America/Mexico_City)
- points_per_currency: Decimal (default: 0.1)
- birthday_bonus_points: Integer (default: 50)
- is_active: Boolean (default: True)
- created_at, updated_at: DateTime
```

#### **Client**
```python
- client_id: UUID (Primary Key)
- business: ForeignKey (Business)
- name: String (max 160 chars)
- email: Email
- phone: String (max 32 chars, optional)
- birthday: Date (optional)
- joined_at: Date (auto-set)
- created_at, updated_at: DateTime
```

#### **Purchase**
```python
- purchase_id: UUID (Primary Key)
- business: ForeignKey (Business)
- client: ForeignKey (Client)
- amount: Decimal (max 12 digits, 2 decimal places)
- currency: String (max 8 chars, default: "MXN")
- purchased_at: DateTime (default: now)
- created_at: DateTime (auto-set)
```

#### **PointEvent**
```python
- event_id: UUID (Primary Key)
- business: ForeignKey (Business)
- client: ForeignKey (Client)
- source: Choice (purchase, birthday, adjustment)
- points: Integer
- related_purchase: ForeignKey (Purchase, optional)
- note: String (max 200 chars, optional)
- occurred_at: DateTime (default: now)
- created_at: DateTime (auto-set)
```

### 6.2 Data Relationships
- **Business** → **Client**: One-to-Many
- **Client** → **LoyaltyAccount**: One-to-One
- **Client** → **Purchase**: One-to-Many
- **Purchase** → **PointEvent**: One-to-One (typically)
- **Client** → **PointEvent**: One-to-Many

### 6.3 Data Constraints
- **Unique Constraints**: (business, email) and (business, phone) in Client model
- **Referential Integrity**: All foreign keys with appropriate ON DELETE behaviors
- **Data Validation**: Email format, phone format, positive amounts and points

---

## 7. Quality Attributes

### 7.1 Reliability
- **Error Recovery**: System gracefully handles database connection failures
- **Data Consistency**: ACID transactions ensure data integrity
- **Fault Tolerance**: Bot continues operating even if some features fail

### 7.2 Scalability
- **Horizontal Scaling**: Stateless design allows multiple server instances
- **Database Optimization**: Indexed queries for performance
- **Caching Ready**: Architecture supports Redis integration

### 7.3 Maintainability
- **Code Organization**: Clear separation of concerns with service layer
- **Documentation**: Comprehensive inline documentation
- **Testing**: Unit tests for critical business logic
- **Configuration**: Environment-based configuration management

### 7.4 Security
- **Data Protection**: Personal information handled according to privacy best practices
- **Access Control**: Business-level data isolation
- **Audit Trail**: Complete transaction history in PointEvent model

---

## 8. Risk Analysis

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Telegram API downtime | Medium | High | Implement retry logic and queue system |
| Database performance issues | Low | High | Optimize queries and implement caching |
| Bot spam/abuse | Medium | Medium | Implement rate limiting and user validation |
| Data loss | Low | Critical | Regular backups and replication |

### 8.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low customer adoption | Medium | High | Provide clear onboarding and support |
| Business resistance to change | Medium | Medium | Offer training and gradual implementation |
| Competition from established solutions | High | Medium | Focus on simplicity and cost-effectiveness |

---

## 9. Testing Requirements

### 9.1 Functional Testing
- **Unit Tests**: All service layer methods
- **Integration Tests**: API endpoints and database operations
- **User Acceptance Tests**: Complete user workflows

### 9.2 Performance Testing
- **Load Testing**: Concurrent user scenarios
- **Stress Testing**: Peak usage simulation
- **Database Testing**: Query performance under load

### 9.3 Security Testing
- **Input Validation**: SQL injection and XSS prevention
- **Authentication**: Business login security
- **Data Privacy**: Personal information protection

---

## 10. Deployment Requirements

### 10.1 Infrastructure
- **Web Server**: Django application server (Gunicorn recommended)
- **Database**: PostgreSQL with backup strategy
- **Bot Hosting**: Separate process for Telegram bot
- **Static Files**: CDN or web server for static content

### 10.2 Environment Configuration
- **Development**: Local PostgreSQL, bot polling mode
- **Staging**: Production-like environment for testing
- **Production**: Load balancer, database clustering, bot webhooks

---

This requirements specification reflects the current MVP implementation of FideloBot and serves as a reference for future development and testing activities.