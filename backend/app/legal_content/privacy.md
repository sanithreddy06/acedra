> Draft for legal review. This policy describes what the ACEDRA software does today. It has not yet been reviewed by a lawyer, and the roles of each party under the Digital Personal Data Protection Act, 2023 and its rules must be confirmed against each institution's service agreement. Items marked "To be confirmed" must be completed before publication.

## 1. Who this policy covers

This policy explains how personal data is handled in ACEDRA, a university intelligence platform operated by [To be confirmed: legal name of the ACEDRA operating entity]. It covers:

- students, faculty, mentors, placement officers and administrators who use an institution's workspace;
- people who submit an institutional enquiry or a contact message on the ACEDRA website;
- members of the ACEDRA team.

## 2. Roles: institutions and ACEDRA

Each institution decides why and how its students' and staff members' data is processed in its workspace. We process that data on the institution's behalf and according to its instructions and service agreement.

> To be confirmed by legal counsel: whether each institution is the Data Fiduciary and ACEDRA its Data Processor for workspace data under the DPDP Act, and the corresponding contractual terms. For website enquiries and contact messages, ACEDRA decides the purposes and is expected to act as the Data Fiduciary.

## 3. Data we hold

**Account data.** Name, email address, role, department, job title, optional phone number, the hashed form of your password (never the password itself), whether your account is invited, active or disabled, and when you last signed in.

**Student academic records,** as provided by the institution, typically by import: university numbers (USN, SRN, roll number), programme, semester and section, attendance by subject, internal assessment marks, examination results and grades, CGPA, skills, certifications, projects, internships and hackathons. Student profiles can also hold date of birth, gender, blood group, address and a guardian's name and contact number if the institution records them.

**Records created in ACEDRA:** early-warning alerts and their explanations, recommendations and progress, placement readiness and applications (including any resume link and cover notes), mentoring interventions, notes, follow-ups and student feedback, notifications, and generated reports.

**AI assistant data:** your questions and the assistant's answers, the documents it cited, and any feedback you give. Documents an administrator uploads are stored as extracted text; original files are not kept.

**Security and operational records:** an audit log of significant actions (for example sign-ins, invitations, configuration changes and any ACEDRA access to student records under a grant), including the IP address and browser description where available; copies of emails the platform sends, such as invitations and password-reset messages; and your acceptance of these legal documents (which version and when).

**Website data:** the details you enter in an institutional enquiry or contact message, such as your name, institutional email, institution and message.

## 4. Why we use it

- To provide the institution's workspace: showing records to people authorised to see them, applying the institution's early-warning rules, generating recommendations and readiness indicators, and supporting mentoring.
- To run accounts securely: invitations, sign-in, password reset, session management and audit logging.
- To answer enquiries and contact messages and to onboard institutions.
- To meet legal obligations and to protect the platform and its users.

We do not sell personal data, and we do not use workspace data for advertising. Alerts, scores and recommendations are produced by rules and calculations that the institution can see and configure; they are not predictive models.

## 5. Who can see it

Inside a workspace, access follows roles (see the Terms and Conditions): a student sees only their own records; faculty, mentors, administrators and placement officers see what their role permits within their own institution. Institutions cannot see each other's data.

ACEDRA team members can configure an institution's workspace but cannot see its student records unless the institution has approved a specific, time-limited access grant; each access under a grant is recorded.

## 6. Service providers and AI

Depending on how a deployment is configured, personal data may be processed by:

- **a hosting provider** that runs the application and database — [To be confirmed: provider and data-centre locations for each deployment];
- **an email delivery service** used to send invitations, password resets and notifications, if SMTP delivery is configured — [To be confirmed: provider];
- **a language-model provider,** only if the deployment enables one. When enabled, the assistant sends your question, the relevant passages from your institution's documents and, in personal mode, a summary of the records you are authorised to see, so that the provider can draft an answer. By default no language model is configured and nothing is sent to any AI provider — [To be confirmed: provider, location and data-use terms if one is enabled].

> To be confirmed: whether any of these providers process data outside India, and the safeguards that apply. This policy does not claim that data stays in India.

## 7. How long we keep it

The software does not currently delete records automatically. Data is kept while an institution's agreement is in force, and deleted or returned at the end of the agreement as that agreement specifies.

> To be confirmed: retention periods for each category (including audit logs, email copies, enquiries and contact messages) and the deletion process at the end of an agreement.

## 8. Security

Measures in the current software include: passwords stored only as salted bcrypt hashes; single-use invitation and reset links stored only as hashes; time-limited sign-in tokens that are revoked when you sign out, change your password or your role changes; separation of each institution's data enforced in the application's data layer; role-based access checks on every request; rate limiting on sign-in and public forms; and audit logging.

Encryption of data in transit (HTTPS) and of stored data depends on how each deployment is hosted.

> To be confirmed for each deployment: HTTPS configuration, encryption of the database and backups, backup schedule, and the breach-notification procedure required under the DPDP rules.

## 9. Your rights

Subject to applicable law, you can ask to access a summary of your personal data, to correct or complete it, to have it erased where it is no longer needed, and to nominate someone to exercise your rights if you are unable to. You can also raise a grievance.

For workspace data, contact your institution first: it decides how its records are kept and corrected. We will help institutions respond. For website enquiries and contact messages, contact us.

> To be confirmed: the grievance officer or contact person, response timelines, and the route to the Data Protection Board of India.

## 10. Children's data

Most university students are adults, but some may be under 18. Under the DPDP Act, processing a child's personal data generally requires verifiable consent from a parent or lawful guardian and must not involve tracking, behavioural monitoring or targeted advertising directed at children.

> To be confirmed with each institution: how students under 18 are identified and how guardian consent is obtained and recorded before their data is processed in ACEDRA.

## 11. Cookies and browser storage

ACEDRA uses only the browser storage needed to keep you signed in and to remember your choices. See the Cookie Policy for details.

## 12. Changes to this policy

Each version of this policy is numbered and dated, and earlier versions remain available. We will ask you to accept a new version where required.

## 13. Contact

Questions and requests about privacy can be sent through the contact form on the ACEDRA website, or to your institution's administrator for workspace data.

> To be confirmed: a dedicated privacy contact email and the operating entity's registered address.
