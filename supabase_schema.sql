-- SQL Schema Migrations for AI Venture Studio
-- Copy and paste this into the Supabase SQL Editor (https://supabase.com)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Profiles Table (linking to Supabase Auth users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read profile details" 
    ON public.profiles FOR SELECT USING (true);

CREATE POLICY "Users can update their own profile details" 
    ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- 2. Projects Table
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    idea_input TEXT NOT NULL,
    description TEXT,
    stage VARCHAR(50) DEFAULT 'Ideation',
    target_customers VARCHAR(255),
    budget NUMERIC(12, 2),
    revenue_model VARCHAR(100),
    timeline VARCHAR(100),
    team_size INT DEFAULT 1,
    goals TEXT[],
    preferred_funding VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read their own projects" 
    ON public.projects FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own projects" 
    ON public.projects FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own projects" 
    ON public.projects FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own projects" 
    ON public.projects FOR DELETE USING (auth.uid() = user_id);

-- 3. Documents Table
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    storage_path TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    status VARCHAR(50) DEFAULT 'Processing',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read documents of their projects" 
    ON public.documents FOR SELECT USING (
        auth.uid() IN (SELECT user_id FROM public.projects WHERE id = documents.project_id)
    );

CREATE POLICY "Users can insert documents into their projects" 
    ON public.documents FOR INSERT WITH CHECK (
        auth.uid() IN (SELECT user_id FROM public.projects WHERE id = documents.project_id)
    );

CREATE POLICY "Users can delete documents from their projects" 
    ON public.documents FOR DELETE USING (
        auth.uid() IN (SELECT user_id FROM public.projects WHERE id = documents.project_id)
    );

-- 4. Reports Table
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    report_type VARCHAR(100) NOT NULL,
    content JSONB NOT NULL,
    scores JSONB,
    status VARCHAR(50) DEFAULT 'Draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read reports of their projects" 
    ON public.reports FOR SELECT USING (
        auth.uid() IN (SELECT user_id FROM public.projects WHERE id = reports.project_id)
    );

-- 5. Agent Logs Table (real-time stream tracking)
CREATE TABLE IF NOT EXISTS public.agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.agent_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view agent logs of their projects" 
    ON public.agent_logs FOR SELECT USING (
        auth.uid() IN (SELECT user_id FROM public.projects WHERE id = agent_logs.project_id)
    );

-- 6. Agent Discussions Table
CREATE TABLE IF NOT EXISTS public.agent_discussions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    message_content TEXT NOT NULL,
    reply_to VARCHAR(100),
    step_index INT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.agent_discussions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view agent discussions of their projects" 
    ON public.agent_discussions FOR SELECT USING (
        auth.uid() IN (SELECT user_id FROM public.projects WHERE id = agent_discussions.project_id)
    );
