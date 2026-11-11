/**
 * Organisation details shown on the public website. They are deliberately NOT hard-coded: set them at build
 * time with the VITE_* variables below once they are confirmed. Until then each one renders as a clearly
 * marked placeholder rather than an invented address, phone number or email.
 */
const env = import.meta.env;
const value = (v: string | undefined) => (v && v.trim() ? v.trim() : null);

export const SITE = {
  operator: value(env.VITE_OPERATOR_NAME),          // registered legal name of the operating entity
  address: value(env.VITE_OPERATOR_ADDRESS),        // registered / office address
  supportEmail: value(env.VITE_SUPPORT_EMAIL),
  phone: value(env.VITE_SUPPORT_PHONE),
  securityEmail: value(env.VITE_SECURITY_EMAIL),
  accessibilityEmail: value(env.VITE_ACCESSIBILITY_EMAIL),
};

export const PLACEHOLDER = (what: string) => `[To be configured: ${what}]`;
