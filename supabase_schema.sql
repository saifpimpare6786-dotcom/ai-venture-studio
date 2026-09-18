-- ============================================================================
-- AI VENTURE STUDIO — SUPABASE POSTGRESQL SCHEMA & ROW LEVEL SECURITY (RLS)
-- Version: 2.2.0 (ECC Universal Edition)
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. PROFILES TABLE (User Accounts & Authentication Extension)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    organization TEXT,
    role TEXT DEFAULT 'founder',
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. PROJECTS TABLE (14-Field Startup Intake Metadata)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    industry TEXT NOT NULL,
    target_country TEXT DEFAULT 'United States' NOT NULL,
    currency TEXT DEFAULT 'USD' NOT NULL,
    stage TEXT DEFAULT 'idea' NOT NULL,
    problem_statement TEXT NOT NULL,
    solution_description TEXT NOT NULL,
    target_customers TEXT NOT NULL,
    customer_segment TEXT,
    competitors TEXT,
    revenue_model TEXT NOT NULL,
    pricing_strategy TEXT,
    budget NUMERIC(15, 2) DEFAULT 0,
    preferred_funding NUMERIC(15, 2) DEFAULT 0,
    team_size INT DEFAULT 1,
    timeline TEXT DEFAULT '12 months',
    goals TEXT[] DEFAULT ARRAY[]::TEXT[],
    notes TEXT,
    status TEXT DEFAULT 'draft' NOT NULL, -- draft, deliberating, completed, failed
    overall_score NUMERIC(5, 2),
    viability_score NUMERIC(5, 2),
    market_fit_score NUMERIC(5, 2),
    financial_score NUMERIC(5, 2),
    is_valid_rules BOOLEAN DEFAULT true,
    rules_validation JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 3. DOCUMENTS TABLE (Uploaded Pitch Decks, Financial Models & PDFs)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL, -- xlsx, csv, pdf, docx, pptx
    category TEXT DEFAULT 'general', -- financial_model, pitch_deck, research, market_data
    storage_path TEXT,
    size_bytes BIGINT NOT NULL,
    sha256_hash TEXT,
    chunk_count INT DEFAULT 0,
    status TEXT DEFAULT 'pending' NOT NULL, -- pending, parsed, indexed, error
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. REPORTS TABLE (The 13 Executive Report Deliverables)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
    report_type TEXT NOT NULL, -- executive_summary, business_plan, swot, pestle, etc.
    title TEXT NOT NULL,
    content JSONB NOT NULL, -- Full structured Pydantic schema
    scores JSONB DEFAULT '{}'::jsonb,
    version INT DEFAULT 1,
    status TEXT DEFAULT 'generated' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT unique_project_report UNIQUE(project_id, report_type)
);

-- ----------------------------------------------------------------------------
-- 5. SIMULATIONS TABLE (Interactive What-If Financial Scenarios)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.simulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
    scenario_name TEXT NOT NULL, -- base_case, bull_case, bear_case, custom
    parameters JSONB NOT NULL, -- pricing, cac, churn, growth, headcount, margin
    projections JSONB NOT NULL, -- 36-month MRR/ARR, cash flow, runway, unit economics
    ai_commentary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 6. AGENT_LOGS TABLE (Deliberation Step Outputs & Tokens)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
    agent_name TEXT NOT NULL, -- finance, strategy, marketing, risk, council, critic
    node_type TEXT NOT NULL,
    status TEXT DEFAULT 'completed' NOT NULL,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    duration_ms INT DEFAULT 0,
    llm_provider TEXT,
    llm_model TEXT,
    summary TEXT,
    payload JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 7. AGENT_DISCUSSIONS TABLE (Real-Time Boardroom Council Messages)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.agent_discussions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE NOT NULL,
    agent_name TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    message_content TEXT NOT NULL,
    reply_to TEXT,
    step_index INT DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ----------------------------------------------------------------------------
-- PERFORMANCE COMPOSITE INDEXES (ECC Postgres Patterns)
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_projects_user_status ON public.projects(user_id, status);
CREATE INDEX IF NOT EXISTS idx_documents_project_status ON public.documents(project_id, status);
CREATE INDEX IF NOT EXISTS idx_reports_project_type ON public.reports(project_id, report_type);
CREATE INDEX IF NOT EXISTS idx_simulations_project ON public.simulations(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_project_ts ON public.agent_logs(project_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_agent_discussions_project_step ON public.agent_discussions(project_id, step_index);

-- ----------------------------------------------------------------------------
-- MIGRATION SAFETY: Ensure existing tables have all recent columns
-- ----------------------------------------------------------------------------
ALTER TABLE IF EXISTS public.projects 
    ADD COLUMN IF NOT EXISTS overall_score NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS viability_score NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS market_fit_score NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS financial_score NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS is_valid_rules BOOLEAN DEFAULT true,
    ADD COLUMN IF NOT EXISTS rules_validation JSONB DEFAULT '{}'::jsonb;

ALTER TABLE IF EXISTS public.reports 
    ADD COLUMN IF NOT EXISTS title TEXT DEFAULT 'Executive Report',
    ADD COLUMN IF NOT EXISTS scores JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;

ALTER TABLE IF EXISTS public.agent_discussions 
    ADD COLUMN IF NOT EXISTS agent_role TEXT DEFAULT 'Advisor',
    ADD COLUMN IF NOT EXISTS reply_to TEXT,
    ADD COLUMN IF NOT EXISTS step_index INT DEFAULT 0;

-- ----------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) POLICIES (Idempotent Drops & Creates)
-- ----------------------------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.simulations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_discussions ENABLE ROW LEVEL SECURITY;

-- Profiles: Users manage their own profile
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Projects: Users manage their own projects
DROP POLICY IF EXISTS "Users can manage own projects" ON public.projects;
CREATE POLICY "Users can manage own projects" ON public.projects FOR ALL USING (auth.uid() = user_id);

-- Documents: Users access documents of their projects
DROP POLICY IF EXISTS "Users can manage own project documents" ON public.documents;
CREATE POLICY "Users can manage own project documents" ON public.documents FOR ALL USING (
    EXISTS (SELECT 1 FROM public.projects WHERE projects.id = documents.project_id AND projects.user_id = auth.uid())
);

-- Reports: Users view reports of their projects
DROP POLICY IF EXISTS "Users can view own project reports" ON public.reports;
CREATE POLICY "Users can view own project reports" ON public.reports FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.projects WHERE projects.id = reports.project_id AND projects.user_id = auth.uid())
);

-- Simulations: Users manage simulations of their projects
DROP POLICY IF EXISTS "Users can manage own project simulations" ON public.simulations;
CREATE POLICY "Users can manage own project simulations" ON public.simulations FOR ALL USING (
    EXISTS (SELECT 1 FROM public.projects WHERE projects.id = simulations.project_id AND projects.user_id = auth.uid())
);

-- Agent Logs & Discussions: Users view logs of their projects
DROP POLICY IF EXISTS "Users can view own project logs" ON public.agent_logs;
CREATE POLICY "Users can view own project logs" ON public.agent_logs FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.projects WHERE projects.id = agent_logs.project_id AND projects.user_id = auth.uid())
);

DROP POLICY IF EXISTS "Users can view own project discussions" ON public.agent_discussions;
CREATE POLICY "Users can view own project discussions" ON public.agent_discussions FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.projects WHERE projects.id = agent_discussions.project_id AND projects.user_id = auth.uid())
);

-- ----------------------------------------------------------------------------
-- REFRESH SCHEMA CACHE
-- ----------------------------------------------------------------------------
NOTIFY pgrst, 'reload schema';
