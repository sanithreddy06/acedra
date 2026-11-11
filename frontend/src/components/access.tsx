import { useAuth } from '../lib/auth';
import { Notice } from './ui';

/** Shown when the university has not enabled a module. */
export function NoModule({ name }: { name: string }) {
  return <Notice title={`${name} isn’t enabled for your university`}>Your administrator can discuss enabling it with your ACEDRA contact.</Notice>;
}

/** Renders its child only when the caller's university has the module enabled. The API enforces the same rule. */
export function ModuleGate({ module, name, children }: { module: string; name: string; children: JSX.Element }) {
  const { hasModule } = useAuth();
  return hasModule(module) ? children : <NoModule name={name} />;
}

export function Forbidden() {
  return <Notice tone="danger" title="This area isn’t available for your role">Use the navigation to return to your workspace.</Notice>;
}
