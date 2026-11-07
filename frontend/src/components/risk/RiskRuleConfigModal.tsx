import React, { useState, useEffect } from 'react';
import {
  X,
  Sliders,
  Plus,
  Trash2,
  Edit2,
  Check,
  AlertCircle,
  ToggleLeft,
  ToggleRight,
  Shield,
  Layers
} from 'lucide-react';
import { api } from '../../api/client';

interface RiskRuleConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRulesUpdated: () => void;
}

export const RiskRuleConfigModal: React.FC<RiskRuleConfigModalProps> = ({
  isOpen,
  onClose,
  onRulesUpdated,
}) => {
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editThreshold, setEditThreshold] = useState<number>(0);
  const [editSeverity, setEditSeverity] = useState<string>('MODERATE');
  const [showCreateDrawer, setShowCreateDrawer] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // New Rule Form
  const [newName, setNewName] = useState('');
  const [newCode, setNewCode] = useState('');
  const [newCategory, setNewCategory] = useState('ATTENDANCE');
  const [newSeverity, setNewSeverity] = useState('HIGH');
  const [newIndicator, setNewIndicator] = useState('attendance_percentage');
  const [newOperator, setNewOperator] = useState('<');
  const [newThreshold, setNewThreshold] = useState<number>(75.0);
  const [newAction, setNewAction] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadRules();
    }
  }, [isOpen]);

  const loadRules = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const data = await api.getRiskRules();
      setRules(data);
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to load rules' });
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (rule: any) => {
    try {
      await api.updateRiskRule(rule.id, { is_active: !rule.is_active });
      await loadRules();
      onRulesUpdated();
      setFeedback({
        type: 'success',
        message: `Rule '${rule.name}' ${!rule.is_active ? 'activated' : 'deactivated'}.`,
      });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleStartEdit = (rule: any) => {
    setEditingId(rule.id);
    setEditThreshold(rule.threshold_value);
    setEditSeverity(rule.severity);
  };

  const handleSaveEdit = async (ruleId: number) => {
    try {
      await api.updateRiskRule(ruleId, {
        threshold_value: Number(editThreshold),
        severity: editSeverity,
      });
      setEditingId(null);
      await loadRules();
      onRulesUpdated();
      setFeedback({ type: 'success', message: 'Rule threshold updated.' });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    if (!window.confirm('Are you sure you want to delete this custom risk rule?')) return;
    try {
      await api.deleteRiskRule(ruleId);
      await loadRules();
      onRulesUpdated();
      setFeedback({ type: 'success', message: 'Rule removed.' });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createRiskRule({
        name: newName,
        code: newCode.toUpperCase().trim(),
        category: newCategory,
        severity: newSeverity,
        indicator_type: newIndicator,
        operator: newOperator,
        threshold_value: Number(newThreshold),
        suggested_action: newAction,
        is_active: true,
      });
      setShowCreateDrawer(false);
      setNewName('');
      setNewCode('');
      setNewAction('');
      await loadRules();
      onRulesUpdated();
      setFeedback({ type: 'success', message: 'New risk policy rule registered.' });
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-brand-50 dark:bg-brand-950/50 text-brand-600 dark:text-brand-400 border border-brand-100 dark:border-brand-900">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Early-Warning Policy Rule Management
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Institutional criteria: Configure thresholds, severity brackets, and support actions without hardcoded policies.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`px-6 py-2.5 text-xs font-medium flex items-center justify-between ${
              feedback.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300'
                : 'bg-rose-50 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300'
            }`}
          >
            <span>{feedback.message}</span>
            <button onClick={() => setFeedback(null)} className="underline ml-4">
              Dismiss
            </button>
          </div>
        )}

        {/* Subheader / Action Bar */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="text-xs font-semibold text-slate-600 dark:text-slate-400">
            Active Rules: <span className="font-bold text-slate-900 dark:text-slate-100">{rules.filter((r) => r.is_active).length}</span> of {rules.length} configured
          </div>
          <button
            onClick={() => setShowCreateDrawer(!showCreateDrawer)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            {showCreateDrawer ? 'Close Form' : 'Add Policy Rule'}
          </button>
        </div>

        {/* Drawer for Adding Custom Rule */}
        {showCreateDrawer && (
          <form onSubmit={handleCreateRule} className="p-6 bg-slate-50 dark:bg-slate-800/70 border-b border-slate-200 dark:border-slate-800 space-y-4">
            <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
              Define New Early-Warning Indicator Rule
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Rule Name *</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g., Mid-Term Assessment Deficit"
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Unique Code *</label>
                <input
                  type="text"
                  required
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value)}
                  placeholder="e.g., RULE_MIDTERM_LOW"
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 uppercase font-mono outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
                >
                  <option value="ATTENDANCE">Attendance</option>
                  <option value="ASSESSMENT">Assessment / CIA</option>
                  <option value="ACADEMIC">Academic / SGPA</option>
                  <option value="BACKLOG">Backlog</option>
                  <option value="COMPOSITE">Composite</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Indicator Type</label>
                <select
                  value={newIndicator}
                  onChange={(e) => setNewIndicator(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
                >
                  <option value="attendance_percentage">Attendance Percentage</option>
                  <option value="assessment_percentage">Assessment Marks %</option>
                  <option value="sgpa_drop">SGPA Decline Drop</option>
                  <option value="backlog_count">Active Backlogs Count</option>
                  <option value="missing_assessments">Missing Evaluations Count</option>
                  <option value="composite">Composite / Multi-Indicator</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Operator</label>
                <select
                  value={newOperator}
                  onChange={(e) => setNewOperator(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-mono outline-none"
                >
                  <option value="<">&lt; (Less than)</option>
                  <option value="<=">&lt;= (Less than or equal)</option>
                  <option value=">">&gt; (Greater than)</option>
                  <option value=">=">&gt;= (Greater than or equal)</option>
                  <option value="==">== (Equal to)</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Threshold Value *</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={newThreshold}
                  onChange={(e) => setNewThreshold(parseFloat(e.target.value))}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-mono outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Alert Severity</label>
                <select
                  value={newSeverity}
                  onChange={(e) => setNewSeverity(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
                >
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MODERATE">Moderate</option>
                  <option value="NORMAL">Normal</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 block mb-1">Recommended Support Action</label>
              <input
                type="text"
                value={newAction}
                onChange={(e) => setNewAction(e.target.value)}
                placeholder="e.g., Mandatory tutorial registration and mentor check-in."
                className="w-full text-xs p-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 outline-none"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowCreateDrawer(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 transition"
              >
                Save & Activate Rule
              </button>
            </div>
          </form>
        )}

        {/* Rules Table */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex justify-center py-12 text-slate-400 text-xs">Loading configurable rules...</div>
          ) : rules.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">No rules configured.</div>
          ) : (
            <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Rule Name & Code</th>
                    <th className="py-3 px-3 font-semibold">Category</th>
                    <th className="py-3 px-3 font-semibold">Severity</th>
                    <th className="py-3 px-3 font-semibold">Condition</th>
                    <th className="py-3 px-3 font-semibold">Threshold</th>
                    <th className="py-3 px-3 font-semibold">Status</th>
                    <th className="py-3 px-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {rules.map((rule) => {
                    const isEditing = editingId === rule.id;

                    return (
                      <tr
                        key={rule.id}
                        className={`hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition ${
                          !rule.is_active ? 'opacity-50 bg-slate-50/30 dark:bg-slate-900/30' : ''
                        }`}
                      >
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-900 dark:text-slate-100">{rule.name}</div>
                          <div className="text-[10px] font-mono text-slate-400">{rule.code}</div>
                        </td>
                        <td className="py-3 px-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                            {rule.category}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          {isEditing ? (
                            <select
                              value={editSeverity}
                              onChange={(e) => setEditSeverity(e.target.value)}
                              className="text-xs p-1 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900"
                            >
                              <option value="CRITICAL">CRITICAL</option>
                              <option value="HIGH">HIGH</option>
                              <option value="MODERATE">MODERATE</option>
                              <option value="NORMAL">NORMAL</option>
                            </select>
                          ) : (
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                rule.severity === 'CRITICAL'
                                  ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                                  : rule.severity === 'HIGH'
                                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                                  : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                              }`}
                            >
                              {rule.severity}
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 font-mono text-[11px] text-slate-600 dark:text-slate-400">
                          {rule.operator}
                        </td>
                        <td className="py-3 px-3 font-mono font-bold text-slate-900 dark:text-slate-100">
                          {isEditing ? (
                            <input
                              type="number"
                              step="0.1"
                              value={editThreshold}
                              onChange={(e) => setEditThreshold(parseFloat(e.target.value))}
                              className="w-20 text-xs p-1 rounded border border-brand-500 bg-white dark:bg-slate-900 font-mono"
                            />
                          ) : (
                            `${rule.threshold_value}${rule.indicator_type.includes('percentage') ? '%' : ''}`
                          )}
                        </td>
                        <td className="py-3 px-3">
                          <button
                            onClick={() => handleToggleActive(rule)}
                            title={rule.is_active ? 'Click to deactivate' : 'Click to activate'}
                            className="flex items-center gap-1 text-[11px] font-semibold text-slate-600 dark:text-slate-400 hover:text-brand-600 transition"
                          >
                            {rule.is_active ? (
                              <ToggleRight className="w-5 h-5 text-emerald-500" />
                            ) : (
                              <ToggleLeft className="w-5 h-5 text-slate-400" />
                            )}
                            <span>{rule.is_active ? 'Active' : 'Disabled'}</span>
                          </button>
                        </td>
                        <td className="py-3 px-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {isEditing ? (
                              <button
                                onClick={() => handleSaveEdit(rule.id)}
                                title="Save changes"
                                className="p-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950 dark:text-emerald-300"
                              >
                                <Check className="w-3.5 h-3.5" />
                              </button>
                            ) : (
                              <button
                                onClick={() => handleStartEdit(rule)}
                                title="Edit threshold & severity"
                                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                            )}

                            {rule.created_by_id && (
                              <button
                                onClick={() => handleDeleteRule(rule.id)}
                                title="Delete custom rule"
                                className="p-1.5 rounded-lg text-rose-400 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs">
          <span className="text-slate-400">
            Rule changes take effect on subsequent risk evaluations.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg font-semibold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
