import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, errorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { ROLE_LABEL } from '../lib/format';
import { PageHeader } from '../components/shell';
import { AssistantWorkspace } from '../components/chat';
import { NoModule } from '../components/access';
import { Button, Field, Input, KeyValues, Panel, useToast } from '../components/ui';

export function AccountPage() {
  const { me, signOut } = useAuth();
  const toast = useToast();
  const nav = useNavigate();
  const [f, setF] = useState({ old_password: '', new_password: '', confirm: '' });
  const [saving, setSaving] = useState(false);
  const save = async () => {
    if (f.new_password !== f.confirm) { toast('The new passwords do not match.', 'error'); return; }
    setSaving(true);
    try { await api.post('/auth/change-password', { old_password: f.old_password, new_password: f.new_password }); toast('Password changed. Please sign in again.'); await signOut(); nav('/login'); }
    catch (e) { toast(errorMessage(e), 'error'); } finally { setSaving(false); }
  };
  if (!me) return null;
  return (
    <div>
      <PageHeader title="Account" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Your details" description="Contact your administrator to change these.">
          <KeyValues cols={1} items={[['Name', me.full_name], ['Email', me.email], ['Phone', me.phone || 'Not recorded'], ['Role', ROLE_LABEL[me.role]],
            ...(me.designation || me.title ? [['Designation', me.designation || me.title] as [string, string]] : []),
            ...(me.department_name ? [['Department', me.department_name] as [string, string]] : []),
            ['Workspace', me.university?.name || 'ACEDRA platform']]} />
        </Panel>
        <Panel title="Change password" description="Changing your password signs you out of every device.">
          <div className="space-y-3">
            <Field label="Current password"><Input type="password" autoComplete="current-password" value={f.old_password} onChange={(e) => setF({ ...f, old_password: e.target.value })} /></Field>
            <Field label="New password" hint="At least 10 characters, mixing three of: lowercase, uppercase, numbers, symbols."><Input type="password" autoComplete="new-password" value={f.new_password} onChange={(e) => setF({ ...f, new_password: e.target.value })} /></Field>
            <Field label="Confirm new password"><Input type="password" autoComplete="new-password" value={f.confirm} onChange={(e) => setF({ ...f, confirm: e.target.value })} /></Field>
            <Button variant="primary" loading={saving} disabled={!f.old_password || !f.new_password} onClick={save}>Change password</Button>
          </div>
        </Panel>
      </div>
    </div>
  );
}

export function AssistantPage() {
  const { hasModule, me } = useAuth();
  if (!hasModule('ai_assistant')) return <NoModule name="The assistant" />;
  return (
    <div>
      <PageHeader title="Assistant" lede={me?.role === 'student' ? 'Ask about university policies, or about your own academic records.' : 'Ask about university policies, or about a student you are authorised to support.'} />
      <AssistantWorkspace />
    </div>
  );
}
