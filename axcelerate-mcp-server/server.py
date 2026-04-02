#!/usr/bin/env python3
"""
Axcelerate MCP Server
Exposes Axcelerate training management system API operations as MCP tools.
"""

import json
import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ── Load credentials ──────────────────────────────────────────────────────────

load_dotenv()

BASE_URL = os.getenv("AXCELERATE_BASE_URL", "")
API_TOKEN = os.getenv("AXCELERATE_API_TOKEN", "")
WS_TOKEN = os.getenv("AXCELERATE_WS_TOKEN", "")

# ── Async HTTP client ─────────────────────────────────────────────────────────


class AxcelerateClient:
    """Async HTTP client for the Axcelerate REST API.

    All POST/PUT requests use form encoding (data=), never JSON,
    as required by the Axcelerate API.
    """

    def __init__(self) -> None:
        self.base_url = BASE_URL.rstrip("/")
        self.headers = {
            "apitoken": API_TOKEN,
            "wstoken": WS_TOKEN,
        }
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=60.0,
            )
        return self._client

    async def get(self, path: str, params: dict | None = None) -> dict | list:
        client = await self._get_client()
        r = await client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    async def post(self, path: str, data: dict | None = None) -> dict | list:
        client = await self._get_client()
        r = await client.post(path, data=data)
        r.raise_for_status()
        if r.status_code == 204:
            return {"status": "success", "code": 204}
        return r.json()

    async def put(self, path: str, data: dict | None = None) -> dict | list:
        client = await self._get_client()
        r = await client.put(path, data=data)
        r.raise_for_status()
        if r.status_code == 204:
            return {"status": "success", "code": 204}
        return r.json()


ax = AxcelerateClient()

# ── MCP Server ─────────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="Axcelerate",
    instructions=(
        "Axcelerate training management system API. "
        "Use these tools to manage contacts, courses, enrolments, "
        "invoices, payments, emails, and reports. "
        "All dates use YYYY-MM-DD format unless noted otherwise. "
        "Course types: w=Workshop, p=Accredited Program, el=E-Learning."
    ),
)

# ──────────────────────────────────────────────────────────────────────────────
#  CONTACT TOOLS
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def search_contacts(
    keyword: Optional[str] = None,
    given_name: Optional[str] = None,
    surname: Optional[str] = None,
    email: Optional[str] = None,
    optional_id: Optional[str] = None,
    contact_id: Optional[int] = None,
    dob: Optional[str] = None,
    offset: int = 0,
    display_length: int = 50,
) -> dict | list:
    """Search for contacts in Axcelerate.

    Args:
        keyword: Free-text search across multiple fields
        given_name: Filter by first name
        surname: Filter by last name
        email: Filter by email address
        optional_id: Filter by optional/student ID
        contact_id: Filter by exact contact ID
        dob: Filter by date of birth (YYYY-MM-DD)
        offset: Pagination start position
        display_length: Max records to return (up to 100)
    """
    params: dict = {"offset": offset, "displayLength": display_length}
    if keyword:
        params["search"] = keyword
    if given_name:
        params["givenName"] = given_name
    if surname:
        params["surname"] = surname
    if email:
        params["emailAddress"] = email
    if optional_id:
        params["optionalID"] = optional_id
    if contact_id:
        params["contactID"] = contact_id
    if dob:
        params["DOB"] = dob
    return await ax.get("/contacts/search", params=params)


@mcp.tool()
async def get_contact(contact_id: int) -> dict:
    """Get full details for a specific contact.

    Args:
        contact_id: The contact ID to retrieve
    """
    return await ax.get(f"/contact/{contact_id}")


@mcp.tool()
async def create_contact(
    given_name: str,
    surname: str,
    email: Optional[str] = None,
    mobile: Optional[str] = None,
    phone: Optional[str] = None,
    dob: Optional[str] = None,
    sex: Optional[str] = None,
    organisation: Optional[str] = None,
    optional_id: Optional[str] = None,
    address1: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postcode: Optional[str] = None,
    country: Optional[str] = None,
    usi: Optional[str] = None,
) -> dict:
    """Create a new contact in Axcelerate. Does not deduplicate.

    Args:
        given_name: First name (max 40 chars)
        surname: Last name (max 40 chars)
        email: Email address
        mobile: Mobile phone number
        phone: Home phone number
        dob: Date of birth (YYYY-MM-DD)
        sex: M, F, or X
        organisation: Organisation name
        optional_id: Optional reference/student ID
        address1: Postal address line 1
        city: Suburb/town
        state: State code (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)
        postcode: Postal code
        country: Country name
        usi: Unique Student Identifier (10 chars)
    """
    data: dict = {"givenName": given_name, "surname": surname}
    if email:
        data["emailAddress"] = email
    if mobile:
        data["mobilephone"] = mobile
    if phone:
        data["phone"] = phone
    if dob:
        data["dob"] = dob
    if sex:
        data["sex"] = sex
    if organisation:
        data["organisation"] = organisation
    if optional_id:
        data["optionalID"] = optional_id
    if address1:
        data["address1"] = address1
    if city:
        data["city"] = city
    if state:
        data["state"] = state
    if postcode:
        data["postcode"] = postcode
    if country:
        data["country"] = country
    if usi:
        data["USI"] = usi
    return await ax.post("/contact/", data=data)


@mcp.tool()
async def update_contact(
    contact_id: int,
    given_name: Optional[str] = None,
    surname: Optional[str] = None,
    email: Optional[str] = None,
    mobile: Optional[str] = None,
    phone: Optional[str] = None,
    dob: Optional[str] = None,
    sex: Optional[str] = None,
    organisation: Optional[str] = None,
    optional_id: Optional[str] = None,
    address1: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postcode: Optional[str] = None,
    usi: Optional[str] = None,
) -> dict:
    """Update an existing contact's details.

    Args:
        contact_id: The contact ID to update
        given_name: First name
        surname: Last name
        email: Email address
        mobile: Mobile phone
        phone: Home phone
        dob: Date of birth (YYYY-MM-DD)
        sex: M, F, or X
        organisation: Organisation name
        optional_id: Optional reference/student ID
        address1: Postal address line 1
        city: Suburb/town
        state: State code
        postcode: Postal code
        usi: Unique Student Identifier
    """
    data: dict = {}
    if given_name:
        data["givenName"] = given_name
    if surname:
        data["surname"] = surname
    if email:
        data["emailAddress"] = email
    if mobile:
        data["mobilephone"] = mobile
    if phone:
        data["phone"] = phone
    if dob:
        data["dob"] = dob
    if sex:
        data["sex"] = sex
    if organisation:
        data["organisation"] = organisation
    if optional_id:
        data["optionalID"] = optional_id
    if address1:
        data["address1"] = address1
    if city:
        data["city"] = city
    if state:
        data["state"] = state
    if postcode:
        data["postcode"] = postcode
    if usi:
        data["USI"] = usi
    return await ax.put(f"/contact/{contact_id}", data=data)


@mcp.tool()
async def add_contact_note(
    contact_id: int,
    note: str,
    note_type_id: str = "88",
) -> dict:
    """Add a note to a contact record.

    Args:
        contact_id: Contact to add the note to
        note: Note content text
        note_type_id: Type of note (default "88" = System Note)
    """
    return await ax.post(
        "/contact/note/",
        data={
            "contactID": contact_id,
            "contactNote": note,
            "noteTypeID": note_type_id,
        },
    )


@mcp.tool()
async def get_contact_enrolments(contact_id: int) -> list:
    """Get all enrolments for a specific contact.

    Args:
        contact_id: The contact ID
    """
    return await ax.get(f"/contact/enrolments/{contact_id}")


@mcp.tool()
async def verify_usi(contact_id: int) -> dict:
    """Verify a contact's Unique Student Identifier (USI).

    Args:
        contact_id: Contact ID to verify USI for
    """
    return await ax.post("/contact/verifyUSI", data={"contactID": contact_id})


# ──────────────────────────────────────────────────────────────────────────────
#  COURSE & INSTANCE TOOLS
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def list_courses(
    course_type: str = "all",
    search_term: Optional[str] = None,
    is_active: Optional[bool] = None,
    offset: int = 0,
    display_length: int = 50,
) -> list:
    """List all courses, optionally filtered.

    Args:
        course_type: w=Workshop, p=Accredited Program, el=E-Learning, all=All
        search_term: Filter by search term
        is_active: Filter by active/inactive status
        offset: Pagination start
        display_length: Records to return (default 50)
    """
    params: dict = {
        "type": course_type,
        "offset": offset,
        "displayLength": display_length,
    }
    if search_term:
        params["searchTerm"] = search_term
    if is_active is not None:
        params["isActive"] = is_active
    return await ax.get("/courses/", params=params)


@mcp.tool()
async def search_instances(
    course_type: str = "all",
    course_id: Optional[int] = None,
    instance_id: Optional[int] = None,
    location: Optional[str] = None,
    name: Optional[str] = None,
    code: Optional[str] = None,
    search_term: Optional[str] = None,
    start_date_min: Optional[str] = None,
    start_date_max: Optional[str] = None,
    is_active: Optional[bool] = None,
    enrolment_open: Optional[bool] = None,
    trainer_contact_id: Optional[int] = None,
    offset: int = 0,
    display_length: int = 50,
) -> list:
    """Search for course instances with flexible filters.

    Args:
        course_type: w=Workshop, p=Program, el=E-Learning, all=All
        course_id: Filter by course/activity type ID
        instance_id: Filter by specific instance ID
        location: Location filter (LIKE search, workshops only)
        name: Course name filter (LIKE search)
        code: Course code filter (prefix match)
        search_term: General search term
        start_date_min: Minimum start date (YYYY-MM-DD)
        start_date_max: Maximum start date (YYYY-MM-DD)
        is_active: Filter active/inactive
        enrolment_open: Only return instances with open enrolment
        trainer_contact_id: Filter by trainer contact ID
        offset: Pagination start
        display_length: Records to return
    """
    params: dict = {
        "type": course_type,
        "offset": offset,
        "displayLength": display_length,
    }
    if course_id:
        params["ID"] = course_id
    if instance_id:
        params["InstanceID"] = instance_id
    if location:
        params["location"] = location
    if name:
        params["name"] = name
    if code:
        params["code"] = code
    if search_term:
        params["searchTerm"] = search_term
    if start_date_min:
        params["startDate_min"] = start_date_min
    if start_date_max:
        params["startDate_max"] = start_date_max
    if is_active is not None:
        params["isActive"] = is_active
    if enrolment_open is not None:
        params["enrolmentOpen"] = enrolment_open
    if trainer_contact_id:
        params["trainerContactID"] = trainer_contact_id
    return await ax.get("/course/instance/search", params=params)


@mcp.tool()
async def get_instance_detail(instance_id: int, course_type: str) -> dict:
    """Get detailed information for a specific course instance.

    Args:
        instance_id: The instance ID
        course_type: w=Workshop, p=Program, el=E-Learning
    """
    return await ax.get(
        "/course/instance/detail",
        params={"instanceID": instance_id, "type": course_type},
    )


@mcp.tool()
async def update_instance(
    instance_id: int,
    course_type: str,
    name: Optional[str] = None,
    start_date: Optional[str] = None,
    finish_date: Optional[str] = None,
    cost: Optional[float] = None,
    max_participants: Optional[int] = None,
) -> dict:
    """Update a course instance.

    Args:
        instance_id: The instance ID
        course_type: w=Workshop, p=Program, el=E-Learning
        name: New instance/course name
        start_date: New start date (YYYY-MM-DD)
        finish_date: New finish date (YYYY-MM-DD)
        cost: Cost per student
        max_participants: Maximum participant capacity
    """
    data: dict = {"ID": instance_id, "type": course_type}
    if name:
        data["ProgramName"] = name
    if start_date:
        data["PStartDate"] = start_date
    if finish_date:
        data["PFinishDate"] = finish_date
    if cost is not None:
        data["cost"] = cost
    if max_participants is not None:
        data["maxparticipants"] = max_participants
    return await ax.put("/course/instance/", data=data)


@mcp.tool()
async def list_locations(
    public: Optional[bool] = None,
    only_future: Optional[bool] = None,
) -> list:
    """List available training locations/venues.

    Args:
        public: Only show public locations
        only_future: Only show locations with future activities
    """
    params: dict = {}
    if public is not None:
        params["public"] = public
    if only_future is not None:
        params["onlyFuture"] = only_future
    return await ax.get("/course/locations", params=params)


# ──────────────────────────────────────────────────────────────────────────────
#  ENROLMENT TOOLS
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def enrol_contact(
    contact_id: int,
    instance_id: int,
    course_type: str,
    generate_invoice: bool = True,
    cost: Optional[float] = None,
    tentative: Optional[bool] = None,
    payer_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    po_number: Optional[str] = None,
    date_commenced: Optional[str] = None,
) -> dict:
    """Enrol a contact into a course instance.

    Args:
        contact_id: Contact being enrolled
        instance_id: Activity instance ID
        course_type: w=Workshop, p=Program, el=E-Learning
        generate_invoice: Create a new invoice (default True)
        cost: Discounted cost (if applying discounts)
        tentative: Enrol as tentative/waitlisted (w and el only)
        payer_id: Contact ID of the payer (if different from student)
        invoice_id: Existing invoice ID to add enrolment to
        po_number: Purchase order number
        date_commenced: Enrolment start date (YYYY-MM-DD)
    """
    data: dict = {
        "contactID": contact_id,
        "instanceID": instance_id,
        "type": course_type,
        "generateInvoice": generate_invoice,
    }
    if cost is not None:
        data["cost"] = cost
    if tentative is not None:
        data["tentative"] = tentative
    if payer_id:
        data["payerID"] = payer_id
    if invoice_id:
        data["invoiceID"] = invoice_id
    if po_number:
        data["PONumber"] = po_number
    if date_commenced:
        data["dateCommenced"] = date_commenced
    return await ax.post("/course/enrol", data=data)


@mcp.tool()
async def bulk_enrol(
    instance_id: int,
    contact_ids: str,
    course_type: str = "w",
    generate_invoice: bool = True,
    cost: Optional[float] = None,
) -> dict:
    """Enrol multiple contacts into a workshop in a single request.

    Args:
        instance_id: Workshop instance ID
        contact_ids: Comma-separated list of contact IDs (e.g. "123,456,789")
        course_type: Must be "w" (workshops only)
        generate_invoice: Create invoices (default True)
        cost: Cost per student
    """
    data: dict = {
        "instanceID": instance_id,
        "type": course_type,
        "contactIDs": contact_ids,
        "generateInvoice": generate_invoice,
    }
    if cost is not None:
        data["cost"] = cost
    return await ax.post("/course/enrolMultiple", data=data)


@mcp.tool()
async def search_enrolments(
    contact_id: Optional[int] = None,
    instance_id: Optional[int] = None,
    course_type: Optional[str] = None,
    course_id: Optional[int] = None,
    org_id: Optional[int] = None,
) -> list:
    """Search enrolments with flexible filters.

    Args:
        contact_id: Filter by contact
        instance_id: Filter by instance
        course_type: w=Workshop, p=Program, el=E-Learning
        course_id: Filter by activity type ID
        org_id: Filter by organisation
    """
    params: dict = {}
    if contact_id:
        params["contactID"] = contact_id
    if instance_id:
        params["instanceID"] = instance_id
    if course_type:
        params["type"] = course_type
    if course_id:
        params["ID"] = course_id
    if org_id:
        params["orgID"] = org_id
    return await ax.get("/course/enrolments", params=params)


@mcp.tool()
async def update_enrolment(
    contact_id: int,
    instance_id: int,
    course_type: str,
    status: Optional[str] = None,
    outcome: Optional[str] = None,
    completion_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Update an existing enrolment record.

    Args:
        contact_id: Contact being updated
        instance_id: Activity instance ID
        course_type: w=Workshop, p=Program, s=Unit, el=E-Learning
        status: Enrolment status code (e.g. A=Active, C=Completed, T=Tentative)
        outcome: Outcome code (e.g. C=Competent)
        completion_date: Completion date (DD/MM/YYYY)
        start_date: Activity start date (YYYY-MM-DD)
        end_date: Activity end date (YYYY-MM-DD)
    """
    data: dict = {
        "contactID": contact_id,
        "instanceID": instance_id,
        "type": course_type,
    }
    if status:
        data["status"] = status
    if outcome:
        data["competent"] = outcome
    if completion_date:
        data["completionDate"] = completion_date
    if start_date:
        data["activityStartDate"] = start_date
    if end_date:
        data["activityEndDate"] = end_date
    return await ax.put("/course/enrolment", data=data)


# ──────────────────────────────────────────────────────────────────────────────
#  INVOICE TOOLS
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def list_invoices(
    contact_id: int,
    external_reference: Optional[str] = None,
) -> list:
    """List invoices for a contact.

    Args:
        contact_id: Contact ID to list invoices for
        external_reference: Filter by external reference
    """
    params: dict = {"contactID": contact_id}
    if external_reference:
        params["externalReference"] = external_reference
    return await ax.get("/accounting/invoice/", params=params)


@mcp.tool()
async def get_invoice(
    invoice_id: int,
    include_enrolment_data: bool = False,
) -> dict:
    """Get detailed information for a specific invoice.

    Args:
        invoice_id: Internal invoice ID (not invoice number)
        include_enrolment_data: Include linked enrolment details with line items
    """
    params: dict = {}
    if include_enrolment_data:
        params["includeEnrolmentData"] = True
    return await ax.get(f"/accounting/invoice/{invoice_id}", params=params)


@mcp.tool()
async def create_invoice(
    contact_id: int,
    firstname: str,
    surname: str,
    invoice_date: str,
    order_date: str,
    items_json: str,
    external_reference: Optional[str] = None,
) -> dict:
    """Create a new invoice with line items.

    Args:
        contact_id: Contact ID for the invoice
        firstname: Contact first name
        surname: Contact surname
        invoice_date: Invoice date (YYYY-MM-DD)
        order_date: Order date (YYYY-MM-DD)
        items_json: JSON array of line items. Each item needs:
            DESCRIPTION, QTY, ITEMCODE, UNITPRICEGROSS, TAXPERCENT, FINANCECODE, HASCHILDREN
            Example: [{"DESCRIPTION":"Course Fee","QTY":1,"ITEMCODE":"COURSE01","UNITPRICEGROSS":500,"TAXPERCENT":10,"FINANCECODE":"","HASCHILDREN":false}]
        external_reference: External reference (max 60 chars)
    """
    data: dict = {
        "contactID": contact_id,
        "firstname": firstname,
        "surname": surname,
        "invoiceDate": invoice_date,
        "orderDate": order_date,
        "aItem": items_json,
    }
    if external_reference:
        data["externalReference"] = external_reference
    return await ax.post("/accounting/invoice/", data=data)


@mcp.tool()
async def approve_invoice(invoice_guid: str) -> dict:
    """Approve an invoice for payment. Returns the payment URL.

    Args:
        invoice_guid: Invoice GUID (UUID string, from INVGUID field)
    """
    return await ax.put(f"/accounting/invoice/{invoice_guid}/approve")


@mcp.tool()
async def void_invoice(invoice_guid: str) -> dict:
    """Void an invoice. Cannot void if payments have been applied.

    Args:
        invoice_guid: Invoice GUID (UUID string, from INVGUID field)
    """
    return await ax.post(f"/accounting/invoice/{invoice_guid}/void")


@mcp.tool()
async def get_payment_url(invoice_id: int) -> dict:
    """Get the native payment URL for an invoice.

    Args:
        invoice_id: Invoice ID
    """
    return await ax.get(f"/accounting/invoice/{invoice_id}/paymenturl")


# ──────────────────────────────────────────────────────────────────────────────
#  CREDIT NOTE TOOLS
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def list_credit_notes(contact_id: int) -> list:
    """List credit notes for a contact.

    Args:
        contact_id: Contact ID
    """
    return await ax.get("/accounting/creditnote/", params={"contactID": contact_id})


@mcp.tool()
async def create_credit_note(
    contact_id: int,
    firstname: str,
    surname: str,
    items_json: str,
) -> dict:
    """Create a credit note (refund).

    Args:
        contact_id: Contact ID
        firstname: Contact first name
        surname: Contact surname
        items_json: JSON array of line items. Each needs:
            DESCRIPTION, QTY, ITEMCODE, TAXPERCENT, UNITPRICEGROSS
    """
    return await ax.post(
        "/accounting/creditnote/",
        data={
            "contactID": contact_id,
            "firstname": firstname,
            "surname": surname,
            "aItem": items_json,
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
#  PAYMENT TOOLS
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def record_payment(
    contact_id: int,
    amount: float,
    payment_method_id: int = 2,
    invoice_id: Optional[int] = None,
    trans_date: Optional[str] = None,
    reference: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """Record a payment transaction.

    If invoice_id is omitted, the payment becomes unallocated credit.

    Args:
        contact_id: Person who made the payment
        amount: Transaction amount in dollars
        payment_method_id: Payment method —
            1=Cash, 2=Credit Card (default), 4=Direct Deposit/EFT,
            5=Cheque, 6=EFTPOS, 8=Bad Debt, 9=Direct Debit, 10=Agent Deduction
        invoice_id: Apply payment to this invoice (omit for unallocated credit)
        trans_date: Transaction date (MM/DD/YYYY, default: now)
        reference: Reference/receipt number
        description: Transaction description
    """
    data: dict = {
        "contactID": contact_id,
        "amount": amount,
        "paymentMethodID": payment_method_id,
    }
    if invoice_id:
        data["invoiceID"] = invoice_id
    if trans_date:
        data["transDate"] = trans_date
    if reference:
        data["reference"] = reference
    if description:
        data["description"] = description
    return await ax.post("/accounting/transaction/", data=data)


@mcp.tool()
async def list_transactions(
    contact_id: int,
    include_fragments: bool = False,
) -> list:
    """List payment transactions for a contact.

    Args:
        contact_id: Contact ID
        include_fragments: Include payment allocation fragments
    """
    params: dict = {"contactID": contact_id}
    if include_fragments:
        params["includeFragments"] = True
    return await ax.get("/accounting/transaction/", params=params)


@mcp.tool()
async def verify_payment(reference: str) -> dict:
    """Verify payment status by reference.

    Args:
        reference: Payment reference to verify
    """
    return await ax.get(f"/accounting/ecommerce/payment/ref/{reference}")


# ──────────────────────────────────────────────────────────────────────────────
#  EMAIL TOOL
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def send_template_email(
    template_id: int,
    contact_id: Optional[int] = None,
    instance_id: Optional[int] = None,
    course_type: Optional[str] = None,
    invoice_id: Optional[int] = None,
    subject: Optional[str] = None,
    sender: Optional[str] = None,
    recipient: Optional[str] = None,
    replace_content: Optional[str] = None,
) -> dict:
    """Send a templated email through Axcelerate.

    Args:
        template_id: Template/plan ID to use
        contact_id: Primary recipient contact ID
        instance_id: Course instance for merge fields
        course_type: Course type for merge fields (w/p/el)
        invoice_id: Associated invoice for merge fields
        subject: Override email subject line
        sender: Sender email or contact ID
        recipient: Recipient specification
        replace_content: JSON key-value pairs to replace in template
            e.g. '{"{{CUSTOM_FIELD}}": "Custom Value"}'
    """
    data: dict = {"planID": template_id}
    if contact_id:
        data["contactID"] = contact_id
    if instance_id:
        data["instanceID"] = instance_id
    if course_type:
        data["type"] = course_type
    if invoice_id:
        data["invoiceID"] = invoice_id
    if subject:
        data["subject"] = subject
    if sender:
        data["from"] = sender
    if recipient:
        data["to"] = recipient
    if replace_content:
        data["replaceContent"] = replace_content
    return await ax.post("/template/email", data=data)


# ──────────────────────────────────────────────────────────────────────────────
#  REPORT TOOLS
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def list_reports() -> list:
    """List all available reports (Live, Warehoused, and Saved)."""
    return await ax.get("/report/list")


@mcp.tool()
async def list_saved_reports() -> list:
    """List the user's saved reports."""
    return await ax.get("/report/saved/list")


@mcp.tool()
async def get_report_fields(report_reference: str) -> list:
    """Get available display and filter fields for a report.

    Args:
        report_reference: The report reference identifier
    """
    return await ax.get("/report/fields", params={"reportReference": report_reference})


@mcp.tool()
async def run_report(
    report_reference: str,
    filter_fields_json: str = "[]",
    view_fields_json: Optional[str] = None,
    display_length: int = 100,
    offset_rows: int = 0,
) -> dict:
    """Execute a live report with filters.

    Args:
        report_reference: Report reference identifier
        filter_fields_json: JSON array of filter objects. Each filter:
            {"name": "fieldReference", "operator": "is", "value": "filterValue"}
            Operators: is, on, between, before, after, startsWith, endsWith, contains, doesNotContain
        view_fields_json: JSON array of field names to display (optional)
        display_length: Records per page (10-1000)
        offset_rows: Records to skip (max 100,000)
    """
    data: dict = {
        "reportReference": report_reference,
        "selectedFilterFields": filter_fields_json,
        "displayLength": display_length,
        "offsetRows": offset_rows,
    }
    if view_fields_json:
        data["selectedViewFields"] = view_fields_json
    return await ax.post("/report/run", data=data)


@mcp.tool()
async def run_saved_report(
    report_id: int,
    display_length: int = 100,
    offset_rows: int = 0,
    filter_override_json: Optional[str] = None,
) -> dict:
    """Execute a saved report.

    Args:
        report_id: Saved report ID
        display_length: Records per page (10-1000)
        offset_rows: Records to skip
        filter_override_json: JSON array to override saved filters
            e.g. [{"NAME": "fieldRef", "VALUE": "newValue"}]
    """
    data: dict = {
        "reportId": report_id,
        "displayLength": display_length,
        "offsetRows": offset_rows,
    }
    if filter_override_json:
        data["filterOverride"] = filter_override_json
    return await ax.post("/report/saved/run", data=data)


# ──────────────────────────────────────────────────────────────────────────────
#  CATALOGUE ITEM TOOLS
# ──────────────────────────────────────────────────────────────────────────────


@mcp.tool()
async def list_catalogue_items() -> list:
    """List all accounting catalogue items."""
    return await ax.get("/accounting/catalogueitem/")


@mcp.tool()
async def get_catalogue_item(item_id: int) -> dict:
    """Get details for a specific catalogue item.

    Args:
        item_id: Catalogue item ID
    """
    return await ax.get(f"/accounting/catalogueitem/{item_id}")


# ──────────────────────────────────────────────────────────────────────────────
#  RESOURCE: API Reference
# ──────────────────────────────────────────────────────────────────────────────

API_REF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".claude",
    "axcelerate_api_reference.md",
)


@mcp.resource("axcelerate://api-reference")
async def api_reference() -> str:
    """Full Axcelerate API reference documentation."""
    try:
        with open(API_REF_PATH, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "API reference file not found."


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
