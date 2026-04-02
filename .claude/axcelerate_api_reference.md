# aXcelerate API Complete Reference

Compiled from:
- https://app.axcelerate.com/apidocs (official API docs)
- https://developer.axcelerate.com/docs/Guides (developer guides)
- https://github.com/chrisjoyce911/axcelerate (GoLang SDK)
- https://pkg.go.dev/github.com/chrisjoyce911/axcelerate (Go package docs)

---

## AUTHENTICATION

All endpoints require two HTTP headers:

| Header     | Type   | Description         |
|------------|--------|---------------------|
| `apitoken` | string | API Key value       |
| `wstoken`  | string | Web Service Key value |

**Base URL:** `https://app.axcelerate.com/api`

**Response Format:** JSON only (XML not supported)

**Common HTTP Status Codes:**
- `200` — Success
- `204` — No Content (successful action with no body)
- `401` — No API token provided / invalid token
- `404` — Resource not found
- `412` — Validation Error

**Standard Error Response:**
```json
{
  "error": true,
  "code": "412",
  "messages": "Brief error description",
  "details": "Detailed explanation of validation errors",
  "data": ""
}
```

---

## COURSE TYPES

| Code | Description             |
|------|-------------------------|
| `w`  | Workshop                |
| `p`  | Accredited Program/Class|
| `s`  | Unit/Subject            |
| `el` | E-Learning              |

---

## 1. CONTACT ENDPOINTS

### POST /contact/
**Description:** Create a new contact record (does not deduplicate)

**Required Parameters:**
| Parameter  | Type   | Description              |
|------------|--------|--------------------------|
| `givenName`| string | First name (max 40 chars)|
| `surname`  | string | Last name (max 40 chars) |

**Optional Parameters:**
| Parameter                     | Type      | Description                                         |
|-------------------------------|-----------|-----------------------------------------------------|
| `title`                       | string    | Salutation/title                                    |
| `emailAddress`                | string    | Valid email address                                 |
| `ContactActive`               | boolean   | Default: true                                       |
| `dob`                         | date      | YYYY-MM-DD; cannot be future-dated                  |
| `sex`                         | char      | M, F, or X                                          |
| `middleName`                  | string    | Max 40 chars                                        |
| `phone`                       | string    | Home phone                                          |
| `mobilephone`                 | string    | Mobile phone                                        |
| `workphone`                   | string    | Work phone                                          |
| `fax`                         | string    | Fax number                                          |
| `organisation`                | string    | Organisation name                                   |
| `orgId`                       | numeric   | Primary organisation ID                             |
| `orgIds`                      | list      | Up to 5 organisation IDs                            |
| `position`                    | string    | Job position                                        |
| `section`                     | string    | Department section                                  |
| `division`                    | string    | Division                                            |
| `SourceCodeID`                | numeric   | Source code ID                                      |
| `HistoricClientID`            | string    | Historic client reference                           |
| `USI`                         | string    | Unique Student Identifier (10 chars; caps + numbers excluding I,1,0,O) |
| `LUI`                         | string    | Learner Unique Identifier (10-digit numeric)        |
| `VSN`                         | string    | Victorian Student Number                            |
| `WorkReadyParticipantNumber`  | string    | Work Ready participant number                       |
| `SACEStudentID`               | string    | SACE Student ID (6 numbers + 1 letter)              |
| `EmergencyContact`            | string    | Emergency contact name                              |
| `EmergencyContactRelation`    | string    | Relationship to emergency contact                   |
| `EmergencyContactPhone`       | string    | Emergency contact phone                             |
| `ParentContactID`             | numeric   | Parent contact ID                                   |
| `optionalID`                  | string    | Optional reference ID                               |
| `categoryIDs`                 | list      | Valid category IDs                                  |
| `customField_[variableName]`  | string    | Custom field (supports comma-delimited or JSON array)|
| `domainIDs`                   | array     | Domain IDs (requires Contact Domains feature)       |
| `checkEmailAddressUnique`     | boolean   | Validate email uniqueness; default: false           |
| `EmailAddressAlternative`     | string    | Alternate email (AVETMISS 8.0)                      |

**Postal Address Parameters:**
| Parameter      | Type    | Description                       |
|----------------|---------|-----------------------------------|
| `buildingName` | string  | AVETMISS 7.0 building name        |
| `unitNo`       | string  | AVETMISS 7.0 unit number          |
| `streetNo`     | string  | AVETMISS 7.0 street number        |
| `streetName`   | string  | AVETMISS 7.0 street name          |
| `POBox`        | string  | AVETMISS 7.0 PO Box               |
| `address1`     | string  | Postal address line 1             |
| `address2`     | string  | Postal address line 2             |
| `city`         | string  | Postal suburb/town                |
| `state`        | string  | NSW, VIC, QLD, SA, WA, TAS, NT, ACT, OTH, OVS |
| `postcode`     | string  | Postal postcode                   |
| `country`      | string  | Country name                      |
| `countryID`    | numeric | 4-digit SACC code                 |

**Residential Address Parameters (prefix 's'):**
| Parameter       | Type    | Description                           |
|-----------------|---------|---------------------------------------|
| `sbuildingName` | string  | Residential building name             |
| `sunitNo`       | string  | Residential unit number               |
| `sstreetNo`     | string  | Residential street number             |
| `sstreetName`   | string  | Residential street name               |
| `sPOBox`        | string  | Residential PO Box                    |
| `saddress1`     | string  | Residential address line 1            |
| `saddress2`     | string  | Residential address line 2            |
| `scity`         | string  | Residential suburb/town               |
| `sstate`        | string  | NSW, VIC, QLD, SA, WA, TAS, NT, ACT, OTH, OVS |
| `spostcode`     | string  | Residential postcode                  |
| `scountry`      | string  | Residential country name              |
| `scountryID`    | numeric | 4-digit SACC code                     |

**Term Address Parameters (VET Student Loan feature):**
| Parameter        | Type    | Description             |
|------------------|---------|-------------------------|
| `termAddress1`   | string  | Term address line 1     |
| `termAddress2`   | string  | Term address line 2     |
| `termCity`       | string  | Term city               |
| `termState`      | string  | Term state              |
| `termPostcode`   | string  | Term postcode           |
| `termCountry`    | string  | Term country            |
| `termCountryID`  | numeric | 4-digit SACC code       |

**AVETMISS / Demographics Parameters:**
| Parameter               | Type    | Description                                    |
|-------------------------|---------|------------------------------------------------|
| `CountryofBirthID`      | numeric | 4-digit SACC code                              |
| `CityofBirth`           | string  | City of birth                                  |
| `CountryofCitizenID`    | numeric | 4-digit SACC code                              |
| `CitizenStatusID`       | numeric | 1–11                                           |
| `ResidencyStatusID`     | numeric | AVETMISS residency code                        |
| `LabourForceID`         | numeric | AVETMISS labour force status                   |
| `MainLanguageID`        | numeric | 4-digit SACC code                              |
| `EnglishProficiencyID`  | numeric | AVETMISS English proficiency code              |
| `EnglishAssistanceFlag` | boolean | Requires English assistance                    |
| `HighestSchoolLevelID`  | numeric | AVETMISS highest school level code             |
| `HighestSchoolLevelYear`| numeric | Year of highest school level (≤ current year)  |
| `AtSchoolFlag`          | boolean | Currently attending school                     |
| `AtSchoolName`          | string  | School name                                    |
| `PriorEducationStatus`  | boolean | Has prior education                            |
| `PriorEducationIDs`     | string  | Comma-delimited AVETMISS codes or JSON array   |
| `DisabilityFlag`        | boolean | Has disability                                 |
| `DisabilityTypeIDs`     | list    | Comma-delimited AVETMISS disability type codes |
| `IndigenousStatusID`    | numeric | AVETMISS Indigenous status code                |
| `ANZSCOCode`            | string  | Australian/NZ Standard Classification of Occupations |
| `ANZSICCode`            | string  | Australian/NZ Standard Industry Classification|
| `SurveyContactStatusCode`| string | AVETMISS 8.0 survey status code               |

**Relationship Parameters:**
| Parameter              | Type    | Description                  |
|------------------------|---------|------------------------------|
| `employerContactID`    | numeric | Employer contact reference   |
| `payerContactID`       | numeric | Payer contact reference      |
| `supervisorContactID`  | numeric | Supervisor contact reference |
| `agentContactID`       | numeric | Agent contact reference      |
| `coachContactID`       | numeric | Coach contact reference      |
| `internationalContactID`| numeric| CRICOS contact reference    |

**Response Fields:**
```json
{
  "CONTACTID": 12345,
  "GIVENNAME": "John",
  "SURNAME": "Smith",
  "EMAILADDRESS": "john@example.com"
}
```

---

### GET /contact/:contactID
**Description:** Retrieve full contact details

**URL Parameter:**
| Parameter   | Type    | Description     |
|-------------|---------|-----------------|
| `contactID` | numeric | Contact ID      |

**Response:** Full contact JSON object with all fields including all address types, AVETMISS demographics, relationship IDs, and custom fields.

---

### PUT /contact/:contactID
**Description:** Update contact information

**URL Parameter:**
| Parameter   | Type    | Description     |
|-------------|---------|-----------------|
| `contactID` | numeric | Contact ID      |

**Parameters:** Same optional parameters as POST /contact/ — all are optional for updates.

**Response:** Updated full contact JSON object.

---

### GET /contacts/search
**Description:** Search for contacts

**Optional Parameters:**
| Parameter         | Type    | Description                                     |
|-------------------|---------|-------------------------------------------------|
| `q` / `search`    | string  | Text search across multiple fields              |
| `offset`          | numeric | Starting record position                        |
| `displayLength`   | numeric | Max records to return (up to 100)               |
| `contactEntryDate`| date    | Filter by entry date (yyyy-mm-dd)               |
| `lastUpdated`     | date    | Filter by update date (yyyy-mm-dd)              |
| `givenName`       | string  | Given (first) name filter                       |
| `surname`         | string  | Last name filter                                |
| `emailAddress`    | string  | Email address filter                            |
| `contactRoleID`   | numeric | Filter by contact role                          |
| `contactIDs`      | string  | Comma-delimited contact ID list                 |
| `contactID`       | numeric | Exact match on single contact ID                |
| `optionalID`      | string  | Exact match on optional ID                      |
| `DOB`             | date    | Date of birth filter (yyyy-mm-dd)               |

**Response:** Array of Contact objects.

---

### POST /contact/note/
**Description:** Add a note to a contact record

**Required Parameters:**
| Parameter     | Type    | Description                    |
|---------------|---------|--------------------------------|
| `contactID`   | numeric | Contact to add the note to     |
| `contactNote` | string  | Note content                   |

**Optional Parameters:**
| Parameter   | Type   | Description                            |
|-------------|--------|----------------------------------------|
| `noteTypeID`| string | Type of note (default: "88" = System Note) |
| `emailNote` | string | Comma-separated contact IDs to email the note to |

**Response Fields:**
```json
{
  "NOTEID": 999,
  "MESSAGE": "Note added successfully",
  "STATUS": "OK"
}
```

---

### POST /contact/verifyUSI
**Description:** Verify a contact's Unique Student Identifier (USI)

**Required Parameters:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `contactID` | numeric | Contact ID  |

---

### GET /contact/enrolments/:contactID
**Description:** Retrieve all enrolments for a specific contact

**URL Parameter:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `contactID` | numeric | Contact ID  |

**Optional Query Parameters:**
| Parameter         | Type   | Description                    |
|-------------------|--------|--------------------------------|
| `parms`           | map    | Additional filter parameters   |

**Response:** Array of ContactEnrolment objects.

---

### GET /contact/enrolment/certificate
**Description:** Download an enrolment certificate as base64-encoded data

**Required Parameters:**
| Parameter | Type    | Description    |
|-----------|---------|----------------|
| `enrolID` | numeric | Enrolment ID   |

**Response:** Base64-encoded certificate with file metadata (filename, type, content type, size).

---

### POST /user/login
**Description:** Login a returning student and retrieve their contact ID

**Required Parameters:**
| Parameter    | Type   | Description     |
|--------------|--------|-----------------|
| Access code  | varies | Student login credentials |

**Response:** Contact ID and session data.

---

## 2. COURSE ENDPOINTS

### GET /courses/
**Description:** Retrieve list of all courses

**Optional Parameters:**
| Parameter        | Type     | Description                                              |
|------------------|----------|----------------------------------------------------------|
| `ID`             | numeric  | Filter by Course ID                                      |
| `searchTerm`     | string   | Filter activities by search term                         |
| `type`           | string   | w=workshop, p=accredited program, el=e-learning, all=all |
| `trainingArea`   | string   | Training area to search                                  |
| `offset`         | numeric  | Pagination start record (default: 0)                     |
| `displayLength`  | numeric  | Records to retrieve (default: 10)                        |
| `sortColumn`     | numeric  | Column index to sort by (default: 1)                     |
| `sortDirection`  | string   | ASC or DESC (default: ASC)                               |
| `current`        | boolean  | Show only current courses (default: true)                |
| `public`         | boolean  | Include public courses only (default: true)              |
| `lastUpdated_min`| datetime | Min last updated (YYYY-MM-DD hh:mm)                      |
| `lastUpdated_max`| datetime | Max last updated (YYYY-MM-DD hh:mm)                      |
| `isActive`       | boolean  | Filter by active/inactive status                         |

**Response:** Array of Course objects with code, cost, delivery method, duration, and status.

---

### GET /course/instances
**Description:** Retrieve instances for a specific course

**Required Parameters:**
| Parameter    | Type    | Description                             |
|--------------|---------|-----------------------------------------|
| `ID`         | numeric | Course ID                               |
| `type`       | string  | w, p, or el                             |

**Optional Parameters:**
| Parameter        | Type     | Description                              |
|------------------|----------|------------------------------------------|
| `public`         | boolean  | Include public courses only              |
| `current`        | boolean  | Include only current/upcoming courses    |
| `isActive`       | boolean  | Filter by active/inactive status         |
| `lastUpdated_min`| datetime | Min last updated (YYYY-MM-DD hh:mm)      |
| `lastUpdated_max`| datetime | Max last updated (YYYY-MM-DD hh:mm)      |

**Response:** Array of course instance objects.

---

### GET /course/instance/search
**Description:** Advanced search for course instances (most flexible filter endpoint)

**Optional Parameters:**
| Parameter              | Type     | Description                                                |
|------------------------|----------|------------------------------------------------------------|
| `ID`                   | numeric  | Activity Type ID                                           |
| `InstanceID`           | numeric  | Specific Instance ID                                       |
| `type`                 | string   | w, p, el, all                                              |
| `trainingCategory`     | string   | Training category (LIKE search)                            |
| `location`             | string   | Course location (LIKE; type w only)                        |
| `state`                | string   | State (types w and p)                                      |
| `code`                 | string   | Course code (LIKE with prefix matching)                    |
| `name`                 | string   | Course name (LIKE)                                         |
| `searchTerm`           | string   | General search                                             |
| `enrolmentOpen`        | boolean  | Return only open enrolment instances                       |
| `startDate_min`        | date     | Min start date                                             |
| `startDate_max`        | date     | Max start date                                             |
| `finishDate_min`       | date     | Min finish date                                            |
| `finishDate_max`       | date     | Max finish date                                            |
| `lastUpdated_min`      | datetime | Min last updated (YYYY-MM-DD hh:mm; must pair with max, max 90 days apart) |
| `lastUpdated_max`      | datetime | Max last updated                                           |
| `trainerContactID`     | numeric  | Trainer/Consultant contact ID                              |
| `domainID`             | numeric  | Domain ID                                                  |
| `deliveryLocationID`   | numeric  | Accredited delivery location ID (type p only)              |
| `orgID`                | numeric  | Organisation ID                                            |
| `orgIDTree`            | numeric  | Organisation ID including child organisations              |
| `offset`               | numeric  | Pagination start                                           |
| `displayLength`        | numeric  | Records per page                                           |
| `sortColumn`           | numeric  | Sort column index                                          |
| `sortDirection`        | string   | ASC or DESC                                                |
| `public`               | boolean  | Include public courses                                     |
| `isActive`             | boolean  | Include/exclude inactive courses                           |
| `purgeCache`           | boolean  | Bypass 30-second query cache                               |
| `groupedCourseName`    | string   | Grouped workshop name search (type w only)                 |
| `groupedCourseID`      | numeric  | Grouped workshop ID (type w only)                          |

**Response:** Array of course instances including `participantVacancy` field for availability.

---

### GET /course/instance/detail
**Description:** Retrieve detailed information for a specific course instance

**Required Parameters:**
| Parameter    | Type    | Description     |
|--------------|---------|-----------------|
| `instanceID` | numeric | Instance ID     |
| `type`       | string  | w, p, or el     |

**Response:** InstanceDetail object with dates, participant counts, location, status, complex dates, trainers, and linked e-learning details.

---

### PUT /course/instance/
**Description:** Update course instance details

**Required Parameters:**
| Parameter    | Type    | Description     |
|--------------|---------|-----------------|
| `ID`         | numeric | Instance ID     |
| `type`       | string  | w, p, or el     |

**Optional Parameters:**
| Parameter          | Type    | Description                           |
|--------------------|---------|---------------------------------------|
| `ProgramName`      | string  | Instance/course name                  |
| `PStartDate`       | date    | Start date                            |
| `PFinishDate`      | date    | Finish date                           |
| `cost`             | numeric | Cost per student                      |
| `maxparticipants`  | numeric | Maximum participant capacity          |

**Response:** UpdateInstanceDetail object with message, status, and metadata.

---

### GET /course/detail
**Description:** Access detailed course type information

**Required Parameters:**
| Parameter | Type    | Description |
|-----------|---------|-------------|
| `ID`      | numeric | Course ID   |

---

### GET /course/locations
**Description:** Retrieve list of training locations

**Optional Parameters:**
| Parameter    | Type    | Description                                              |
|--------------|---------|----------------------------------------------------------|
| `public`     | boolean | Show only public locations (attached to public activity) |
| `onlyFuture` | boolean | Show only locations with a future activity               |

**Response:** Alphabetized array of location strings.

---

### GET /course/enrolments
**Description:** List enrolments across courses

**Optional Parameters:**
| Parameter          | Type     | Description                                   |
|--------------------|----------|-----------------------------------------------|
| `contactID`        | numeric  | Filter by contact                             |
| `orgID`            | numeric  | Filter by organisation                        |
| `instanceID`       | numeric  | Filter by activity instance                   |
| `ID`               | numeric  | Filter by activity type ID                    |
| `lastUpdated_min`  | datetime | Min last updated (YYYY-MM-DD hh:mm; pair with max) |
| `lastUpdated_max`  | datetime | Max last updated                              |
| `enrolmentDate_min`| datetime | Min enrolment date (pair with max)            |
| `enrolmentDate_max`| datetime | Max enrolment date                            |
| `type`             | string   | w, p, or el                                   |
| `filterType`       | string   | s=subjects/e-learning, el=e-learning only     |

**Response:** Array of Enrolment objects with learner and contact enrolment information.

---

### GET /course/discounts
**Description:** Check applicable discounts for a contact/instance combination

**Required Parameters:**
| Parameter       | Type    | Description                        |
|-----------------|---------|------------------------------------|
| `type`          | string  | w=Workshop, p=Class                |
| `contactID`     | numeric | Contact ID                         |
| `instanceID`    | numeric | Instance ID                        |
| `originalPrice` | numeric | Original course price              |

**Response:** Discount IDs and revised price with total savings.

---

### POST /course/enrol
**Description:** Enrol a contact into a course instance

**Required Parameters:**
| Parameter    | Type    | Description                           |
|--------------|---------|---------------------------------------|
| `contactID`  | numeric | Contact being enrolled                |
| `instanceID` | numeric | Activity Instance ID                  |
| `type`       | string  | w=Workshop, p=Class, el=E-Learning    |

**Optional Parameters:**
| Parameter                      | Type    | Description                                             |
|--------------------------------|---------|---------------------------------------------------------|
| `tentative`                    | boolean | Enrol as tentative status (w and el only)               |
| `payerID`                      | numeric | Contact ID of payer                                     |
| `invoiceID`                    | numeric | Existing invoice to add enrolment to (default: 0)       |
| `PONumber`                     | string  | Purchase order number                                   |
| `generateInvoice`              | boolean | Create new invoice (default: true)                      |
| `lockInvoiceItems`             | boolean | Lock invoice items (default: true; set 0 for class/tentative) |
| `archiveInvoice`               | boolean | Archive invoice after creation (default: false)         |
| `forceBooking`                 | boolean | Override course closure checks                          |
| `suppressSendAdminNotifications`| boolean | Suppress admin notification emails                    |
| `dateCommenced`                | date    | Enrolment start date                                    |
| `cost`                         | numeric | Discounted cost (use with course/discounts)             |
| `discountIdList`               | string  | Discount IDs to apply (from course/discounts response)  |
| `useRegistrationFormDefaults`  | boolean | Apply default enrolment form values from system settings|
| `customField_[variableName]`   | string  | Custom field values                                     |

**Response Fields:**
```json
{
  "INVOICEID": 67890,
  "CONTACTID": 12345,
  "LEARNERID": 99999,
  "AMOUNT": 500.00
}
```

---

### POST /course/enrolMultiple
**Description:** Enrol multiple contacts into a workshop in a single request (no tentative option)

**Required Parameters:**
| Parameter    | Type    | Description                       |
|--------------|---------|-----------------------------------|
| `instanceID` | numeric | Workshop Instance ID              |
| `type`       | string  | w (workshops only)                |
| `contactIDs` | list    | Multiple contact IDs to enrol     |

**Optional Parameters:** Same as /course/enrol (excluding `tentative`)

---

### PUT /course/enrolment
**Description:** Update an existing enrolment record

**Required Parameters:**
| Parameter       | Type    | Description                                      |
|-----------------|---------|--------------------------------------------------|
| `contactID`     | numeric | Contact being updated                            |
| `instanceID`    | numeric | Activity Instance ID (not required when using subjectCode) |
| `type`          | string  | w, p, s (unit), or el                            |

**Optional Parameters for Unit Enrolment Updates (type=s):**
| Parameter           | Type    | Description                              |
|---------------------|---------|------------------------------------------|
| `programInstanceId` | numeric | Class ID (required for unit updates)     |
| `competent`         | numeric | Outcome code                             |
| `activityStartDate` | date    | YYYY-MM-DD                               |
| `activityEndDate`   | date    | YYYY-MM-DD                               |

**Response:** EnrolmentUpdate object with data, error, messages, code, and details fields.

---

### GET /course/instance/attendance
**Description:** Retrieve attendance records for a workshop instance

**Required Parameters:**
| Parameter    | Type    | Description                                    |
|--------------|---------|------------------------------------------------|
| `instanceID` | numeric | Instance ID (currently workshops only, type=w) |
| `type`       | string  | Must be "w"                                    |

**Optional Parameters:**
| Parameter   | Type    | Description                                                          |
|-------------|---------|----------------------------------------------------------------------|
| `contactID` | numeric | Contact ID of the enrollee (required when updating attendance)       |
| `attended`  | numeric | 1=attended, 0=did not attend (required when updating)                |
| `complexID` | numeric | Complex Session ID (required when updating)                          |
| `arrival`   | datetime| Arrival date & time (yyyy-mm-dd hh:mm)                               |
| `departure` | datetime| Departure date & time (yyyy-mm-dd hh:mm)                             |
| `comment`   | string  | Comment for attendance record                                        |

**Response:** Array of Attendeds objects.

---

## 3. LEARNING PLAN / MODULE ENDPOINTS

### PUT /v2/learningPlan/modules/enrolments
**Description:** Update a module enrolment in a learning plan

**Required Parameters:**
| Parameter         | Type    | Description       |
|-------------------|---------|-------------------|
| `contactId`       | numeric | Student contact ID|
| `enrolId`         | numeric | Enrolment ID      |
| `classId`         | numeric | Class ID          |
| `moduleEnrolmentId`| numeric| Module enrolment ID|

**Optional Parameters:**
| Parameter       | Type    | Description                             |
|-----------------|---------|-----------------------------------------|
| `accessOverride`| boolean | Override access (true, false, or empty) |
| `startDate`     | date    | YYYY-MM-DD                              |
| `endDate`       | date    | YYYY-MM-DD                              |
| `useCache`      | boolean | Set false to return updated enrolment   |

---

## 4. ACCOUNTING ENDPOINTS

### GET /accounting/invoice/
**Description:** Retrieve invoices for a contact

**Required Parameters:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `contactID` | numeric | Contact ID  |

**Optional Parameters:**
| Parameter           | Type   | Description               |
|---------------------|--------|---------------------------|
| `externalReference` | string | Filter by ext. reference (max 60 chars) |

**Response Fields:**
`INVOICENR`, `PRICEGROSS`, `DUEDATE`, `INVOICEID`, `AREITEMSLOCKED`, `FIRSTNAME`, `LASTNAME`, `ISCANCELLED`, `BALANCE`, `INVOICEDATE`, `ISPAID`, `ISVOID`

---

### POST /accounting/invoice/
**Description:** Create a new invoice

**Required Parameters:**
| Parameter     | Type    | Description                   |
|---------------|---------|-------------------------------|
| `contactID`   | numeric | Contact ID                    |
| `firstname`   | string  | Contact first name            |
| `surname`     | string  | Contact surname               |
| `invoiceDate` | date    | Invoice date (YYYY-MM-DD)     |
| `orderDate`   | date    | Order date (YYYY-MM-DD)       |
| `aItem`       | JSON    | Line items array (see below)  |

**Optional Parameters:**
| Parameter           | Type   | Description          |
|---------------------|--------|----------------------|
| `externalReference` | string | Max 60 chars         |

**aItem Required Fields:**
| Field           | Type    | Description           |
|-----------------|---------|-----------------------|
| `DESCRIPTION`   | string  | Item description      |
| `QTY`           | numeric | Quantity (must be >0) |
| `ITEMCODE`      | string  | Item code             |
| `UNITPRICEGROSS`| numeric | Unit price (gross)    |
| `TAXPERCENT`    | numeric | Tax percentage        |
| `FINANCECODE`   | string  | Finance code          |
| `HASCHILDREN`   | boolean | Has child line items  |

**aItem Optional Fields:**
| Field           | Type    | Description              |
|-----------------|---------|--------------------------|
| `ITEMID`        | numeric | For editing existing items|
| `COSTCENTRECODE`| string  | Cost centre code         |
| `DOMAINID`      | numeric | Domain ID                |
| `SERVICEDATE`   | date    | Service date             |
| `PARTID`        | numeric | Part ID                  |
| `DATA`          | string  | Additional data          |

---

### GET /accounting/invoice/:invoiceID
**Description:** Retrieve specific invoice details

**URL Parameter:**
| Parameter   | Type    | Description                              |
|-------------|---------|------------------------------------------|
| `invoiceID` | numeric | Internal invoice ID (not invoice number) |

**Optional Query Parameters:**
| Parameter            | Type    | Description                                   |
|----------------------|---------|-----------------------------------------------|
| `includeEnrolmentData`| boolean| Include linked enrolment details with line items|

**Response:** Full invoice object with ITEMS array and PAYMENTS array including `INVOICENR`, `CONTACTNAME`, `PRICEGROSS`, `PRICENETT`, `BALANCE`, `ISPAID`, `CURRENCY`.

---

### PUT /accounting/invoice/:invoiceID
**Description:** Update an invoice

**URL Parameter:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `invoiceID` | numeric | Invoice ID  |

**Optional Parameters:**
| Parameter         | Type    | Description                      |
|-------------------|---------|----------------------------------|
| `contactID`       | numeric | Contact ID                       |
| `firstname`       | string  | First name                       |
| `surname`         | string  | Surname                          |
| `INVOICEDATE`     | date    | Invoice date (yyyy-mm-dd)        |
| `ORDERDATE`       | date    | Order date (yyyy-mm-dd)          |
| `aItem`           | JSON    | Line items array                 |
| `STREET`          | string  | Street address                   |
| `HOUSENR`         | numeric | House number                     |
| `ADDRESS2`        | string  | Address line 2                   |
| `CITY`            | string  | City                             |
| `STATE`           | string  | State                            |
| `POSTCODE`        | string  | Postcode                         |
| `COUNTRY`         | string  | Country                          |
| `COUNTRYISO3166`  | numeric | Country ISO code                 |
| `PHONENR`         | string  | Phone number                     |
| `EMAIL`           | string  | Email address                    |
| `COMMENT`         | string  | Comment                          |
| `ORDERNR`         | numeric | Order number                     |
| `EXTERNALREFERENCE`| string | External reference (max 60 chars)|
| `ORGID`           | numeric | Organisation ID                  |
| `SHIPFIRSTNAME`   | string  | Shipping first name              |
| `SHIPLASTNAME`    | string  | Shipping last name               |
| `SHIPSTREET`      | string  | Shipping street                  |
| `SHIPHOUSENR`     | numeric | Shipping house number            |
| `SHIPCITY`        | string  | Shipping city                    |
| `SHIPSTATE`       | string  | Shipping state                   |
| `SHIPPOSTCODE`    | numeric | Shipping postcode                |
| `SHIPADDRESS2`    | string  | Shipping address line 2          |
| `SHIPCOUNTRYISO3166`| numeric| Shipping country ISO code      |
| `SHIPORGANISATION`| string  | Shipping organisation            |

---

### GET /accounting/invoice/:invoiceID/paymenturl
**Description:** Retrieve aXcelerate's native payment URL for an invoice

**URL Parameter:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `invoiceID` | numeric | Invoice ID  |

**Response:** `{ "PAYMENTURL": "https://..." }`

---

### PUT /accounting/invoice/:invoiceGUID/approve
**Description:** Prepare an invoice for payment and return payment URL

**URL Parameter:**
| Parameter    | Type    | Description  |
|--------------|---------|--------------|
| `invoiceGUID`| string  | Invoice GUID |

**Response:** `{ "PAYMENTURL": "https://..." }`

---

### POST /accounting/invoice/:invoiceGUID/unarchive
**Description:** Unlock a finalized invoice for editing (requires Master Finance permission)

**URL Parameter:**
| Parameter    | Type   | Description  |
|--------------|--------|--------------|
| `invoiceGUID`| string | Invoice GUID |

**Response:** 204 No Content

---

### POST /accounting/invoice/:invoiceGUID/void
**Description:** Void an invoice (cannot void if payments applied)

**URL Parameter:**
| Parameter    | Type   | Description  |
|--------------|--------|--------------|
| `invoiceGUID`| string | Invoice GUID |

**Response:** 204 No Content

---

### GET /accounting/creditnote/
**Description:** Retrieve credit notes for a contact

**Required Parameters:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `contactID` | numeric | Contact ID  |

**Response Fields:** `CREDITNOTENR`, `PRICEGROSS`, `ORDERDATE`, `CREDITNOTEID`, `AREITEMSLOCKED`, `FIRSTNAME`, `LASTNAME`, `CREDITNOTEDATE`, `ISCREDITED`, `ISVOID`

---

### POST /accounting/creditnote/
**Description:** Create a new credit note

**Required Parameters:**
| Parameter   | Type    | Description              |
|-------------|---------|--------------------------|
| `contactID` | numeric | Contact ID               |
| `firstname` | string  | Contact first name       |
| `surname`   | string  | Contact surname          |
| `aItem`     | JSON    | Line items array         |

**aItem Required Fields:** DESCRIPTION, QTY, ITEMCODE, TAXPERCENT, UNITPRICEGROSS

**aItem Optional Fields:** ITEMID, FINANCECODE, DOMAINID, COSTCENTRECODE, SERVICEDATE, PARTID, DATA, CHILDREN (JSON)

---

### GET /accounting/creditnote/:creditnoteID
**Description:** Retrieve specific credit note details

**URL Parameter:**
| Parameter      | Type    | Description    |
|----------------|---------|----------------|
| `creditnoteID` | numeric | Credit note ID |

**Response:** Credit note object with ITEMS array including `CREDITNOTENR`, `CONTACTNAME`, `PRICEGROSS`, `CREDITNOTEID`, `CREDITNOTEDATE`, `ISVOID`, `ISPAID`, `BALANCE`.

---

### PUT /accounting/creditnote/:creditnoteID
**Description:** Update a credit note

**URL Parameter:**
| Parameter      | Type    | Description    |
|----------------|---------|----------------|
| `creditnoteID` | numeric | Credit note ID |

**Optional Parameters:**
| Parameter          | Type    | Description                      |
|--------------------|---------|----------------------------------|
| `contactID`        | numeric | Contact ID                       |
| `firstname`        | string  | First name                       |
| `surname`          | string  | Surname                          |
| `CREDITNOTEDATE`   | date    | Credit note date (yyyy-mm-dd)    |
| `aItem`            | JSON    | Line items                       |
| `HOUSENR`          | numeric | House number                     |
| `ADDRESS2`         | string  | Address line 2                   |
| `ORDERDATE`        | date    | Order date                       |
| `COUNTRYID`        | numeric | Country ID                       |
| `STATE`            | string  | State                            |
| `COMMENT`          | string  | Comment                          |
| `PHONENR`          | string  | Phone number                     |
| `MOBILECOUNTRYCODE`| string  | Mobile country code              |
| `CITY`             | string  | City                             |
| `ORGID`            | numeric | Organisation ID                  |
| `ORDERNR`          | numeric | Order number                     |
| `EMAIL`            | string  | Email address                    |
| `STREET`           | string  | Street address                   |
| `POSTCODE`         | string  | Postcode                         |
| `FORCENOTEXPORTABLE`| boolean| Force not exportable             |

---

### GET /accounting/transaction/
**Description:** Retrieve transactions for a contact

**Required Parameters:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `contactID` | numeric | Contact ID  |

**Optional Parameters:**
| Parameter         | Type    | Description                              |
|-------------------|---------|------------------------------------------|
| `includeFragments`| boolean | Include fragments array (default: false) |

**Response Fields:** `TRANSACTIONID`, `CONTACTID`, `GUID`, `AMOUNT`, `TRANSDATE`, `REFERENCE`, `PAYMENTMETHOD`, `PAYMENTMETHODID`, `TRANSACTIONTYPE`, `TRANSACTIONTYPEID`, `CURRENCY`, `DESCRIPTION`, `FRAGMENTS`

---

### POST /accounting/transaction/
**Description:** Record a new payment transaction

**Required Parameters:**
| Parameter   | Type    | Description                         |
|-------------|---------|-------------------------------------|
| `contactID` | numeric | Person who made the payment         |
| `amount`    | numeric | Transaction amount (in dollars)     |

**Optional Parameters:**
| Parameter         | Type     | Description                                                  |
|-------------------|----------|--------------------------------------------------------------|
| `invoiceID`       | numeric  | Apply transaction to specific invoice                        |
| `paymentMethodID` | numeric  | 1=Cash, 2=Credit Card (default), 4=Direct Deposit, 5=Cheque, 6=EFTPOS |
| `transDate`       | datetime | Transaction date/time in MM/DD/YYYY format (default: now)    |
| `reference`       | string   | Reference/receipt number                                     |
| `description`     | string   | Transaction description                                      |
| `ChequeNr`        | string   | Cheque number (type 5 only)                                  |
| `ChequeDrawer`    | string   | Cheque drawer name (type 5 only)                             |
| `BankName`        | string   | Bank name (type 5 only)                                      |
| `BankBSB`         | string   | BSB number (6 digits; type 5 only)                           |

**Response Fields:** `TRANSACTIONID`, `CONTACTID`, `GUID`, `AMOUNT`, `UNASSIGNEDAMOUNT`, `TRANSDATE`, `PAYMENTMETHODID`, `REFERENCE`, `DESCRIPTION`, `ISCOMPLETED`, `CURRENCY`, `FRAGMENTS` (array with INVOICEID, AMOUNT, APPLIEDDATE, FRAGMENTID)

---

### GET /accounting/catalogueitem/
**Description:** Retrieve all catalogue items

**Response Fields:** `ITEMID`, `ITEMDESCRIPTION`, `ITEMCODE`, `DEFAULTPRICE`, `FINCODE`, `CATEGORY`, `INACTIVE`, `DISPLAYPUBLIC`, `POSTAGE_GROSS`, `POSTAGE_NETT`, `PRICEGSTINCLUSIVE`

---

### POST /accounting/catalogueitem/
**Description:** Create a new catalogue item

**Required Parameters:**
| Parameter        | Type   | Description               |
|------------------|--------|---------------------------|
| `ItemDescription`| string | Item description          |
| `itemCode`       | string | Item code                 |
| `DefaultPrice`   | money  | Default price             |

**Optional Parameters:**
| Parameter           | Type    | Description                          |
|---------------------|---------|--------------------------------------|
| `FinCodeID`         | numeric | Finance code ID                      |
| `GST_type`          | numeric | 0=no GST, 1=GST included, 2=GST exclusive |
| `GST_type_postage`  | numeric | GST type for postage                 |
| `Inactive`          | boolean | Mark as inactive                     |
| `Item_Details`      | string  | Extended item details                |
| `Category`          | string  | Item category                        |
| `DisplayPublic`     | boolean | Show publicly                        |
| `Postage_tax_percent`| money  | Postage tax percentage               |

---

### GET /accounting/catalogueitem/:itemID
**Description:** Retrieve specific catalogue item

**URL Parameter:**
| Parameter | Type    | Description      |
|-----------|---------|------------------|
| `itemID`  | numeric | Catalogue Item ID|

**Response Fields:** `PK`, `ItemDescription`, `ItemCode`, `DefaultPrice`, `FinCodeID`, `GST_type`, `GST_type_postage`, `Inactive`, `LMSID`, `Item_Details`, `Category`, `ImageName`, `DisplayPublic`, `Postage_nett`, `Postage_gross`, `Postage_tax_percent`, `DomainID`

---

### PUT /accounting/catalogueitem/:itemID
**Description:** Update a catalogue item

**URL Parameter:**
| Parameter | Type    | Description      |
|-----------|---------|------------------|
| `itemID`  | numeric | Catalogue Item ID|

**Optional Parameters:** All POST fields are optional for updates.

---

### GET /accounting/ecommerce/payment/url
**Description:** Generate a payment redirect URL for integrated payment gateways

**Required Parameters:**
| Parameter    | Type   | Description                          |
|--------------|--------|--------------------------------------|
| `invoiceGuid`| string | Invoice GUID                         |
| `reference`  | string | Internal identifier for verification |

**Optional Parameters:**
| Parameter     | Type   | Description                    |
|---------------|--------|--------------------------------|
| `redirectURL` | string | URL to redirect after payment  |
| `cancelURL`   | string | URL to redirect on cancellation|

**Response Fields:** `PAYMENTURL`

---

### POST /accounting/ecommerce/payment/form
**Description:** Generate a payment form for integrated payment gateways

**Required Parameters:**
| Parameter    | Type   | Description                          |
|--------------|--------|--------------------------------------|
| `invoiceGuid`| string | Invoice GUID                         |
| `reference`  | string | Internal identifier for verification |

**Optional Parameters:**
| Parameter   | Type   | Description                   |
|-------------|--------|-------------------------------|
| `redirectURL`| string| URL to redirect after payment |

---

### GET /accounting/ecommerce/payment/ref/:reference
**Description:** Verify payment status by reference

**URL Parameter:**
| Parameter   | Type   | Description                    |
|-------------|--------|--------------------------------|
| `reference` | string | Payment reference to verify    |

**Response:** Payment status (pending, paid, or failed) with error details if applicable.

---

## 5. REPORT ENDPOINTS

### GET /report/list
**Description:** Retrieve all available reports (Live, Warehoused, and saved)

**Response:** Array of reports with name, description, and reportReference.

---

### GET /report/saved/list
**Description:** Retrieve user's saved reports

**Response:** Array of saved reports with `reportId` key.

---

### GET /report/fields
**Description:** Get available display fields for a specific report

**Required Parameters:**
| Parameter         | Type   | Description      |
|-------------------|--------|------------------|
| `reportReference` | string | Report reference |

**Response:** Array of fields with `name` key (fieldReference).

---

### GET /report/field
**Description:** Discover filter operators available for a specific field

**Required Parameters:**
| Parameter        | Type   | Description      |
|------------------|--------|------------------|
| `fieldReference` | string | Field reference  |

**Response:** `operatorOptions` array with operators: `is`, `on`, `between`, `before`, `after`, `startsWith`, `endsWith`, `contains`, `doesNotContain`.

---

### GET /report/saved
**Description:** View display and filter fields for a saved report

**Required Parameters:**
| Parameter  | Type    | Description  |
|------------|---------|--------------|
| `reportId` | numeric | Report ID    |

**Response:** `viewFields` array, `filterFields` array.

---

### POST /report/run
**Description:** Execute a live report

**Required Parameters:**
| Parameter              | Type   | Description                               |
|------------------------|--------|-------------------------------------------|
| `reportReference`      | string | Report reference identifier               |
| `selectedFilterFields` | array  | Filter fields as stringified JSON objects |

**Optional Parameters:**
| Parameter           | Type    | Description                                         |
|---------------------|---------|-----------------------------------------------------|
| `selectedViewFields`| array   | Fields to display in output                         |
| `reportId`          | numeric | Saved report ID                                     |
| `displayLength`     | numeric | Records per page (10–1000)                          |
| `offsetRows`        | numeric | Records to skip (max 100,000)                       |

**Filter Field Structure:**
```json
{
  "name": "fieldReference",
  "operator": "is",
  "value": "filterValue",
  "value2": "optionalSecondValue"
}
```

**Response:** Report data with count and field values.

---

### POST /report/saved/run
**Description:** Execute a saved report

**Required Parameters:**
| Parameter  | Type    | Description     |
|------------|---------|-----------------|
| `reportId` | numeric | Saved report ID |

**Optional Parameters:**
| Parameter        | Type    | Description                                         |
|------------------|---------|-----------------------------------------------------|
| `filterOverride` | JSON    | Override standard filter values: `[{NAME, VALUE, VALUE2}]` |
| `displayLength`  | numeric | Records per page (10–1000)                          |
| `offsetRows`     | numeric | Records to skip (max 100,000 for warehoused reports)|

**Response Fields:** `ReportType`, `Data`, `ErrorMsg`, `Count`, `ReportName`, `Success`, filter information.

---

## 6. AGENT ENDPOINTS

### POST /agent/
**Description:** Create a new marketing agent

**Required Parameters:**
| Parameter    | Type    | Description                                     |
|--------------|---------|-------------------------------------------------|
| `contactID`  | numeric | Contact ID of the agent                         |
| `taxRuleID`  | numeric | 1=Excluding GST, 2=Including GST, 3=Exempt      |

**Optional Parameters:**
| Parameter                    | Type    | Description                        |
|------------------------------|---------|------------------------------------|
| `commissionRate`             | numeric | Commission percentage (0–100; default: 0) |
| `Custom_Field_[VariableName]`| text    | Custom field values                |

**Response Fields:** `MARKETINGAGENTID`, `CONTACTID`, `DEFAULTCOMMISSIONRATE`, `ACTIVE`, `CUSTOMFIELD_*`

---

### PUT /agent/
**Description:** Update a marketing agent (by body parameters)

**Required Parameters:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `contactID` | numeric | Contact ID  |

**Optional Parameters:**
| Parameter                    | Type    | Description                |
|------------------------------|---------|----------------------------|
| `agentID`                    | numeric | Agent ID (alternative to contactID) |
| `commissionRate`             | numeric | Commission percentage (0–100) |
| `taxRuleID`                  | numeric | 1=Excl. GST, 2=Incl. GST, 3=Exempt |
| `Custom_Field_[variableName]`| text    | Custom field values        |

---

### GET /agent/:contactID
**Description:** Retrieve agent details by contact ID

**URL Parameter:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `contactID` | numeric | Contact ID  |

**Response:** Agent object; returns 204 No Content if contact is not an agent.

---

### PUT /agent/:contactID
**Description:** Update agent by contact ID

**URL Parameter:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `contactID` | numeric | Contact ID  |

**Optional Parameters:**
| Parameter                    | Type    | Description                   |
|------------------------------|---------|-------------------------------|
| `taxRuleID`                  | numeric | 1=Excl. GST, 2=Incl. GST, 3=Exempt |
| `commissionRate`             | numeric | Commission percentage (0–100) |
| `Custom_Field_[variableName]`| text    | Custom field values           |

**Response:** Agent object; returns 404 if record doesn't exist.

---

## 7. TRAINER ENDPOINTS

### GET /trainer/:trainerID
**Description:** Retrieve trainer details

**URL Parameter:**
| Parameter   | Type    | Description |
|-------------|---------|-------------|
| `trainerID` | numeric | Trainer ID  |

**Response:** Trainer struct with `ConsultantID`, `Name`, `Email`, `Experience`, and time-tracking fields.

---

## 8. VENUE ENDPOINTS

### POST /venues
**Description:** Retrieve venue(s) details or create venue

**Optional Parameters:**
| Parameter      | Type    | Description                    |
|----------------|---------|--------------------------------|
| `contactID`    | numeric | Related Contact ID             |
| `offset`       | numeric | Pagination start (default: 0)  |
| `displayLength`| numeric | Records per page (default: 10, max: 100) |
| `name`         | string  | Venue name filter              |
| `sAddress1`    | string  | Address line 1                 |
| `sAddress2`    | string  | Address line 2                 |
| `sCity`        | string  | City                           |
| `sState`       | string  | State                          |
| `sPostcode`    | string  | Postcode                       |
| `mobilePhone`  | string  | Contact mobile phone           |

**Response:** Venue details with optional error information.

---

## 9. TEMPLATE / EMAIL ENDPOINTS

### POST /template/email
**Description:** Send a templated email

**Optional Parameters:**
| Parameter                    | Type    | Description                                          |
|------------------------------|---------|------------------------------------------------------|
| `planID`                     | numeric | Template ID to use                                   |
| `contactID`                  | numeric | Primary contact to email                             |
| `instanceID`                 | numeric | Course instance                                      |
| `invoiceID`                  | numeric | Associated invoice                                   |
| `subject`                    | string  | Email subject override                               |
| `type`                       | string  | Course type                                          |
| `invoiceAttachmentPlanID`    | numeric | Invoice template attachment ID                       |
| `hasIcalAttachment`          | boolean | Attach iCalendar events                              |
| `verbose`                    | boolean | Include detailed report                              |
| `content`                    | string  | Template content                                     |
| `from`                       | string  | Sender email or contactID                            |
| `to`                         | string  | Recipient specification                              |
| `includeStatus`              | string  | Student status filter                                |
| `honourUnsubscribed`         | boolean | Respect unsubscribe preference                       |
| `attachmentPlanID`           | numeric | PDF template attachment ID                           |
| `attachAccreditedCertificate`| boolean | Attach accredited certificate                        |
| `attachWorkshopCertificate`  | boolean | Attach workshop certificate                          |
| `userRoleID`                 | numeric | Filter recipients by user role                       |
| `contactRoleID`              | numeric | Filter recipients by contact role                    |
| `skillGroupID`               | numeric | Filter recipients by skill group                     |
| `replaceContent`             | string  | JSON key-value pairs to replace in template          |
| `copyToAlternateEmailAddress`| boolean | Send to alternate email addresses                    |

**Response Fields:** `FAILEDCOUNT`, `ATTEMPTEDCOUNT`, `SUCCESSCOUNT`, `MESSAGE`

---

## 10. USER ENDPOINTS

### POST /user
**Description:** Create a user record

**Parameters:** User account details

**Note:** User records are automatically generated when contacts enrol in courses.

---

### GET /user/roles
**Description:** Retrieve available user roles

**Response:** Array of available roles.

---

## 11. WEBHOOK EVENTS

Webhook payloads use this envelope:
```json
{
  "type": "namespace.event_name",
  "message": {},
  "clientId": 12345678,
  "messageId": "669ee575-71c1-5cf2-97ee-bb20be1f817d",
  "timestamp": "2024-02-25T23:30:38.056Z"
}
```

**Security Headers:** `Ax-Signature-Version`, `Ax-Signature` (SHA256 signing)

**Retry Policy:** Up to 20 automatic retry attempts on failed delivery

### Calendar Events
| Event                    | Description         |
|--------------------------|---------------------|
| `calendar.event_created` | New event added     |
| `calendar.event_updated` | Event modified      |
| `calendar.event_deleted` | Event removed       |

### Contact Events
| Event                    | Description                         |
|--------------------------|-------------------------------------|
| `contact.contact_created`| New contact created                 |
| `contact.contact_updated`| Contact record updated              |
| `contact.contact_deleted`| Contact record deleted              |
| `contact.contact_merged` | Multiple contacts consolidated      |

### Course Events
| Event                             | Description                   |
|-----------------------------------|-------------------------------|
| `course.venue_created`            | New venue created             |
| `course.venue_updated`            | Venue updated                 |
| `course.venue_deleted`            | Venue deleted                 |
| `course.qualification_created`    | Qualification created         |
| `course.qualification_updated`    | Qualification updated         |
| `course.qualification_deleted`    | Qualification deleted         |
| `course.workshop_type_created`    | Workshop type created         |
| `course.workshop_type_updated`    | Workshop type updated         |
| `course.workshop_type_deleted`    | Workshop type deleted         |
| `course.workshop_created`         | Workshop created              |
| `course.workshop_updated`         | Workshop updated              |
| `course.workshop_deleted`         | Workshop deleted              |
| `course.class_created`            | Class created                 |
| `course.class_updated`            | Class updated                 |
| `course.class_deleted`            | Class deleted                 |

### Student / Enrolment Events
| Event                                   | Description                        |
|-----------------------------------------|------------------------------------|
| `student.workshop_enrolment_created`    | Workshop enrolment created         |
| `student.workshop_enrolment_updated`    | Workshop enrolment updated         |
| `student.workshop_enrolment_deleted`    | Workshop enrolment deleted         |
| `student.workshop_enrolment_status_changed` | Workshop enrolment status changed |
| `student.class_enrolment_created`       | Class enrolment created            |
| `student.class_enrolment_updated`       | Class enrolment updated            |
| `student.class_enrolment_deleted`       | Class enrolment deleted            |
| `student.class_enrolment_status_changed`| Class enrolment status changed     |
| `student.unit_enrolment_created`        | Unit enrolment created             |
| `student.unit_enrolment_status_changed` | Unit enrolment status changed      |
| `student.activity_enrolment_created`    | Activity enrolment created         |
| `student.activity_enrolment_updated`    | Activity enrolment updated         |
| `student.activity_enrolment_deleted`    | Activity enrolment deleted         |

### Trainer Events
| Event                    | Description         |
|--------------------------|---------------------|
| `trainer.trainer_created`| Trainer created     |
| `trainer.trainer_updated`| Trainer updated     |
| `trainer.trainer_deleted`| Trainer deleted     |

---

## QUICK REFERENCE — COMPLETE ENDPOINT LIST

| Method   | Endpoint                                             | Description                                |
|----------|------------------------------------------------------|--------------------------------------------|
| POST     | `/contact/`                                          | Create contact                             |
| GET      | `/contact/:contactID`                                | Get contact details                        |
| PUT      | `/contact/:contactID`                                | Update contact                             |
| GET      | `/contacts/search`                                   | Search contacts                            |
| POST     | `/contact/note/`                                     | Add note to contact                        |
| POST     | `/contact/verifyUSI`                                 | Verify USI for contact                     |
| GET      | `/contact/enrolments/:contactID`                     | Get contact's enrolments                   |
| GET      | `/contact/enrolment/certificate`                     | Download enrolment certificate             |
| GET      | `/courses/`                                          | List all courses                           |
| GET      | `/course/instances`                                  | Get instances for a course                 |
| GET      | `/course/instance/search`                            | Advanced course instance search            |
| GET      | `/course/instance/detail`                            | Get course instance details                |
| PUT      | `/course/instance/`                                  | Update course instance                     |
| GET      | `/course/detail`                                     | Get course type detail                     |
| GET      | `/course/locations`                                  | List training locations                    |
| GET      | `/course/enrolments`                                 | List enrolments                            |
| GET      | `/course/discounts`                                  | Check applicable discounts                 |
| POST     | `/course/enrol`                                      | Enrol contact in course                    |
| POST     | `/course/enrolMultiple`                              | Enrol multiple contacts                    |
| PUT      | `/course/enrolment`                                  | Update enrolment record                    |
| GET      | `/course/instance/attendance`                        | Get attendance records                     |
| PUT      | `/v2/learningPlan/modules/enrolments`               | Update learning plan module enrolment      |
| GET      | `/accounting/invoice/`                               | List invoices for contact                  |
| POST     | `/accounting/invoice/`                               | Create invoice                             |
| GET      | `/accounting/invoice/:invoiceID`                     | Get invoice details                        |
| PUT      | `/accounting/invoice/:invoiceID`                     | Update invoice                             |
| GET      | `/accounting/invoice/:invoiceID/paymenturl`          | Get payment URL                            |
| PUT      | `/accounting/invoice/:invoiceGUID/approve`           | Approve invoice for payment                |
| POST     | `/accounting/invoice/:invoiceGUID/unarchive`         | Unarchive invoice                          |
| POST     | `/accounting/invoice/:invoiceGUID/void`              | Void invoice                               |
| GET      | `/accounting/creditnote/`                            | List credit notes for contact              |
| POST     | `/accounting/creditnote/`                            | Create credit note                         |
| GET      | `/accounting/creditnote/:creditnoteID`               | Get credit note details                    |
| PUT      | `/accounting/creditnote/:creditnoteID`               | Update credit note                         |
| GET      | `/accounting/transaction/`                           | List transactions for contact              |
| POST     | `/accounting/transaction/`                           | Record transaction                         |
| GET      | `/accounting/catalogueitem/`                         | List catalogue items                       |
| POST     | `/accounting/catalogueitem/`                         | Create catalogue item                      |
| GET      | `/accounting/catalogueitem/:itemID`                  | Get catalogue item                         |
| PUT      | `/accounting/catalogueitem/:itemID`                  | Update catalogue item                      |
| GET      | `/accounting/ecommerce/payment/url`                  | Generate payment redirect URL              |
| POST     | `/accounting/ecommerce/payment/form`                 | Generate payment form                      |
| GET      | `/accounting/ecommerce/payment/ref/:reference`       | Verify payment status                      |
| GET      | `/report/list`                                       | List available reports                     |
| GET      | `/report/saved/list`                                 | List saved reports                         |
| GET      | `/report/fields`                                     | Get report display fields                  |
| GET      | `/report/field`                                      | Get filter operators for a field           |
| GET      | `/report/saved`                                      | View saved report fields                   |
| POST     | `/report/run`                                        | Run a live report                          |
| POST     | `/report/saved/run`                                  | Run a saved report                         |
| POST     | `/agent/`                                            | Create marketing agent                     |
| PUT      | `/agent/`                                            | Update agent (by body)                     |
| GET      | `/agent/:contactID`                                  | Get agent by contact                       |
| PUT      | `/agent/:contactID`                                  | Update agent by contact                    |
| GET      | `/trainer/:trainerID`                                | Get trainer details                        |
| POST     | `/venues`                                            | Get/search venues                          |
| POST     | `/template/email`                                    | Send templated email                       |
| POST     | `/user`                                              | Create user                                |
| GET      | `/user/roles`                                        | List user roles                            |
| POST     | `/user/login`                                        | Login returning student                    |
