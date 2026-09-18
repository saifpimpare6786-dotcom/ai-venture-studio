import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

export function useSimulator(initialParams = {}) {
  const defaultParams = {
    starter_price: 299,
    growth_price: 799,
    enterprise_price: 1999,
    starter_share_pct: 60,
    growth_share_pct: 30,
    enterprise_share_pct: 10,
    cac: 150,
    monthly_growth_rate_pct: 15,
    monthly_churn_rate_pct: 2.5,
    gross_margin_pct: 80,
    headcount: 4,
    avg_monthly_salary: 4500,
    fixed_monthly_opex: 2500,
    initial_capital: 100000,
    months: 36,
    ...initialParams
  };

  const [params, setParams] = useState(defaultParams);
  const [simulation, setSimulation] = useState(null);
  const [scenarios, setScenarios] = useState(null);
  const [activeScenario, setActiveScenario] = useState('base_case');
  const [aiCommentary, setAiCommentary] = useState('');
  const [loading, setLoading] = useState(false);

  const recalculate = useCallback(async (customParams = params) => {
    try {
      setLoading(true);
      const res = await api.calculateSimulation(customParams);
      const sc = await api.getScenarios(customParams);
      setSimulation(res);
      setScenarios(sc);
    } catch (err) {
      console.error('Simulator recalculation failed:', err);
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    recalculate(params);
  }, []);

  const updateParam = (key, value) => {
    const next = { ...params, [key]: Number(value) };
    setParams(next);
    recalculate(next);
  };

  const requestAiAnalysis = async (projectId) => {
    try {
      setLoading(true);
      const res = await api.getAiAnalysis(projectId, params);
      setAiCommentary(res.ai_commentary);
      if (res.simulation) setSimulation(res.simulation);
    } catch (err) {
      console.error('Failed to get AI analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  return {
    params,
    setParams,
    updateParam,
    simulation: activeScenario === 'base_case' ? simulation : (scenarios ? scenarios[activeScenario] : simulation),
    scenarios,
    activeScenario,
    setActiveScenario,
    aiCommentary,
    requestAiAnalysis,
    loading,
    recalculate
  };
}
