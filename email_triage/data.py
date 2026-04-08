"""
Email dataset for the Email Triage environment.
Contains realistic synthetic emails across three task difficulty levels.
Each email includes the correct expected action for grading.
"""
from __future__ import annotations

from typing import Dict, List

from .models import EmailData

# ── TASK 1: Easy — Basic spam/urgent detection ───────────────────────────────
# 5 emails. Clear signals. Binary decisions.

TASK_EASY_EMAILS: List[EmailData] = [
    EmailData(
        id="easy_001",
        subject="URGENT: Production server is DOWN",
        sender="Ops Monitoring",
        sender_email="alerts@ops.yourcompany.com",
        body=(
            "CRITICAL ALERT\n\n"
            "Production server prod-us-east-1 has been unreachable for 4 minutes.\n"
            "CPU: N/A | Memory: N/A | Disk: N/A\n"
            "Last successful health check: 2024-01-15 09:12 UTC\n\n"
            "Incident ID: INC-20240115-4421\n"
            "On-call engineer: Please respond immediately.\n"
        ),
        timestamp="2024-01-15T09:16:00Z",
        metadata={"category": "system_alert", "severity": "critical"},
    ),
    EmailData(
        id="easy_002",
        subject="You've WON a $1,000 Amazon Gift Card!!!",
        sender="Rewards Center",
        sender_email="noreply@amaz0n-rewards-center.tk",
        body=(
            "Congratulations! You have been selected as today's lucky winner!\n\n"
            "CLAIM YOUR $1,000 AMAZON GIFT CARD NOW!\n"
            "Click here: http://bit.ly/freecard999\n\n"
            "Offer expires in 24 hours. Act now!\n"
            "To unsubscribe reply STOP (this will not remove you from our list)\n"
        ),
        timestamp="2024-01-15T08:00:00Z",
        metadata={"category": "promotional", "suspicious_links": True},
    ),
    EmailData(
        id="easy_003",
        subject="Team lunch Friday - 12:30pm",
        sender="Sarah Chen",
        sender_email="sarah.chen@yourcompany.com",
        body=(
            "Hi team!\n\n"
            "Quick reminder that we're doing team lunch this Friday at 12:30pm "
            "at The Garden Cafe (the one on Main St).\n\n"
            "Please let me know if you can make it so I can make a reservation.\n\n"
            "Best,\nSarah"
        ),
        timestamp="2024-01-15T10:00:00Z",
        metadata={"category": "social", "requires_response": True},
    ),
    EmailData(
        id="easy_004",
        subject="Nigerian Prince needs your help — CONFIDENTIAL",
        sender="Prince Adebayo",
        sender_email="prince.help@gmail.com",
        body=(
            "CONFIDENTIAL BUSINESS PROPOSAL\n\n"
            "I am Prince Adebayo, son of the late General Sani Abacha of Nigeria. "
            "I need to transfer USD $24,500,000 out of the country urgently. "
            "I require a trustworthy foreign partner to help me.\n\n"
            "In return I will give you 30% of the funds. "
            "Please reply with your bank details to proceed.\n\n"
            "Yours faithfully,\nPrince Adebayo"
        ),
        timestamp="2024-01-15T07:45:00Z",
        metadata={"category": "scam", "suspicious_links": False},
    ),
    EmailData(
        id="easy_005",
        subject="Your AWS bill for December: $4,832.17",
        sender="AWS Billing",
        sender_email="billing@amazon.com",
        body=(
            "Your AWS monthly bill is ready.\n\n"
            "Account: 123456789012\n"
            "Period: December 2023\n"
            "Total charges: $4,832.17\n\n"
            "This is higher than your usual monthly spend ($1,200-$1,500). "
            "Please review your bill for unexpected charges.\n\n"
            "View invoice: https://console.aws.amazon.com/billing/\n"
        ),
        timestamp="2024-01-15T06:00:00Z",
        metadata={"category": "billing", "anomaly": True},
    ),
]

# Expected correct actions for easy task
TASK_EASY_CORRECT: Dict[str, dict] = {
    "easy_001": {
        "action_type": "label",
        "label": "urgent",
        "explanation": "Critical production outage requires immediate attention",
    },
    "easy_002": {
        "action_type": "label",
        "label": "spam",
        "explanation": "Classic phishing/prize scam with suspicious domain and URL",
    },
    "easy_003": {
        "action_type": "label",
        "label": "needs_reply",
        "explanation": "Colleague asked for RSVP — needs a response",
    },
    "easy_004": {
        "action_type": "label",
        "label": "spam",
        "explanation": "Classic advance-fee fraud (Nigerian prince scam)",
    },
    "easy_005": {
        "action_type": "label",
        "label": "urgent",
        "explanation": "Billing anomaly (3x normal spend) requires investigation",
    },
}

# ── TASK 2: Medium — Mixed inbox with replies needed ─────────────────────────
# 8 emails. Some require drafted replies, some forwarding, some archiving.

TASK_MEDIUM_EMAILS: List[EmailData] = [
    EmailData(
        id="med_001",
        subject="Re: Q4 report — final numbers needed by EOD",
        sender="David Park (CFO)",
        sender_email="d.park@yourcompany.com",
        body=(
            "Following up on my earlier email.\n\n"
            "We're presenting to the board in 3 hours and I still don't have "
            "the Q4 revenue numbers from your team. This is holding up the entire presentation.\n\n"
            "Please send the final figures immediately or let me know if there's a blocker.\n\n"
            "— David"
        ),
        timestamp="2024-01-15T11:30:00Z",
        is_reply=True,
        metadata={"from_executive": True, "deadline": "14:30"},
    ),
    EmailData(
        id="med_002",
        subject="Newsletter: 10 productivity hacks you need to know",
        sender="ProductivityHub",
        sender_email="newsletter@productivityhub.io",
        body=(
            "Hi there!\n\n"
            "This week in our newsletter:\n"
            "• 10 Productivity Hacks for 2024\n"
            "• The Pomodoro Method: Does it work?\n"
            "• Best apps for time management\n\n"
            "Read the full article: https://productivityhub.io/newsletter/jan15\n\n"
            "You're receiving this because you subscribed in 2022.\n"
            "Unsubscribe: https://productivityhub.io/unsubscribe\n"
        ),
        timestamp="2024-01-15T08:00:00Z",
        metadata={"category": "newsletter", "subscribed": True},
    ),
    EmailData(
        id="med_003",
        subject="Customer complaint — Order #89234 not delivered",
        sender="Emma Wilson",
        sender_email="emma.wilson@gmail.com",
        body=(
            "Hello,\n\n"
            "I placed order #89234 on January 5th and paid for 3-day shipping. "
            "It is now January 15th and my order has still not arrived.\n\n"
            "I've been a customer for 5 years and have never had this problem before. "
            "I need this package — it was a birthday gift — and the birthday was yesterday.\n\n"
            "Please resolve this immediately. If it cannot be delivered today, "
            "I would like a full refund.\n\n"
            "Emma Wilson"
        ),
        timestamp="2024-01-15T09:45:00Z",
        metadata={"customer_tenure": "5_years", "issue_type": "lost_package"},
    ),
    EmailData(
        id="med_004",
        subject="IT Security: Mandatory password reset by Jan 20",
        sender="IT Security Team",
        sender_email="security@yourcompany.com",
        body=(
            "SECURITY NOTICE\n\n"
            "As part of our annual security audit, all employees must reset their "
            "corporate passwords by January 20, 2024.\n\n"
            "How to reset:\n"
            "1. Go to https://sso.yourcompany.com/reset\n"
            "2. Enter your current credentials\n"
            "3. Choose a new password (12+ chars, mix of upper/lower/numbers/symbols)\n\n"
            "Accounts not reset by the deadline will be locked.\n\n"
            "IT Security Team"
        ),
        timestamp="2024-01-15T08:30:00Z",
        metadata={"action_required": True, "deadline": "2024-01-20"},
    ),
    EmailData(
        id="med_005",
        subject="Invoice #2024-0089 attached — Payment due Feb 1",
        sender="Acme Software Ltd",
        sender_email="accounts@acme-software.com",
        body=(
            "Dear Accounts Team,\n\n"
            "Please find attached invoice #2024-0089 for software licenses "
            "renewed in December 2023.\n\n"
            "Amount: $3,600.00\n"
            "Due date: February 1, 2024\n"
            "Payment reference: INV-2024-0089\n\n"
            "Please confirm receipt of this invoice.\n"
            "Acme Software Ltd"
        ),
        timestamp="2024-01-15T09:00:00Z",
        has_attachment=True,
        metadata={"invoice_amount": 3600, "requires_forwarding": True},
    ),
    EmailData(
        id="med_006",
        subject="Re: Interview feedback for Maria Santos",
        sender="HR — Jennifer Liu",
        sender_email="j.liu@yourcompany.com",
        body=(
            "Hi,\n\n"
            "Could you please share your interview feedback for Maria Santos "
            "(Python Engineer candidate, interviewed yesterday)?\n\n"
            "We need all feedback submitted in Greenhouse by 3pm today so we can "
            "make a hiring decision by end of week.\n\n"
            "Thanks,\nJennifer"
        ),
        timestamp="2024-01-15T10:15:00Z",
        is_reply=True,
        metadata={"deadline": "15:00", "requires_action": True},
    ),
    EmailData(
        id="med_007",
        subject="Congratulations on your LinkedIn work anniversary!",
        sender="LinkedIn",
        sender_email="notifications@linkedin.com",
        body=(
            "Say congratulations!\n\n"
            "Alex Johnson is celebrating 5 years at your company. "
            "Say congrats to help them celebrate!\n\n"
            "View Alex's profile: https://linkedin.com/in/alexjohnson\n\n"
            "Manage notification settings in LinkedIn.\n"
        ),
        timestamp="2024-01-15T07:00:00Z",
        metadata={"category": "social_notification", "platform": "linkedin"},
    ),
    EmailData(
        id="med_008",
        subject="URGENT: Legal review needed — NDA for Meridian deal",
        sender="Tom Bradley (Business Dev)",
        sender_email="t.bradley@yourcompany.com",
        body=(
            "Hi,\n\n"
            "Meridian Partners wants to sign an NDA before our demo next Tuesday. "
            "They sent their standard NDA which has some unusual clauses around IP.\n\n"
            "I'm attaching their NDA. We need legal to review and either approve "
            "or send back redlines by Thursday COB.\n\n"
            "This is a $500K potential deal — critical we don't miss the Tuesday slot.\n\n"
            "Tom"
        ),
        timestamp="2024-01-15T11:00:00Z",
        has_attachment=True,
        metadata={"deal_value": 500000, "requires_forwarding": True},
    ),
]

TASK_MEDIUM_CORRECT: Dict[str, dict] = {
    "med_001": {
        "action_type": "reply",
        "label": "urgent",
        "key_content": ["apologize", "send numbers", "estimate"],
        "explanation": "Executive needs urgent data for board presentation in 3 hours",
    },
    "med_002": {
        "action_type": "archive",
        "label": "normal",
        "explanation": "Legitimate newsletter, not urgent, can be archived or unsubscribed",
    },
    "med_003": {
        "action_type": "reply",
        "label": "urgent",
        "key_content": ["apologize", "investigate", "refund", "resolve"],
        "explanation": "Long-term customer with legitimate complaint about late delivery",
    },
    "med_004": {
        "action_type": "label",
        "label": "needs_reply",
        "explanation": "Required IT action by deadline — needs to be acknowledged and actioned",
    },
    "med_005": {
        "action_type": "forward",
        "label": "normal",
        "explanation": "Invoice should be forwarded to accounts payable team",
    },
    "med_006": {
        "action_type": "reply",
        "label": "urgent",
        "key_content": ["feedback", "Greenhouse", "submit"],
        "explanation": "Time-sensitive HR request with same-day deadline",
    },
    "med_007": {
        "action_type": "archive",
        "label": "normal",
        "explanation": "Social notification with no action required — archive it",
    },
    "med_008": {
        "action_type": "forward",
        "label": "urgent",
        "explanation": "NDA requires legal review — forward to legal team immediately",
    },
}

# ── TASK 3: Hard — Complex inbox requiring nuanced prioritization ─────────────
# 10 emails. Competing priorities, ambiguous signals, nested context.

TASK_HARD_EMAILS: List[EmailData] = [
    EmailData(
        id="hard_001",
        subject="Re: Re: Re: Project Phoenix go/no-go decision",
        sender="Alex Rivera (CTO)",
        sender_email="a.rivera@yourcompany.com",
        body=(
            "I've read the risk analysis. Despite the concerns raised by engineering, "
            "I want to proceed. The market window won't wait.\n\n"
            "However, I need a revised launch plan that addresses the top 3 technical risks "
            "from the engineering report — specifically the database migration risk "
            "and the API rate limiting issue.\n\n"
            "Can you coordinate with engineering and send me a revised plan by 9am tomorrow? "
            "If we can't address those risks adequately, we go back to no-go.\n\n"
            "— Alex"
        ),
        timestamp="2024-01-15T14:00:00Z",
        is_reply=True,
        thread_length=4,
        metadata={
            "from_cto": True,
            "project": "phoenix",
            "decision_pending": True,
            "deadline": "09:00_tomorrow",
        },
    ),
    EmailData(
        id="hard_002",
        subject="Resignation — effective Feb 1",
        sender="Marcus Thompson",
        sender_email="m.thompson@yourcompany.com",
        body=(
            "Hi,\n\n"
            "I'm writing to formally give my two weeks notice. My last day will be February 1, 2024.\n\n"
            "It's been a great 3 years. I've grown a lot and I'm grateful for the opportunities, "
            "but I've decided to pursue a position closer to family.\n\n"
            "I'm happy to help with the transition in any way I can — documenting my work, "
            "training a replacement, or anything else that would be helpful.\n\n"
            "I'll set up a meeting to discuss transition planning.\n\n"
            "Marcus"
        ),
        timestamp="2024-01-15T09:00:00Z",
        metadata={
            "is_resignation": True,
            "notice_period": "2_weeks",
            "employee_tenure": "3_years",
        },
    ),
    EmailData(
        id="hard_003",
        subject="Security incident report — possible data breach",
        sender="SOC Alert System",
        sender_email="soc@yourcompany.com",
        body=(
            "SECURITY INCIDENT — SEVERITY: HIGH\n"
            "Incident ID: SEC-2024-0047\n\n"
            "Anomalous data exfiltration pattern detected from user account: jsmith@yourcompany.com\n"
            "• 2.3 GB transferred to external IP: 185.220.101.x (Tor exit node)\n"
            "• Transfer started: 2024-01-15 13:47 UTC\n"
            "• Files accessed: /shared/customer-data/, /confidential/contracts/\n\n"
            "The account has been temporarily suspended. Security team is investigating.\n\n"
            "ACTION REQUIRED: Please acknowledge and escalate to CISO within 30 minutes.\n"
        ),
        timestamp="2024-01-15T13:52:00Z",
        metadata={
            "is_security_incident": True,
            "severity": "high",
            "escalation_required": True,
            "time_critical": True,
        },
    ),
    EmailData(
        id="hard_004",
        subject="Re: Salary review — disappointed with outcome",
        sender="Priya Nair",
        sender_email="p.nair@yourcompany.com",
        body=(
            "Hi,\n\n"
            "I received my performance review and salary adjustment letter this morning. "
            "I want to be honest: I'm very disappointed.\n\n"
            "I was told my performance was 'exceeds expectations' and I've been leading "
            "the ML platform project single-handedly for 6 months. A 2.5% increase feels "
            "deeply disconnected from my contributions.\n\n"
            "I've had a competing offer at $145K (vs my current $118K). I've turned it down "
            "twice out of loyalty to the team, but I'm struggling to justify that decision.\n\n"
            "I'd like to discuss this. Are you available this week?\n\n"
            "Priya"
        ),
        timestamp="2024-01-15T11:30:00Z",
        is_reply=True,
        metadata={
            "is_retention_risk": True,
            "has_competing_offer": True,
            "offer_gap": 27000,
            "performance_rating": "exceeds_expectations",
        },
    ),
    EmailData(
        id="hard_005",
        subject="Partner API integration broken — 40% of orders failing",
        sender="Stripe Integration Monitor",
        sender_email="alerts@stripe-monitor.yourcompany.com",
        body=(
            "INTEGRATION ALERT\n\n"
            "Stripe payment webhook failing since 13:15 UTC today.\n"
            "Error: SSL certificate mismatch on endpoint https://api.yourcompany.com/webhooks/stripe\n\n"
            "Impact:\n"
            "• 847 failed payment confirmations in last 45 minutes\n"
            "• ~$34,000 in unconfirmed revenue\n"
            "• Customers receiving payment failure errors\n\n"
            "This is a P0 incident. On-call engineer has been paged but has not acknowledged."
        ),
        timestamp="2024-01-15T14:00:00Z",
        metadata={
            "is_production_incident": True,
            "revenue_impact": 34000,
            "customers_affected": True,
        },
    ),
    EmailData(
        id="hard_006",
        subject="Vendor proposal: switch analytics platform — saves $180K/year",
        sender="DataViz Pro Sales",
        sender_email="sales@datavizpro.com",
        body=(
            "Hi,\n\n"
            "Following our call last week, I wanted to send over our formal proposal.\n\n"
            "DataViz Pro vs your current Tableau setup:\n"
            "• License cost: $20K/year vs $200K/year (saves $180K annually)\n"
            "• Migration effort: ~3 weeks for your 45 dashboards\n"
            "• Feature parity: 90% coverage, missing: Tableau Prep, some connector types\n\n"
            "We're offering a 60-day free trial with full migration support.\n\n"
            "Happy to arrange a technical eval. Proposal attached.\n\n"
            "Best,\nJamie"
        ),
        timestamp="2024-01-15T10:00:00Z",
        has_attachment=True,
        metadata={"potential_saving": 180000, "migration_risk": "medium"},
    ),
    EmailData(
        id="hard_007",
        subject="Whistleblower concern — accounting irregularities in Q3",
        sender="Anonymous",
        sender_email="anon-report@protonmail.com",
        body=(
            "I am an employee and I'm writing anonymously because I'm concerned about "
            "retaliation.\n\n"
            "During Q3 close, I noticed that certain sales figures were being recorded "
            "before contracts were fully executed. This happened at least 4 times, "
            "involving deals totaling approximately $2.1M.\n\n"
            "I raised this with my manager and was told to 'not worry about it.' "
            "I'm not sure if this is a genuine accounting error or something worse.\n\n"
            "I don't want to get anyone in trouble but I felt someone should know.\n"
        ),
        timestamp="2024-01-15T07:00:00Z",
        metadata={
            "is_whistleblower": True,
            "financial_irregularity": True,
            "amount_implicated": 2100000,
            "legal_risk": "high",
        },
    ),
    EmailData(
        id="hard_008",
        subject="Urgent: CEO interview request — TechCrunch, response needed today",
        sender="Rachel Kim (PR)",
        sender_email="r.kim@yourcompany.com",
        body=(
            "Hi,\n\n"
            "TechCrunch reached out — they want to interview the CEO for a piece "
            "on AI startups coming out Thursday. They need a yes/no by 4pm today.\n\n"
            "This is a good opportunity (estimated 50K+ readers) but the article "
            "is framed around 'AI companies that overpromised.' They'll want to ask "
            "about our January product delay.\n\n"
            "I think we should do it but with careful prep. The CEO is in meetings until 3pm.\n\n"
            "What do you think? Should I confirm?\n\n"
            "Rachel"
        ),
        timestamp="2024-01-15T13:00:00Z",
        metadata={"media_opportunity": True, "reputational_risk": "medium", "deadline": "16:00"},
    ),
    EmailData(
        id="hard_009",
        subject="Re: Your employment contract — clause 7.3 query",
        sender="Legal — Samantha Osei",
        sender_email="s.osei@yourcompany.com",
        body=(
            "Hi,\n\n"
            "Following your query about clause 7.3 (non-compete): the clause as written "
            "prevents you from joining any 'company in a substantially similar industry' "
            "for 18 months post-employment.\n\n"
            "This is enforceable in your jurisdiction with some caveats. "
            "If you're considering a role at a competitor, I'd strongly recommend "
            "a confidential conversation with an employment lawyer before making any decisions.\n\n"
            "Happy to discuss further.\n\n"
            "Samantha"
        ),
        timestamp="2024-01-15T12:30:00Z",
        is_reply=True,
        metadata={"is_sensitive_legal": True, "relates_to_employee_departure": True},
    ),
    EmailData(
        id="hard_010",
        subject="Customer Success: Acme Corp threatening churn ($420K ARR)",
        sender="Lisa Park (CSM)",
        sender_email="l.park@yourcompany.com",
        body=(
            "Hi,\n\n"
            "I need to flag a serious situation. Acme Corp ($420K ARR, our 3rd largest customer) "
            "just told me they're evaluating competitors because:\n"
            "1. Three P1 bugs went unresolved for 6+ weeks\n"
            "2. Our support response time has degraded from 2hr SLA to ~18hr average\n"
            "3. They feel 'deprioritized' since we released the enterprise tier\n\n"
            "They have a board meeting on the 22nd where this decision will be finalized.\n\n"
            "I've scheduled a call with their VP on Thursday but I think we need an executive "
            "to join. Can you or someone senior jump on that call?\n\n"
            "Lisa"
        ),
        timestamp="2024-01-15T10:45:00Z",
        metadata={
            "at_risk_arr": 420000,
            "customer_tier": "enterprise",
            "churn_risk": "high",
            "decision_date": "2024-01-22",
        },
    ),
]

TASK_HARD_CORRECT: Dict[str, dict] = {
    "hard_001": {
        "action_type": "reply",
        "label": "urgent",
        "key_content": ["coordinate", "engineering", "risk", "plan", "9am"],
        "explanation": "CTO directive with next-day deadline for major product decision",
    },
    "hard_002": {
        "action_type": "reply",
        "label": "needs_reply",
        "key_content": ["thank", "transition", "meeting", "HR"],
        "explanation": "Resignation requires acknowledgment, transition planning, HR notification",
    },
    "hard_003": {
        "action_type": "forward",
        "label": "urgent",
        "key_content": ["CISO", "security", "escalate"],
        "explanation": "Active data breach — must escalate to CISO within 30 min per protocol",
    },
    "hard_004": {
        "action_type": "reply",
        "label": "urgent",
        "key_content": ["meeting", "discuss", "acknowledge", "appreciate"],
        "explanation": "High-retention-risk employee with competing offer needs immediate response",
    },
    "hard_005": {
        "action_type": "label",
        "label": "urgent",
        "key_content": ["P0", "oncall", "engineering"],
        "explanation": "Active P0 payment outage with $34K revenue impact and unacknowledged page",
    },
    "hard_006": {
        "action_type": "label",
        "label": "normal",
        "explanation": "Interesting vendor proposal but not urgent — evaluate when time permits",
    },
    "hard_007": {
        "action_type": "forward",
        "label": "urgent",
        "key_content": ["legal", "compliance", "confidential"],
        "explanation": "Whistleblower complaint with financial irregularity must go to legal/compliance immediately",
    },
    "hard_008": {
        "action_type": "reply",
        "label": "urgent",
        "key_content": ["CEO", "prep", "confirm", "TechCrunch"],
        "explanation": "PR opportunity with same-day deadline requiring strategic response",
    },
    "hard_009": {
        "action_type": "label",
        "label": "normal",
        "explanation": "Legal response received — file for reference, no immediate action needed",
    },
    "hard_010": {
        "action_type": "reply",
        "label": "urgent",
        "key_content": ["Thursday", "executive", "call", "customer", "churn"],
        "explanation": "$420K ARR at risk — needs executive involvement and immediate response",
    },
}

# ── Task registry ─────────────────────────────────────────────────────────────

TASKS = {
    "email_triage_easy": {
        "emails": TASK_EASY_EMAILS,
        "correct_actions": TASK_EASY_CORRECT,
        "description": "Triage 5 emails: identify spam, urgent alerts, and items needing replies",
        "difficulty": "easy",
        "max_steps": 10,
    },
    "email_triage_medium": {
        "emails": TASK_MEDIUM_EMAILS,
        "correct_actions": TASK_MEDIUM_CORRECT,
        "description": "Process 8 mixed-priority emails including customer complaints, invoices, and HR requests",
        "difficulty": "medium",
        "max_steps": 20,
    },
    "email_triage_hard": {
        "emails": TASK_HARD_EMAILS,
        "correct_actions": TASK_HARD_CORRECT,
        "description": "Handle 10 complex, high-stakes emails including security incidents, resignations, and crises",
        "difficulty": "hard",
        "max_steps": 30,
    },
}
