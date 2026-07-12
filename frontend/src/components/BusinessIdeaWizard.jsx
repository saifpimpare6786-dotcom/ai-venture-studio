import React, { useState } from 'react';
import { 
  Briefcase, 
  Building2, 
  Globe, 
  FileText, 
  Lightbulb, 
  Target, 
  Users, 
  TrendingUp, 
  DollarSign, 
  PiggyBank, 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle2, 
  AlertCircle,
  Layers,
  HelpCircle
} from 'lucide-react';

const INDUSTRIES = [
  'Software as a Service (SaaS)',
  'E-commerce & Retail',
  'Healthcare & MedTech',
  'Financial Technology (FinTech)',
  'Artificial Intelligence & DeepTech',
  'CleanTech & Sustainability',
  'EdTech & Education',
  'Logistics & Supply Chain',
  'Agriculture & AgTech',
  'Real Estate & PropTech',
  'Entertainment & Media',
  'Food & Beverage'
];

const REVENUE_MODELS = [
  'Subscription (Recurring Revenue)',
  'Transactional / Commission-based',
  'Direct Sales (B2B or B2C)',
  'Freemium / Premium Add-ons',
  'Advertising / Sponsored Content',
  'Licensing / IP Royalties',
  'Marketplace / Platform Fees'
];

export default function BusinessIdeaWizard({ onSubmitSuccess }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    businessName: '',
    industry: '',
    problemStatement: '',
    solution: '',
    targetAudience: '',
    customerSegment: '',
    revenueModel: '',
    pricing: '',
    budget: '',
    country: '',
    businessGoals: '',
    fundingRequirement: '',
    growthExpectations: '',
    optionalNotes: ''
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitComplete, setSubmitComplete] = useState(false);

  const steps = [
    { id: 1, title: 'Core Concept', icon: Briefcase, desc: 'Name, industry, and location' },
    { id: 2, title: 'Problem & Solution', icon: Lightbulb, desc: 'What & how you solve' },
    { id: 3, title: 'Market & Audience', icon: Users, desc: 'Who you serve & target scale' },
    { id: 4, title: 'Financials & Goals', icon: DollarSign, desc: 'Monetization & milestones' }
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear validation error when user types
    if (errors[name]) {
      setErrors(prev => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  const validateStep = (step) => {
    const stepErrors = {};
    if (step === 1) {
      if (!formData.businessName.trim()) stepErrors.businessName = 'Business Name is required';
      if (!formData.industry) stepErrors.industry = 'Industry selection is required';
      if (!formData.country.trim()) stepErrors.country = 'Target Country is required';
    } else if (step === 2) {
      if (!formData.problemStatement.trim()) stepErrors.problemStatement = 'Problem Statement is required';
      if (!formData.solution.trim()) stepErrors.solution = 'Solution description is required';
    } else if (step === 3) {
      if (!formData.targetAudience.trim()) stepErrors.targetAudience = 'Target Audience description is required';
      if (!formData.customerSegment.trim()) stepErrors.customerSegment = 'Customer Segment is required';
    } else if (step === 4) {
      if (!formData.revenueModel) stepErrors.revenueModel = 'Revenue Model selection is required';
      if (!formData.pricing.trim()) stepErrors.pricing = 'Pricing Strategy details are required';
      if (!formData.budget.trim()) stepErrors.budget = 'Initial Budget is required';
      if (!formData.fundingRequirement.trim()) stepErrors.fundingRequirement = 'Funding Requirement is required';
      if (!formData.businessGoals.trim()) stepErrors.businessGoals = 'Business Goals are required';
    }

    setErrors(stepErrors);
    return Object.keys(stepErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, steps.length));
    }
  };

  const handlePrev = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validateStep(currentStep)) return;

    setIsSubmitting(true);
    
    // Simulate API call to FastAPI backend
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitComplete(true);
      if (onSubmitSuccess) {
        onSubmitSuccess(formData);
      }
    }, 2000);
  };

  const progressPercentage = (currentStep / steps.length) * 100;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 md:p-8 select-none">
      {/* Background radial effects */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px] animate-pulse-slow"></div>
        <div className="absolute -bottom-[10%] -right-[10%] w-[50%] h-[50%] bg-cyan-500/10 rounded-full blur-[120px] animate-pulse-slow"></div>
      </div>

      <div className="w-full max-w-4xl z-10">
        {/* Header */}
        <div className="text-center mb-8 animate-float">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-purple-500/30 bg-purple-500/5 text-purple-300 text-xs font-semibold tracking-wider uppercase mb-3">
            <Layers className="w-3.5 h-3.5" />
            AI Venture Studio Setup
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-400 via-indigo-200 to-cyan-400 mb-2">
            Formulate Your Venture
          </h1>
          <p className="text-gray-400 max-w-lg mx-auto text-sm md:text-base">
            Provide the foundation of your business idea. Our specialized AI boardroom will analyze, refine, and generate investment-grade blueprints.
          </p>
        </div>

        {/* Wizard Card */}
        <div className="glass rounded-2xl border border-white/5 shadow-2xl overflow-hidden backdrop-blur-xl">
          {/* Progress bar */}
          <div className="w-full h-1 bg-white/5 relative">
            <div 
              className="h-full bg-gradient-to-r from-purple-500 via-indigo-500 to-cyan-500 transition-all duration-500 ease-out"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>

          {/* Form Step Headers */}
          <div className="hidden md:grid grid-cols-4 border-b border-white/5 bg-white/[0.01]">
            {steps.map(step => {
              const Icon = step.icon;
              const isActive = step.id === currentStep;
              const isCompleted = step.id < currentStep;
              return (
                <div 
                  key={step.id} 
                  className={`p-4 flex items-center gap-3 border-r last:border-r-0 border-white/5 transition-colors duration-300 ${
                    isActive ? 'bg-white/[0.03]' : ''
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                    isActive 
                      ? 'bg-purple-500 text-white shadow-[0_0_15px_rgba(168,85,247,0.5)]' 
                      : isCompleted 
                        ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' 
                        : 'bg-white/5 text-gray-500 border border-white/5'
                  }`}>
                    {isCompleted ? <CheckCircle2 className="w-4.5 h-4.5" /> : <Icon className="w-4.5 h-4.5" />}
                  </div>
                  <div>
                    <h3 className={`text-xs font-semibold transition-colors ${
                      isActive ? 'text-purple-300' : isCompleted ? 'text-cyan-400' : 'text-gray-500'
                    }`}>
                      Step {step.id}
                    </h3>
                    <p className={`text-[10px] truncate max-w-[120px] ${isActive ? 'text-white font-medium' : 'text-gray-500'}`}>
                      {step.title}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Form Content */}
          <div className="p-6 md:p-8">
            {submitComplete ? (
              <div className="text-center py-12 flex flex-col items-center justify-center">
                <div className="w-16 h-16 bg-cyan-500/20 border border-cyan-500/30 rounded-full flex items-center justify-center text-cyan-400 mb-6 shadow-[0_0_30px_rgba(6,182,212,0.2)] animate-bounce">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Venture Configured Successfully!</h2>
                <p className="text-gray-400 max-w-md mx-auto mb-8 text-sm">
                  Your business inputs have been stored. The planning agent is ready to design the deliberation blueprint and activate the AI boardroom.
                </p>
                <button
                  onClick={() => window.location.reload()}
                  className="px-6 py-2.5 rounded-lg font-semibold bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600 text-white shadow-lg transition-all"
                >
                  Configure Another Idea
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Step 1: Core Concept */}
                {currentStep === 1 && (
                  <div className="space-y-5 animate-fadeIn">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2 border-b border-white/5 pb-2">
                      <Briefcase className="w-5 h-5 text-purple-400" />
                      Core Venture Details
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Business / Startup Name <span className="text-purple-400">*</span>
                        </label>
                        <input
                          type="text"
                          name="businessName"
                          value={formData.businessName}
                          onChange={handleInputChange}
                          placeholder="e.g. InnovateHQ, EcoSphere"
                          className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                            errors.businessName 
                              ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                          }`}
                        />
                        {errors.businessName && (
                          <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {errors.businessName}
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Industry / Domain <span className="text-purple-400">*</span>
                        </label>
                        <select
                          name="industry"
                          value={formData.industry}
                          onChange={handleInputChange}
                          className={`w-full px-4 py-3 rounded-lg border bg-gray-950 text-white focus:outline-none transition-all ${
                            errors.industry 
                              ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                          }`}
                        >
                          <option value="" className="text-gray-600">Select an industry...</option>
                          {INDUSTRIES.map(ind => (
                            <option key={ind} value={ind}>{ind}</option>
                          ))}
                        </select>
                        {errors.industry && (
                          <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {errors.industry}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Target Location / Country <span className="text-purple-400">*</span>
                        </label>
                        <input
                          type="text"
                          name="country"
                          value={formData.country}
                          onChange={handleInputChange}
                          placeholder="e.g. United States, Global, India"
                          className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                            errors.country 
                              ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                          }`}
                        />
                        {errors.country && (
                          <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {errors.country}
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Optional Notes / Context
                        </label>
                        <input
                          type="text"
                          name="optionalNotes"
                          value={formData.optionalNotes}
                          onChange={handleInputChange}
                          placeholder="e.g. Hyper-local focus, B2B SaaS background"
                          className="w-full px-4 py-3 rounded-lg border border-white/10 bg-white/[0.02] text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20 transition-all placeholder:text-gray-600"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 2: Problem & Solution */}
                {currentStep === 2 && (
                  <div className="space-y-5 animate-fadeIn">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2 border-b border-white/5 pb-2">
                      <Lightbulb className="w-5 h-5 text-yellow-400" />
                      Problem & Solution Framing
                    </h2>

                    <div>
                      <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                        Problem Statement <span className="text-purple-400">*</span>
                      </label>
                      <textarea
                        name="problemStatement"
                        value={formData.problemStatement}
                        onChange={handleInputChange}
                        rows="3"
                        placeholder="What specific paint point or friction does your target market experience? Make it quantitative if possible."
                        className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 resize-none ${
                          errors.problemStatement 
                            ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                        }`}
                      />
                      {errors.problemStatement && (
                        <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" /> {errors.problemStatement}
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                        Your Solution <span className="text-purple-400">*</span>
                      </label>
                      <textarea
                        name="solution"
                        value={formData.solution}
                        onChange={handleInputChange}
                        rows="3"
                        placeholder="How does your product/service uniquely resolve this problem? Highlight core features or unique value props."
                        className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 resize-none ${
                          errors.solution 
                            ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                            : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                        }`}
                      />
                      {errors.solution && (
                        <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" /> {errors.solution}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Step 3: Market & Audience */}
                {currentStep === 3 && (
                  <div className="space-y-5 animate-fadeIn">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2 border-b border-white/5 pb-2">
                      <Users className="w-5 h-5 text-cyan-400" />
                      Target Market & Customer Segments
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Target Audience / Ideal Buyer <span className="text-purple-400">*</span>
                        </label>
                        <input
                          type="text"
                          name="targetAudience"
                          value={formData.targetAudience}
                          onChange={handleInputChange}
                          placeholder="e.g. Sales Directors, Busy Parents, College Students"
                          className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                            errors.targetAudience 
                              ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                          }`}
                        />
                        {errors.targetAudience && (
                          <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {errors.targetAudience}
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Customer Segment Profile <span className="text-purple-400">*</span>
                        </label>
                        <input
                          type="text"
                          name="customerSegment"
                          value={formData.customerSegment}
                          onChange={handleInputChange}
                          placeholder="e.g. B2B Mid-Market Enterprise, B2C Tech Adopters"
                          className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                            errors.customerSegment 
                              ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                          }`}
                        />
                        {errors.customerSegment && (
                          <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {errors.customerSegment}
                          </p>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                        Growth Expectations & TAM Scale
                      </label>
                      <textarea
                        name="growthExpectations"
                        value={formData.growthExpectations}
                        onChange={handleInputChange}
                        rows="2"
                        placeholder="Define target growth metrics (e.g., 20% MoM, $50M TAM in 3 years, viral expansion loops)."
                        className="w-full px-4 py-3 rounded-lg border border-white/10 bg-white/[0.02] text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20 transition-all placeholder:text-gray-600 resize-none"
                      />
                    </div>
                  </div>
                )}

                {/* Step 4: Financials & Goals */}
                {currentStep === 4 && (
                  <div className="space-y-5 animate-fadeIn">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2 border-b border-white/5 pb-2">
                      <DollarSign className="w-5 h-5 text-emerald-400" />
                      Financial Assumptions & Milestones
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Revenue Model <span className="text-purple-400">*</span>
                        </label>
                        <select
                          name="revenueModel"
                          value={formData.revenueModel}
                          onChange={handleInputChange}
                          className={`w-full px-4 py-3 rounded-lg border bg-gray-950 text-white focus:outline-none transition-all ${
                            errors.revenueModel 
                              ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                          }`}
                        >
                          <option value="">Select monetization style...</option>
                          {REVENUE_MODELS.map(model => (
                            <option key={model} value={model}>{model}</option>
                          ))}
                        </select>
                        {errors.revenueModel && (
                          <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {errors.revenueModel}
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Pricing Strategy <span className="text-purple-400">*</span>
                        </label>
                        <input
                          type="text"
                          name="pricing"
                          value={formData.pricing}
                          onChange={handleInputChange}
                          placeholder="e.g. $49/mo basic tier, 5% transactional fee"
                          className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                            errors.pricing 
                              ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                          }`}
                        />
                        {errors.pricing && (
                          <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {errors.pricing}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Launch Budget ($) <span className="text-purple-400">*</span>
                        </label>
                        <input
                          type="number"
                          name="budget"
                          value={formData.budget}
                          onChange={handleInputChange}
                          placeholder="e.g. 50000"
                          className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                            errors.budget 
                              ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                          }`}
                        />
                        {errors.budget && (
                          <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {errors.budget}
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                          Funding Requirement <span className="text-purple-400">*</span>
                        </label>
                        <input
                          type="text"
                          name="fundingRequirement"
                          value={formData.fundingRequirement}
                          onChange={handleInputChange}
                          placeholder="e.g. Bootstrapped, $150k pre-seed"
                          className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                            errors.fundingRequirement 
                              ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                              : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                          }`}
                        />
                        {errors.fundingRequirement && (
                          <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {errors.fundingRequirement}
                          </p>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                        Core Business Goals / Milestones <span className="text-purple-400">*</span>
                      </label>
                      <textarea
                        name="businessGoals"
                        value={formData.businessGoals}
                        onChange={handleInputChange}
                        rows="3"
                        placeholder="Specify key short-term achievements (e.g. Build MVP in 3 months, sign first 10 pilot clients, establish partner deals)."
                        className={`w-full px-4 py-3 rounded-lg border bg-white/[0.02] text-white focus:outline-none transition-all placeholder:text-gray-600 resize-none ${
                          errors.businessGoals 
                            ? 'border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/20' 
                            : 'border-white/10 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20'
                        }`}
                      />
                      {errors.businessGoals && (
                        <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" /> {errors.businessGoals}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Footer Controls */}
                <div className="flex items-center justify-between border-t border-white/5 pt-6 mt-8">
                  <button
                    type="button"
                    onClick={handlePrev}
                    disabled={currentStep === 1 || isSubmitting}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold border border-white/10 transition-all ${
                      currentStep === 1
                        ? 'opacity-40 cursor-not-allowed text-gray-500'
                        : 'text-white bg-white/5 hover:bg-white/10'
                    }`}
                  >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                  </button>

                  <div className="flex items-center gap-2">
                    {currentStep < steps.length ? (
                      <button
                        type="button"
                        onClick={handleNext}
                        className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold text-white bg-purple-500 hover:bg-purple-600 shadow-[0_0_15px_rgba(168,85,247,0.3)] transition-all"
                      >
                        Next Step
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-semibold text-white bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-purple-600 hover:to-cyan-600 shadow-[0_0_20px_rgba(168,85,247,0.4)] transition-all"
                      >
                        {isSubmitting ? (
                          <>
                            <span className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin"></span>
                            Creating Workspace...
                          </>
                        ) : (
                          <>
                            Initialize Venture Board
                            <CheckCircle2 className="w-4 h-4" />
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
