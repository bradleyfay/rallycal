# Product Requirements Document: RallyCal

## Family Sports Calendar Aggregator

### Product Overview

RallyCal is a lightweight Python application that aggregates multiple sports calendar feeds from various youth sports platforms (LeagueApps, Crossbar, TeamSnap) into a single subscribable calendar feed. The primary goal is to simplify calendar management for busy sports families by eliminating the need for family members to subscribe to multiple individual calendars.

### Vision & Mission

**Vision:** Simplify family sports scheduling by providing one unified calendar view of all children's sports activities.

**Mission:** Create a lightweight, automated solution that aggregates multiple sports calendars and provides a single subscription point for family members to stay informed about all sports events.

### Core Features

1. **Calendar Aggregation**: Combine multiple iCal/ICS feeds from sports platforms
2. **Color Coding**: Visual distinction between different sports/calendars
3. **Manual Event Support**: Ability to add one-off events (birthdays, family events)
4. **Git-based Configuration**: Version-controlled calendar management
5. **Automated Deployment**: Infrastructure-as-code deployment to cloud
6. **Single Feed Output**: Standard iCal feed for universal calendar app compatibility

### User Personas

#### Primary User: Sports Parent Administrator

- **Role**: Parent managing multiple children's sports schedules
- **Pain Points**:
  - Managing 6+ different calendar subscriptions from sports apps
  - Family members unable/unwilling to subscribe to multiple calendars
  - Manual copy-paste of events is time-consuming and error-prone
- **Goals**:
  - Centralize all sports calendars in one place
  - Provide simple subscription URL to family members
  - Maintain calendar automatically without manual intervention

#### Secondary Users: Family Members

- **Role**: Spouse, grandparents, other family members
- **Pain Points**:
  - Too many calendar subscriptions to manage
  - Confusion about which events belong to which child/sport
- **Goals**:
  - Subscribe to one calendar and see all family sports events
  - Easily distinguish between different sports/children
  - Access calendar on any device/platform

### User Stories

#### Core Functionality

1. **As a sports parent**, I want to configure multiple sports calendar URLs in a file so that I can manage all calendar sources in one place
2. **As a sports parent**, I want the system to automatically fetch and merge calendar data so that I don't have to manually maintain events
3. **As a sports parent**, I want to add manual events (birthdays, family events) so that the aggregated calendar includes non-sports events
4. **As a family member**, I want to subscribe to one calendar URL so that I can see all sports events without managing multiple subscriptions
5. **As a family member**, I want events from different sports to be visually distinct so that I can quickly identify which sport/child each event belongs to

#### Configuration Management

6. **As a sports parent**, I want to update calendar sources via Git so that I can make changes from my phone using the GitHub app
7. **As a sports parent**, I want changes to automatically deploy so that calendar updates happen without manual server management
8. **As a sports parent**, I want removed calendars to automatically clean up their events so that old data doesn't persist

#### System Reliability

9. **As a sports parent**, I want configurable sync frequency so that I can balance update frequency with system load
10. **As a family member**, I want the calendar feed to work with standard calendar apps (iPhone, Google Calendar) so that I can use my preferred calendar application

### Functional Requirements

#### Calendar Aggregation (Core)

1. The system must support iCal/ICS feed ingestion from URLs
2. The system must support Google Calendar integration
3. The system must merge multiple calendar sources into a single output feed
4. The system must preserve original event details (time, location, description)
5. The system must detect and remove duplicate events based on strict criteria (same title, time, location)
6. The system must show overlapping events from different calendars

#### Visual Identification

7. The system must automatically assign different colors to each source calendar
8. The system must include source calendar name in event titles
9. The system must maintain consistent color assignment for each calendar source

#### Manual Event Management

10. The system must allow manual addition of events not available via subscription
11. Manual events must be color-coded and labeled consistently with subscribed calendars

#### Configuration Management

12. The system must read calendar sources from a configuration file (YAML/JSON)
13. The system must support Git-based configuration management
14. The system must detect configuration file changes and trigger automatic updates
15. Calendar source addition must automatically begin aggregating new feeds
16. Calendar source removal must automatically remove associated events from output

#### Feed Generation

17. The system must generate a standards-compliant iCal feed
18. The output feed must be accessible via public HTTP URL
19. The output feed must work with standard calendar applications (iOS Calendar, Google Calendar, Outlook)

#### Sync Management

20. The system must support configurable sync intervals for source calendars
21. The system must handle temporary source calendar unavailability gracefully
22. The system must log sync activities for troubleshooting

### Non-Functional Requirements

#### Performance

- Support 2-10 source calendars initially
- Support 5-10 concurrent subscribers initially
- Sync frequency configurable from 15 minutes to daily
- Response time < 2 seconds for calendar feed requests

#### Reliability

- 99% uptime for calendar feed availability
- Graceful handling of source calendar outages
- Automatic retry logic for failed calendar fetches
- Data persistence across application restarts

#### Scalability

- Architecture must support future multi-tenant expansion
- Database design must accommodate multiple independent calendar groups
- Configuration management must scale to multiple administrators

#### Security

- Public calendar access (no authentication required for MVP)
- Secure handling of source calendar URLs
- No exposure of sensitive configuration data in logs

#### Maintainability

- Containerized deployment using Docker
- Infrastructure-as-code using Terraform/Pulumi
- Automated deployment pipeline
- Comprehensive logging for troubleshooting

### Technical Architecture

#### High-Level Components

1. **Calendar Fetcher Service**: Retrieves data from source calendars
2. **Event Processor**: Merges, deduplicates, and color-codes events
3. **Configuration Manager**: Handles Git-based config updates
4. **iCal Generator**: Produces standards-compliant output feed
5. **Web Server**: Serves the aggregated calendar feed
6. **Database**: Stores processed events and configuration state

#### Technology Stack

- **Language**: Python 3.9+
- **Web Framework**: FastAPI or Flask
- **Database**: SQLite (MVP) with PostgreSQL migration path
- **Containerization**: Docker
- **Infrastructure**: Cloud service (AWS/GCP/Azure)
- **IaC**: Terraform or Pulumi
- **CI/CD**: GitHub Actions

#### Integration Points

- Git webhooks for configuration updates
- HTTP endpoints for calendar feed access
- iCal/ICS format for data exchange
- Standard calendar application compatibility

### Success Metrics

#### Primary Metrics

- **Calendar Sync Success Rate**: >95% successful syncs
- **Feed Availability**: >99% uptime
- **Family Adoption**: All intended family members successfully subscribe

#### Secondary Metrics

- **Sync Frequency**: Configurable and performing as expected
- **Event Accuracy**: Manual validation of event data consistency
- **Deployment Success**: Automated deployments complete without intervention

### Roadmap

#### Phase 1: MVP (Core Product)

- [ ] Basic calendar aggregation (2+ sources)
- [ ] Color coding and event labeling
- [ ] Git-based configuration management
- [ ] Single public feed output
- [ ] Docker containerization
- [ ] Cloud deployment with IaC

#### Phase 2: Enhanced Features

- [ ] Web UI for calendar management
- [ ] Enhanced duplicate detection
- [ ] Manual event management interface
- [ ] Monitoring and alerting

#### Phase 3: Multi-Tenant Support

- [ ] Multiple independent calendar groups
- [ ] User authentication and authorization
- [ ] Per-group configuration management
- [ ] Enhanced security features

### Open Questions

1. **Duplicate Detection Logic**: What specific criteria should be used for duplicate event detection? (title + time + location exact match?)
2. **Color Coding Implementation**: Should colors be embedded in event descriptions, titles, or handled via calendar metadata?
3. **Manual Event Interface**: Should manual events be added via config file or require a simple web form?
4. **Error Handling**: How should the system behave when source calendars are temporarily unavailable?
5. **Git Webhook Security**: Should we implement webhook signature verification for production deployment?
6. **Database Migration**: At what scale should we migrate from SQLite to PostgreSQL?

---

*This PRD serves as the foundation for implementing RallyCal. All requirements should be validated with stakeholders before development begins.*
