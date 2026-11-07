import React from 'react';
import {
  GraduationCap,
  CalendarCheck,
  BookOpen,
  UserCheck,
  Users,
  Award,
  Activity,
  AlertTriangle,
  TrendingUp,
  ShieldCheck,
  Building2,
  Briefcase,
  CheckCircle2,
  BarChart3,
  User,
  ArrowUpRight,
  ArrowDownRight,
  Minus
} from 'lucide-react';
import { SummaryCard } from '../../types';

interface SummaryCardsGridProps {
  cards: SummaryCard[];
}

const iconMap: Record<string, React.ElementType> = {
  GraduationCap,
  CalendarCheck,
  BookOpen,
  UserCheck,
  Users,
  Award,
  Activity,
  AlertTriangle,
  TrendingUp,
  ShieldCheck,
  Building2,
  Briefcase,
  CheckCircle2,
  BarChart3,
  User,
};

export const SummaryCardsGrid: React.FC<SummaryCardsGridProps> = ({ cards }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = iconMap[card.icon] || Activity;
        const isPositive = card.trend === 'positive';
        const isNegative = card.trend === 'negative';

        return (
          <div
            key={idx}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                {card.title}
              </span>
              <div className="p-2 rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950 dark:text-brand-400">
                <Icon className="w-4 h-4" />
              </div>
            </div>

            <div className="mt-3">
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                {card.value}
              </h3>
              <div className="mt-1 flex items-center space-x-1.5 text-xs">
                {isPositive && (
                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center">
                    <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                  </span>
                )}
                {isNegative && (
                  <span className="text-rose-600 dark:text-rose-400 font-semibold flex items-center">
                    <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
                  </span>
                )}
                {!isPositive && !isNegative && (
                  <span className="text-slate-400 dark:text-slate-500 flex items-center">
                    <Minus className="w-3.5 h-3.5 mr-0.5" />
                  </span>
                )}
                <span className="text-slate-500 dark:text-slate-400 truncate">
                  {card.change}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
