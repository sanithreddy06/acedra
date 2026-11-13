/**
 * Organisation details shown on the public website. They are deliberately NOT hard-coded: set them at build
 * time with the VITE_* variables below once they are confirmed. Until then each one renders as a clearly
 * marked placeholder rather than an invented address, phone number or email.
 *
 * Exception: the local development server (`vite`, used for demonstrations) fills the contact fields with the
 * demonstration values in DEMO_CONTACT when none of them is configured. Pages label them as placeholders, and
 * production builds never include them.
 */
const env = import.meta.env;
const value = (v: string | undefined) => (v && v.trim() ? v.trim() : null);

/** Demonstration placeholders, not genuine contact information. */
const DEMO_CONTACT = {
  address: 'Bengaluru, Karnataka, India',
  supportEmail: 'hello@acedra.example',
  phone: '9999999999',
  website: 'https://acedra.example',
};

const configuredContact = {
  address: value(env.VITE_OPERATOR_ADDRESS),        // registered / office address
  supportEmail: value(env.VITE_SUPPORT_EMAIL),
  phone: value(env.VITE_SUPPORT_PHONE),
  website: value(env.VITE_OPERATOR_WEBSITE),
};

/** True on the development server when no contact detail is configured, so the demonstration values are shown. */
const demoContact = !!env.DEV && Object.values(configuredContact).every((v) => v === null);

export const SITE = {
  operator: value(env.VITE_OPERATOR_NAME),          // registered legal name of the operating entity
  ...(demoContact ? DEMO_CONTACT : configuredContact),
  securityEmail: value(env.VITE_SECURITY_EMAIL),
  accessibilityEmail: value(env.VITE_ACCESSIBILITY_EMAIL),
  demoContact,
};

export const PLACEHOLDER = (what: string) => `[To be configured: ${what}]`;
